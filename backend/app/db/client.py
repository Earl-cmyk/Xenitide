from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client wrapper with enhanced functionality"""
    
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.admin_client: Optional[Client] = None
        
        if settings.SUPABASE_SERVICE_ROLE_KEY:
            self.admin_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
    
    def get_client(self, use_admin: bool = False) -> Client:
        """Get Supabase client (admin or regular)"""
        if use_admin and self.admin_client:
            return self.admin_client
        return self.client
    
    def auth(self):
        """Get auth client"""
        return self.client.auth
    
    def table(self, table_name: str):
        """Get table reference"""
        return self.client.table(table_name)
    
    def admin_table(self, table_name: str):
        """Get admin table reference"""
        if not self.admin_client:
            raise Exception("Admin client not configured")
        return self.admin_client.table(table_name)
    
    async def execute_query(self, query_func, table_name: str, operation: str = "select"):
        """Execute query with error handling"""
        try:
            result = query_func()
            return result
        except Exception as e:
            logger.error(f"Error executing {operation} on {table_name}: {str(e)}")
            raise
    
    async def insert_record(self, table_name: str, data: Dict[str, Any], use_admin: bool = False):
        """Insert a record into a table"""
        client = self.get_client(use_admin)
        query = client.table(table_name).insert(data)
        return await self.execute_query(lambda: query.execute(), table_name, "insert")
    
    async def select_records(
        self, 
        table_name: str, 
        filters: Optional[Dict[str, Any]] = None,
        columns: str = "*",
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ):
        """Select records from a table"""
        query = self.table(table_name).select(columns)
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    query = query.in_(key, value)
                else:
                    query = query.eq(key, value)
        
        if order:
            query = query.order(order)
        
        if limit:
            query = query.limit(limit)
        
        if offset:
            query = query.offset(offset)
        
        return await self.execute_query(lambda: query.execute(), table_name, "select")
    
    async def update_record(
        self, 
        table_name: str, 
        filters: Dict[str, Any], 
        data: Dict[str, Any],
        use_admin: bool = False
    ):
        """Update records in a table"""
        client = self.get_client(use_admin)
        query = client.table(table_name).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        return await self.execute_query(lambda: query.execute(), table_name, "update")
    
    async def delete_record(self, table_name: str, filters: Dict[str, Any], use_admin: bool = False):
        """Delete records from a table"""
        client = self.get_client(use_admin)
        query = client.table(table_name).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        return await self.execute_query(lambda: query.execute(), table_name, "delete")
    
    async def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all projects accessible to a user (owned + member)"""
        # Using RPC function for better performance
        try:
            result = self.client.rpc('get_user_projects', {'user_uuid': user_id}).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user projects: {str(e)}")
            # Fallback to manual query
            owned_projects = await self.select_records('projects', {'owner_id': user_id})
            member_projects = await self.select_records(
                'project_members', 
                {'user_id': user_id},
                columns='projects(*)',
                order='created_at.desc'
            )
            return (owned_projects.data or []) + (member_projects.data or [])
    
    async def check_project_permission(
        self, 
        project_id: str, 
        user_id: str, 
        required_role: str = 'viewer'
    ) -> bool:
        """Check if user has permission for project"""
        try:
            result = self.client.rpc(
                'has_project_permission', 
                {
                    'project_uuid': project_id,
                    'required_role': required_role,
                    'user_uuid': user_id
                }
            ).execute()
            return result.data or False
        except Exception as e:
            logger.error(f"Error checking project permission: {str(e)}")
            return False
    
    async def create_storage_file(
        self, 
        project_id: str, 
        file_name: str, 
        file_data: bytes,
        mime_type: str
    ) -> Dict[str, Any]:
        """Upload file to Supabase storage and create database record"""
        try:
            # Upload to storage
            storage_path = f"{project_id}/{file_name}"
            storage_result = self.client.storage \
                .from('project-files') \
                .upload(storage_path, file_data, {'content-type': mime_type})
            
            if storage_result.data is None:
                raise Exception("Storage upload failed")
            
            # Get public URL
            public_url = self.client.storage \
                .from('project-files') \
                .get_public_url(storage_path)
            
            # Create database record
            file_record = {
                'project_id': project_id,
                'file_name': file_name,
                'file_url': storage_path,
                'file_type': 'image' if mime_type.startswith('image/') else 'document',
                'file_size': len(file_data),
                'mime_type': mime_type
            }
            
            result = await self.insert_record('storage_files', file_record)
            return {
                'storage_data': storage_result.data,
                'public_url': public_url,
                'db_data': result.data
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise
    
    async def delete_storage_file(self, file_id: str, file_url: str) -> bool:
        """Delete file from storage and database"""
        try:
            # Delete from storage
            storage_result = self.client.storage \
                .from('project-files') \
                .remove([file_url])
            
            # Delete from database
            await self.delete_record('storage_files', {'id': file_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False


# Global instance
supabase_client = SupabaseClient()
