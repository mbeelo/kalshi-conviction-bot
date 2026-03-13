"""Kalshi API authentication module with HMAC signature support."""
import base64
import datetime
import os
from urllib.parse import urlparse
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from config import Config


class KalshiAuth:
    """Handles Kalshi API authentication with RSA-PSS signatures."""

    def __init__(self):
        self.api_key_id = os.getenv('KALSHI_API_KEY_ID')
        self.private_key_path = os.getenv('KALSHI_PRIVATE_KEY_PATH')
        self.demo_mode = os.getenv('KALSHI_DEMO', 'true').lower() == 'true'

        # Set base URL based on demo mode
        if self.demo_mode:
            self.base_url = 'https://demo-api.kalshi.co/trade-api/v2'
        else:
            self.base_url = 'https://api.elections.kalshi.com/trade-api/v2'

        self.private_key = self._load_private_key()

    def _load_private_key(self):
        """Load the private key from file or base64 environment variable."""
        # Try loading from base64 environment variable first (for Railway deployment)
        base64_key = os.getenv('KALSHI_PRIVATE_KEY_BASE64')
        if base64_key:
            try:
                key_data = base64.b64decode(base64_key)
                return serialization.load_pem_private_key(
                    key_data,
                    password=None,
                    backend=default_backend()
                )
            except Exception as e:
                raise ValueError(f"Failed to load private key from base64: {e}")

        # Fallback to file path
        if not self.private_key_path or not os.path.exists(self.private_key_path):
            raise ValueError(f"Private key not found at: {self.private_key_path} and no KALSHI_PRIVATE_KEY_BASE64 set")

        try:
            with open(self.private_key_path, "rb") as f:
                return serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
        except Exception as e:
            raise ValueError(f"Failed to load private key from file: {e}")

    def create_signature(self, timestamp: str, method: str, path: str) -> str:
        """
        Create the request signature for Kalshi API.

        Args:
            timestamp: Request timestamp in milliseconds
            method: HTTP method (GET, POST, etc.)
            path: API path without query parameters

        Returns:
            Base64 encoded signature
        """
        # Strip query parameters before signing
        path_without_query = path.split('?')[0]

        # Create the message to sign: timestamp + method + path
        message = f"{timestamp}{method}{path_without_query}".encode('utf-8')

        # Sign with RSA-PSS
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )

        # Return base64 encoded signature
        return base64.b64encode(signature).decode('utf-8')

    def get_auth_headers(self, method: str, path: str) -> dict:
        """
        Generate authentication headers for Kalshi API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., '/portfolio/balance')

        Returns:
            Dictionary with authentication headers
        """
        # Generate timestamp in milliseconds
        timestamp = str(int(datetime.datetime.now().timestamp() * 1000))

        # Create full path for signing (includes /trade-api/v2)
        full_path = urlparse(self.base_url + path).path

        # Generate signature
        signature = self.create_signature(timestamp, method, full_path)

        return {
            'KALSHI-ACCESS-KEY': self.api_key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }

    def get_base_url(self) -> str:
        """Get the base URL for API requests."""
        return self.base_url

    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return self.demo_mode