from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class PaymentLinkCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: Optional[str] = Field(None, max_length=500)
    project_id: str
    currency: str = "PHP"
    expires_at: Optional[datetime] = None


class PaymentLinkUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, regex="^(active|expired|paused)$")
    currency: Optional[str] = None
    expires_at: Optional[datetime] = None


class PaymentLinkResponse(BaseModel):
    id: str
    amount: Decimal
    description: Optional[str] = None
    project_id: str
    status: str
    currency: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentLinkWithStats(PaymentLinkResponse):
    transaction_count: int = 0
    total_amount: Decimal = Decimal('0.00')
    successful_transactions: int = 0
    pending_transactions: int = 0
    failed_transactions: int = 0
    revenue: Decimal = Decimal('0.00')


class TransactionCreate(BaseModel):
    payment_link_id: str
    user_email: str = Field(..., regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = "PHP"
    payment_method: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TransactionUpdate(BaseModel):
    status: Optional[str] = Field(None, regex="^(pending|paid|failed|refunded)$")
    payment_method: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    transaction_id: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    payment_link_id: str
    transaction_id: Optional[str] = None
    user_email: str
    amount: Decimal
    currency: str
    status: str
    payment_method: Optional[str] = None
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
    average_transaction_value: Decimal


class PaymentDashboard(BaseModel):
    stats: PaymentStats
    recent_transactions: List[TransactionWithDetails]
    recent_links: List[PaymentLinkWithStats]
    revenue_chart: List[Dict[str, Any]]


class WebhookEvent(BaseModel):
    event_id: str
    event: str
    created: datetime
    data: Dict[str, Any]


class RefundRequest(BaseModel):
    transaction_id: str
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    reason: Optional[str] = Field(None, max_length=500)


class RefundResponse(BaseModel):
    id: str
    transaction_id: str
    amount: Decimal
    status: str
    reason: Optional[str] = None
    created_at: datetime


class PaymentExport(BaseModel):
    format: str = Field("csv", regex="^(csv|json|xlsx)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    payment_link_id: Optional[str] = None
    status: Optional[str] = None


class PaymentAnalytics(BaseModel):
    daily_revenue: List[Dict[str, Any]]
    transaction_volume: List[Dict[str, Any]]
    payment_methods: Dict[str, int]
    top_customers: List[Dict[str, Any]]
    conversion_rates: Dict[str, float]
