from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime


class DatabaseTableBase(BaseModel):
    name: str
    schema: Dict[str, Any]  # Column definitions


class DatabaseTableCreate(DatabaseTableBase):
    project_id: str


class DatabaseTableUpdate(BaseModel):
    name: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None


class DatabaseTableResponse(DatabaseTableBase):
    id: str
    project_id: str
    row_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DatabaseRowBase(BaseModel):
    data: Dict[str, Any]


class DatabaseRowCreate(DatabaseRowBase):
    table_id: str


class DatabaseRowUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None


class DatabaseRowResponse(DatabaseRowBase):
    id: str
    table_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TableColumn(BaseModel):
    name: str
    type: str
    required: bool = False
    unique: bool = False
    primary_key: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None


class TableSchema(BaseModel):
    name: str
    columns: List[TableColumn]
    indexes: Optional[List[Dict[str, Any]]] = None
    constraints: Optional[List[Dict[str, Any]]] = None


class CreateTableRequest(BaseModel):
    name: str
    schema: TableSchema


class QueryRequest(BaseModel):
    table_id: str
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[List[Dict[str, Any]]] = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0


class QueryResponse(BaseModel):
    rows: List[Dict[str, Any]]
    total: int
    page: int
    size: int


class BulkOperation(BaseModel):
    operation: str  # 'insert', 'update', 'delete'
    data: Optional[List[Dict[str, Any]]] = None
    filters: Optional[Dict[str, Any]] = None


class BulkOperationResponse(BaseModel):
    operation: str
    affected_rows: int
    errors: Optional[List[str]] = None


class DatabaseStats(BaseModel):
    total_tables: int
    total_rows: int
    storage_used: int  # in bytes
    most_recent_table: Optional[str] = None
    largest_table: Optional[str] = None


class DatabaseActivity(BaseModel):
    id: str
    table_id: str
    action: str
    details: Dict[str, Any]
    created_at: datetime
    user: Optional[Dict[str, Any]] = None


class DatabaseDashboard(BaseModel):
    tables: List[DatabaseTableResponse]
    stats: DatabaseStats
    recent_activity: List[DatabaseActivity]


class ExportRequest(BaseModel):
    table_id: str
    format: str = "csv"  # 'csv', 'json', 'sql'
    filters: Optional[Dict[str, Any]] = None


class ImportRequest(BaseModel):
    table_id: str
    format: str = "csv"
    data: str  # File content or data
    mapping: Optional[Dict[str, str]] = None  # Column mapping


class ImportResponse(BaseModel):
    imported_rows: int
    skipped_rows: int
    errors: List[str]
