"""
Django Backend Integration with All1ZED Payment Gateway
=====================================================

This example shows how a Django backend would authenticate and consume
the payment gateway API from start to finish.
"""

import requests
import json
from typing import Dict, Any, Optional

class PaymentGatewayClient:
    """Client for Django backend to interact with payment gateway"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = None
        self.jwt_token = None
        
    def register_backend(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        Step 1: Register the Django backend as a user in the payment gateway
        This is typically done once during setup.
        """
        url = f"{self.base_url}/api/v1/auth/register"
        payload = {
            "username": username,
            "email": email,
            "password": password
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        print("✅ Backend registered successfully")
        return response.json()
    
    def login_and_get_jwt(self, username: str, password: str) -> str:
        """
        Step 2: Login to get JWT token for API key management
        """
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {
            "username": username,
            "password": password
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        self.jwt_token = data["access_token"]
        
        print("✅ JWT token obtained")
        return self.jwt_token
    
    def create_api_key(self, key_name: str) -> str:
        """
        Step 3: Create an API key for the backend service
        This is the key that will be used for all payment operations.
        """
        if not self.jwt_token:
            raise ValueError("Must login first to get JWT token")
        
        url = f"{self.base_url}/api/v1/auth/api-keys"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        payload = {"name": key_name}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        self.api_key = data["key_hash"]  # This is the actual API key
        
        print(f"✅ API key created: {self.api_key[:10]}...")
        return self.api_key
    
    def initiate_payment(self, customer_mobile: str, amount: float, network: str, 
                        webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Step 4: Make payment API calls using the API key
        This is what the Django backend will do for each payment.
        """
        if not self.api_key:
            raise ValueError("Must create API key first")
        
        url = f"{self.base_url}/api/v1/payments/initiate"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "customer_mobile": customer_mobile,
            "txn_amount": amount,
            "network": network
        }
        
        if webhook_url:
            payload["webhook_url"] = webhook_url
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        print("✅ Payment initiated successfully")
        return response.json()
    
    def query_payment_status(self, payment_reference: str) -> Dict[str, Any]:
        """Query payment status"""
        if not self.api_key:
            raise ValueError("Must create API key first")
        
        url = f"{self.base_url}/api/v1/payments/query/{payment_reference}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        if not self.api_key:
            raise ValueError("Must create API key first")
        
        url = f"{self.base_url}/api/v1/payments/balance"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()


# Example Django settings.py configuration
DJANGO_PAYMENT_GATEWAY_CONFIG = {
    "BASE_URL": "http://localhost:8000",
    "API_KEY": "your_api_key_here",  # Store this securely
    "WEBHOOK_SECRET": "your_webhook_secret",  # For webhook verification
    "DEFAULT_NETWORK": "MTN",
    "RETRY_ATTEMPTS": 3,
    "TIMEOUT": 30,
}


# Example Django model for storing payment gateway credentials
"""
# models.py
from django.db import models

class PaymentGatewayConfig(models.Model):
    api_key = models.CharField(max_length=255)
    base_url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment Gateway Configuration"
        verbose_name_plural = "Payment Gateway Configurations"
"""


# Example Django service class
"""
# services.py
import requests
from django.conf import settings
from typing import Dict, Any

class PaymentGatewayService:
    def __init__(self):
        self.base_url = settings.PAYMENT_GATEWAY_CONFIG["BASE_URL"]
        self.api_key = settings.PAYMENT_GATEWAY_CONFIG["API_KEY"]
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def initiate_payment(self, customer_mobile: str, amount: float, 
                        network: str = "MTN") -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/payments/initiate"
        payload = {
            "customer_mobile": customer_mobile,
            "txn_amount": amount,
            "network": network,
            "webhook_url": f"{settings.BASE_URL}/api/payments/webhook/"
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def query_payment(self, payment_reference: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/payments/query/{payment_reference}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
"""


# Complete setup example
def setup_django_backend():
    """Complete setup process for Django backend"""
    
    # Initialize client
    client = PaymentGatewayClient("http://localhost:8000")
    
    # Step 1: Register the backend (do this once during setup)
    try:
        client.register_backend(
            username="django_backend",
            email="backend@yourcompany.com",
            password="secure_password_123"
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print("Backend already registered, proceeding to login...")
        else:
            raise
    
    # Step 2: Login to get JWT token
    client.login_and_get_jwt("django_backend", "secure_password_123")
    
    # Step 3: Create API key for the backend
    api_key = client.create_api_key("Django Backend API Key")
    
    # Step 4: Store this API key securely in Django settings
    print(f"\n🔐 Store this API key in your Django settings:")
    print(f"PAYMENT_GATEWAY_API_KEY = '{api_key}'")
    
    # Step 5: Test the integration
    print("\n🧪 Testing payment initiation...")
    result = client.initiate_payment(
        customer_mobile="260977123456",
        amount=100.00,
        network="MTN"
    )
    print(f"Payment result: {result}")
    
    return api_key


if __name__ == "__main__":
    # Run the complete setup
    api_key = setup_django_backend()
    print(f"\n✅ Django backend setup complete!")
    print(f"API Key: {api_key}") 