from fastapi import APIRouter
from routers import auth, employees, requests, departments, reports, notifications, salary

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(employees.router, prefix="/employees", tags=["Employees"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(salary.router, prefix="/salary", tags=["Salary"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
