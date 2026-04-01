from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class DeploymentBase(BaseModel):
    status: str = "pending"  # 'pending', 'building', 'success', 'failed', 'cancelled'
    url: Optional[str] = None
    branch: str = "main"


class DeploymentCreate(DeploymentBase):
    project_id: str
    commit_id: Optional[str] = None


class DeploymentUpdate(BaseModel):
    status: Optional[str] = None
    url: Optional[str] = None
    build_start_time: Optional[datetime] = None
    build_end_time: Optional[datetime] = None


class DeploymentResponse(DeploymentBase):
    id: str
    project_id: str
    commit_id: Optional[str] = None
    build_start_time: Optional[datetime] = None
    build_end_time: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeploymentWithDetails(DeploymentResponse):
    project: Optional[Dict[str, Any]] = None
    commit: Optional[Dict[str, Any]] = None
    log_count: Optional[int] = 0
    build_duration: Optional[int] = None  # in seconds


class LogBase(BaseModel):
    level: str  # 'info', 'warn', 'error', 'debug'
    message: str


class LogCreate(LogBase):
    deployment_id: str


class LogResponse(LogBase):
    id: str
    deployment_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class EnvironmentVariableBase(BaseModel):
    key: str
    value: str
    is_secret: bool = False


class EnvironmentVariableCreate(EnvironmentVariableBase):
    project_id: str


class EnvironmentVariableUpdate(BaseModel):
    value: Optional[str] = None
    is_secret: Optional[bool] = None


class EnvironmentVariableResponse(EnvironmentVariableBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BuildConfig(BaseModel):
    build_command: str = "npm run build"
    output_directory: str = "dist"
    node_version: str = "18"
    environment_variables: Dict[str, str] = {}


class DeploymentConfig(BaseModel):
    build_config: BuildConfig
    domain: Optional[str] = None
    ssl_enabled: bool = True
    auto_deploy: bool = False
    deploy_branch: str = "main"


class DeploymentStats(BaseModel):
    total_deployments: int
    successful_deployments: int
    failed_deployments: int
    pending_deployments: int
    average_build_time: Optional[float] = None  # in seconds
    last_deployment: Optional[datetime] = None
    uptime_percentage: Optional[float] = None


class DeploymentActivity(BaseModel):
    id: str
    deployment_id: str
    action: str
    details: Dict[str, Any]
    created_at: datetime
    user: Optional[Dict[str, Any]] = None


class DeploymentDashboard(BaseModel):
    deployment: DeploymentWithDetails
    logs: List[LogResponse]
    environment_variables: List[EnvironmentVariableResponse]
    stats: DeploymentStats
    recent_activity: List[DeploymentActivity]


class RollbackRequest(BaseModel):
    deployment_id: str
    reason: Optional[str] = None


class RollbackResponse(BaseModel):
    rollback_deployment: DeploymentResponse
    original_deployment: DeploymentResponse
    status: str
