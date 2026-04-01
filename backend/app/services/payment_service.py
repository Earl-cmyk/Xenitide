from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
import requests
import uuid
from fastapi import HTTPException, status
from app.core.config import settings
from app.db.client import supabase_client
from app.schemas.payment import (
    PaymentLinkCreate, PaymentLinkUpdate, PaymentLinkResponse, PaymentLinkWithStats,
    TransactionCreate, TransactionUpdate, TransactionResponse, TransactionWithDetails,
    XenditInvoiceRequest, XenditInvoiceResponse,
    PaymentStats, PaymentDashboard
)
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment processing service using Xendit"""
    
    def __init__(self):
        self.xendit_url = "https://api.xendit.co/v2"
        self.xendit_secret_key = settings.XENDIT_SECRET_KEY
        self.xendit_public_key = settings.XENDIT_PUBLIC_KEY
    
    async def create_payment_link(
        self, 
        link_data: PaymentLinkCreate,
        user_id: str
    ) -> PaymentLinkResponse:
        """
        Create a new payment link
        """
        try:
            # Check user has editor access to project
            has_access = await supabase_client.check_project_permission(
                link_data.project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Create payment link record
            link_record = {
                "project_id": link_data.project_id,
                "amount": float(link_data.amount),
                "description": link_data.description,
                "currency": link_data.currency,
                "status": "active",
                "expires_at": link_data.expires_at.isoformat() if link_data.expires_at else None,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('payment_links', link_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create payment link"
                )
            
            return PaymentLinkResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"Create payment link error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment link"
            )
    
    async def get_payment_links(
        self, 
        project_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[PaymentLinkWithStats]:
        """
        Get project payment links with statistics
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return []
            
            # Get payment links
            result = await supabase_client.select_records(
                'payment_links',
                {'project_id': project_id},
                columns='id, project_id, amount, description, currency, status, expires_at, created_at',
                order='created_at.desc',
                limit=limit
            )
            
            links_with_stats = []
            for link in result.data or []:
                # Get transaction statistics
                transactions_result = await supabase_client.select_records(
                    'transactions',
                    {'payment_link_id': link['id']},
                    columns='status, amount'
                )
                
                transactions = transactions_result.data or []
                successful_transactions = len([t for t in transactions if t['status'] == 'paid'])
                pending_transactions = len([t for t in transactions if t['status'] == 'pending'])
                failed_transactions = len([t for t in transactions if t['status'] == 'failed'])
                
                total_amount = sum(
                    Decimal(str(t['amount'])) for t in transactions 
                    if t['status'] == 'paid'
                )
                
                link_with_stats = {
                    **link,
                    "transaction_count": len(transactions),
                    "total_amount": total_amount,
                    "successful_transactions": successful_transactions,
                    "pending_transactions": pending_transactions,
                    "failed_transactions": failed_transactions,
                    "revenue": total_amount
                }
                
                links_with_stats.append(PaymentLinkWithStats(**link_with_stats))
            
            return links_with_stats
            
        except Exception as e:
            logger.error(f"Get payment links error: {str(e)}")
            return []
    
    async def update_payment_link(
        self, 
        link_id: str,
        updates: PaymentLinkUpdate,
        user_id: str
    ) -> Optional[PaymentLinkResponse]:
        """
        Update payment link
        """
        try:
            # Get payment link to check project access
            link_result = await supabase_client.select_records(
                'payment_links',
                {'id': link_id},
                columns='project_id'
            )
            
            if not link_result.data:
                return None
            
            project_id = link_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Update payment link
            update_data = updates.dict(exclude_unset=True)
            if update_data.get('expires_at'):
                update_data['expires_at'] = update_data['expires_at'].isoformat()
            
            result = await supabase_client.update_record(
                'payment_links',
                {'id': link_id},
                update_data
            )
            
            if result.data:
                return PaymentLinkResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Update payment link error: {str(e)}")
            return None
    
    async def delete_payment_link(self, link_id: str, user_id: str) -> bool:
        """
        Delete payment link
        """
        try:
            # Get payment link to check project access
            link_result = await supabase_client.select_records(
                'payment_links',
                {'id': link_id},
                columns='project_id'
            )
            
            if not link_result.data:
                return False
            
            project_id = link_result.data[0]['project_id']
            
            # Check user has editor access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "editor"
            )
            
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Delete payment link
            await supabase_client.delete_record('payment_links', {'id': link_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Delete payment link error: {str(e)}")
            return False
    
    async def create_transaction(
        self, 
        transaction_data: TransactionCreate
    ) -> TransactionResponse:
        """
        Create a transaction
        """
        try:
            # Get payment link
            link_result = await supabase_client.select_records(
                'payment_links',
                {'id': transaction_data.payment_link_id},
                columns='id, amount, currency, status'
            )
            
            if not link_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment link not found"
                )
            
            payment_link = link_result.data[0]
            
            # Check if payment link is active
            if payment_link['status'] != 'active':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment link is not active"
            )
            
            # Check if amount matches
            if float(transaction_data.amount) != payment_link['amount']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Amount does not match payment link amount"
                )
            
            # Create transaction record
            transaction_record = {
                "payment_link_id": transaction_data.payment_link_id,
                "transaction_id": transaction_data.transaction_id or str(uuid.uuid4()),
                "user_email": transaction_data.user_email,
                "amount": float(transaction_data.amount),
                "currency": transaction_data.currency,
                "status": transaction_data.status,
                "payment_method": transaction_data.payment_method,
                "metadata": transaction_data.metadata,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.insert_record('transactions', transaction_record)
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create transaction"
                )
            
            return TransactionResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"Create transaction error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create transaction"
            )
    
    async def get_transactions(
        self, 
        payment_link_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20
    ) -> List[TransactionWithDetails]:
        """
        Get transactions
        """
        try:
            filters = {}
            
            if payment_link_id:
                filters['payment_link_id'] = payment_link_id
            
            if project_id:
                # Get payment links for this project
                links_result = await supabase_client.select_records(
                    'payment_links',
                    {'project_id': project_id},
                    columns='id'
                )
                
                if links_result.data:
                    link_ids = [link['id'] for link in links_result.data]
                    filters['payment_link_id'] = link_ids
            
            # Get transactions
            result = await supabase_client.select_records(
                'transactions',
                filters,
                columns='id, payment_link_id, transaction_id, user_email, amount, currency, status, payment_method, metadata, created_at, updated_at',
                order='created_at.desc',
                limit=limit
            )
            
            transactions = []
            for transaction in result.data or []:
                # Get payment link details
                link_result = await supabase_client.select_records(
                    'payment_links',
                    {'id': transaction['payment_link_id']},
                    columns='id, project_id, description'
                )
                
                transaction_with_details = {
                    **transaction,
                    "payment_link": link_result.data[0] if link_result.data else None
                }
                
                transactions.append(TransactionWithDetails(**transaction_with_details))
            
            return transactions
            
        except Exception as e:
            logger.error(f"Get transactions error: {str(e)}")
            return []
    
    async def update_transaction_status(
        self, 
        transaction_id: str,
        status: str,
        user_id: Optional[str] = None
    ) -> Optional[TransactionResponse]:
        """
        Update transaction status
        """
        try:
            # Get transaction
            trans_result = await supabase_client.select_records(
                'transactions',
                {'id': transaction_id},
                columns='payment_link_id'
            )
            
            if not trans_result.data:
                return None
            
            transaction = trans_result.data[0]
            
            # Check project access if user_id provided
            if user_id:
                link_result = await supabase_client.select_records(
                    'payment_links',
                    {'id': transaction['payment_link_id']},
                    columns='project_id'
                )
                
                if link_result.data:
                    has_access = await supabase_client.check_project_permission(
                        link_result.data[0]['project_id'], user_id, "viewer"
                    )
                    
                    if not has_access:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Insufficient permissions"
                        )
            
            # Update transaction
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = await supabase_client.update_record(
                'transactions',
                {'id': transaction_id},
                update_data
            )
            
            if result.data:
                return TransactionResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Update transaction status error: {str(e)}")
            return None
    
    async def create_xendit_invoice(
        self, 
        invoice_data: XenditInvoiceRequest
    ) -> XenditInvoiceResponse:
        """
        Create Xendit invoice
        """
        try:
            if not self.xendit_secret_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Xendit not configured"
                )
            
            headers = {
                "Authorization": f"Basic {self.xendit_secret_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "external_id": invoice_data.external_id,
                "amount": float(invoice_data.amount),
                "description": invoice_data.description,
                "currency": invoice_data.currency,
                "should_send_email": invoice_data.should_send_email
            }
            
            if invoice_data.customer:
                payload["customer"] = invoice_data.customer
            
            if invoice_data.items:
                payload["items"] = invoice_data.items
            
            if invoice_data.fees:
                payload["fees"] = invoice_data.fees
            
            response = requests.post(
                f"{self.xendit_url}/invoices",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Xendit API error: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create Xendit invoice"
                )
            
            return XenditInvoiceResponse(**response.json())
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Xendit request error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect to Xendit"
            )
        except Exception as e:
            logger.error(f"Create Xendit invoice error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invoice"
            )
    
    async def get_payment_stats(self, project_id: str, user_id: str) -> Optional[PaymentStats]:
        """
        Get payment statistics for project
        """
        try:
            # Check user has access
            has_access = await supabase_client.check_project_permission(
                project_id, user_id, "viewer"
            )
            
            if not has_access:
                return None
            
            # Get payment links
            links_result = await supabase_client.select_records(
                'payment_links',
                {'project_id': project_id},
                columns='id, status'
            )
            
            links = links_result.data or []
            total_links = len(links)
            active_links = len([link for link in links if link['status'] == 'active'])
            
            # Get transactions
            transactions_result = await supabase_client.select_records(
                'transactions',
                {'payment_link_id': 'in.(select id from payment_links where project_id=eq.{project_id})'},
                columns='status, amount, created_at'
            )
            
            transactions = transactions_result.data or []
            total_transactions = len(transactions)
            successful_transactions = len([t for t in transactions if t['status'] == 'paid'])
            pending_transactions = len([t for t in transactions if t['status'] == 'pending'])
            failed_transactions = len([t for t in transactions if t['status'] == 'failed'])
            
            # Calculate revenue
            total_revenue = sum(
                Decimal(str(t['amount'])) for t in transactions 
                if t['status'] == 'paid'
            )
            
            # Calculate monthly revenue
            one_month_ago = datetime.utcnow() - timedelta(days=30)
            monthly_revenue = sum(
                Decimal(str(t['amount'])) for t in transactions 
                if t['status'] == 'paid' and 
                datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')) > one_month_ago
            )
            
            # Calculate average transaction value
            avg_transaction_value = (
                total_revenue / successful_transactions 
                if successful_transactions > 0 else Decimal('0.00')
            )
            
            stats = PaymentStats(
                total_links=total_links,
                active_links=active_links,
                total_transactions=total_transactions,
                successful_transactions=successful_transactions,
                pending_transactions=pending_transactions,
                failed_transactions=failed_transactions,
                total_revenue=total_revenue,
                monthly_revenue=monthly_revenue,
                average_transaction_value=avg_transaction_value
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Get payment stats error: {str(e)}")
            return None
    
    async def get_payment_dashboard(
        self, 
        project_id: str,
        user_id: str
    ) -> Optional[PaymentDashboard]:
        """
        Get payment dashboard data
        """
        try:
            # Get stats
            stats = await self.get_payment_stats(project_id, user_id)
            if not stats:
                return None
            
            # Get recent transactions
            recent_transactions = await self.get_transactions(
                project_id=project_id,
                limit=10
            )
            
            # Get recent links
            recent_links = await self.get_payment_links(
                project_id=project_id,
                user_id=user_id,
                limit=5
            )
            
            # Generate revenue chart data (last 7 days)
            revenue_chart = []
            for i in range(7):
                date = datetime.utcnow() - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                
                # Calculate revenue for this date
                transactions_result = await supabase_client.select_records(
                    'transactions',
                    {
                        'payment_link_id': 'in.(select id from payment_links where project_id=eq.{project_id})',
                        'status': 'eq.paid',
                        'created_at': f'gte.{date_str}'
                    },
                    columns='amount'
                )
                
                daily_revenue = sum(
                    Decimal(str(t['amount'])) for t in transactions_result.data or []
                )
                
                revenue_chart.append({
                    "date": date_str,
                    "revenue": float(daily_revenue)
                })
            
            dashboard = PaymentDashboard(
                stats=stats,
                recent_transactions=recent_transactions,
                recent_links=recent_links,
                revenue_chart=list(reversed(revenue_chart))
            )
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Get payment dashboard error: {str(e)}")
            return None
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Process Xendit webhook
        """
        try:
            event_type = webhook_data.get('event')
            data = webhook_data.get('data', {})
            
            if event_type == 'invoice.paid':
                # Update transaction status to paid
                external_id = data.get('external_id')
                if external_id:
                    await self.update_transaction_status(external_id, 'paid')
            
            elif event_type == 'invoice.expired':
                # Update transaction status to failed
                external_id = data.get('external_id')
                if external_id:
                    await self.update_transaction_status(external_id, 'failed')
            
            return True
            
        except Exception as e:
            logger.error(f"Process webhook error: {str(e)}")
            return False


# Global service instance
payment_service = PaymentService()
