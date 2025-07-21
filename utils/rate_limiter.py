from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "default": "100/minute",
    "auth": "10/minute",
    "payments": "50/minute",
    "analytics": "30/minute",
    "webhooks": "1000/minute"
}

def get_rate_limit_for_path(path: str) -> str:
    """Get appropriate rate limit based on path"""
    if path.startswith("/auth"):
        return RATE_LIMITS["auth"]
    elif path.startswith("/payments"):
        return RATE_LIMITS["payments"]
    elif path.startswith("/analytics"):
        return RATE_LIMITS["analytics"]
    elif path.startswith("/webhooks"):
        return RATE_LIMITS["webhooks"]
    else:
        return RATE_LIMITS["default"]

def rate_limit_middleware(request: Request):
    """Custom rate limiting middleware"""
    client_ip = get_remote_address(request)
    path = request.url.path
    
    # Get rate limit for this path
    rate_limit = get_rate_limit_for_path(path)
    
    # Check if client has exceeded rate limit
    if limiter.is_rate_limited(client_ip, rate_limit):
        logger.warning(f"🚫 Rate limit exceeded for {client_ip} on {path}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Limit: {rate_limit}"
        )
    
    # Add rate limit headers to response
    request.state.rate_limit_info = {
        "limit": rate_limit,
        "remaining": limiter.get_remaining(client_ip, rate_limit),
        "reset_time": limiter.get_reset_time(client_ip, rate_limit)
    }

# Rate limit decorators for specific endpoints
def rate_limit_payments():
    """Rate limit decorator for payment endpoints"""
    return limiter.limit(RATE_LIMITS["payments"])

def rate_limit_auth():
    """Rate limit decorator for authentication endpoints"""
    return limiter.limit(RATE_LIMITS["auth"])

def rate_limit_analytics():
    """Rate limit decorator for analytics endpoints"""
    return limiter.limit(RATE_LIMITS["analytics"])

def rate_limit_webhooks():
    """Rate limit decorator for webhook endpoints"""
    return limiter.limit(RATE_LIMITS["webhooks"]) 