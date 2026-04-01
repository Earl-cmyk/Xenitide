from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.services.project_service import project_service
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithDetails,
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse,
    ProjectList, ProjectStats, ProjectActivity
)
from app.api.deps import (
    get_current_user, require_project_access, require_project_owner,
    get_pagination_params
)
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new project
    """
    try:
        return await project_service.create_project(project_data, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create project error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/", response_model=ProjectList)
async def get_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get user's projects (owned + member)
    """
    try:
        return await project_service.get_projects(
            current_user.get("sub"),
            page=page,
            size=size,
            search=search
        )
    except Exception as e:
        logger.error(f"Get projects error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch projects"
        )


@router.get("/{project_id}", response_model=ProjectWithDetails)
async def get_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get project by ID with details
    """
    try:
        project = await project_service.get_project_by_id(project_id, current_user.get("sub"))
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    updates: ProjectUpdate,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "editor"))
):
    """
    Update project
    """
    try:
        project = await project_service.update_project(project_id, updates, current_user.get("sub"))
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update project error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_owner(project_id))
):
    """
    Delete project (owner only)
    """
    try:
        success = await project_service.delete_project(project_id, current_user.get("sub"))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete project error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get project statistics
    """
    try:
        stats = await project_service.get_project_stats(project_id, current_user.get("sub"))
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project stats"
        )


@router.get("/{project_id}/activity", response_model=list[ProjectActivity])
async def get_project_activity(
    project_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get recent project activity
    """
    try:
        return await project_service.get_project_activity(project_id, current_user.get("sub"), limit)
    except Exception as e:
        logger.error(f"Get project activity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch project activity"
        )


# Project Members endpoints

@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: str,
    member_data: ProjectMemberCreate,
    current_user: Dict[str, Any] = Depends(require_project_owner(project_id))
):
    """
    Add member to project (owner only)
    """
    try:
        return await project_service.add_member(
            project_id,
            member_data.user_id,
            member_data.role
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add member error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add member"
        )


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def get_project_members(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get project members
    """
    try:
        return await project_service.get_members(project_id, current_user.get("sub"))
    except Exception as e:
        logger.error(f"Get members error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch members"
        )


@router.put("/{project_id}/members/{member_id}", response_model=ProjectMemberResponse)
async def update_member_role(
    project_id: str,
    member_id: str,
    role_update: ProjectMemberUpdate,
    current_user: Dict[str, Any] = Depends(require_project_owner(project_id))
):
    """
    Update member role (owner only)
    """
    try:
        member = await project_service.update_member_role(
            project_id,
            member_id,
            role_update.role,
            current_user.get("sub")
        )
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        return member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update member role error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update member role"
        )


@router.delete("/{project_id}/members/{member_id}")
async def remove_member(
    project_id: str,
    member_id: str,
    current_user: Dict[str, Any] = Depends(require_project_owner(project_id))
):
    """
    Remove member from project (owner only)
    """
    try:
        success = await project_service.remove_member(
            project_id,
            member_id,
            current_user.get("sub")
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        return {"message": "Member removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove member error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )


@router.post("/{project_id}/clone", response_model=ProjectResponse)
async def clone_project(
    project_id: str,
    clone_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Clone project (experimental)
    """
    try:
        # Get original project
        original_project = await project_service.get_project_by_id(project_id, current_user.get("sub"))
        
        if not original_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Create new project
        new_project_data = ProjectCreate(
            name=clone_data.get("name", f"Copy of {original_project.name}"),
            description=clone_data.get("description", original_project.description)
        )
        
        new_project = await project_service.create_project(new_project_data, current_user.get("sub"))
        
        # TODO: Clone repositories, env vars, etc. based on clone_data
        
        return new_project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clone project error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone project"
        )


@router.post("/{project_id}/export")
async def export_project(
    project_id: str,
    export_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Export project data
    """
    try:
        # TODO: Implement project export functionality
        return {"message": "Export functionality not yet implemented"}
    except Exception as e:
        logger.error(f"Export project error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export project"
        )
