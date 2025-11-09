from fastapi import APIRouter, Depends, status

router = APIRouter(
    prefix="/shift-assignments", tags=["Shift Assignments"]
)