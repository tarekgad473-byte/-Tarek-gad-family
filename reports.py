from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from models.db_models import Employee, Request, SalaryRecord, User
from database import get_db
from routers.auth import get_current_user
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

router = APIRouter()

@router.get("/weekly")
async def weekly_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["super_admin", "hr_manager", "factory_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    requests = db.query(Request).filter(Request.created_at >= week_ago).all()
    
    return {
        "period": "weekly",
        "total_requests": len(requests),
        "approved": len([r for r in requests if r.status == "approved"]),
        "pending": len([r for r in requests if r.status == "pending"]),
        "rejected": len([r for r in requests if r.status == "rejected"]),
        "by_type": {
            "leave": len([r for r in requests if r.request_type == "leave"]),
            "mission": len([r for r in requests if r.request_type == "mission"]),
            "bonus": len([r for r in requests if r.request_type == "bonus"]),
            "penalty": len([r for r in requests if r.request_type == "penalty"]),
            "overtime": len([r for r in requests if r.request_type == "overtime"]),
            "meal_allowance": len([r for r in requests if r.request_type == "meal_allowance"]),
            "loan": len([r for r in requests if r.request_type == "loan"])
        }
    }

@router.get("/monthly")
async def monthly_report(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["super_admin", "hr_manager", "factory_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    salary_records = db.query(SalaryRecord).filter(
        SalaryRecord.month == month,
        SalaryRecord.year == year
    ).all()
    
    total_salaries = sum([r.total_salary for r in salary_records])
    total_bonuses = sum([r.bonuses for r in salary_records])
    total_deductions = sum([r.deductions for r in salary_records])
    
    return {
        "period": "monthly",
        "month": month,
        "year": year,
        "total_employees": len(salary_records),
        "total_salaries": total_salaries,
        "total_bonuses": total_bonuses,
        "total_deductions": total_deductions
    }

@router.get("/annual")
async def annual_report(
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["super_admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    salary_records = db.query(SalaryRecord).filter(SalaryRecord.year == year).all()
    
    total_salaries = sum([r.total_salary for r in salary_records])
    monthly_breakdown = {}
    for i in range(1, 13):
        month_records = [r for r in salary_records if r.month == i]
        monthly_breakdown[i] = sum([r.total_salary for r in month_records])
    
    return {
        "period": "annual",
        "year": year,
        "total_salaries": total_salaries,
        "monthly_breakdown": monthly_breakdown
    }

@router.get("/export/excel")
async def export_to_excel(
    report_type: str,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["super_admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="Not authorize