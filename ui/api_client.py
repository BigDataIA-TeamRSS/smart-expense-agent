"""API client for Streamlit to communicate with FastAPI backend"""
import requests
import os
from typing import Optional, Dict, List
from streamlit import session_state as st_session


class APIClient:
    """Client for making API calls to FastAPI backend"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the FastAPI backend. Defaults to environment variable or localhost
        """
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        self._token = None
    
    @property
    def token(self) -> Optional[str]:
        """Get authentication token from session state"""
        return st_session.get("api_token")
    
    @token.setter
    def token(self, value: str):
        """Set authentication token in session state"""
        st_session["api_token"] = value
    
    def _get_headers(self, require_auth: bool = True) -> Dict[str, str]:
        """Get headers with optional authentication"""
        headers = {"Content-Type": "application/json"}
        if require_auth:
            token = self.token
            if token:
                headers["Authorization"] = f"Bearer {token}"
                print(f"[API] Token found: {token[:20]}..." if len(token) > 20 else f"[API] Token found: {token}")
            else:
                print("[API] WARNING: No token found in session state!")
        return headers
    
    def _request(self, method: str, endpoint: str, require_auth: bool = True, **kwargs) -> requests.Response:
        """Make HTTP request"""
        import time
        request_start = time.time()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(require_auth=require_auth)
        headers.update(kwargs.pop("headers", {}))
        
        print(f"[API] Calling {method} {url} at {request_start:.3f}")
        if kwargs.get("json"):
            print(f"[API] Request body: {kwargs['json']}")
        if kwargs.get("params"):
            print(f"[API] Query params: {kwargs['params']}")
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            request_time = time.time() - request_start
            print(f"[API] Response status: {response.status_code} in {request_time:.3f}s")
            response.raise_for_status()
            print(f"[API] Success: {endpoint} (took {request_time:.3f}s)")
            return response
        except requests.exceptions.RequestException as e:
            request_time = time.time() - request_start
            print(f"[API] Error calling {endpoint} after {request_time:.3f}s: {str(e)}")
            raise
    
    # Authentication endpoints (no auth required)
    def register(self, username: str, email: str, password: str) -> Dict:
        """Register a new user - no authentication required"""
        response = self._request(
            "POST",
            "/api/auth/register",
            require_auth=False,  # Registration doesn't need auth
            json={"username": username, "email": email, "password": password}
        )
        return response.json()
    
    def login(self, username: str, password: str) -> Dict:
        """Login and get token - no authentication required"""
        response = self._request(
            "POST",
            "/api/auth/login",
            require_auth=False,  # Login doesn't need auth
            json={"username": username, "password": password}
        )
        data = response.json()
        token = data.get("access_token")
        if token:
            self.token = token
            print(f"[API] Token saved to session state: {token[:20]}..." if len(token) > 20 else f"[API] Token saved: {token}")
        else:
            print("[API] WARNING: No access_token in login response!")
        return data
    
    # User endpoints (now under /api/auth)
    def get_current_user(self) -> Dict:
        """Get current user profile"""
        response = self._request("GET", "/api/auth/me")
        return response.json()
    
    def update_profile(self, **profile_data) -> Dict:
        """Update user profile"""
        response = self._request(
            "PUT",
            "/api/auth/me/profile",
            json=profile_data
        )
        return response.json()
    
    def update_preferences(self, **preferences) -> Dict:
        """Update user preferences"""
        response = self._request(
            "PUT",
            "/api/auth/me/preferences",
            json=preferences
        )
        return response.json()
    
    def change_password(self, current_password: str, new_password: str) -> Dict:
        """Change password"""
        response = self._request(
            "POST",
            "/api/auth/me/password",
            json={"current_password": current_password, "new_password": new_password}
        )
        return response.json()
    
    def clear_user_data(self) -> Dict:
        """Clear all user data"""
        response = self._request("DELETE", "/api/auth/me/data")
        return response.json()
    
    # Account endpoints
    def get_accounts(self) -> List[Dict]:
        """Get all user accounts"""
        response = self._request("GET", "/api/accounts")
        return response.json()
    
    def get_account(self, account_id: str) -> Dict:
        """Get specific account"""
        response = self._request("GET", f"/api/accounts/{account_id}")
        return response.json()
    
    def refresh_account(self, account_id: str) -> Dict:
        """Refresh a single account"""
        response = self._request("POST", f"/api/accounts/{account_id}/refresh")
        return response.json()
    
    def refresh_all_accounts(self) -> Dict:
        """Refresh all accounts"""
        response = self._request("POST", "/api/accounts/refresh-all")
        return response.json()
    
    def delete_account(self, account_id: str) -> Dict:
        """Delete an account"""
        response = self._request("DELETE", f"/api/accounts/{account_id}")
        return response.json()
    
    # Transaction endpoints
    def get_transactions(
        self,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Get transactions with optional filters"""
        params = {
            "limit": limit,
            "offset": offset
        }
        if account_id:
            params["account_id"] = account_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if search:
            params["search"] = search
        if min_amount is not None:
            params["min_amount"] = min_amount
        if max_amount is not None:
            params["max_amount"] = max_amount
        
        response = self._request("GET", "/api/transactions", params=params)
        return response.json()
    
    def get_transaction_summary(
        self,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get transaction summary"""
        params = {}
        if account_id:
            params["account_id"] = account_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = self._request("GET", "/api/transactions/summary", params=params)
        return response.json()
    
    # Plaid endpoints
    def create_link_token(self) -> Dict:
        """Create Plaid Link token"""
        response = self._request("POST", "/api/plaid/link-token")
        return response.json()
    
    def get_link_status(self, link_token: str) -> Dict:
        """Get Plaid Link token status"""
        response = self._request("GET", f"/api/plaid/link-status?link_token={link_token}")
        return response.json()
    
    def exchange_public_token(self, public_token: str) -> Dict:
        """Exchange Plaid public token"""
        response = self._request(
            "POST",
            "/api/plaid/exchange-token",
            json={"public_token": public_token}
        )
        return response.json()
    
    def sync_transactions(self, account_id: str) -> Dict:
        """Sync transactions for an account"""
        response = self._request("POST", f"/api/plaid/sync/{account_id}")
        return response.json()
    
    # Statement endpoints
    def upload_statement(self, file_bytes: bytes, filename: str) -> Dict:
        """Upload PDF statement"""
        print(f"[API] Uploading statement: {filename} ({len(file_bytes)} bytes)")
        files = {"file": (filename, file_bytes, "application/pdf")}
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        print(f"[API] Calling POST {self.base_url}/api/statements/upload")
        try:
            response = requests.post(
                f"{self.base_url}/api/statements/upload",
                files=files,
                headers=headers
            )
            print(f"[API] Upload response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"[API] Upload successful: {result.get('transactions_count', 0)} transactions")
            return result
        except requests.exceptions.RequestException as e:
            print(f"[API] Error uploading statement: {str(e)}")
            raise
    
    def get_upload_history(self) -> Dict:
        """Get PDF upload history"""
        response = self._request("GET", "/api/statements/history")
        return response.json()
    
    # Analytics endpoints
    def get_dashboard(self) -> Dict:
        """Get dashboard data"""
        response = self._request("GET", "/api/analytics/dashboard")
        return response.json()
    
    def get_spending_by_category(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get spending by category"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = self._request("GET", "/api/analytics/spending-by-category", params=params)
        return response.json()
    
    def get_monthly_trends(self, months: int = 6) -> Dict:
        """Get monthly spending trends"""
        response = self._request("GET", f"/api/analytics/monthly-trends?months={months}")
        return response.json()
    
    # AI Agent endpoints
    def get_recommendations(self) -> Dict:
        """Get AI recommendations"""
        response = self._request("POST", "/api/ai/recommendations")
        return response.json()
    
    def chat_with_ai(self, message: str) -> Dict:
        """Chat with AI"""
        response = self._request(
            "POST",
            "/api/ai/chat",
            json={"message": message}
        )
        return response.json()
    
    def get_daily_summary(self) -> Dict:
        """Get daily summary"""
        response = self._request("POST", "/api/ai/daily-summary")
        return response.json()


# Global instance
def get_api_client() -> APIClient:
    """Get or create API client instance"""
    if "api_client" not in st_session:
        st_session["api_client"] = APIClient()
    return st_session["api_client"]
