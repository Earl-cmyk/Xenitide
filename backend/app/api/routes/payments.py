from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from app.services.payment_service import payment_service
from app.schemas.payment import (
    PaymentLinkCreate, PaymentLinkUpdate, PaymentLinkResponse, PaymentLinkWithStats,
    TransactionCreate, TransactionUpdate, TransactionResponse, TransactionWithDetails,
    XenditInvoiceRequest, XenditInvoiceResponse,
    PaymentStats, PaymentDashboard
)
from app.api.deps import (
    get_current_user, require_project_access, require_project_editor,
    get_pagination_params
)
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


# Payment Links endpoints

@router.post("/links", response_model=PaymentLinkResponse)
async def create_payment_link(
    link_data: PaymentLinkCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new payment link
    """
    try:
        return await payment_service.create_payment_link(link_data, current_user.get("sub"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create payment link error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment link"
        )


@router.get("/links/project/{project_id}", response_model=list[PaymentLinkWithStats])
async def get_project_payment_links(
    project_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get project payment links with statistics
    """
    try:
        return await payment_service.get_payment_links(project_id, current_user.get("sub"), limit)
    except Exception as e:
        logger.error(f"Get payment links error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment links"
        )


@router.get("/links/{link_id}", response_model=PaymentLinkWithStats)
async def get_payment_link(
    link_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get payment link by ID with statistics
    """
    try:
        # Get payment link to check project access
        links = await payment_service.get_payment_links(
            current_user.get("project_id"),  # This would need to be passed differently
            current_user.get("sub"),
            1
        )
        
        # For now, return a placeholder
        return {"message": "Get single payment link not yet implemented"}
    except Exception as e:
        logger.error(f"Get payment link error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment link"
        )


@router.put("/links/{link_id}", response_model=PaymentLinkResponse)
async def update_payment_link(
    link_id: str,
    updates: PaymentLinkUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update payment link
    """
    try:
        link = await payment_service.update_payment_link(link_id, updates, current_user.get("sub"))
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        return link
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update payment link error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update payment link"
        )


@router.delete("/links/{link_id}")
async def delete_payment_link(
    link_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete payment link
    """
    try:
        success = await payment_service.delete_payment_link(link_id, current_user.get("sub"))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        return {"message": "Payment link deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete payment link error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete payment link"
        )


# Transactions endpoints

@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a transaction
    """
    try:
        return await payment_service.create_transaction(transaction_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create transaction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction"
        )


@router.get("/transactions", response_model=list[TransactionWithDetails])
async def get_transactions(
    payment_link_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get transactions
    """
    try:
        return await payment_service.get_transactions(
            payment_link_id=payment_link_id,
            user_id=current_user.get("sub"),
            project_id=project_id,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Get transactions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transactions"
        )


@router.get("/transactions/{transaction_id}", response_model=TransactionWithDetails)
async def get_transaction(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get transaction by ID
    """
    try:
        transactions = await payment_service.get_transactions(
            user_id=current_user.get("sub"),
            limit=1
        )
        
        # For now, return a placeholder
        return {"message": "Get single transaction not yet implemented"}
    except Exception as e:
        logger.error(f"Get transaction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transaction"
        )


@router.put("/transactions/{transaction_id}/status")
async def update_transaction_status(
    transaction_id: str,
    status_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update transaction status
    """
    try:
        status = status_data.get("status")
        if not status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status is required"
            )
        
        transaction = await payment_service.update_transaction_status(
            transaction_id,
            status,
            current_user.get("sub")
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return {"message": "Transaction status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update transaction status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transaction status"
        )


# Xendit integration endpoints

@router.post("/xendit/invoices", response_model=XenditInvoiceResponse)
async def create_xendit_invoice(
    invoice_data: XenditInvoiceRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create Xendit invoice
    """
    try:
        return await payment_service.create_xendit_invoice(invoice_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create Xendit invoice error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Xendit invoice"
        )


@router.post("/xendit/webhook")
async def xendit_webhook(
    request: Request,
    webhook_token: Optional[str] = Query(None)
):
    """
    Process Xendit webhook
    """
    try:
        # Verify webhook token if configured
        # TODO: Implement webhook verification
        
        # Get webhook data
        webhook_data = await request.json()
        
        # Process webhook
        success = await payment_service.process_webhook(webhook_data)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process webhook"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )


# Statistics and dashboard endpoints

@router.get("/project/{project_id}/stats", response_model=PaymentStats)
async def get_payment_stats(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get payment statistics for project
    """
    try:
        stats = await payment_service.get_payment_stats(project_id, current_user.get("sub"))
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get payment stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment stats"
        )


@router.get("/project/{project_id}/dashboard", response_model=PaymentDashboard)
async def get_payment_dashboard(
    project_id: str,
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get payment dashboard
    """
    try:
        dashboard = await payment_service.get_payment_dashboard(project_id, current_user.get("sub"))
        
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get payment dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment dashboard"
        )


# Additional utility endpoints

@router.post("/links/{link_id}/activate")
async def activate_payment_link(
    link_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Activate payment link
    """
    try:
        link = await payment_service.update_payment_link(
            link_id,
            PaymentLinkUpdate(status="active"),
            current_user.get("sub")
        )
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        return {"message": "Payment link activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate payment link error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate payment link"
        )


@router.post("/links/{link_id}/deactivate")
async def deactivate_payment_link(
    link_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deactivate payment link
    """
    try:
        link = await payment_service.update_payment_link(
            link_id,
            PaymentLinkUpdate(status="paused"),
            current_user.get("sub")
        )
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment link not found"
            )
        
        return {"message": "Payment link deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate payment link error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate payment link"
        )


@router.post("/transactions/{transaction_id}/refund")
async def refund_transaction(
    transaction_id: str,
    refund_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Refund transaction
    """
    try:
        # TODO: Implement refund functionality
        return {"message": "Refund functionality not yet implemented"}
    except Exception as e:
        logger.error(f"Refund transaction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refund transaction"
        )


@router.get("/project/{project_id}/export")
async def export_payment_data(
    project_id: str,
    format: str = Query("csv", regex="^(csv|json|xlsx)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Export payment data
    """
    try:
        # TODO: Implement export functionality
        return {"message": "Export functionality not yet implemented"}
    except Exception as e:
        logger.error(f"Export payment data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export payment data"
        )


@router.get("/project/{project_id}/analytics")
async def get_payment_analytics(
    project_id: str,
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    current_user: Dict[str, Any] = Depends(require_project_access(project_id, "viewer"))
):
    """
    Get payment analytics
    """
    try:
        # TODO: Implement analytics functionality
        return {"message": "Analytics functionality not yet implemented"}
    except Exception as e:
        logger.error(f"Get payment analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment analytics"
        )
