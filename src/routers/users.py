from fastapi import APIRouter, Request, HTTPException
from typing import List
from src.core.decorators.response import handle_request
from src.core.responses.schemas import (
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse
)
from src.core.schemas.user import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("")
@handle_request
async def list_users(
    request: Request,
    page: int = 1,
    page_size: int = 20
) -> dict:
    users = [User(username=f"user{i}", hashed_password="hash") for i in range(page_size)]
    total = 100

    request.state.pagination = PaginationInfo(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size
    )

    return users

@router.get("/{user_id}")
@handle_request
async def get_user(request: Request, user_id: int) -> dict:
    if user_id <= 0:
        raise ValueError("Invalid user ID")

    if user_id > 100:
        raise HTTPException(status_code=404, detail="User not found")

    return User(username=f"user{user_id}", hashed_password="hash")

@router.post("")
@handle_request
async def create_user(request: Request, user_data: User) -> dict:
    return user_data
