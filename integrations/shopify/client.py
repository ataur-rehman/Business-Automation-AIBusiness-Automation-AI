"""
Shopify Admin API Client
Basic implementation for Streamlit frontend
"""
import httpx
from typing import Dict, Any, Optional, List
import asyncio


class ShopifyAuthError(Exception):
    """Raised when authentication fails"""
    pass


class ShopifyAPIError(Exception):
    """Raised when API request fails"""
    pass


class ShopifyAdminClient:
    """Simple Shopify Admin API client"""
    
    def __init__(self, shop_domain: str, access_token: str):
        # Clean and validate domain
        self.shop_domain = shop_domain.strip().replace('https://', '').replace('http://', '')
        
        # Remove trailing slashes and paths
        self.shop_domain = self.shop_domain.split('/')[0]
        
        # Ensure it ends with .myshopify.com
        if not self.shop_domain:
            raise ValueError("Shop domain cannot be empty")
        
        if '.myshopify.com' not in self.shop_domain:
            # If user just provided the shop name, append .myshopify.com
            self.shop_domain = f"{self.shop_domain}.myshopify.com"
        
        self.access_token = access_token.strip()
        self.base_url = f"https://{self.shop_domain}/admin/api/2024-10"
        
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        self._client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close any open connections"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection by fetching shop info"""
        try:
            async with httpx.AsyncClient(verify=True, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/shop.json",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 401:
                    raise ShopifyAuthError("Invalid access token. Please check your Admin API access token.")
                elif response.status_code == 404:
                    raise ShopifyAuthError(f"Shop not found. Please verify your domain: {self.shop_domain}")
                elif response.status_code != 200:
                    raise ShopifyAPIError(f"API error: {response.status_code} - {response.text}")
                
                data = response.json()
                return {
                    'success': True,
                    'shop': data.get('shop', {})
                }
        except httpx.ConnectError:
            raise ShopifyAPIError(f"Cannot connect to {self.shop_domain}. Please verify your shop domain is correct (e.g., your-store.myshopify.com)")
        except httpx.TimeoutException:
            raise ShopifyAPIError("Connection timeout. Please try again.")
        except httpx.RequestError as e:
            raise ShopifyAPIError(f"Connection error: {str(e)}")
    
    async def get_shop_info(self) -> Dict[str, Any]:
        """Get shop information"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/shop.json",
                headers=self.headers,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json().get('shop', {})
    
    async def get_products(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get products from shop"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/products.json",
                headers=self.headers,
                params={'limit': limit},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json().get('products', [])
    
    async def get_orders(self, limit: int = 50, status: str = 'any') -> List[Dict[str, Any]]:
        """Get orders from shop"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/orders.json",
                headers=self.headers,
                params={'limit': limit, 'status': status},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json().get('orders', [])
    
    async def get_customers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get customers from shop"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/customers.json",
                headers=self.headers,
                params={'limit': limit},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json().get('customers', [])


class ShopifyCapabilityChecker:
    """Check what API capabilities are available"""
    
    def __init__(self, client: ShopifyAdminClient):
        self.client = client
    
    async def check_all_capabilities(self) -> Dict[str, bool]:
        """Check all API capabilities"""
        capabilities = {
            'shop_info': False,
            'products': False,
            'orders': False,
            'customers': False,
        }
        
        try:
            await self.client.get_shop_info()
            capabilities['shop_info'] = True
        except:
            pass
        
        try:
            await self.client.get_products(limit=1)
            capabilities['products'] = True
        except:
            pass
        
        try:
            await self.client.get_orders(limit=1)
            capabilities['orders'] = True
        except:
            pass
        
        try:
            await self.client.get_customers(limit=1)
            capabilities['customers'] = True
        except:
            pass
        
        return capabilities
