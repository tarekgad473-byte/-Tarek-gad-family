from fastapi import APIRouter
from routers import auth, employees, requests, departments, reports, notifications, salary

api_router = APIRouter()

apirouter.includerouter(auth.router, prefix="/auth", tags=["Authentication"])
apirouter.includerouter(employees.router, prefix="/employees", tags=["Employees"])
apirouter.includerouter(departments.router, prefix="/departments", tags=["Departments"])
apirouter.includerouter(requests.router, prefix="/requests", tags=["Requests"])
apirouter.includerouter(salary.router, prefix="/salary", tags=["Salary"])
apirouter.includerouter(reports.router, prefix="/reports", tags=["Reports"])
apirouter.includerouter(notifications.router, prefix="/notifications", tags=["Notifications"])
