from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import json
from fastapi import HTTPException, status
from app.db.client import supabase_client
from app.schemas.repo import (
    RepositoryCreate, RepositoryUpdate, RepositoryResponse, RepositoryWithDetails,
    FileCreate, FileUpdate, FileResponse,
    CommitCreate, CommitResponse, CommitWithDetails,
    FileOperation, BulkFileOperation, RepositoryTree
)
import logging

logger = logging.getLogger(__name__)


class RepositoryService:
    """Repository management service"""
    
    async def create_repository(
        self, 
        repo_data: RepositoryCreate,
        user_id: str
    ) -> RepositoryResponse:
        """
        Create a new repository
        """
        try:
            # Check user has editor access to project
            has_access = await supabase_client.check_project_permission(
                repo_data.project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            repo_record = {
                "name": repo_data.name,
                "description": repo_data.description,
                "project_id": repo_data.project_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('repositories', repo_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create repository"
                )
            
            return RepositoryResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"Create repository error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create repository"
            )
    
    async def get_repositories(
        self, 
        project_id: str,
        user_id: str
    ) -> List[RepositoryWithDetails]:
        """
        Get project repositories
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return []
            
            # Get repositories
            result = await supabase_client.select_records(
                'repositories',
                {'project_id': project_id},
                columns='id, name, description, project_id, created_at, updated_at',
                order='created_at.desc'
            )
            
            repositories = []
            for repo in result.data or []:
                # Get file count
                files_result = await supabase_client.select_records(
                    'files',
                    {'repository_id': repo['id']},
                    columns='count(*)'
                )
                
                # Get commit count
                commits_result = await supabase_client.select_records(
                    'commits',
                    {'repository_id': repo['id']},
                    columns='count(*)'
                )
                
                # Get latest commit
                latest_commit_result = await supabase_client.select_records(
                    'commits',
                    {'repository_id': repo['id']},
                    columns='id, message, created_at',
                    order='created_at.desc',
                    limit=1
                )
                
                repo_with_details = {
                    **repo,
                    "file_count": len(files_result.data) if files_result.data else 0,
                    "commit_count": len(commits_result.data) if commits_result.data else 0,
                    "latest_commit": latest_commit_result.data[0] if latest_commit_result.data else None
                }
                
                repositories.append(RepositoryWithDetails(**repo_with_details))
            
            return repositories
            
        except Exception as e:
            logger.error(f"Get repositories error: {str(e)}")
            return []
    
    async def get_repository_by_id(
        self, 
        repo_id: str,
        user_id: str
    ) -> Optional[RepositoryWithDetails]:
        """
        Get repository by ID with details
        """
        try:
            # Get repository
            result = await supabase_client.select_records(
                'repositories',
                {'id': repo_id},
                columns='id, name, description, project_id, created_at, updated_at'
            )
            
            if not result.data:
                return None
            
            repo = result.data[0]
            
            # Check user has access to project
            has_access = await supabase_client.check_project_permission(
                repo['project_id'], user_id, "viewer"
            )
            
            if not has_access:
                return None
            
            # Get file count
            files_result = await supabase_client.select_records(
                'files',
                {'repository_id': repo_id},
                columns='count(*)'
            )
            
            # Get commit count
            commits_result = await supabase_client.select_records(
                'commits',
                {'repository_id': repo_id},
                columns='count(*)'
            )
            
            # Get latest commit
            latest_commit_result = await supabase_client.select_records(
                'commits',
                {'repository_id': repo_id},
                columns='id, message, created_at',
                order='created_at.desc',
                limit=1
            )
            
            repo_with_details = {
                **repo,
                "file_count": len(files_result.data) if files_result.data else 0,
                "commit_count": len(commits_result.data) if commits_result.data else 0,
                "latest_commit": latest_commit_result.data[0] if latest_commit_result.data else None
            }
            
            return RepositoryWithDetails(**repo_with_details)
            
        except Exception as e:
            logger.error(f"Get repository error: {str(e)}")
            return None
    
    async def update_repository(
        self, 
        repo_id: str,
        updates: RepositoryUpdate,
        user_id: str
    ) -> Optional[RepositoryResponse]:
        """
        Update repository
        """
        try:
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': repo_id},
                columns='project_id'
            )
            
            if not repo_result.data:
                return None
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Update repository
            update_data = updates.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = await supabase_client.update_record(
                'repositories',
                {'id': repo_id},
                update_data
            )
            
            if result.data:
                return RepositoryResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Update repository error: {str(e)}")
            return None
    
    async def delete_repository(self, repo_id: str, user_id: str) -> bool:
        """
        Delete repository
        """
        try:
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': repo_id},
                columns='project_id'
            )
            
            if not repo_result.data:
                return False
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Delete repository (cascade should handle related records)
            await supabase_client.delete_record('repositories', {'id': repo_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Delete repository error: {str(e)}")
            return False
    
    async def get_files(
        self, 
        repo_id: str,
        user_id: str,
        path: Optional[str] = None
    ) -> List[FileResponse]:
        """
        Get repository files
        """
        try:
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': repo_id},
                columns='project_id'
            )
            
            if not repo_result.data:
                return []
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return []
            
            # Get files
            filters = {'repository_id': repo_id}
            if path:
                filters['path'] = f"like.{path}%"
            
            result = await supabase_client.select_records(
                'files',
                filters,
                columns='id, path, content, repository_id, file_size, created_at, updated_at',
                order='path.asc'
            )
            
            return [FileResponse(**file) for file in result.data or []]
            
        except Exception as e:
            logger.error(f"Get files error: {str(e)}")
            return []
    
    async def get_file_content(
        self, 
        file_id: str,
        user_id: str
    ) -> Optional[FileResponse]:
        """
        Get file content
        """
        try:
            # Get file
            result = await supabase_client.select_records(
                'files',
                {'id': file_id},
                columns='id, path, content, repository_id, file_size, created_at, updated_at'
            )
            
            if not result.data:
                return None
            
            file_data = result.data[0]
            
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': file_data['repository_id']},
                columns='project_id'
            )
            
            if not repo_result.data:
                return None
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return None
            
            return FileResponse(**file_data)
            
        except Exception as e:
            logger.error(f"Get file content error: {str(e)}")
            return None
    
    async def create_file(
        self, 
        file_data: FileCreate,
        user_id: str
    ) -> FileResponse:
        """
        Create or update file
        """
        try:
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': file_data.repository_id},
                columns='project_id'
            )
            
            if not repo_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Repository not found"
                )
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Check if file exists
            existing_file = await supabase_client.select_records(
                'files',
                {'repository_id': file_data.repository_id, 'path': file_data.path},
                columns='id'
            )
            
            file_record = {
                "repository_id": file_data.repository_id,
                "path": file_data.path,
                "content": file_data.content or "",
                "file_size": len(file_data.content or ""),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if existing_file.data:
                # Update existing file
                result = await supabase_client.update_record(
                    'files',
                    {'id': existing_file.data[0]['id']},
                    {
                        "content": file_record["content"],
                        "file_size": file_record["file_size"],
                        "updated_at": file_record["updated_at"]
                    }
                )
            else:
                # Create new file
                result = await supabase_client.insert_record('files', file_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to save file"
                )
            
            return FileResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"Create file error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file"
            )
    
    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """
        Delete file
        """
        try:
            # Get file to check repository access
            file_result = await supabase_client.select_records(
                'files',
                {'id': file_id},
                columns='repository_id'
            )
            
            if not file_result.data:
                return False
            
            repo_id = file_result.data[0]['repository_id']
            
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': repo_id},
                columns='project_id'
            )
            
            if not repo_result.data:
                return False
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Delete file
            await supabase_client.delete_record('files', {'id': file_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Delete file error: {str(e)}")
            return False
    
    async def create_commit(
        self, 
        commit_data: CommitCreate,
        user_id: str
    ) -> CommitResponse:
        """
        Create commit
        """
        try:
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': commit_data.repository_id},
                columns='project_id'
            )
            
            if not repo_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Repository not found"
                )
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Generate commit hash
            commit_hash = hashlib.sha1(
                f"{commit_data.message}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
            
            commit_record = {
                "repository_id": commit_data.repository_id,
                "message": commit_data.message,
                "author_id": user_id,
                "commit_hash": commit_hash,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('commits', commit_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create commit"
                )
            
            return CommitResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"Create commit error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create commit"
            )
    
    async def get_commits(
        self, 
        repo_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[CommitResponse]:
        """
        Get repository commits
        """
        try:
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': repo_id},
                columns='project_id'
            )
            
            if not repo_result.data:
                return []
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return []
            
            # Get commits
            result = await supabase_client.select_records(
                'commits',
                {'repository_id': repo_id},
                columns='id, message, repository_id, author_id, commit_hash, created_at',
                order='created_at.desc',
                limit=limit
            )
            
            commits = []
            for commit in result.data or []:
                # Get author details
                author_result = await supabase_client.select_records(
                    'users',
                    {'id': commit['author_id']},
                    columns='id, email, username'
                )
                
                commit_data = {
                    **commit,
                    "author": author_result.data[0] if author_result.data else None
                }
                
                commits.append(CommitResponse(**commit_data))
            
            return commits
            
        except Exception as e:
            logger.error(f"Get commits error: {str(e)}")
            return []
    
    async def bulk_file_operations(
        self, 
        operation_data: BulkFileOperation,
        user_id: str
    ) -> CommitResponse:
        """
        Perform bulk file operations and create commit
        """
        try:
            # Get repository to check project access
            repo_result = await supabase_client.select_records(
                'repositories',
                {'id': operation_data.repository_id},
                columns='project_id'
            )
            
            if not repo_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Repository not found"
                )
            
            project_id = repo_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Perform operations
            for operation in operation_data.operations:
                if operation.operation == "create" or operation.operation == "update":
                    await self.create_file(
                        FileCreate(
                            repository_id=operation_data.repository_id,
                            path=operation.path,
                            content=operation.content
                        ),
                        user_id
                    )
                elif operation.operation == "delete":
                    # Find file by path and delete
                    files_result = await supabase_client.select_records(
                        'files',
                        {'repository_id': operation_data.repository_id, 'path': operation.path},
                        columns='id'
                    )
                    
                    if files_result.data:
                        await self.delete_file(files_result.data[0]['id'], user_id)
            
            # Create commit
            commit = await self.create_commit(
                CommitCreate(
                    repository_id=operation_data.repository_id,
                    message=operation_data.commit_message,
                    author_id=user_id
                ),
                user_id
            )
            
            return commit
            
        except Exception as e:
            logger.error(f"Bulk file operations error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to perform file operations"
            )
    
    async def get_repository_tree(
        self, 
        repo_id: str,
        user_id: str,
        path: str = ""
    ) -> List[RepositoryTree]:
        """
        Get repository file tree
        """
        try:
            files = await self.get_files(repo_id, user_id, path)
            
            # Build tree structure
            tree = {}
            for file in files:
                parts = file.path.split('/')
                current = tree
                
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        # File
                        current[part] = {
                            "name": part,
                            "path": file.path,
                            "type": "file",
                            "size": file.file_size,
                            "modified_at": file.updated_at
                        }
                    else:
                        # Directory
                        if part not in current:
                            current[part] = {
                                "name": part,
                                "path": "/".join(parts[:i+1]),
                                "type": "directory",
                                "children": {}
                            }
                        current = current[part]["children"]
            
            # Convert to list
            def tree_to_dict(tree_dict):
                result = []
                for item in tree_dict.values():
                    if item["type"] == "directory":
                        item["children"] = tree_to_dict(item["children"])
                    result.append(item)
                return result
            
            return tree_to_dict(tree)
            
        except Exception as e:
            logger.error(f"Get repository tree error: {str(e)}")
            return []


# Global service instance
repo_service = RepositoryService()
