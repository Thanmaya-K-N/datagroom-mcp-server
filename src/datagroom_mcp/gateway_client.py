"""HTTP client for Datagroom Gateway API requests."""

import httpx
from typing import Any, Dict, Optional
import logging

from .config import Config

logger = logging.getLogger(__name__)


class GatewayClient:
    """Async HTTP client for Datagroom Gateway with PAT authentication."""
    
    def __init__(self):
        self.base_url = Config.GATEWAY_URL
        self.pat_token = Config.PAT_TOKEN
        self.timeout = httpx.Timeout(60.0)  # 60 second timeout
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with PAT authentication."""
        return {
            "Authorization": f"Bearer {self.pat_token}",
            "Content-Type": "application/json",
        }
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """
        Make GET request to Gateway.
        
        Args:
            endpoint: API endpoint (e.g., "/api/datasets")
            
        Returns:
            JSON response as dictionary
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = Config.get_gateway_url(endpoint)
        
        logger.info(f"GET {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
    
    async def post(
        self, 
        endpoint: str, 
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request to Gateway.
        
        Args:
            endpoint: API endpoint
            json: JSON body
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = Config.get_gateway_url(endpoint)
        
        logger.info(f"POST {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url, 
                headers=self._get_headers(),
                json=json,
                params=params
            )
            response.raise_for_status()
            return response.json()


# Global client instance
gateway_client = GatewayClient()
