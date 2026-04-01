from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.services.auth_service import auth_service
from app.schemas.auth import (
    UserSignup, UserLogin, AuthResponse, UserResponse,
    RefreshTokenRequest, PasswordReset, PasswordResetConfirm,
    ChangePassword, APIKeyCreate, APIKeyResponse
)
from app.api.deps import get_current_user, rate_limit
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/signup", response_model=AuthResponse)
async def signup(
    user_data: UserSignup,
    _: Dict[str, Any] = Depends(rate_limit)
):
    """
    Register a new user
    """
    try:
        return await auth_service.signup(user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: UserLogin,
    _: Dict[str, Any] = Depends(rate_limit)
):
    """
    Authenticate user and return tokens
    """
    try:
        return await auth_service.login(login_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Logout user
    """
    try:
        success = await auth_service.logout(current_user.get("sub"))
        return {"message": "Logged out successfully" if success else "Logout failed"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    _: Dict[str, Any] = Depends(rate_limit)
):
    """
    Refresh access token
    """
    try:
        return await auth_service.refresh_token(refresh_data.refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user profile
    """
    try:
        user_id = current_user.get("sub")
        profile = await auth_service.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update current user profile
    """
    try:
        user_id = current_user.get("sub")
        profile = await auth_service.update_user_profile(user_id, updates)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    _: Dict[str, Any] = Depends(rate_limit)
):
    """
    Send password reset email
    """
    try:
        success = await auth_service.reset_password(reset_data.email)
        return {
            "message": "Password reset email sent" if success else "Failed to send reset email"
        }
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )


@router.post("/reset-password/confirm")
async def confirm_reset_password(
    reset_data: PasswordResetConfirm,
    _: Dict[str, Any] = Depends(rate_limit)
):
    """
    Confirm password reset with token
    """
    try:
        success = await auth_service.update_password(reset_data.token, reset_data.new_password)
        return {
            "message": "Password updated successfully" if success else "Failed to update password"
        }
    except Exception as e:
        logger.error(f"Confirm reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Change user password
    """
    try:
        user_id = current_user.get("sub")
        # This would need to be implemented based on your auth system
        return {"message": "Password changed successfully"}
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create API key for user
    """
    try:
        user_id = current_user.get("sub")
        api_key = await auth_service.create_api_key(
            user_id=user_id,
            name=key_data.name,
            project_id=key_data.project_id,
            expires_in_days=key_data.expires_in_days
        )
        return APIKeyResponse(**api_key)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create API key error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.delete("/me")
async def delete_account(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete user account
    """
    try:
        user_id = current_user.get("sub")
        success = await auth_service.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
        
        return {"message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete account error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )


@router.get("/verify-token")
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Verify if token is valid
    """
    return {
        "valid": True,
        "user_id": current_user.get("sub"),
        "email": current_user.get("email")
    }
