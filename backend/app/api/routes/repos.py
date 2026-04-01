from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.services.repo_service import repo_service
from app.schemas.repo import (
    RepositoryCreate, RepositoryUpdate, RepositoryResponse, RepositoryWithDetails,
    FileCreate, FileUpdate, FileResponse,
    CommitCreate, CommitResponse, CommitWithDetails,
    BulkFileOperation, RepositoryTree
)
from app.api.deps import (
    get_current_user, require_project_access, require_project_editor,
    get_pagination_params
)
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["repositories"])


@router.post("/", response_model=RepositoryResponse)
async def create_repository(
    repo_data: RepositoryCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new repository
    """
    try:
        return await repo_service.create_repository(repo_data, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create repository error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create repository"
        )


@router.get("/project/{project_id}", response_model=list[RepositoryWithDetails])
async def get_project_repositories(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get project repositories
    """
    try:
        return await repo_service.get_repositories(project_id, current_user.get("sub"))
    except Exception as e:
        logger.error(f"Get repositories error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch repositories"
        )


@router.get("/{repo_id}", response_model=RepositoryWithDetails)
async def get_repository(
    repo_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get repository by ID with details
    """
    try:
        repository = await repo_service.get_repository_by_id(repo_id, current_user.get("sub"))
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        return repository
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get repository error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch repository"
        )


@router.put("/{repo_id}", response_model=RepositoryResponse)
async def update_repository(
    repo_id: str,
    updates: RepositoryUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update repository
    """
    try:
        repository = await repo_service.update_repository(repo_id, updates, current_user.get("sub"))
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        return repository
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update repository error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update repository"
        )


@router.delete("/{repo_id}")
async def delete_repository(
    repo_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete repository
    """
    try:
        success = await repo_service.delete_repository(repo_id, current_user.get("sub"))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        return {"message": "Repository deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete repository error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete repository"
        )


# File management endpoints

@router.get("/{repo_id}/files", response_model=list[FileResponse])
async def get_repository_files(
    repo_id: str,
    path: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get repository files
    """
    try:
        return await repo_service.get_files(repo_id, current_user.get("sub"), path)
    except Exception as e:
        logger.error(f"Get files error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch files"
        )


@router.get("/{repo_id}/files/{file_id}", response_model=FileResponse)
async def get_file_content(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get file content
    """
    try:
        file_content = await repo_service.get_file_content(file_id, current_user.get("sub"))
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return file_content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file content error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch file content"
        )


@router.post("/{repo_id}/files", response_model=FileResponse)
async def create_or_update_file(
    repo_id: str,
    file_data: FileCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create or update file
    """
    try:
        file_data.repository_id = repo_id
        return await repo_service.create_file(file_data, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create file error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )


@router.put("/{repo_id}/files/{file_id}", response_model=FileResponse)
async def update_file(
    repo_id: str,
    file_id: str,
    updates: FileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update file
    """
    try:
        # Get current file content
        current_file = await repo_service.get_file_content(file_id, current_user.get("sub"))
        
        if not current_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Update file
        file_data = FileCreate(
            repository_id=repo_id,
            path=updates.path or current_file.path,
            content=updates.content if updates.content is not None else current_file.content
        )
        
        return await repo_service.create_file(file_data, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update file error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file"
        )


@router.delete("/{repo_id}/files/{file_id}")
async def delete_file(
    repo_id: str,
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete file
    """
    try:
        success = await repo_service.delete_file(file_id, current_user.get("sub"))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete file error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.get("/{repo_id}/tree", response_model=list[RepositoryTree])
async def get_repository_tree(
    repo_id: str,
    path: str = Query(""),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get repository file tree
    """
    try:
        return await repo_service.get_repository_tree(repo_id, current_user.get("sub"), path)
    except Exception as e:
        logger.error(f"Get repository tree error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch repository tree"
        )


@router.post("/{repo_id}/bulk-operations", response_model=CommitResponse)
async def bulk_file_operations(
    repo_id: str,
    operations: BulkFileOperation,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Perform bulk file operations and create commit
    """
    try:
        operations.repository_id = repo_id
        return await repo_service.bulk_file_operations(operations, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk file operations error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform file operations"
        )


# Commit endpoints

@router.post("/{repo_id}/commits", response_model=CommitResponse)
async def create_commit(
    repo_id: str,
    commit_data: CommitCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create commit
    """
    try:
        commit_data.repository_id = repo_id
        return await repo_service.create_commit(commit_data, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create commit error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create commit"
        )


@router.get("/{repo_id}/commits", response_model=list[CommitResponse])
async def get_commits(
    repo_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get repository commits
    """
    try:
        return await repo_service.get_commits(repo_id, current_user.get("sub"), limit)
    except Exception as e:
        logger.error(f"Get commits error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch commits"
        )


@router.get("/{repo_id}/commits/{commit_id}", response_model=CommitWithDetails)
async def get_commit_details(
    repo_id: str,
    commit_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get commit details with files
    """
    try:
        # TODO: Implement commit details with files
        commits = await repo_service.get_commits(repo_id, current_user.get("sub"), 1)
        
        if not commits:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commit not found"
            )
        
        # Return first commit as placeholder
        return CommitWithDetails(**commits[0].dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get commit details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch commit details"
        )


@router.post("/{repo_id}/deploy")
async def deploy_repository(
    repo_id: str,
    deploy_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deploy repository (trigger deployment)
    """
    try:
        # Get repository to check project access
        repository = await repo_service.get_repository_by_id(repo_id, current_user.get("sub"))
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Create deployment
        from app.services.deploy_service import deploy_service
        from app.schemas.deployment import DeploymentCreate
        
        deployment = await deploy_service.create_deployment(
            DeploymentCreate(
                project_id=repository.project_id,
                branch=deploy_data.get("branch", "main"),
                commit_id=deploy_data.get("commit_id")
            ),
            current_user.get("sub")
        )
        
        return {"message": "Deployment started", "deployment_id": deployment.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deploy repository error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start deployment"
        )
