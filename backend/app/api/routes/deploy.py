from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.services.deploy_service import deploy_service
from app.schemas.deployment import (
    DeploymentCreate, DeploymentUpdate, DeploymentResponse, DeploymentWithDetails,
    LogCreate, LogResponse,
    EnvironmentVariableCreate, EnvironmentVariableUpdate, EnvironmentVariableResponse,
    DeploymentStats, DeploymentDashboard
)
from app.api.deps import (
    get_current_user, require_project_access, require_project_editor,
    get_pagination_params
)
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deploy", tags=["deployments"])


@router.post("/", response_model=DeploymentResponse)
async def create_deployment(
    deploy_data: DeploymentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new deployment
    """
    try:
        return await deploy_service.create_deployment(deploy_data, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create deployment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create deployment"
        )


@router.get("/project/{project_id}", response_model=list[DeploymentWithDetails])
async def get_project_deployments(
    project_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get project deployments
    """
    try:
        return await deploy_service.get_deployments(project_id, current_user.get("sub"), limit)
    except Exception as e:
        logger.error(f"Get deployments error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployments"
        )


@router.get("/{deployment_id}", response_model=DeploymentWithDetails)
async def get_deployment(
    deployment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get deployment by ID with details
    """
    try:
        deployment = await deploy_service.get_deployment_by_id(deployment_id, current_user.get("sub"))
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )
        
        return deployment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get deployment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployment"
        )


@router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: str,
    updates: DeploymentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update deployment status (internal use)
    """
    try:
        deployment = await deploy_service.update_deployment_status(
            deployment_id,
            updates.status,
            updates.url,
            updates.build_start_time,
            updates.build_end_time
        )
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )
        
        return deployment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update deployment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update deployment"
        )


@router.post("/{deployment_id}/retry", response_model=DeploymentResponse)
async def retry_deployment(
    deployment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retry a failed deployment
    """
    try:
        deployment = await deploy_service.retry_deployment(deployment_id, current_user.get("sub"))
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )
        
        return deployment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry deployment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry deployment"
        )


@router.post("/{deployment_id}/cancel")
async def cancel_deployment(
    deployment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cancel a deployment
    """
    try:
        success = await deploy_service.cancel_deployment(deployment_id, current_user.get("sub"))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )
        
        return {"message": "Deployment cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel deployment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel deployment"
        )


# Log endpoints

@router.post("/{deployment_id}/logs", response_model=LogResponse)
async def add_deployment_log(
    deployment_id: str,
    log_data: LogCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Add deployment log (internal use)
    """
    try:
        log_data.deployment_id = deployment_id
        return await deploy_service.add_log(log_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add log error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add log"
        )


@router.get("/{deployment_id}/logs", response_model=list[LogResponse])
async def get_deployment_logs(
    deployment_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get deployment logs
    """
    try:
        return await deploy_service.get_deployment_logs(deployment_id, current_user.get("sub"), limit)
    except Exception as e:
        logger.error(f"Get deployment logs error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployment logs"
        )


@router.get("/{deployment_id}/logs/stream")
async def stream_deployment_logs(
    deployment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Stream deployment logs (WebSocket/SSE)
    """
    try:
        # TODO: Implement real-time log streaming
        return {"message": "Log streaming not yet implemented"}
    except Exception as e:
        logger.error(f"Stream logs error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream logs"
        )


# Environment variables endpoints

@router.post("/project/{project_id}/env", response_model=EnvironmentVariableResponse)
async def create_environment_variable(
    project_id: str,
    env_data: EnvironmentVariableCreate,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "editor"))
):
    """
    Create environment variable
    """
    try:
        env_data.project_id = project_id
        return await deploy_service.create_environment_variable(env_data, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create environment variable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create environment variable"
        )


@router.get("/project/{project_id}/env", response_model=list[EnvironmentVariableResponse])
async def get_environment_variables(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "editor"))
):
    """
    Get project environment variables
    """
    try:
        return await deploy_service.get_environment_variables(project_id, current_user.get("sub"))
    except Exception as e:
        logger.error(f"Get environment variables error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch environment variables"
        )


@router.put("/project/{project_id}/env/{env_id}", response_model=EnvironmentVariableResponse)
async def update_environment_variable(
    project_id: str,
    env_id: str,
    updates: EnvironmentVariableUpdate,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "editor"))
):
    """
    Update environment variable
    """
    try:
        env_var = await deploy_service.update_environment_variable(env_id, updates, current_user.get("sub"))
        
        if not env_var:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment variable not found"
            )
        
        return env_var
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update environment variable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update environment variable"
        )


@router.delete("/project/{project_id}/env/{env_id}")
async def delete_environment_variable(
    project_id: str,
    env_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "editor"))
):
    """
    Delete environment variable
    """
    try:
        success = await deploy_service.delete_environment_variable(env_id, current_user.get("sub"))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment variable not found"
            )
        
        return {"message": "Environment variable deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete environment variable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete environment variable"
        )


# Statistics and dashboard endpoints

@router.get("/project/{project_id}/stats", response_model=DeploymentStats)
async def get_deployment_stats(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get deployment statistics
    """
    try:
        stats = await deploy_service.get_deployment_stats(project_id, current_user.get("sub"))
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get deployment stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployment stats"
        )


@router.get("/project/{project_id}/dashboard", response_model=DeploymentDashboard)
async def get_deployment_dashboard(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get deployment dashboard
    """
    try:
        # Get stats
        stats = await deploy_service.get_deployment_stats(project_id, current_user.get("sub"))
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get recent deployments
        recent_deployments = await deploy_service.get_deployments(project_id, current_user.get("sub"), 5)
        
        # Get environment variables
        env_vars = await deploy_service.get_environment_variables(project_id, current_user.get("sub"))
        
        # Get recent logs (from latest deployment)
        recent_logs = []
        if recent_deployments:
            latest_deployment = recent_deployments[0]
            recent_logs = await deploy_service.get_deployment_logs(latest_deployment.id, current_user.get("sub"), 20)
        
        dashboard = DeploymentDashboard(
            deployment=recent_deployments[0] if recent_deployments else None,
            recent_deployments=recent_deployments,
            logs=recent_logs,
            environment_variables=env_vars,
            stats=stats,
            recent_activity=[]  # TODO: Implement activity tracking
        )
        
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get deployment dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployment dashboard"
        )


@router.post("/{deployment_id}/rollback")
async def rollback_deployment(
    deployment_id: str,
    rollback_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Rollback to previous deployment
    """
    try:
        # TODO: Implement rollback functionality
        return {"message": "Rollback functionality not yet implemented"}
    except Exception as e:
        logger.error(f"Rollback deployment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rollback deployment"
        )


@router.get("/{deployment_id}/status")
async def get_deployment_status(
    deployment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get deployment status (for polling)
    """
    try:
        deployment = await deploy_service.get_deployment_by_id(deployment_id, current_user.get("sub"))
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )
        
        return {
            "id": deployment.id,
            "status": deployment.status,
            "url": deployment.url,
            "build_start_time": deployment.build_start_time,
            "build_end_time": deployment.build_end_time,
            "build_duration": deployment.build_duration
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get deployment status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch deployment status"
        )
