from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from models.database import Transaction, User
from models.schemas import AnalyticsResponse

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        pass
    
    def get_transaction_analytics(self, db: Session, user_id: int = None, days: int = 30) -> AnalyticsResponse:
        """Get comprehensive transaction analytics"""
        try:
            # Base query
            query = db.query(Transaction)
            
            # Filter by user if specified
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            # Filter by date range
            start_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Transaction.created_at >= start_date)
            
            # Get total transactions
            total_transactions = query.count()
            
            # Get successful transactions
            successful_transactions = query.filter(Transaction.status == "success").count()
            
            # Get failed transactions
            failed_transactions = query.filter(Transaction.status == "failed").count()
            
            # Calculate success rate
            success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
            
            # Get total amount
            total_amount_result = query.with_entities(func.sum(Transaction.amount)).scalar()
            total_amount = float(total_amount_result) if total_amount_result else 0.0
            
            # Calculate average amount
            average_amount = (total_amount / total_transactions) if total_transactions > 0 else 0.0
            
            # Get transactions by network
            network_stats = db.query(
                Transaction.network,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.created_at >= start_date
            )
            
            if user_id:
                network_stats = network_stats.filter(Transaction.user_id == user_id)
            
            network_stats = network_stats.group_by(Transaction.network).all()
            
            transactions_by_network = {
                stat.network: {
                    "count": stat.count,
                    "total_amount": float(stat.total_amount) if stat.total_amount else 0.0
                }
                for stat in network_stats
            }
            
            # Get transactions by provider
            provider_stats = db.query(
                Transaction.provider,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.created_at >= start_date
            )
            
            if user_id:
                provider_stats = provider_stats.filter(Transaction.user_id == user_id)
            
            provider_stats = provider_stats.group_by(Transaction.provider).all()
            
            transactions_by_provider = {
                stat.provider: {
                    "count": stat.count,
                    "total_amount": float(stat.total_amount) if stat.total_amount else 0.0
                }
                for stat in provider_stats
            }
            
            return AnalyticsResponse(
                total_transactions=total_transactions,
                successful_transactions=successful_transactions,
                failed_transactions=failed_transactions,
                total_amount=total_amount,
                success_rate=success_rate,
                average_amount=average_amount,
                transactions_by_network=transactions_by_network,
                transactions_by_provider=transactions_by_provider
            )
            
        except Exception as e:
            logger.error(f"❌ Analytics error: {str(e)}")
            raise
    
    def get_daily_transactions(self, db: Session, user_id: int = None, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily transaction counts"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.query(
                func.date(Transaction.created_at).label('date'),
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(Transaction.created_at >= start_date)
            
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            daily_stats = query.group_by(func.date(Transaction.created_at)).all()
            
            return [
                {
                    "date": stat.date,
                    "count": stat.count,
                    "total_amount": float(stat.total_amount) if stat.total_amount else 0.0
                }
                for stat in daily_stats
            ]
            
        except Exception as e:
            logger.error(f"❌ Daily transactions error: {str(e)}")
            return []
    
    def get_failed_transactions(self, db: Session, user_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent failed transactions"""
        try:
            query = db.query(Transaction).filter(Transaction.status == "failed")
            
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            failed_transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "txn_id": txn.txn_id,
                    "payment_reference": txn.payment_reference,
                    "customer_mobile": txn.customer_mobile,
                    "amount": txn.amount,
                    "network": txn.network,
                    "provider": txn.provider,
                    "response_code": txn.response_code,
                    "response_message": txn.response_message,
                    "retry_count": txn.retry_count,
                    "created_at": txn.created_at.isoformat()
                }
                for txn in failed_transactions
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed transactions error: {str(e)}")
            return []
    
    def get_retry_analytics(self, db: Session, user_id: int = None) -> Dict[str, Any]:
        """Get retry analytics"""
        try:
            query = db.query(Transaction)
            
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            # Get transactions that have been retried
            retried_transactions = query.filter(Transaction.retry_count > 0).count()
            
            # Get transactions that succeeded after retry
            retry_success = query.filter(
                and_(Transaction.retry_count > 0, Transaction.status == "success")
            ).count()
            
            # Get average retry count
            avg_retry_result = db.query(func.avg(Transaction.retry_count)).scalar()
            avg_retry_count = float(avg_retry_result) if avg_retry_result else 0.0
            
            return {
                "total_retried_transactions": retried_transactions,
                "retry_success_count": retry_success,
                "retry_success_rate": (retry_success / retried_transactions * 100) if retried_transactions > 0 else 0,
                "average_retry_count": avg_retry_count
            }
            
        except Exception as e:
            logger.error(f"❌ Retry analytics error: {str(e)}")
            return {}
    
    def get_provider_performance(self, db: Session, user_id: int = None) -> Dict[str, Any]:
        """Get performance metrics by provider"""
        try:
            start_date = datetime.utcnow() - timedelta(days=30)
            
            query = db.query(
                Transaction.provider,
                func.count(Transaction.id).label('total'),
                func.sum(func.case((Transaction.status == "success", 1), else_=0)).label('success'),
                func.avg(Transaction.amount).label('avg_amount'),
                func.avg(Transaction.retry_count).label('avg_retries')
            ).filter(Transaction.created_at >= start_date)
            
            if user_id:
                query = query.filter(Transaction.user_id == user_id)
            
            provider_stats = query.group_by(Transaction.provider).all()
            
            performance = {}
            for stat in provider_stats:
                success_rate = (stat.success / stat.total * 100) if stat.total > 0 else 0
                performance[stat.provider] = {
                    "total_transactions": stat.total,
                    "successful_transactions": stat.success,
                    "success_rate": success_rate,
                    "average_amount": float(stat.avg_amount) if stat.avg_amount else 0.0,
                    "average_retries": float(stat.avg_retries) if stat.avg_retries else 0.0
                }
            
            return performance
            
        except Exception as e:
            logger.error(f"❌ Provider performance error: {str(e)}")
            return {}

# Global analytics service instance
analytics_service = AnalyticsService() 