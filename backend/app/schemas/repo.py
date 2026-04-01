from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class RepositoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    project_id: str


class RepositoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class RepositoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RepositoryWithDetails(RepositoryResponse):
    file_count: Optional[int] = 0
    commit_count: Optional[int] = 0
    latest_commit: Optional[Dict[str, Any]] = None


class FileCreate(BaseModel):
    path: str = Field(..., min_length=1)
    content: Optional[str] = ""
    repository_id: str


class FileUpdate(BaseModel):
    content: Optional[str] = None
    path: Optional[str] = None


class FileResponse(BaseModel):
    id: str
    path: str
    content: Optional[str] = None
    repository_id: str
    file_size: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommitCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    repository_id: str
    files: Optional[List[Dict[str, Any]]] = None


class CommitResponse(BaseModel):
    id: str
    message: str
    repository_id: str
    author_id: str
    commit_hash: Optional[str] = None
    created_at: datetime
    author: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CommitWithDetails(CommitResponse):
    files: List[Dict[str, Any]] = []
    changes_count: int = 0


class FileOperation(BaseModel):
    operation: str = Field(..., regex="^(create|update|delete)$")
    path: str
    content: Optional[str] = None


class BulkFileOperation(BaseModel):
    repository_id: str
    operations: List[FileOperation]
    commit_message: str = Field(..., min_length=1)


class RepositoryTree(BaseModel):
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    modified_at: Optional[datetime] = None
    children: Optional[List['RepositoryTree']] = None


class RepositoryStats(BaseModel):
    total_files: int
    total_commits: int
    total_size: int
    last_commit: Optional[datetime] = None
    branches: List[str] = []
    tags: List[str] = []


class RepositoryDiff(BaseModel):
    file_path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    diff_type: str  # 'added', 'modified', 'deleted'


class RepositoryCompare(BaseModel):
    base_commit: str
    head_commit: str
    files_changed: List[RepositoryDiff]
    stats: Dict[str, int]


class RepositoryBranch(BaseModel):
    name: str
    commit_hash: str
    is_default: bool = False
    last_commit: Optional[datetime] = None


class RepositoryTag(BaseModel):
    name: str
    commit_hash: str
    message: Optional[str] = None
    created_at: datetime


class RepositorySearch(BaseModel):
    query: str = Field(..., min_length=1)
    file_types: Optional[List[str]] = None
    include_content: bool = False


class RepositorySearchResult(BaseModel):
    file_path: str
    content_snippet: Optional[str] = None
    line_number: Optional[int] = None
    match_count: int = 1


class RepositoryClone(BaseModel):
    name: str
    description: Optional[str] = None
    source_repository_id: str
    include_history: bool = True
