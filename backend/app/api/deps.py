from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token, verify_api_key
from app.db.client import supabase_client
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer for JWT tokens
security = HTTPBearer()

# HTTP Bearer for API keys
api_key_security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    """
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Verify user exists in database
        try:
            result = await supabase_client.select_records(
                'users',
                {'id': user_id},
                columns='id, email, username, created_at'
            )
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            user_data = result.data[0]
            return {
                **payload,
                **user_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching user data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User verification failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(api_key_security)
) -> Optional[Dict[str, Any]]:
    """
    Optional dependency to get current user (doesn't raise exception if not authenticated)
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_current_user_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(api_key_security)
) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current user from API key or JWT token
    """
    if credentials is None:
        return None
    
    # Try to verify as API key first
    try:
        payload = verify_api_key(credentials.credentials)
        return {
            "sub": payload.get("user_id"),
            "project_id": payload.get("project_id"),
            "auth_type": "api_key",
            **payload
        }
    except HTTPException:
        # If not API key, try as JWT token
        try:
            return await get_current_user(credentials)
        except HTTPException:
            return None


async def require_project_access(
    project_id: str,
    required_role: str = "viewer",
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to require project access with specific role
    """
    user_id = current_user.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    # Check project permission
    has_permission = await supabase_client.check_project_permission(
        project_id, user_id, required_role
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions for project. Required role: {required_role}"
        )
    
    return {
        **current_user,
        "project_id": project_id,
        "project_role": required_role
    }


async def require_project_owner(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to require project owner access
    """
    return await require_project_access(project_id, "owner", current_user)


async def require_project_editor(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to require project editor access
    """
    return await require_project_access(project_id, "editor", current_user)


def get_pagination_params(
    page: int = 1,
    size: int = 20,
    max_size: int = 100
) -> Dict[str, int]:
    """
    Get pagination parameters with validation
    """
    if page < 1:
        page = 1
    
    if size < 1:
        size = 20
    elif size > max_size:
        size = max_size
    
    offset = (page - 1) * size
    
    return {
        "page": page,
        "size": size,
        "offset": offset
    }


def get_sort_params(
    sort_by: Optional[str] = None,
    order: Optional[str] = "desc"
) -> Dict[str, str]:
    """
    Get sorting parameters with validation
    """
    if order not in ["asc", "desc"]:
        order = "desc"
    
    if not sort_by:
        return {"order": "created_at.desc"}
    
    return {"order": f"{sort_by}.{order}"}


async def validate_project_exists(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate that project exists and user has access
    """
    try:
        result = await supabase_client.select_records(
            'projects',
            {'id': project_id},
            columns='id, name, owner_id'
        )
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = result.data[0]
        
        # Check if user is owner or member
        await require_project_access(project_id, "viewer", current_user)
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating project"
        )


class RateLimiter:
    """
    Simple rate limiter for API endpoints
    """
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    def is_allowed(self, key: str) -> bool:
        import time
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests (older than 1 minute)
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < 60
        ]
        
        if len(self.requests[key]) >= self.requests_per_minute:
            return False
        
        self.requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Rate limiting dependency
    """
    user_id = current_user.get("sub", "anonymous")
    
    if not rate_limiter.is_allowed(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return current_user
