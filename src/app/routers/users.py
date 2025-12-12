"""User profile management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from src.app.dependencies import get_current_user, get_db
from src.app.schemas.user import (
    UserResponse, UserProfileUpdate, UserPreferencesUpdate, PasswordChange
)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get current user profile"""
    return current_user


@router.put("/me/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update user profile"""
    updated_user = db.update_user_profile(
        current_user["id"],
        **profile_data.dict(exclude_unset=True)
    )
    return updated_user


@router.put("/me/preferences", response_model=UserResponse)
async def update_preferences(
    preferences: UserPreferencesUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update user preferences"""
    updated_user = db.update_user_preferences(
        current_user["id"],
        **preferences.dict(exclude_unset=True)
    )
    return updated_user


@router.post("/me/password")
async def change_password(
    password_data: PasswordChange,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    user = db.authenticate_user(current_user["username"], password_data.current_password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid current password")
    
    db.change_password(current_user["id"], password_data.new_password)
    return {"message": "Password changed successfully"}


@router.delete("/me/data")
async def clear_user_data(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Clear all user data (transactions and accounts)"""
    db.clear_user_data(current_user["id"])
    return {"message": "User data cleared successfully"}


@router.delete("/me")
async def delete_account(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete user account"""
    db.delete_user(current_user["id"])
    return {"message": "Account deleted successfully"}
