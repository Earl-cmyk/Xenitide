from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.db.client import supabase_client
from app.core.security import create_access_token, get_password_hash, verify_password
from app.schemas.auth import UserSignup, UserLogin, UserResponse, AuthResponse
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""
    
    async def signup(self, user_data: UserSignup) -> AuthResponse:
        """
        Register a new user
        """
        try:
            # Create user in Supabase Auth
            auth_result = supabase_client.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "username": user_data.username
                    }
                }
            })
            
            if auth_result.user is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user"
                )
            
            # Create user record in our users table
            user_record = {
                "id": auth_result.user.id,
                "email": auth_result.user.email,
                "username": user_data.username,
                "created_at": datetime.utcnow().isoformat()
            }
            
            await supabase_client.insert_record('users', user_record)
            
            # Create access token
            access_token = create_access_token(
                data={"sub": auth_result.user.id, "email": auth_result.user.email}
            )
            
            return AuthResponse(
                user=UserResponse(
                    id=auth_result.user.id,
                    email=auth_result.user.email,
                    username=user_data.username,
                    created_at=auth_result.user.created_at
                ),
                access_token=access_token,
                refresh_token=auth_result.session.refresh_token if auth_result.session else "",
                expires_in=24 * 3600  # 24 hours in seconds
            )
            
        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            if hasattr(e, 'message') and e.message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=e.message
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def login(self, login_data: UserLogin) -> AuthResponse:
        """
        Authenticate user and return tokens
        """
        try:
            # Sign in with Supabase Auth
            auth_result = supabase_client.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if auth_result.user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Get user data from our database
            result = await supabase_client.select_records(
                'users',
                {'id': auth_result.user.id},
                columns='id, email, username, created_at'
            )
            
            if not result.data:
                # Create user record if it doesn't exist
                user_record = {
                    "id": auth_result.user.id,
                    "email": auth_result.user.email,
                    "username": auth_result.user.user_metadata.get('username'),
                    "created_at": auth_result.user.created_at
                }
                await supabase_client.insert_record('users', user_record)
                user_data = user_record
            else:
                user_data = result.data[0]
            
            # Create access token
            access_token = create_access_token(
                data={"sub": auth_result.user.id, "email": auth_result.user.email}
            )
            
            return AuthResponse(
                user=UserResponse(**user_data),
                access_token=access_token,
                refresh_token=auth_result.session.refresh_token,
                expires_in=24 * 3600
            )
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            if hasattr(e, 'message') and e.message:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=e.message
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    
    async def logout(self, token: str) -> bool:
        """
        Logout user and invalidate token
        """
        try:
            # Sign out from Supabase Auth
            supabase_client.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        """
        Refresh access token using refresh token
        """
        try:
            # Refresh session with Supabase Auth
            auth_result = supabase_client.auth.refresh_session(refresh_token)
            
            if auth_result.user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Get user data
            result = await supabase_client.select_records(
                'users',
                {'id': auth_result.user.id},
                columns='id, email, username, created_at'
            )
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            user_data = result.data[0]
            
            # Create new access token
            access_token = create_access_token(
                data={"sub": auth_result.user.id, "email": auth_result.user.email}
            )
            
            return AuthResponse(
                user=UserResponse(**user_data),
                access_token=access_token,
                refresh_token=auth_result.session.refresh_token,
                expires_in=24 * 3600
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token"
            )
    
    async def reset_password(self, email: str) -> bool:
        """
        Send password reset email
        """
        try:
            supabase_client.auth.reset_password_email(email)
            return True
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return False
    
    async def update_password(self, token: str, new_password: str) -> bool:
        """
        Update password using reset token
        """
        try:
            # This would need to be implemented based on Supabase's password reset flow
            # For now, return a placeholder
            return True
        except Exception as e:
            logger.error(f"Password update error: {str(e)}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[UserResponse]:
        """
        Get user profile
        """
        try:
            result = await supabase_client.select_records(
                'users',
                {'id': user_id},
                columns='id, email, username, created_at'
            )
            
            if result.data:
                return UserResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Get user profile error: {str(e)}")
            return None
    
    async def update_user_profile(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[UserResponse]:
        """
        Update user profile
        """
        try:
            result = await supabase_client.update_record(
                'users',
                {'id': user_id},
                updates
            )
            
            if result.data:
                return UserResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Update user profile error: {str(e)}")
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user account
        """
        try:
            # Delete user from our database
            await supabase_client.delete_record('users', {'id': user_id})
            
            # Delete from Supabase Auth (this might need admin access)
            # supabase_client.admin.auth.admin.delete_user(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Delete user error: {str(e)}")
            return False
    
    async def create_api_key(
        self, 
        user_id: str, 
        name: str, 
        project_id: Optional[str] = None,
        expires_in_days: int = 365
    ) -> Dict[str, Any]:
        """
        Create API key for user
        """
        try:
            from app.core.security import create_api_key
            
            api_key = create_api_key(user_id, project_id)
            
            # Store API key in database (you might want to create a separate table for this)
            api_key_record = {
                "user_id": user_id,
                "project_id": project_id,
                "name": name,
                "api_key": api_key,
                "expires_at": (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # This would require an api_keys table
            # await supabase_client.insert_record('api_keys', api_key_record)
            
            return {
                "api_key": api_key,
                "name": name,
                "expires_at": api_key_record["expires_at"]
            }
            
        except Exception as e:
            logger.error(f"Create API key error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )


# Global service instance
auth_service = AuthService()
