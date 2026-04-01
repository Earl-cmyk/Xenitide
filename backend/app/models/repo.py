from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class RepositoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    project_id: str


class RepositoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RepositoryResponse(RepositoryBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RepositoryWithDetails(RepositoryResponse):
    file_count: Optional[int] = 0
    commit_count: Optional[int] = 0
    latest_commit: Optional[Dict[str, Any]] = None


class FileBase(BaseModel):
    path: str
    content: Optional[str] = None


class FileCreate(FileBase):
    repository_id: str


class FileUpdate(BaseModel):
    content: Optional[str] = None
    path: Optional[str] = None


class FileResponse(FileBase):
    id: str
    repository_id: str
    file_size: Optional[int] = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommitBase(BaseModel):
    message: str
    commit_hash: Optional[str] = None


class CommitCreate(CommitBase):
    repository_id: str
    author_id: str


class CommitResponse(CommitBase):
    id: str
    repository_id: str
    author_id: str
    created_at: datetime
    author: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CommitFileBase(BaseModel):
    file_id: str
    content_snapshot: Optional[str] = None
    operation: str  # 'add', 'modify', 'delete'


class CommitFileCreate(CommitFileBase):
    commit_id: str


class CommitFileResponse(CommitFileBase):
    id: str
    commit_id: str
    file_id: str
    created_at: datetime
    file: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CommitWithDetails(CommitResponse):
    files: List[CommitFileResponse] = []


class RepositoryTree(BaseModel):
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    children: Optional[List['RepositoryTree']] = None


class FileOperation(BaseModel):
    operation: str  # 'create', 'update', 'delete'
    file_path: str
    content: Optional[str] = None


class BulkFileOperation(BaseModel):
    repository_id: str
    operations: List[FileOperation]
    commit_message: str


class RepositoryStats(BaseModel):
    total_files: int
    total_commits: int
    total_size: int
    last_commit: Optional[datetime] = None


class RepositoryActivity(BaseModel):
    id: str
    repository_id: str
    action: str
    details: Dict[str, Any]
    created_at: datetime
    user: Optional[Dict[str, Any]] = None
