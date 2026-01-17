from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from models.schemas import RequestCreate, RequestResponse, RequestUpdate
from models.db_models import Request, User, Employee
from database import get_db
from routers.auth import get_current_user
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    request_data: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    new_request = Request(
        **request_data.dict(),
        employee_id=employee.id,
        status="pending",
        current_approver_level=1
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/", response_model=List[RequestResponse])
async def get_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Request)
    
    if current_user.role == "employee":
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if employee:
            query = query.filter(Request.employee_id == employee.id)
    
    if status:
        query = query.filter(Request.status == status)
    if request_type:
        query = query.filter(Request.request_type == request_type)
    
    requests = query.offset(skip).limit(limit).all()
    return requests

@router.get("/pending-approval", response_model=List[RequestResponse])
async def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role_level_map = {
        "supervisor": 1,
        "department_manager": 2,
        "factory_manager": 3,
        "hr_manager": 4
    }
    
    if current_user.role not in role_level_map:
        return []
    
    level = role_level_map[current_user.role]
    requests = db.query(Request).filter(
        Request.status == "pending",
        Request.current_approver_level == level
    ).all()
    return requests

@router.put("/{request_id}/approve", response_model=RequestResponse)
async def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role_level_map = {
        "supervisor": 1,
        "department_manager": 2,
        "factory_manager": 3,
        "hr_manager": 4
    }
    
    if current_user.role not in role_level_map:
        raise HTTPException(status_code=403, detail="Not authorized to approve")
    
    request_obj = db.query(Request).filter(Request.id == request_id).first()
    if not request_obj:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request_obj.current_approver_level != role_level_map[current_user.role]:
        raise HTTPException(status_code=403, detail="Not your turn to approve")
    
    if request_obj.current_approver_level < 4:
        request_obj.current_approver_level += 1
    else:
        request_obj.status = "approved"
        request_obj.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(request_obj)
    return request_obj

@router.put("/{request_id}/reject", response_model=RequestResponse)
async def reject_request(
    request_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role_level_map = {
        "supervisor": 1,
        "department_manager": 2,
        "factory_manager": 3,
        "hr_manager": 4
    }
    
    if current_user.role not in role_level_map:
        raise HTTPException(status_code=403, detail="Not authorized to reject")
    
    request_obj = db.query(Request).filter(Request.id == request_id).first()
    if not request_obj:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request_obj.current_approver_level != role_level_map[current_user.role]:
        raise HTTPException(status_code=403, detail="Not your turn to reject")
    
    request_obj.status = "rejected"
    request_obj.rejection_reason = reason
    db.commit()
    db.refresh(request_obj)
    return request_obj
