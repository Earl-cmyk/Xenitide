from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import uuid
from fastapi import HTTPException, status
from app.db.client import supabase_client
from app.schemas.deployment import (
    DeploymentCreate, DeploymentUpdate, DeploymentResponse, DeploymentWithDetails,
    LogCreate, LogResponse,
    EnvironmentVariableCreate, EnvironmentVariableUpdate, EnvironmentVariableResponse,
    DeploymentStats, DeploymentActivity, DeploymentDashboard
)
import logging

logger = logging.getLogger(__name__)


class DeploymentService:
    """Deployment management service"""
    
    async def create_deployment(
        self, 
        deploy_data: DeploymentCreate,
        user_id: str
    ) -> DeploymentResponse:
        """
        Create a new deployment
        """
        try:
            # Check user has editor access to project
            has_access = await supabase_client.check_project_permission(
                deploy_data.project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            deploy_record = {
                "project_id": deploy_data.project_id,
                "status": "pending",
                "branch": deploy_data.branch,
                "commit_id": deploy_data.commit_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('deployments', deploy_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create deployment"
                )
            
            deployment = DeploymentResponse(**result.data[0])
            
            # Start deployment process in background
            asyncio.create_task(self._process_deployment(deployment.id))
            
            return deployment
            
        except Exception as e:
            logger.error(f"Create deployment error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create deployment"
            )
    
    async def _process_deployment(self, deployment_id: str):
        """
        Process deployment in background (simulate CI/CD)
        """
        try:
            # Update status to building
            await self.update_deployment_status(
                deployment_id,
                "building",
                build_start_time=datetime.utcnow()
            )
            
            # Add initial log
            await self.add_log(LogCreate(
                deployment_id=deployment_id,
                level="info",
                message="Deployment started"
            ))
            
            # Simulate build process
            await asyncio.sleep(2)
            
            await self.add_log(LogCreate(
                deployment_id=deployment_id,
                level="info",
                message="Installing dependencies..."
            ))
            
            await asyncio.sleep(1)
            
            await self.add_log(LogCreate(
                deployment_id=deployment_id,
                level="info",
                message="Building application..."
            ))
            
            await asyncio.sleep(2)
            
            # Get deployment details for URL generation
            deploy_result = await supabase_client.select_records(
                'deployments',
                {'id': deployment_id},
                columns='project_id'
            )
            
            if deploy_result.data:
                project_id = deploy_result.data[0]['project_id']
                deployment_url = f"https://{project_id}.xenitide.app"
                
                # Update status to success
                await self.update_deployment_status(
                    deployment_id,
                    "success",
                    url=deployment_url,
                    build_end_time=datetime.utcnow()
                )
                
                await self.add_log(LogCreate(
                    deployment_id=deployment_id,
                    level="info",
                    message=f"Deployment successful! Available at: {deployment_url}"
                ))
            else:
                # Update status to failed
                await self.update_deployment_status(
                    deployment_id,
                    "failed",
                    build_end_time=datetime.utcnow()
                )
                
                await self.add_log(LogCreate(
                    deployment_id=deployment_id,
                    level="error",
                    message="Deployment failed: Project not found"
                ))
                
        except Exception as e:
            logger.error(f"Process deployment error: {str(e)}")
            
            # Update status to failed
            await self.update_deployment_status(
                deployment_id,
                "failed",
                build_end_time=datetime.utcnow()
            )
            
            await self.add_log(LogCreate(
                deployment_id=deployment_id,
                level="error",
                message=f"Deployment failed: {str(e)}"
            ))
    
    async def update_deployment_status(
        self,
        deployment_id: str,
        status: str,
        url: Optional[str] = None,
        build_start_time: Optional[datetime] = None,
        build_end_time: Optional[datetime] = None
    ) -> Optional[DeploymentResponse]:
        """
        Update deployment status
        """
        try:
            update_data = {"status": status}
            
            if url:
                update_data["url"] = url
            if build_start_time:
                update_data["build_start_time"] = build_start_time.isoformat()
            if build_end_time:
                update_data["build_end_time"] = build_end_time.isoformat()
            
            result = await supabase_client.update_record(
                'deployments',
                {'id': deployment_id},
                update_data
            )
            
            if result.data:
                return DeploymentResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Update deployment status error: {str(e)}")
            return None
    
    async def get_deployments(
        self, 
        project_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[DeploymentWithDetails]:
        """
        Get project deployments
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return []
            
            # Get deployments
            result = await supabase_client.select_records(
                'deployments',
                {'project_id': project_id},
                columns='id, project_id, status, url, branch, commit_id, build_start_time, build_end_time, created_at',
                order='created_at.desc',
                limit=limit
            )
            
            deployments = []
            for deploy in result.data or []:
                # Get log count
                logs_result = await supabase_client.select_records(
                    'logs',
                    {'deployment_id': deploy['id']},
                    columns='count(*)'
                )
                
                # Calculate build duration
                build_duration = None
                if deploy.get('build_start_time') and deploy.get('build_end_time'):
                    start = datetime.fromisoformat(deploy['build_start_time'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(deploy['build_end_time'].replace('Z', '+00:00'))
                    build_duration = int((end - start).total_seconds())
                
                deploy_with_details = {
                    **deploy,
                    "log_count": len(logs_result.data) if logs_result.data else 0,
                    "build_duration": build_duration
                }
                
                deployments.append(DeploymentWithDetails(**deploy_with_details))
            
            return deployments
            
        except Exception as e:
            logger.error(f"Get deployments error: {str(e)}")
            return []
    
    async def get_deployment_by_id(
        self, 
        deployment_id: str,
        user_id: str
    ) -> Optional[DeploymentWithDetails]:
        """
        Get deployment by ID with details
        """
        try:
            # Get deployment
            result = await supabase_client.select_records(
                'deployments',
                {'id': deployment_id},
                columns='id, project_id, status, url, branch, commit_id, build_start_time, build_end_time, created_at'
            )
            
            if not result.data:
                return None
            
            deploy = result.data[0]
            
            # Check user has access to project
            has_access = await supabase_client.check_project_permission(
                deploy['project_id'], user_id, "viewer"
            )
            
            if not has_access:
                return None
            
            # Get log count
            logs_result = await supabase_client.select_records(
                'logs',
                {'deployment_id': deployment_id},
                columns='count(*)'
            )
            
            # Calculate build duration
            build_duration = None
            if deploy.get('build_start_time') and deploy.get('build_end_time'):
                start = datetime.fromisoformat(deploy['build_start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(deploy['build_end_time'].replace('Z', '+00:00'))
                build_duration = int((end - start).total_seconds())
            
            deploy_with_details = {
                **deploy,
                "log_count": len(logs_result.data) if logs_result.data else 0,
                "build_duration": build_duration
            }
            
            return DeploymentWithDetails(**deploy_with_details)
            
        except Exception as e:
            logger.error(f"Get deployment error: {str(e)}")
            return None
    
    async def add_log(self, log_data: LogCreate) -> LogResponse:
        """
        Add deployment log
        """
        try:
            log_record = {
                "deployment_id": log_data.deployment_id,
                "level": log_data.level,
                "message": log_data.message,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('logs', log_record)
            
            if result.data:
                return LogResponse(**result.data[0])
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add log"
            )
            
        except Exception as e:
            logger.error(f"Add log error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add log"
            )
    
    async def get_deployment_logs(
        self, 
        deployment_id: str,
        user_id: str,
        limit: int = 100
    ) -> List[LogResponse]:
        """
        Get deployment logs
        """
        try:
            # Get deployment to check project access
            deploy_result = await supabase_client.select_records(
                'deployments',
                {'id': deployment_id},
                columns='project_id'
            )
            
            if not deploy_result.data:
                return []
            
            project_id = deploy_result.data[0]['project_id']
            
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return []
            
            # Get logs
            result = await supabase_client.select_records(
                'logs',
                {'deployment_id': deployment_id},
                columns='id, deployment_id, level, message, created_at',
                order='created_at.asc',
                limit=limit
            )
            
            return [LogResponse(**log) for log in result.data or []]
            
        except Exception as e:
            logger.error(f"Get deployment logs error: {str(e)}")
            return []
    
    async def retry_deployment(self, deployment_id: str, user_id: str) -> Optional[DeploymentResponse]:
        """
        Retry a failed deployment
        """
        try:
            # Get deployment
            deploy_result = await supabase_client.select_records(
                'deployments',
                {'id': deployment_id},
                columns='project_id, branch, commit_id'
            )
            
            if not deploy_result.data:
                return None
            
            deploy = deploy_result.data[0]
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                deploy['project_id'], user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Create new deployment
            new_deploy = await self.create_deployment(
                DeploymentCreate(
                    project_id=deploy['project_id'],
                    branch=deploy['branch'],
                    commit_id=deploy['commit_id']
                ),
                user_id
            )
            
            return new_deploy
            
        except Exception as e:
            logger.error(f"Retry deployment error: {str(e)}")
            return None
    
    async def cancel_deployment(self, deployment_id: str, user_id: str) -> bool:
        """
        Cancel a deployment
        """
        try:
            # Get deployment
            deploy_result = await supabase_client.select_records(
                'deployments',
                {'id': deployment_id},
                columns='project_id, status'
            )
            
            if not deploy_result.data:
                return False
            
            deploy = deploy_result.data[0]
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                deploy['project_id'], user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Can only cancel pending or building deployments
            if deploy['status'] not in ['pending', 'building']:
                return False
            
            # Update status to cancelled
            await self.update_deployment_status(
                deployment_id,
                "cancelled",
                build_end_time=datetime.utcnow()
            )
            
            await self.add_log(LogCreate(
                deployment_id=deployment_id,
                level="info",
                message="Deployment cancelled"
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Cancel deployment error: {str(e)}")
            return False
    
    async def get_deployment_stats(self, project_id: str, user_id: str) -> Optional[DeploymentStats]:
        """
        Get deployment statistics
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return None
            
            # Get all deployments
            result = await supabase_client.select_records(
                'deployments',
                {'project_id': project_id},
                columns='id, status, build_start_time, build_end_time, created_at'
            )
            
            deployments = result.data or []
            
            total_deployments = len(deployments)
            successful_deployments = len([d for d in deployments if d['status'] == 'success'])
            failed_deployments = len([d for d in deployments if d['status'] == 'failed'])
            pending_deployments = len([d for d in deployments if d['status'] == 'pending'])
            
            # Calculate average build time
            build_times = []
            for d in deployments:
                if d.get('build_start_time') and d.get('build_end_time'):
                    start = datetime.fromisoformat(d['build_start_time'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(d['build_end_time'].replace('Z', '+00:00'))
                    build_times.append((end - start).total_seconds())
            
            average_build_time = sum(build_times) / len(build_times) if build_times else None
            
            # Get last deployment
            last_deployment = None
            if deployments:
                last_deployment = max(
                    [datetime.fromisoformat(d['created_at'].replace('Z', '+00:00')) for d in deployments]
                )
            
            # Calculate success rate
            success_rate = (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0
            
            stats = DeploymentStats(
                total_deployments=total_deployments,
                successful_deployments=successful_deployments,
                failed_deployments=failed_deployments,
                pending_deployments=pending_deployments,
                average_build_time=average_build_time,
                last_deployment=last_deployment,
                success_rate=success_rate
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Get deployment stats error: {str(e)}")
            return None
    
    async def create_environment_variable(
        self, 
        env_data: EnvironmentVariableCreate,
        user_id: str
    ) -> EnvironmentVariableResponse:
        """
        Create environment variable
        """
        try:
            # Check user has editor access to project
            has_access = await supabase_client.check_project_permission(
                env_data.project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            env_record = {
                "project_id": env_data.project_id,
                "key": env_data.key,
                "value": env_data.value,
                "is_secret": env_data.is_secret,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('env_variables', env_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create environment variable"
                )
            
            return EnvironmentVariableResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"Create environment variable error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create environment variable"
            )
    
    async def get_environment_variables(
        self, 
        project_id: str,
        user_id: str
    ) -> List[EnvironmentVariableResponse]:
        """
        Get project environment variables
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                return []
            
            # Get environment variables (hide secret values)
            result = await supabase_client.select_records(
                'env_variables',
                {'project_id': project_id},
                columns='id, project_id, key, is_secret, created_at, updated_at',
                order='key.asc'
            )
            
            env_vars = []
            for env in result.data or []:
                env_data = {
                    **env,
                    "value": "********" if env.get('is_secret') else env.get('value', '')
                }
                env_vars.append(EnvironmentVariableResponse(**env_data))
            
            return env_vars
            
        except Exception as e:
            logger.error(f"Get environment variables error: {str(e)}")
            return []
    
    async def update_environment_variable(
        self, 
        env_id: str,
        updates: EnvironmentVariableUpdate,
        user_id: str
    ) -> Optional[EnvironmentVariableResponse]:
        """
        Update environment variable
        """
        try:
            # Get env variable to check project access
            env_result = await supabase_client.select_records(
                'env_variables',
                {'id': env_id},
                columns='project_id'
            )
            
            if not env_result.data:
                return None
            
            project_id = env_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Update environment variable
            update_data = updates.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = await supabase_client.update_record(
                'env_variables',
                {'id': env_id},
                update_data
            )
            
            if result.data:
                env_data = {
                    **result.data[0],
                    "value": "********" if result.data[0].get('is_secret') else result.data[0].get('value', '')
                }
                return EnvironmentVariableResponse(**env_data)
            return None
            
        except Exception as e:
            logger.error(f"Update environment variable error: {str(e)}")
            return None
    
    async def delete_environment_variable(self, env_id: str, user_id: str) -> bool:
        """
        Delete environment variable
        """
        try:
            # Get env variable to check project access
            env_result = await supabase_client.select_records(
                'env_variables',
                {'id': env_id},
                columns='project_id'
            )
            
            if not env_result.data:
                return False
            
            project_id = env_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Delete environment variable
            await supabase_client.delete_record('env_variables', {'id': env_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Delete environment variable error: {str(e)}")
            return False


# Global service instance
deploy_service = DeploymentService()
