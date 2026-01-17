from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.schemas import SalaryRecordResponse, SalaryCalculation
from models.db_models import SalaryRecord, Employee, Request, User
from database import get_db
from routers.auth import get_current_user
from datetime import datetime
from decimal import Decimal

router = APIRouter()

@router.post("/calculate/{employee_id}", response_model=SalaryCalculation)
async def calculate_salary(
    employee_id: int,
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["super_admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    base_salary = Decimal(str(employee.salary))
    bonuses = Decimal("0")
    deductions = Decimal("0")
    overtime_pay = Decimal("0")
    meal_allowance = Decimal("0")
    
    approved_requests = db.query(Request).filter(
        Request.employee_id == employee_id,
        Request.status == "approved"
    ).all()
    
    for req in approved_requests:
        if req.request_type == "bonus" and req.amount:
            bonuses += Decimal(str(req.amount))
        elif req.request_type == "penalty" and req.amount:
            deductions += Decimal(str(req.amount))
        elif req.request_type == "overtime" and req.amount:
            overtime_pay += Decimal(str(req.amount))
        elif req.request_type == "meal_allowance" and req.amount:
            meal_allowance += Decimal(str(req.amount))
        elif req.request_type == "loan" and req.amount:
            deductions += Decimal(str(req.amount))
    
    total_salary = base_salary + bonuses + overtime_pay + meal_allowance - deductions
    
    return {
        "employee_id": employee_id,
        "month": month,
        "year": year,
        "base_salary": float(base_salary),
        "bonuses": float(bonuses),
        "deductions": float(deductions),
        "overtime_pay": float(overtime_pay),
        "meal_allowance": float(meal_allowance),
        "total_salary": float(total_salary)
    }

@router.post("/records", response_model=SalaryRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_salary_record(
    salary_calc: SalaryCalculation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["super_admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_record = SalaryRecord(**salary_calc.dict())
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@router.get("/records/{employee_id}", response_model=List[SalaryRecordResponse])
async def get_salary_records(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    records = db.query(SalaryRecord).filter(SalaryRecord.employee_id == employee_id).all()
    return records
