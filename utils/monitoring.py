from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Prometheus metrics
PAYMENT_REQUESTS = Counter('payment_requests_total', 'Total payment requests', ['status', 'network', 'provider'])
PAYMENT_DURATION = Histogram('payment_duration_seconds', 'Payment processing duration', ['network', 'provider'])
WEBHOOK_REQUESTS = Counter('webhook_requests_total', 'Total webhook requests', ['provider', 'status'])
RETRY_ATTEMPTS = Counter('retry_attempts_total', 'Total retry attempts', ['status'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')
SYSTEM_MEMORY = Gauge('system_memory_bytes', 'System memory usage in bytes')
SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU usage percentage')

class MonitoringMiddleware:
    """Middleware for monitoring requests and system metrics"""
    
    def __init__(self):
        self.start_time = time.time()
    
    async def __call__(self, request: Request, call_next):
        # Record request start time
        start_time = time.time()
        
        # Update system metrics
        self._update_system_metrics()
        
        # Process request
        response = await call_next(request)
        
        # Record request duration
        duration = time.time() - start_time
        
        # Record metrics based on path
        self._record_request_metrics(request, response, duration)
        
        return response
    
    def _update_system_metrics(self):
        """Update system-level metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY.set(memory.used)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            SYSTEM_CPU.set(cpu_percent)
            
        except Exception as e:
            logger.error(f"❌ Error updating system metrics: {str(e)}")
    
    def _record_request_metrics(self, request: Request, response: Response, duration: float):
        """Record request-specific metrics"""
        path = request.url.path
        
        if path.startswith("/payments/initiate"):
            # Record payment metrics
            status = "success" if response.status_code == 200 else "failed"
            network = "unknown"
            provider = "unknown"
            
            # Try to extract network and provider from request body
            try:
                body = request.body()
                if body:
                    import json
                    data = json.loads(body)
                    network = data.get("network", "unknown")
                    provider = "konik"  # Default for now
            except:
                pass
            
            PAYMENT_REQUESTS.labels(status=status, network=network, provider=provider).inc()
            PAYMENT_DURATION.labels(network=network, provider=provider).observe(duration)
            
        elif path.startswith("/webhooks"):
            # Record webhook metrics
            provider = path.split("/")[-1] if path != "/webhooks" else "unknown"
            status = "success" if response.status_code == 200 else "failed"
            WEBHOOK_REQUESTS.labels(provider=provider, status=status).inc()
            
        elif path.startswith("/payments/retry"):
            # Record retry metrics
            status = "success" if response.status_code == 200 else "failed"
            RETRY_ATTEMPTS.labels(status=status).inc()

class HealthChecker:
    """Health check utilities"""
    
    @staticmethod
    def check_database_connection(db_session) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # Try to execute a simple query
            db_session.execute("SELECT 1")
            return {
                "status": "healthy",
                "message": "Database connection is working"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
    
    @staticmethod
    def check_external_services() -> Dict[str, Any]:
        """Check external service connectivity"""
        services = {}
        
        # Check Konik service
        try:
            from services.konik_client import KonikClient
            konik = KonikClient()
            konik.service.getAccountBalance()
            services["konik"] = {"status": "healthy", "message": "Konik service is reachable"}
        except Exception as e:
            services["konik"] = {"status": "unhealthy", "message": f"Konik service error: {str(e)}"}
        
        return services
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get overall system health"""
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "memory_usage_percent": memory.percent,
                    "cpu_usage_percent": cpu_percent,
                    "disk_usage_percent": (disk.used / disk.total) * 100
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"System health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

# Global monitoring instance
monitoring_middleware = MonitoringMiddleware()
health_checker = HealthChecker()

def get_metrics():
    """Get Prometheus metrics"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST) 