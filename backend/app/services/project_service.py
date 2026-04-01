from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import HTTPException, status
from app.db.client import supabase_client
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectWithDetails,
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse,
    ProjectList, ProjectStats, ProjectActivity
)
import logging

logger = logging.getLogger(__name__)


class ProjectService:
    """Project management service"""
    
    async def create_project(
        self, 
        project_data: ProjectCreate, 
        owner_id: str
    ) -> ProjectResponse:
        """
        Create a new project
        """
        try:
            project_record = {
                "name": project_data.name,
                "description": project_data.description,
                "owner_id": owner_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('projects', project_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create project"
                )
            
            # Add owner as project member
            await self.add_member(
                result.data[0]["id"], 
                owner_id, 
                "owner"
            )
            
            return ProjectResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"Create project error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project"
            )
    
    async def get_projects(
        self, 
        user_id: str,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None
    ) -> ProjectList:
        """
        Get user's projects (owned + member)
        """
        try:
            offset = (page - 1) * size
            
            # Get projects using RPC function or manual query
            projects = await supabase_client.get_user_projects(user_id)
            
            # Apply search filter if provided
            if search:
                projects = [
                    p for p in projects 
                    if search.lower() in p.get('name', '').lower() or 
                       search.lower() in p.get('description', '').lower()
                ]
            
            # Get total count
            total = len(projects)
            
            # Apply pagination
            start_idx = offset
            end_idx = start_idx + size
            paginated_projects = projects[start_idx:end_idx]
            
            # Enhance with additional details
            projects_with_details = []
            for project in paginated_projects:
                # Get member count
                members_result = await supabase_client.select_records(
                    'project_members',
                    {'project_id': project['id']},
                    columns='count(*)'
                )
                
                # Get repository count
                repos_result = await supabase_client.select_records(
                    'repositories',
                    {'project_id': project['id']},
                    columns='count(*)'
                )
                
                # Get deployment count
                deployments_result = await supabase_client.select_records(
                    'deployments',
                    {'project_id': project['id']},
                    columns='count(*)'
                )
                
                project_with_details = {
                    **project,
                    "member_count": len(members_result.data) if members_result.data else 0,
                    "repository_count": len(repos_result.data) if repos_result.data else 0,
                    "deployment_count": len(deployments_result.data) if deployments_result.data else 0
                }
                
                projects_with_details.append(ProjectWithDetails(**project_with_details))
            
            return ProjectList(
                projects=projects_with_details,
                total=total,
                page=page,
                size=size,
                has_next=end_idx < total,
                has_prev=page > 1
            )
            
        except Exception as e:
            logger.error(f"Get projects error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch projects"
            )
    
    async def get_project_by_id(
        self, 
        project_id: str,
        user_id: str
    ) -> Optional[ProjectWithDetails]:
        """
        Get project by ID with details
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return None
            
            # Get project details
            result = await supabase_client.select_records(
                'projects',
                {'id': project_id},
                columns='id, name, description, owner_id, created_at, updated_at'
            )
            
            if not result.data:
                return None
            
            project = result.data[0]
            
            # Get owner details
            owner_result = await supabase_client.select_records(
                'users',
                {'id': project['owner_id']},
                columns='id, email, username'
            )
            
            # Get counts
            members_count = await supabase_client.select_records(
                'project_members',
                {'project_id': project_id},
                columns='count(*)'
            )
            
            repos_count = await supabase_client.select_records(
                'repositories',
                {'project_id': project_id},
                columns='count(*)'
            )
            
            deployments_count = await supabase_client.select_records(
                'deployments',
                {'project_id': project_id},
                columns='count(*)'
            )
            
            project_with_details = {
                **project,
                "owner": owner_result.data[0] if owner_result.data else None,
                "member_count": len(members_count.data) if members_count.data else 0,
                "repository_count": len(repos_count.data) if repos_count.data else 0,
                "deployment_count": len(deployments_count.data) if deployments_count.data else 0
            }
            
            return ProjectWithDetails(**project_with_details)
            
        except Exception as e:
            logger.error(f"Get project error: {str(e)}")
            return None
    
    async def update_project(
        self, 
        project_id: str,
        updates: ProjectUpdate,
        user_id: str
    ) -> Optional[ProjectResponse]:
        """
        Update project
        """
        try:
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Update project
            update_data = updates.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = await supabase_client.update_record(
                'projects',
                {'id': project_id},
                update_data
            )
            
            if result.data:
                return ProjectResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Update project error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update project"
            )
    
    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """
        Delete project (owner only)
        """
        try:
            # Check user is owner
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "owner"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only project owners can delete projects"
                )
            
            # Delete project (cascade should handle related records)
            await supabase_client.delete_record('projects', {'id': project_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Delete project error: {str(e)}")
            return False
    
    async def add_member(
        self, 
        project_id: str, 
        user_id: str, 
        role: str
    ) -> ProjectMemberResponse:
        """
        Add member to project
        """
        try:
            # Check if user exists
            user_result = await supabase_client.select_records(
                'users',
                {'id': user_id},
                columns='id, email, username'
            )
            
            if not user_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Add member
            member_record = {
                "project_id": project_id,
                "user_id": user_id,
                "role": role,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('project_members', member_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to add member"
                )
            
            member_data = {
                **result.data[0],
                "user": user_result.data[0]
            }
            
            return ProjectMemberResponse(**member_data)
            
        except Exception as e:
            logger.error(f"Add member error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add member"
            )
    
    async def get_members(self, project_id: str, user_id: str) -> List[ProjectMemberResponse]:
        """
        Get project members
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return []
            
            # Get members with user details
            result = await supabase_client.select_records(
                'project_members',
                {'project_id': project_id},
                columns='id, project_id, user_id, role, created_at',
                order='created_at.asc'
            )
            
            members = []
            for member in result.data or []:
                # Get user details
                user_result = await supabase_client.select_records(
                    'users',
                    {'id': member['user_id']},
                    columns='id, email, username'
                )
                
                member_data = {
                    **member,
                    "user": user_result.data[0] if user_result.data else None
                }
                
                members.append(ProjectMemberResponse(**member_data))
            
            return members
            
        except Exception as e:
            logger.error(f"Get members error: {str(e)}")
            return []
    
    async def update_member_role(
        self, 
        project_id: str,
        member_id: str,
        role: str,
        current_user_id: str
    ) -> Optional[ProjectMemberResponse]:
        """
        Update member role
        """
        try:
            # Check current user is owner
            has_access = await supabase_client.check_project_permission(
                project_id, current_user_id, "owner"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only project owners can update member roles"
                )
            
            # Update member
            result = await supabase_client.update_record(
                'project_members',
                {'id': member_id, 'project_id': project_id},
                {'role': role}
            )
            
            if result.data:
                return ProjectMemberResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Update member role error: {str(e)}")
            return None
    
    async def remove_member(
        self, 
        project_id: str,
        member_id: str,
        current_user_id: str
    ) -> bool:
        """
        Remove member from project
        """
        try:
            # Check current user is owner
            has_access = await supabase_client.check_project_permission(
                project_id, current_user_id, "owner"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only project owners can remove members"
                )
            
            # Remove member
            await supabase_client.delete_record(
                'project_members',
                {'id': member_id, 'project_id': project_id}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Remove member error: {str(e)}")
            return False
    
    async def get_project_stats(self, project_id: str, user_id: str) -> Optional[ProjectStats]:
        """
        Get project statistics
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return None
            
            # Get various counts
            projects_result = await supabase_client.select_records(
                'projects',
                {'id': project_id},
                columns='count(*)'
            )
            
            members_result = await supabase_client.select_records(
                'project_members',
                {'project_id': project_id},
                columns='count(*)'
            )
            
            deployments_result = await supabase_client.select_records(
                'deployments',
                {'project_id': project_id},
                columns='count(*)'
            )
            
            files_result = await supabase_client.select_records(
                'files',
                {'repository_id': 'in.(select id from repositories where project_id=eq.{project_id})'},
                columns='count(*), sum(file_size)'
            )
            
            stats = ProjectStats(
                total_projects=len(projects_result.data) if projects_result.data else 0,
                active_projects=1,  # Assuming project is active if it exists
                total_members=len(members_result.data) if members_result.data else 0,
                total_deployments=len(deployments_result.data) if deployments_result.data else 0,
                total_files=len(files_result.data) if files_result.data else 0,
                storage_used=sum(f.get('file_size', 0) for f in files_result.data or [])
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Get project stats error: {str(e)}")
            return None
    
    async def get_project_activity(
        self, 
        project_id: str, 
        user_id: str,
        limit: int = 20
    ) -> List[ProjectActivity]:
        """
        Get recent project activity
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return []
            
            # Get audit logs
            result = await supabase_client.select_records(
                'audit_logs',
                {'project_id': project_id},
                columns='id, action, table_name, created_at, user_id',
                order='created_at.desc',
                limit=limit
            )
            
            activities = []
            for log in result.data or []:
                # Get user details
                user_result = await supabase_client.select_records(
                    'users',
                    {'id': log['user_id']},
                    columns='id, email, username'
                )
                
                activity_data = {
                    **log,
                    "user": user_result.data[0] if user_result.data else None
                }
                
                activities.append(ProjectActivity(**activity_data))
            
            return activities
            
        except Exception as e:
            logger.error(f"Get project activity error: {str(e)}")
            return []


# Global service instance
project_service = ProjectService()
