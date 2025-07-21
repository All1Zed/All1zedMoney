from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NetworkProvider(str, Enum):
    MTN = "MTN"
    AIRTEL = "Airtel"
    ZAMTEL = "Zamtel"

class PaymentProvider(str, Enum):
    KONIK = "konik"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    MPESA = "mpesa"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"

class PaymentRequest(BaseModel):
    customer_mobile: str
    txn_amount: float
    network: NetworkProvider
    reference: Optional[str] = None
    webhook_url: Optional[str] = None

class PaymentResponse(BaseModel):
    success: bool
    message: str
    txn_id: Optional[str] = None
    payment_reference: Optional[str] = None
    response_code: Optional[int] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

class APIKeyCreate(BaseModel):
    name: str

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_hash: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

class TransactionResponse(BaseModel):
    id: int
    txn_id: str
    payment_reference: str
    customer_mobile: str
    amount: float
    network: str
    provider: str
    status: str
    response_code: Optional[int]
    response_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime

class WebhookPayload(BaseModel):
    txn_id: str
    payment_reference: str
    status: TransactionStatus
    amount: float
    customer_mobile: str
    network: str
    provider: str
    response_code: Optional[int]
    response_message: Optional[str]
    timestamp: datetime

class RetryRequest(BaseModel):
    txn_id: str

class BalanceResponse(BaseModel):
    success: bool
    balance: Optional[float] = None
    message: Optional[str] = None
    txn_id: Optional[str] = None

class AnalyticsResponse(BaseModel):
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    total_amount: float
    success_rate: float
    average_amount: float
    transactions_by_network: dict
    transactions_by_provider: dict 
    