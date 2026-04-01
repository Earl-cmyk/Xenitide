from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class PaymentLinkBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None
    currency: str = "PHP"


class PaymentLinkCreate(PaymentLinkBase):
    project_id: str
    expires_at: Optional[datetime] = None


class PaymentLinkUpdate(BaseModel):
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    status: Optional[str] = None  # 'active', 'expired', 'paused'
    expires_at: Optional[datetime] = None


class PaymentLinkResponse(PaymentLinkBase):
    id: str
    project_id: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentLinkWithStats(PaymentLinkResponse):
    transaction_count: int = 0
    total_amount: Decimal = Decimal('0.00')
    successful_transactions: int = 0
    pending_transactions: int = 0


class TransactionBase(BaseModel):
    user_email: str
    amount: Decimal = Field(..., gt=0)
    currency: str = "PHP"
    payment_method: Optional[str] = None


class TransactionCreate(TransactionBase):
    payment_link_id: str
    transaction_id: Optional[str] = None  # External payment processor ID
    status: str = "pending"  # 'pending', 'paid', 'failed', 'refunded'
    metadata: Optional[Dict[str, Any]] = None


class TransactionUpdate(BaseModel):
    status: Optional[str] = None
    payment_method: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TransactionResponse(TransactionBase):
    id: str
    payment_link_id: str
    transaction_id: Optional[str] = None
    status: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionWithDetails(TransactionResponse):
    payment_link: Optional[Dict[str, Any]] = None


class XenditInvoiceRequest(BaseModel):
    external_id: str
    amount: Decimal
    description: Optional[str] = None
    currency: str = "PHP"
    should_send_email: bool = True
    customer: Optional[Dict[str, Any]] = None
    items: Optional[List[Dict[str, Any]]] = None
    fees: Optional[List[Dict[str, Any]]] = None


class XenditInvoiceResponse(BaseModel):
    id: str
    external_id: str
    user_id: str
    status: str
    merchant_name: str
    amount: Decimal
    description: Optional[str] = None
    invoice_url: str
    expiry_date: Optional[datetime] = None
    created: datetime
    updated: datetime
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    paid_amount: Optional[Decimal] = None
    currency: str
    customer: Optional[Dict[str, Any]] = None
    items: Optional[List[Dict[str, Any]]] = None
    fees: Optional[List[Dict[str, Any]]] = None


class PaymentStats(BaseModel):
    total_links: int
    active_links: int
    total_transactions: int
    successful_transactions: int
    pending_transactions: int
    failed_transactions: int
    total_revenue: Decimal
    monthly_revenue: Decimal


class PaymentDashboard(BaseModel):
    stats: PaymentStats
    recent_transactions: List[TransactionWithDetails]
    recent_links: List[PaymentLinkWithStats]


class WebhookEvent(BaseModel):
    event_id: str
    event: str
    created: datetime
    data: Dict[str, Any]


class RefundRequest(BaseModel):
    transaction_id: str
    amount: Optional[Decimal] = None
    reason: Optional[str] = None


class RefundResponse(BaseModel):
    id: str
    transaction_id: str
    amount: Decimal
    status: str
    created_at: datetime
