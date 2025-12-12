# FastAPI Application

This FastAPI application provides REST API endpoints for the Smart Expense Analyzer, designed to work with the Streamlit frontend and deploy on Google Cloud Run.

## Structure

```
src/app/
├── main.py              # FastAPI application entry point
├── dependencies.py      # Shared dependencies (DB, Plaid, Auth)
├── exceptions.py       # Exception handlers
├── routers/            # API route handlers
│   ├── auth.py         # Authentication & user profile management
│   ├── accounts.py     # Bank account management
│   ├── transactions.py  # Transaction queries
│   ├── plaid.py        # Plaid integration
│   ├── statements.py   # PDF statement upload
│   ├── analytics.py    # Analytics endpoints
│   └── ai_agents.py    # AI agent endpoints
└── schemas/            # Pydantic models for validation
    ├── user.py
    ├── account.py
    ├── transaction.py
    └── common.py
```

## Endpoints

### Authentication & User Management
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/me/profile` - Update profile
- `PUT /api/auth/me/preferences` - Update preferences
- `POST /api/auth/me/password` - Change password
- `DELETE /api/auth/me/data` - Clear user data
- `DELETE /api/auth/me` - Delete account

### Accounts
- `GET /api/accounts` - Get all accounts
- `GET /api/accounts/{id}` - Get specific account
- `POST /api/accounts/{id}/refresh` - Refresh account data
- `POST /api/accounts/refresh-all` - Refresh all accounts
- `DELETE /api/accounts/{id}` - Delete account

### Transactions
- `GET /api/transactions` - Get transactions (with filters)
- `GET /api/transactions/summary` - Get summary statistics

### Plaid
- `POST /api/plaid/link-token` - Create Plaid Link token
- `GET /api/plaid/link-status` - Check link token status
- `POST /api/plaid/exchange-token` - Exchange public token
- `POST /api/plaid/sync/{account_id}` - Sync transactions

### Statements
- `POST /api/statements/upload` - Upload PDF statement
- `GET /api/statements/history` - Get upload history

### Analytics
- `GET /api/analytics/dashboard` - Dashboard summary
- `GET /api/analytics/spending-by-category` - Category spending
- `GET /api/analytics/monthly-trends` - Monthly trends

### AI Agents
- `POST /api/ai/recommendations` - Get recommendations
- `POST /api/ai/chat` - Chat with AI
- `POST /api/ai/daily-summary` - Daily summary

## Authentication

Currently uses simple token-based authentication:
- Token format: `username:password_hash`
- Include in header: `Authorization: Bearer username:password_hash`
- Or: `Authorization: username:password_hash`

**Note:** For production, upgrade to JWT authentication.

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables in .env file
# See DEPLOYMENT.md for required variables

# Run the application
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Or
python -m src.app.main
```

## Testing

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Deployment

See `DEPLOYMENT.md` in the project root for Cloud Run deployment instructions.
