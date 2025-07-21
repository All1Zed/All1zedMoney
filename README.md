# All1ZED Payment Gateway

A comprehensive payment gateway that supports mobile money providers (MTN, Airtel, Zamtel) with authentication, webhooks, retry mechanisms, analytics, and SRE practices.

## Features

### ✅ Authentication & Security
- **JWT Authentication**: Secure token-based authentication
- **API Key Management**: Generate and manage API keys for different users
- **User Registration & Login**: Complete user management system
- **Password Hashing**: Secure password storage with bcrypt

### ✅ Database Storage
- **PostgreSQL/SQLite Support**: Flexible database options
- **Transaction Tracking**: Complete transaction history and status
- **User Management**: User accounts and API key storage
- **Retry Logs**: Detailed retry attempt tracking
- **Webhook Logs**: Webhook delivery tracking

### ✅ Webhook Support
- **Provider Webhooks**: Receive status updates from payment providers
- **Custom Webhooks**: Send notifications to external systems
- **Webhook Logging**: Track webhook delivery success/failure
- **Konik Integration**: Mobile money webhook support

### ✅ Retry & Reconciliation
- **Automatic Retries**: Configurable retry mechanism for failed transactions
- **Exponential Backoff**: Smart retry delays (1min, 5min, 15min)
- **Reconciliation**: Query provider status to reconcile transactions
- **Retry Analytics**: Track retry success rates and patterns

### ✅ Mobile Money Support
- **MTN Mobile Money**: Via Konik SOAP gateway
- **Airtel Money**: Via Konik SOAP gateway
- **Zamtel Mobile Money**: Via Konik SOAP gateway
- **Extensible Architecture**: Easy to add new mobile money providers

### ✅ Rate Limiting & Analytics
- **Rate Limiting**: Protect API from abuse with configurable limits
- **Transaction Analytics**: Success rates, amounts, trends
- **Provider Performance**: Performance metrics by provider
- **Daily Reports**: Daily transaction summaries
- **Failed Transaction Tracking**: Monitor and analyze failures

### ✅ SRE & Monitoring
- **Prometheus Metrics**: Comprehensive monitoring metrics
- **Health Checks**: Database, external services, system health
- **System Monitoring**: CPU, memory, disk usage
- **Request Tracking**: Payment duration, success rates
- **Error Tracking**: Detailed error logging and monitoring

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd payment_gateway

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration
```

### 2. Environment Configuration

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=sqlite:///./payment_gateway.db
# or for PostgreSQL: postgresql://user:password@localhost/payment_gateway

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# Konik SOAP Configuration
WSDL_URL=https://konik.cgrate.com/wsdl
SERVICE_URL=https://konik.cgrate.com/service
KONIK_USERNAME=your_username
KONIK_PASSWORD=your_password
```

### 3. Run the Application

```bash
# Start the server
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## API Usage

### Authentication

#### 1. Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword"
  }'
```

#### 2. Login and Get Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepassword"
  }'
```

#### 3. Create API Key
```bash
curl -X POST "http://localhost:8000/api/v1/auth/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My API Key"
  }'
```

### Payment Processing

#### Initiate Payment
```bash
curl -X POST "http://localhost:8000/api/v1/payments/initiate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_mobile": "260977123456",
    "txn_amount": 100.00,
    "network": "MTN",
    "webhook_url": "https://your-app.com/webhook"
  }'
```

#### Query Payment Status
```bash
curl -X GET "http://localhost:8000/api/v1/payments/query/PAYMENT_REFERENCE" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Retry Failed Transaction
```bash
curl -X POST "http://localhost:8000/api/v1/payments/retry" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "txn_id": "TRANSACTION_ID"
  }'
```

### Analytics

#### Get Transaction Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/payments/analytics?days=30" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Get Daily Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/payments/analytics/daily?days=7" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Get Failed Transactions
```bash
curl -X GET "http://localhost:8000/api/v1/payments/analytics/failed?limit=50" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Webhooks

#### Receive Provider Webhooks
```bash
# Konik webhook
curl -X POST "http://localhost:8000/api/v1/webhooks/konik" \
  -H "Content-Type: application/json" \
  -d '{
    "paymentReference": "REF123",
    "responseCode": 200,
    "responseMessage": "Payment successful"
  }'
```

## Database Schema

### Tables

1. **users**: User accounts and authentication
2. **api_keys**: API key management
3. **transactions**: Payment transaction records
4. **retry_logs**: Retry attempt tracking
5. **webhook_logs**: Webhook delivery tracking

### Key Relationships

- Users can have multiple API keys
- Users can have multiple transactions
- Transactions can have multiple retry attempts
- Transactions can have multiple webhook delivery attempts

## Monitoring & SRE

### Health Checks

- **Database Connectivity**: Verify database connection
- **External Services**: Check Konik service availability
- **System Health**: Monitor CPU, memory, disk usage

### Metrics (Prometheus)

- **Payment Requests**: Total requests by status, network, provider
- **Payment Duration**: Processing time histograms
- **Webhook Requests**: Webhook delivery metrics
- **Retry Attempts**: Retry success/failure rates
- **System Metrics**: Memory, CPU usage

### Rate Limiting

- **Authentication**: 10 requests/minute
- **Payments**: 50 requests/minute
- **Analytics**: 30 requests/minute
- **Webhooks**: 1000 requests/minute

## Development

### Project Structure

```
payment_gateway/
├── main.py                 # Main application
├── config.py              # Configuration settings
├── requirements.txt        # Dependencies
├── models/
│   ├── database.py        # Database models
│   └── schemas.py         # Pydantic schemas
├── api/
│   ├── auth.py           # Authentication endpoints
│   ├── payments.py       # Payment endpoints
│   ├── webhooks.py       # Webhook endpoints
│   └── health.py         # Health check endpoints
├── services/
│   ├── konik_client.py   # Konik SOAP client
│   ├── webhook_service.py # Webhook handling
│   ├── retry_service.py  # Retry mechanism
│   └── analytics_service.py # Analytics
└── utils/
    ├── auth.py           # Authentication utilities
    ├── helpers.py        # Helper functions
    ├── rate_limiter.py   # Rate limiting
    └── monitoring.py     # Monitoring & SRE
```

### Adding New Mobile Money Providers

1. Create provider client in `services/`
2. Add provider enum in `models/schemas.py`
3. Update payment processing logic in `api/payments.py`
4. Add webhook handler in `api/webhooks.py`

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```

## Production Deployment

### Environment Variables

Set these in production:

```env
DATABASE_URL=postgresql://user:password@host/database
SECRET_KEY=your-super-secure-secret-key
WSDL_URL=https://konik.cgrate.com/wsdl
SERVICE_URL=https://konik.cgrate.com/service
KONIK_USERNAME=production_username
KONIK_PASSWORD=production_password
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Monitoring Setup

1. **Prometheus**: Scrape metrics from `/metrics`
2. **Grafana**: Create dashboards for payment metrics
3. **Alerting**: Set up alerts for high failure rates
4. **Logging**: Configure structured logging

## Security Considerations

- Use strong SECRET_KEY in production
- Enable HTTPS in production
- Configure CORS appropriately
- Implement proper API key rotation
- Monitor for suspicious activity
- Regular security audits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 