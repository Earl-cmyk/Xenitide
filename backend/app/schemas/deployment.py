from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class DeploymentCreate(BaseModel):
    project_id: str
    branch: str = "main"
    commit_id: Optional[str] = None
    build_config: Optional[Dict[str, Any]] = None


class DeploymentUpdate(BaseModel):
    status: Optional[str] = Field(None, regex="^(pending|building|success|failed|cancelled)$")
    url: Optional[str] = None
    build_start_time: Optional[datetime] = None
    build_end_time: Optional[datetime] = None


class DeploymentResponse(BaseModel):
    id: str
    project_id: str
    status: str
    url: Optional[str] = None
    branch: str
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
    build_config: Optional[Dict[str, Any]] = None


class LogCreate(BaseModel):
    deployment_id: str
    level: str = Field(..., regex="^(info|warn|error|debug)$")
    message: str = Field(..., min_length=1)


class LogResponse(BaseModel):
    id: str
    deployment_id: str
    level: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class EnvironmentVariableCreate(BaseModel):
    project_id: str
    key: str = Field(..., min_length=1, max_length=100)
    value: str
    is_secret: bool = False


class EnvironmentVariableUpdate(BaseModel):
    value: Optional[str] = None
    is_secret: Optional[bool] = None


class EnvironmentVariableResponse(BaseModel):
    id: str
    project_id: str
    key: str
    value: str
    is_secret: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BuildConfig(BaseModel):
    build_command: str = "npm run build"
    output_directory: str = "dist"
    node_version: str = "18"
    install_command: str = "npm install"
    environment_variables: Dict[str, str] = {}


class DeploymentConfig(BaseModel):
    build_config: BuildConfig
    domain: Optional[str] = None
    ssl_enabled: bool = True
    auto_deploy: bool = False
    deploy_branch: str = "main"
    custom_headers: Optional[Dict[str, str]] = None
    redirects: Optional[List[Dict[str, Any]]] = None


class DeploymentStats(BaseModel):
    total_deployments: int
    successful_deployments: int
    failed_deployments: int
    pending_deployments: int
    average_build_time: Optional[float] = None  # in seconds
    last_deployment: Optional[datetime] = None
    uptime_percentage: Optional[float] = None
    success_rate: float


class DeploymentActivity(BaseModel):
    id: str
    deployment_id: str
    action: str
    details: Dict[str, Any]
    created_at: datetime
    user: Optional[Dict[str, Any]] = None


class DeploymentDashboard(BaseModel):
    deployment: Optional[DeploymentWithDetails] = None
    recent_deployments: List[DeploymentWithDetails]
    logs: List[LogResponse]
    environment_variables: List[EnvironmentVariableResponse]
    stats: DeploymentStats
    recent_activity: List[DeploymentActivity]


class RollbackRequest(BaseModel):
    deployment_id: str
    reason: Optional[str] = Field(None, max_length=500)


class RollbackResponse(BaseModel):
    rollback_deployment: DeploymentResponse
    original_deployment: DeploymentResponse
    status: str
    message: Optional[str] = None


class DeploymentPreview(BaseModel):
    files_changed: List[str]
    commit_hash: str
    commit_message: str
    estimated_build_time: Optional[int] = None  # in seconds


class DeploymentWebhook(BaseModel):
    url: str
    events: List[str] = Field(..., regex="^(deployment_started|deployment_success|deployment_failed)$")
    secret: Optional[str] = None
    active: bool = True


class DeploymentMetrics(BaseModel):
    build_time_history: List[Dict[str, Any]]
    deployment_frequency: List[Dict[str, Any]]
    error_rate_history: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
