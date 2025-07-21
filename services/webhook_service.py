import httpx
import asyncio
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
import logging

from models.database import WebhookLog, Transaction
from models.schemas import WebhookPayload

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self):
        self.timeout = 30  # seconds
        
    async def send_webhook(self, webhook_url: str, payload: Dict[str, Any], db: Session) -> bool:
        """Send webhook notification to external system"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                # Log webhook attempt
                webhook_log = WebhookLog(
                    transaction_id=payload.get("transaction_id"),
                    webhook_url=webhook_url,
                    payload=str(payload),
                    response_status=response.status_code,
                    response_body=response.text
                )
                db.add(webhook_log)
                db.commit()
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"✅ Webhook sent successfully to {webhook_url}")
                    return True
                else:
                    logger.warning(f"❌ Webhook failed with status {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Webhook error: {str(e)}")
            
            # Log failed webhook attempt
            webhook_log = WebhookLog(
                transaction_id=payload.get("transaction_id"),
                webhook_url=webhook_url,
                payload=str(payload),
                response_status=0,
                response_body=str(e)
            )
            db.add(webhook_log)
            db.commit()
            
            return False
    
    def create_webhook_payload(self, transaction: Transaction) -> Dict[str, Any]:
        """Create webhook payload from transaction"""
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
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def notify_payment_status(self, transaction: Transaction, webhook_url: str, db: Session):
        """Notify external system about payment status change"""
        payload = self.create_webhook_payload(transaction)
        
        # Send webhook asynchronously
        success = await self.send_webhook(webhook_url, payload, db)
        
        if success:
            logger.info(f"✅ Payment status notification sent for txn {transaction.txn_id}")
        else:
            logger.error(f"❌ Failed to send payment status notification for txn {transaction.txn_id}")
        
        return success

# Global webhook service instance
webhook_service = WebhookService() 