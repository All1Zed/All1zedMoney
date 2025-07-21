from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from models.database import get_db, Transaction
from models.schemas import WebhookPayload
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/konik")
async def konik_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive webhook notifications from Konik provider"""
    try:
        # Get the raw body
        body = await request.body()
        payload = json.loads(body)
        
        logger.info(f"📥 Received Konik webhook: {payload}")
        
        # Extract payment reference from payload
        payment_reference = payload.get("paymentReference")
        if not payment_reference:
            raise HTTPException(status_code=400, detail="Missing payment reference")
        
        # Find the transaction
        transaction = db.query(Transaction).filter(
            Transaction.payment_reference == payment_reference
        ).first()
        
        if not transaction:
            logger.warning(f"❌ Transaction not found for payment reference: {payment_reference}")
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Update transaction status based on webhook payload
        response_code = payload.get("responseCode", 0)
        response_message = payload.get("responseMessage", "")
        
        if response_code == 200:
            transaction.status = "success"
            logger.info(f"✅ Transaction {transaction.txn_id} marked as successful")
        else:
            transaction.status = "failed"
            logger.warning(f"❌ Transaction {transaction.txn_id} marked as failed: {response_message}")
        
        transaction.response_code = response_code
        transaction.response_message = response_message
        transaction.updated_at = datetime.utcnow()
        db.commit()
        
        return {"status": "success", "message": "Webhook processed successfully"}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/logs")
async def get_webhook_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get webhook logs for debugging"""
    from models.database import WebhookLog
    
    logs = db.query(WebhookLog).order_by(
        WebhookLog.sent_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "transaction_id": log.transaction_id,
            "webhook_url": log.webhook_url,
            "payload": log.payload,
            "response_status": log.response_status,
            "response_body": log.response_body,
            "sent_at": log.sent_at.isoformat()
        }
        for log in logs
    ] 