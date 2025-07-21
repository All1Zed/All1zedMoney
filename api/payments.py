from services.konik_client import KonikClient
from services.webhook_service import webhook_service
from services.retry_service import retry_service
from services.analytics_service import analytics_service
from utils.helpers import generate_payment_reference
from utils.auth import get_user_from_api_key
from models.database import get_db, Transaction, User
from models.schemas import (
    PaymentRequest, PaymentResponse, BalanceResponse, 
    TransactionResponse, RetryRequest, AnalyticsResponse
)
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import uuid4
from zeep.exceptions import Fault
from datetime import datetime
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

konik = KonikClient()

def get_history():
    # Access and print raw request and response
    if konik.history.last_sent:
        request_str = konik.get_raw_request()
        print("\n📤 SOAP Request:")
        print(request_str)

    if konik.history.last_received:
        response_str = konik.get_raw_response()
        print("\n📥 SOAP Response:")
        print(response_str)

@router.get("/balance", response_model=BalanceResponse)
def check_balance(
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Check account balance"""
    txn_id = str(uuid4())
    try:
        result = konik.service.getAccountBalance()
        return {
            "success": True,
            "balance": result,
            "txn_id": txn_id,
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "txn_id": txn_id,
        }

@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(
    request: PaymentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Initiate a payment transaction"""
    logger.info("🚀 Initiating payment for %s", request.customer_mobile)
    
    # Generate transaction ID and payment reference
    txn_id = str(uuid4())
    payment_reference = request.reference or generate_payment_reference()
    
    # Create transaction record
    transaction = Transaction(
        txn_id=txn_id,
        payment_reference=payment_reference,
        customer_mobile=request.customer_mobile,
        amount=request.txn_amount,
        network=request.network.value,
        provider="konik",
        status="pending",
        user_id=current_user.id
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    try:
        # Process mobile money payment through Konik
        result = await _process_mobile_money_payment(request, payment_reference)
        
        # Update transaction with result
        transaction.status = "success" if result["success"] else "failed"
        transaction.response_code = result.get("response_code", 0)
        transaction.response_message = result.get("message", "")
        transaction.updated_at = datetime.utcnow()
        db.commit()
        
        # Send webhook notification if URL provided
        if request.webhook_url:
            background_tasks.add_task(
                webhook_service.notify_payment_status,
                transaction,
                request.webhook_url,
                db
            )
        
        if not result["success"]:
            logger.warning("❌ Payment failed: %s", result.get("message"))
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return {
            "success": True,
            "message": result.get("message", "Payment processed successfully"),
            "txn_id": txn_id,
            "payment_reference": payment_reference,
            "response_code": result.get("response_code", 0)
        }
        
    except Exception as e:
        # Update transaction as failed
        transaction.status = "failed"
        transaction.response_message = str(e)
        transaction.updated_at = datetime.utcnow()
        db.commit()
        
        logger.error("❌ Payment error: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def _process_mobile_money_payment(request: PaymentRequest, payment_reference: str) -> Dict[str, Any]:
    """Process mobile money payment through Konik"""
    try:
        response = konik.service.processCustomerPayment(
            transactionAmount=request.txn_amount,
            customerMobile=request.customer_mobile,
            paymentReference=payment_reference
        )
        
        logger.info("✅ Mobile money payment initiated successfully")
        
        return {
            "success": True,
            "message": response.get("responseMessage", "Payment processed"),
            "response_code": response.get("responseCode", 0),
        }
        
    except Fault as fault:
        return {
            "success": False,
            "message": f"SOAP Fault: {fault.message}",
            "response_code": -1,
        }

@router.get("/query/{payment_reference}", response_model=Dict[str, Any])
def query_status(
    payment_reference: str,
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Query payment status"""
    logger.info("🔍 Querying payment status for %s", payment_reference)
    
    # First check database
    transaction = db.query(Transaction).filter(
        Transaction.payment_reference == payment_reference,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If transaction is pending, query the provider
    if transaction.status == "pending":
        try:
            response = konik.service.queryCustomerPayment(paymentReference=payment_reference)
            
            # Update transaction status
            if response.get("paymentID"):
                transaction.status = "success"
            else:
                transaction.status = "failed"
            
            transaction.response_code = response.get("responseCode", 0)
            transaction.response_message = response.get("responseMessage", "")
            transaction.updated_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            logger.error(f"❌ Query error: {str(e)}")
    
    return {
        "txn_id": transaction.txn_id,
        "payment_reference": transaction.payment_reference,
        "status": transaction.status,
        "amount": transaction.amount,
        "customer_mobile": transaction.customer_mobile,
        "network": transaction.network,
        "provider": transaction.provider,
        "response_code": transaction.response_code,
        "response_message": transaction.response_message,
        "retry_count": transaction.retry_count,
        "created_at": transaction.created_at.isoformat(),
        "updated_at": transaction.updated_at.isoformat()
    }

@router.post("/retry", response_model=Dict[str, Any])
async def retry_transaction(
    retry_request: RetryRequest,
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Retry a failed transaction"""
    logger.info("🔄 Retrying transaction %s", retry_request.txn_id)
    
    transaction = db.query(Transaction).filter(
        Transaction.txn_id == retry_request.txn_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status == "success":
        raise HTTPException(status_code=400, detail="Transaction already successful")
    
    if transaction.retry_count >= transaction.max_retries:
        raise HTTPException(status_code=400, detail="Transaction has exceeded max retries")
    
    success = await retry_service.retry_failed_transaction(transaction, db)
    
    return {
        "success": success,
        "message": "Transaction retried successfully" if success else "Retry failed",
        "txn_id": transaction.txn_id,
        "retry_count": transaction.retry_count
    }

@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Get user's transactions"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return transactions

@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    days: int = 30,
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Get transaction analytics"""
    return analytics_service.get_transaction_analytics(db, current_user.id, days)

@router.get("/analytics/daily")
def get_daily_analytics(
    days: int = 7,
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Get daily transaction analytics"""
    return analytics_service.get_daily_transactions(db, current_user.id, days)

@router.get("/analytics/failed")
def get_failed_transactions(
    limit: int = 50,
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Get failed transactions"""
    return analytics_service.get_failed_transactions(db, current_user.id, limit)

@router.get("/analytics/retry")
def get_retry_analytics(
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Get retry analytics"""
    return analytics_service.get_retry_analytics(db, current_user.id)

@router.get("/analytics/providers")
def get_provider_analytics(
    current_user: User = Depends(get_user_from_api_key),
    db: Session = Depends(get_db)
):
    """Get provider performance analytics"""
    return analytics_service.get_provider_performance(db, current_user.id)
