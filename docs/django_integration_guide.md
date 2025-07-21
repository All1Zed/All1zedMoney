# Django Backend Integration Guide

## 🔐 **Complete Authentication Flow**

### **Step-by-Step Process:**

#### **Step 1: Initial Setup (One-time)**

```python
# 1. Register your Django backend as a user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "django_backend",
    "email": "backend@yourcompany.com",
    "password": "secure_password_123"
  }'
```

#### **Step 2: Get JWT Token**

```python
# 2. Login to get JWT token for API key management
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "django_backend",
    "password": "secure_password_123"
  }'
```

#### **Step 3: Create API Key**

```python
# 3. Create API key using JWT token
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Django Backend API Key"
  }'
```

#### **Step 4: Store API Key Securely**

```python
# Django settings.py
PAYMENT_GATEWAY_CONFIG = {
    "BASE_URL": "http://localhost:8000",
    "API_KEY": "your_generated_api_key_here",  # Store this securely
    "DEFAULT_NETWORK": "MTN",
    "TIMEOUT": 30,
}
```

#### **Step 5: Make API Calls**

```python
# 5. Use API key for all payment operations
curl -X POST "http://localhost:8000/api/v1/payments/initiate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_mobile": "260977123456",
    "txn_amount": 100.00,
    "network": "MTN"
  }'
```

## 🏗️ **Django Implementation**

### **1. Django Settings Configuration**

```python
# settings.py
import os
from pathlib import Path

# Payment Gateway Configuration
PAYMENT_GATEWAY_CONFIG = {
    "BASE_URL": os.getenv("PAYMENT_GATEWAY_BASE_URL", "http://localhost:8000"),
    "API_KEY": os.getenv("PAYMENT_GATEWAY_API_KEY"),  # Store in environment
    "DEFAULT_NETWORK": os.getenv("PAYMENT_GATEWAY_NETWORK", "MTN"),
    "TIMEOUT": int(os.getenv("PAYMENT_GATEWAY_TIMEOUT", "30")),
    "WEBHOOK_SECRET": os.getenv("PAYMENT_GATEWAY_WEBHOOK_SECRET"),
}

# Environment variables (.env file)
# PAYMENT_GATEWAY_BASE_URL=http://localhost:8000
# PAYMENT_GATEWAY_API_KEY=your_api_key_here
# PAYMENT_GATEWAY_NETWORK=MTN
# PAYMENT_GATEWAY_WEBHOOK_SECRET=your_webhook_secret
```

### **2. Django Service Class**

```python
# services/payment_gateway.py
import requests
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PaymentGatewayService:
    """Service class for interacting with payment gateway"""
    
    def __init__(self):
        self.base_url = settings.PAYMENT_GATEWAY_CONFIG["BASE_URL"]
        self.api_key = settings.PAYMENT_GATEWAY_CONFIG["API_KEY"]
        self.default_network = settings.PAYMENT_GATEWAY_CONFIG["DEFAULT_NETWORK"]
        self.timeout = settings.PAYMENT_GATEWAY_CONFIG["TIMEOUT"]
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def initiate_payment(self, customer_mobile: str, amount: float, 
                        network: Optional[str] = None, 
                        webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Initiate a payment transaction"""
        
        url = f"{self.base_url}/api/v1/payments/initiate"
        payload = {
            "customer_mobile": customer_mobile,
            "txn_amount": amount,
            "network": network or self.default_network
        }
        
        if webhook_url:
            payload["webhook_url"] = webhook_url
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Payment initiated for {customer_mobile}: {amount}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment initiation failed: {str(e)}")
            raise
    
    def query_payment_status(self, payment_reference: str) -> Dict[str, Any]:
        """Query payment status"""
        
        url = f"{self.base_url}/api/v1/payments/query/{payment_reference}"
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment query failed: {str(e)}")
            raise
    
    def retry_payment(self, txn_id: str) -> Dict[str, Any]:
        """Retry a failed payment"""
        
        url = f"{self.base_url}/api/v1/payments/retry"
        payload = {"txn_id": txn_id}
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Payment retry initiated for {txn_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment retry failed: {str(e)}")
            raise
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        
        url = f"{self.base_url}/api/v1/payments/balance"
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Balance query failed: {str(e)}")
            raise
```

### **3. Django Models**

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class PaymentTransaction(models.Model):
    """Django model to store payment transactions"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retry', 'Retry'),
    ]
    
    NETWORK_CHOICES = [
        ('MTN', 'MTN'),
        ('Airtel', 'Airtel'),
        ('Zamtel', 'Zamtel'),
    ]
    
    # Django user who initiated the payment
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Payment gateway transaction details
    txn_id = models.CharField(max_length=255, unique=True)
    payment_reference = models.CharField(max_length=255, unique=True)
    customer_mobile = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    network = models.CharField(max_length=10, choices=NETWORK_CHOICES)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Response details
    response_code = models.IntegerField(null=True, blank=True)
    response_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
    
    def __str__(self):
        return f"{self.txn_id} - {self.customer_mobile} - {self.amount}"
```

### **4. Django Views**

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from .services.payment_gateway import PaymentGatewayService
from .models import PaymentTransaction

@login_required
@require_http_methods(["POST"])
def initiate_payment(request):
    """Initiate a payment from Django"""
    
    try:
        data = json.loads(request.body)
        customer_mobile = data.get('customer_mobile')
        amount = data.get('amount')
        network = data.get('network', 'MTN')
        
        # Validate input
        if not customer_mobile or not amount:
            return JsonResponse({
                'success': False,
                'message': 'customer_mobile and amount are required'
            }, status=400)
        
        # Initialize payment gateway service
        pg_service = PaymentGatewayService()
        
        # Initiate payment
        result = pg_service.initiate_payment(
            customer_mobile=customer_mobile,
            amount=amount,
            network=network,
            webhook_url=f"{request.build_absolute_uri('/api/payments/webhook/')}"
        )
        
        # Store transaction in Django database
        transaction = PaymentTransaction.objects.create(
            user=request.user,
            txn_id=result['txn_id'],
            payment_reference=result['payment_reference'],
            customer_mobile=customer_mobile,
            amount=amount,
            network=network,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Payment initiated successfully',
            'data': result,
            'transaction_id': transaction.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def query_payment_status(request, payment_reference):
    """Query payment status"""
    
    try:
        pg_service = PaymentGatewayService()
        result = pg_service.query_payment_status(payment_reference)
        
        # Update local transaction if found
        try:
            transaction = PaymentTransaction.objects.get(
                payment_reference=payment_reference
            )
            transaction.status = result['status']
            transaction.response_code = result.get('response_code')
            transaction.response_message = result.get('response_message')
            transaction.save()
        except PaymentTransaction.DoesNotExist:
            pass
        
        return JsonResponse({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """Handle webhook notifications from payment gateway"""
    
    try:
        data = json.loads(request.body)
        payment_reference = data.get('payment_reference')
        status = data.get('status')
        
        # Update local transaction
        try:
            transaction = PaymentTransaction.objects.get(
                payment_reference=payment_reference
            )
            transaction.status = status
            transaction.response_code = data.get('response_code')
            transaction.response_message = data.get('response_message')
            transaction.save()
            
            # You can add additional logic here (send notifications, etc.)
            
        except PaymentTransaction.DoesNotExist:
            pass
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
```

### **5. Django URLs**

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/payments/initiate/', views.initiate_payment, name='initiate_payment'),
    path('api/payments/query/<str:payment_reference>/', views.query_payment_status, name='query_payment_status'),
    path('api/payments/webhook/', views.payment_webhook, name='payment_webhook'),
]
```

## 🔄 **Complete Flow Summary:**

1. **Setup Phase (One-time):**
   - Register Django backend as user
   - Login to get JWT token
   - Create API key
   - Store API key securely

2. **Runtime Phase (Every API call):**
   - Use API key in Authorization header
   - Make payment API calls
   - Handle responses and webhooks

3. **Security:**
   - API key stored in environment variables
   - HTTPS in production
   - Rate limiting handled by payment gateway
   - Webhook verification (optional)

This setup provides a secure, scalable way for your Django backend to authenticate and consume the payment gateway API! 