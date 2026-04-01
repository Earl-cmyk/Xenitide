from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
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


class ProjectMemberBase(BaseModel):
    role: str  # 'owner', 'editor', 'viewer'


class ProjectMemberCreate(ProjectMemberBase):
    project_id: str
    user_id: str


class ProjectMemberResponse(ProjectMemberBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    user: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ProjectMemberUpdate(BaseModel):
    role: str


class ProjectStats(BaseModel):
    total_projects: int
    active_projects: int
    total_members: int
    total_deployments: int
    total_files: int
    storage_used: int


class ProjectActivity(BaseModel):
    id: str
    project_id: str
    action: str
    table_name: Optional[str] = None
    created_at: datetime
    user: Optional[Dict[str, Any]] = None


class ProjectDashboard(BaseModel):
    project: ProjectWithDetails
    recent_activity: List[ProjectActivity]
    stats: Dict[str, Any]


class ProjectList(BaseModel):
    projects: List[ProjectWithDetails]
    total: int
    page: int
    size: int
