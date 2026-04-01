from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectWithDetails(ProjectResponse):
    owner: Optional[Dict[str, Any]] = None
    member_count: Optional[int] = 0
    repository_count: Optional[int] = 0
    deployment_count: Optional[int] = 0
    storage_used: Optional[int] = 0


class ProjectMemberCreate(BaseModel):
    user_id: str
    role: str = Field(..., regex="^(owner|editor|viewer)$")


class ProjectMemberUpdate(BaseModel):
    role: str = Field(..., regex="^(owner|editor|viewer)$")


class ProjectMemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    created_at: datetime
    user: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    projects: List[ProjectWithDetails]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class ProjectStats(BaseModel):
    total_projects: int
    active_projects: int
    total_members: int
    total_deployments: int
    total_files: int
    storage_used: int
    recent_activity: List[Dict[str, Any]]


class ProjectActivity(BaseModel):
    id: str
    project_id: str
    action: str
    table_name: Optional[str] = None
    created_at: datetime
    user: Optional[Dict[str, Any]] = None


class ProjectInviteCreate(BaseModel):
    email: str
    role: str = Field(..., regex="^(editor|viewer)$")
    message: Optional[str] = None


class ProjectInviteResponse(BaseModel):
    id: str
    project_id: str
    email: str
    role: str
    message: Optional[str] = None
    token: str
    expires_at: datetime
    created_at: datetime


class ProjectSettings(BaseModel):
    name: str
    description: Optional[str] = None
    allow_guest_access: bool = False
    default_member_role: str = "viewer"
    auto_deploy: bool = False
    deploy_branch: str = "main"


class ProjectClone(BaseModel):
    name: str
    description: Optional[str] = None
    clone_repositories: bool = True
    clone_env_vars: bool = False
    clone_database: bool = False


class ProjectExport(BaseModel):
    include_repositories: bool = True
    include_database: bool = True
    include_env_vars: bool = False
    format: str = "json"  # "json", "zip"
