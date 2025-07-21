import asyncio
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import logging

from models.database import Transaction, RetryLog
from services.konik_client import KonikClient
from services.webhook_service import webhook_service

logger = logging.getLogger(__name__)

class RetryService:
    def __init__(self):
        self.konik = KonikClient()
        self.max_retries = 3
        self.retry_delays = [60, 300, 900]  # 1min, 5min, 15min in seconds
        
    async def retry_failed_transaction(self, transaction: Transaction, db: Session) -> bool:
        """Retry a failed transaction"""
        if transaction.retry_count >= transaction.max_retries:
            logger.warning(f"❌ Transaction {transaction.txn_id} has exceeded max retries")
            return False
        
        try:
            # Increment retry count
            transaction.retry_count += 1
            transaction.status = "retry"
            transaction.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"🔄 Retrying transaction {transaction.txn_id} (attempt {transaction.retry_count})")
            
            # Retry the payment
            if transaction.provider == "konik":
                success = await self._retry_konik_payment(transaction, db)
            else:
                logger.warning(f"❌ Unsupported provider for retry: {transaction.provider}")
                return False
            
            # Log retry attempt
            retry_log = RetryLog(
                transaction_id=transaction.id,
                retry_number=transaction.retry_count,
                status="success" if success else "failed",
                retry_at=datetime.utcnow()
            )
            db.add(retry_log)
            db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Retry error for transaction {transaction.txn_id}: {str(e)}")
            
            # Log failed retry
            retry_log = RetryLog(
                transaction_id=transaction.id,
                retry_number=transaction.retry_count,
                status="failed",
                response_message=str(e),
                retry_at=datetime.utcnow()
            )
            db.add(retry_log)
            db.commit()
            
            return False
    
    async def _retry_konik_payment(self, transaction: Transaction, db: Session) -> bool:
        """Retry payment using Konik provider"""
        try:
            response = self.konik.service.processCustomerPayment(
                transactionAmount=transaction.amount,
                customerMobile=transaction.customer_mobile,
                paymentReference=transaction.payment_reference
            )
            
            # Update transaction status
            transaction.response_code = response.get("responseCode", 0)
            transaction.response_message = response.get("responseMessage", "")
            
            if response.get("responseCode") == 200:  # Success
                transaction.status = "success"
                logger.info(f"✅ Retry successful for transaction {transaction.txn_id}")
                return True
            else:
                transaction.status = "failed"
                logger.warning(f"❌ Retry failed for transaction {transaction.txn_id}: {response.get('responseMessage')}")
                return False
                
        except Exception as e:
            transaction.status = "failed"
            transaction.response_message = str(e)
            logger.error(f"❌ Retry exception for transaction {transaction.txn_id}: {str(e)}")
            return False
        finally:
            transaction.updated_at = datetime.utcnow()
            db.commit()
    
    async def reconcile_transaction(self, transaction: Transaction, db: Session) -> bool:
        """Reconcile transaction by querying provider status"""
        try:
            logger.info(f"🔍 Reconciling transaction {transaction.txn_id}")
            
            if transaction.provider == "konik":
                return await self._reconcile_konik_transaction(transaction, db)
            else:
                logger.warning(f"❌ Unsupported provider for reconciliation: {transaction.provider}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Reconciliation error for transaction {transaction.txn_id}: {str(e)}")
            return False
    
    async def _reconcile_konik_transaction(self, transaction: Transaction, db: Session) -> bool:
        """Reconcile transaction with Konik provider"""
        try:
            response = self.konik.service.queryCustomerPayment(
                paymentReference=transaction.payment_reference
            )
            
            # Update transaction based on reconciliation
            transaction.response_code = response.get("responseCode", 0)
            transaction.response_message = response.get("responseMessage", "")
            
            if response.get("paymentID"):
                transaction.status = "success"
                logger.info(f"✅ Reconciliation successful for transaction {transaction.txn_id}")
                return True
            else:
                transaction.status = "failed"
                logger.warning(f"❌ Reconciliation failed for transaction {transaction.txn_id}")
                return False
                
        except Exception as e:
            transaction.response_message = str(e)
            logger.error(f"❌ Reconciliation exception for transaction {transaction.txn_id}: {str(e)}")
            return False
        finally:
            transaction.updated_at = datetime.utcnow()
            db.commit()
    
    async def process_pending_transactions(self, db: Session):
        """Process all pending transactions that need retry"""
        pending_transactions = db.query(Transaction).filter(
            Transaction.status.in_(["failed", "retry"]),
            Transaction.retry_count < Transaction.max_retries
        ).all()
        
        logger.info(f"🔄 Processing {len(pending_transactions)} pending transactions")
        
        for transaction in pending_transactions:
            # Check if enough time has passed since last retry
            if self._should_retry_transaction(transaction):
                await self.retry_failed_transaction(transaction, db)
                
                # Add delay between retries to avoid overwhelming the provider
                await asyncio.sleep(1)
    
    def _should_retry_transaction(self, transaction: Transaction) -> bool:
        """Check if enough time has passed to retry transaction"""
        if transaction.retry_count == 0:
            return True
        
        # Get the appropriate delay for this retry attempt
        if transaction.retry_count <= len(self.retry_delays):
            delay_seconds = self.retry_delays[transaction.retry_count - 1]
        else:
            delay_seconds = self.retry_delays[-1]  # Use last delay for subsequent retries
        
        # Check if enough time has passed
        time_since_update = datetime.utcnow() - transaction.updated_at
        return time_since_update.total_seconds() >= delay_seconds

# Global retry service instance
retry_service = RetryService() 