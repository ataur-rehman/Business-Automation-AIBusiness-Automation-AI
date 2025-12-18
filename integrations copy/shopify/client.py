"""
Shopify Admin API Client
Reusable API client with rate limiting, retry logic, and multi-tenant support.

API Version: 2025-10
Rate Limit: 2 calls/second (REST API), 40 points/second (GraphQL)
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import httpx

from .models import (
    ShopInfo,
    ShopifyProduct,
    ShopifyOrder,
    ShopifyCustomer,
    ShopifyBlog,
    ShopifyArticle,
    ShopifyPolicy,
    ShopifyWebhook,
    ShopifyAPIResponse,
    PaginatedResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    ArticleCreateRequest,
    WebhookCreateRequest,
)

logger = logging.getLogger(__name__)


class ShopifyAPIError(Exception):
    """Base exception for Shopify API errors"""
    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body or {}


class ShopifyRateLimitError(ShopifyAPIError):
    """Rate limit exceeded"""
    def __init__(self, retry_after: float = 1.0):
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s", status_code=429)
        self.retry_after = retry_after


class ShopifyAuthError(ShopifyAPIError):
    """Authentication/authorization error"""
    pass


class ShopifyNotFoundError(ShopifyAPIError):
    """Resource not found"""
    pass


class ShopifyAdminClient:
    """
    Shopify Admin API Client with rate limiting and retry logic.
    
    Supports multi-tenant access via per-store tokens.
    
    Usage:
        client = ShopifyAdminClient(
            shop_domain="my-store.myshopify.com",
            access_token="shpat_xxxxx"
        )
        shop = await client.get_shop_info()
        products = await client.get_products(limit=50)
    """
    
    API_VERSION = "2025-10"
    
    # Rate limiting: 2 calls per second for REST API
    RATE_LIMIT_CALLS = 2
    RATE_LIMIT_PERIOD = 1.0  # seconds
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 1.0
    RETRY_BACKOFF_MAX = 30.0
    
    # Timeout configuration
    DEFAULT_TIMEOUT = 30.0
    LONG_TIMEOUT = 60.0
    
    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str = None,
        timeout: float = None,
    ):
        """
        Initialize Shopify Admin API client.
        
        Args:
            shop_domain: Store domain (e.g., "my-store.myshopify.com")
            access_token: Shopify Admin API access token
            api_version: API version (default: 2025-10)
            timeout: Request timeout in seconds
        """
        # Normalize shop domain
        self.shop_domain = self._normalize_domain(shop_domain)
        self.access_token = access_token
        self.api_version = api_version or self.API_VERSION
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Build base URL
        self.base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"
        
        # Rate limiting state
        self._call_timestamps: List[float] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # HTTP client (lazy initialization)
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"Initialized ShopifyAdminClient for {self.shop_domain} (API v{self.api_version})")
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize shop domain to just the hostname"""
        # Remove protocol if present
        if domain.startswith(("http://", "https://")):
            parsed = urlparse(domain)
            domain = parsed.netloc or parsed.path
        
        # Remove trailing slashes
        domain = domain.rstrip("/")
        
        # Ensure .myshopify.com suffix
        if not domain.endswith(".myshopify.com"):
            if "." not in domain:
                domain = f"{domain}.myshopify.com"
        
        return domain
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "X-Shopify-Access-Token": self.access_token,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # =========================================================================
    # Rate Limiting
    # =========================================================================
    
    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        async with self._rate_limit_lock:
            now = time.monotonic()
            
            # Remove old timestamps outside the rate limit window
            self._call_timestamps = [
                ts for ts in self._call_timestamps 
                if now - ts < self.RATE_LIMIT_PERIOD
            ]
            
            # If at limit, wait for oldest call to expire
            if len(self._call_timestamps) >= self.RATE_LIMIT_CALLS:
                oldest = min(self._call_timestamps)
                wait_time = self.RATE_LIMIT_PERIOD - (now - oldest)
                if wait_time > 0:
                    logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            
            # Record this call
            self._call_timestamps.append(time.monotonic())
    
    def _parse_rate_limit_headers(self, response: httpx.Response) -> Tuple[int, int]:
        """Parse rate limit info from response headers"""
        # Shopify returns: X-Shopify-Shop-Api-Call-Limit: "32/40"
        limit_header = response.headers.get("X-Shopify-Shop-Api-Call-Limit", "")
        if "/" in limit_header:
            used, max_limit = limit_header.split("/")
            return int(used), int(max_limit)
        return 0, 40
    
    # =========================================================================
    # HTTP Methods with Retry
    # =========================================================================
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        timeout: float = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting and retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/products.json")
            params: Query parameters
            json_data: JSON body data
            timeout: Request timeout override
            
        Returns:
            Response JSON data
            
        Raises:
            ShopifyAPIError: On API errors
            ShopifyRateLimitError: On rate limit (after retries)
            ShopifyAuthError: On authentication errors
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        client = await self._get_client()
        
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Wait for rate limit
                await self._wait_for_rate_limit()
                
                # Make request
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=timeout or self.timeout,
                )
                
                # Parse rate limit headers
                used, max_limit = self._parse_rate_limit_headers(response)
                logger.debug(f"API call: {method} {endpoint} - Rate: {used}/{max_limit}")
                
                # Handle response
                if response.status_code == 200:
                    return response.json()
                
                elif response.status_code == 201:
                    return response.json()
                
                elif response.status_code == 204:
                    return {}  # No content (successful DELETE)
                
                elif response.status_code == 429:
                    # Rate limited - extract retry-after
                    retry_after = float(response.headers.get("Retry-After", 2.0))
                    logger.warning(f"Rate limited. Retry after {retry_after}s (attempt {attempt + 1})")
                    await asyncio.sleep(retry_after)
                    continue
                
                elif response.status_code == 401:
                    raise ShopifyAuthError(
                        "Invalid or expired access token",
                        status_code=401,
                        response_body=response.json() if response.content else {}
                    )
                
                elif response.status_code == 403:
                    error_body = response.json() if response.content else {}
                    raise ShopifyAuthError(
                        f"Access forbidden: {error_body.get('errors', 'Insufficient permissions')}",
                        status_code=403,
                        response_body=error_body
                    )
                
                elif response.status_code == 404:
                    raise ShopifyNotFoundError(
                        f"Resource not found: {endpoint}",
                        status_code=404
                    )
                
                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    backoff = min(
                        self.RETRY_BACKOFF_BASE * (2 ** attempt),
                        self.RETRY_BACKOFF_MAX
                    )
                    logger.warning(f"Server error {response.status_code}. Retrying in {backoff}s")
                    await asyncio.sleep(backoff)
                    continue
                
                else:
                    error_body = response.json() if response.content else {}
                    errors = error_body.get('errors', response.text)
                    
                    # Provide clearer error messages for common issues
                    error_message = f"API error: {errors}"
                    if "Unavailable Shop" in str(errors):
                        error_message = (
                            f"Unavailable Shop: The shop '{self.shop_domain}' cannot be accessed. "
                            "Please verify: 1) The shop domain is correct (e.g., 'your-store.myshopify.com'), "
                            "2) The access token is valid and belongs to this shop, "
                            "3) The shop is active and not paused/closed."
                        )
                    
                    raise ShopifyAPIError(
                        error_message,
                        status_code=response.status_code,
                        response_body=error_body
                    )
                    
            except httpx.TimeoutException as e:
                last_error = ShopifyAPIError(f"Request timeout: {e}")
                backoff = min(self.RETRY_BACKOFF_BASE * (2 ** attempt), self.RETRY_BACKOFF_MAX)
                logger.warning(f"Timeout. Retrying in {backoff}s (attempt {attempt + 1})")
                await asyncio.sleep(backoff)
                
            except httpx.RequestError as e:
                last_error = ShopifyAPIError(f"Request error: {e}")
                backoff = min(self.RETRY_BACKOFF_BASE * (2 ** attempt), self.RETRY_BACKOFF_MAX)
                logger.warning(f"Request error: {e}. Retrying in {backoff}s")
                await asyncio.sleep(backoff)
        
        # All retries exhausted
        raise last_error or ShopifyAPIError("Request failed after all retries")
    
    async def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """GET request"""
        return await self._request("GET", endpoint, params=params)
    
    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request"""
        return await self._request("POST", endpoint, json_data=data)
    
    async def _put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request"""
        return await self._request("PUT", endpoint, json_data=data)
    
    async def _delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        return await self._request("DELETE", endpoint)
    
    # =========================================================================
    # Pagination Helper
    # =========================================================================
    
    def _parse_link_header(self, link_header: str) -> Optional[str]:
        """Parse Link header for next page cursor"""
        if not link_header:
            return None
        
        # Format: <url>; rel="next", <url>; rel="previous"
        for part in link_header.split(","):
            if 'rel="next"' in part:
                # Extract URL and get page_info parameter
                url_part = part.split(";")[0].strip().strip("<>")
                parsed = urlparse(url_part)
                params = parse_qs(parsed.query)
                if "page_info" in params:
                    return params["page_info"][0]
        return None
    
    async def _paginate(
        self,
        endpoint: str,
        result_key: str,
        params: Dict[str, Any] = None,
        limit: int = 250,
        max_pages: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all pages of a paginated endpoint.
        
        Args:
            endpoint: API endpoint
            result_key: Key in response containing items (e.g., "products")
            params: Additional query parameters
            limit: Items per page (max 250)
            max_pages: Maximum pages to fetch (None = all)
            
        Returns:
            List of all items
        """
        all_items = []
        page_count = 0
        params = params or {}
        params["limit"] = min(limit, 250)
        
        client = await self._get_client()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        
        while True:
            await self._wait_for_rate_limit()
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                break
            
            data = response.json()
            items = data.get(result_key, [])
            all_items.extend(items)
            
            page_count += 1
            logger.debug(f"Fetched page {page_count}: {len(items)} items (total: {len(all_items)})")
            
            # Check for next page
            link_header = response.headers.get("Link", "")
            next_cursor = self._parse_link_header(link_header)
            
            if not next_cursor:
                break
            
            if max_pages and page_count >= max_pages:
                logger.info(f"Reached max pages limit ({max_pages})")
                break
            
            # Update params for next page
            params = {"page_info": next_cursor, "limit": params["limit"]}
        
        return all_items
    
    # =========================================================================
    # Shop API
    # =========================================================================
    
    async def get_shop_info(self) -> ShopInfo:
        """
        Get shop information.
        
        Returns:
            ShopInfo model with store details
        """
        response = await self._get("/shop.json")
        return ShopInfo(**response.get("shop", {}))
    
    async def get_access_scopes(self) -> List[str]:
        """
        Get OAuth access scopes granted to this token.
        
        Returns:
            List of scope handles (e.g., ['read_products', 'write_orders'])
        """
        response = await self._get("/oauth/access_scopes.json")
        scopes = response.get("access_scopes", [])
        return [s.get("handle", s) if isinstance(s, dict) else s for s in scopes]
    
    # =========================================================================
    # Products API
    # =========================================================================
    
    async def get_products(
        self,
        limit: int = 250,
        status: str = None,
        product_type: str = None,
        vendor: str = None,
        collection_id: int = None,
        ids: List[int] = None,
        since_id: int = None,
        created_at_min: datetime = None,
        updated_at_min: datetime = None,
        fields: List[str] = None,
        max_pages: int = None,
    ) -> List[ShopifyProduct]:
        """
        Get all products with optional filters.
        
        Args:
            limit: Products per page (max 250)
            status: Filter by status (active, archived, draft)
            product_type: Filter by product type
            vendor: Filter by vendor
            collection_id: Filter by collection
            ids: Filter by specific product IDs
            since_id: Only products after this ID
            created_at_min: Only products created after this date
            updated_at_min: Only products updated after this date
            fields: Limit fields returned
            max_pages: Maximum pages to fetch
            
        Returns:
            List of ShopifyProduct models
        """
        params = {}
        
        if status:
            params["status"] = status
        if product_type:
            params["product_type"] = product_type
        if vendor:
            params["vendor"] = vendor
        if collection_id:
            params["collection_id"] = collection_id
        if ids:
            params["ids"] = ",".join(str(i) for i in ids)
        if since_id:
            params["since_id"] = since_id
        if created_at_min:
            params["created_at_min"] = created_at_min.isoformat()
        if updated_at_min:
            params["updated_at_min"] = updated_at_min.isoformat()
        if fields:
            params["fields"] = ",".join(fields)
        
        items = await self._paginate(
            "/products.json",
            "products",
            params=params,
            limit=limit,
            max_pages=max_pages,
        )
        
        return [ShopifyProduct(**item) for item in items]
    
    async def get_product(self, product_id: int, fields: List[str] = None) -> ShopifyProduct:
        """Get a single product by ID"""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        response = await self._get(f"/products/{product_id}.json", params=params)
        return ShopifyProduct(**response.get("product", {}))
    
    async def get_product_count(self, status: str = None) -> int:
        """Get total product count"""
        params = {}
        if status:
            params["status"] = status
        
        response = await self._get("/products/count.json", params=params)
        return response.get("count", 0)
    
    async def create_product(self, product: ProductCreateRequest) -> ShopifyProduct:
        """Create a new product"""
        response = await self._post("/products.json", {"product": product.model_dump(exclude_none=True)})
        return ShopifyProduct(**response.get("product", {}))
    
    async def update_product(self, product_id: int, updates: ProductUpdateRequest) -> ShopifyProduct:
        """
        Update an existing product.
        
        Args:
            product_id: Product ID to update
            updates: Fields to update
            
        Returns:
            Updated ShopifyProduct model
        """
        data = updates.model_dump(exclude_none=True)
        data["id"] = product_id
        
        response = await self._put(f"/products/{product_id}.json", {"product": data})
        return ShopifyProduct(**response.get("product", {}))
    
    async def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        await self._delete(f"/products/{product_id}.json")
        return True
    
    # =========================================================================
    # Orders API
    # =========================================================================
    
    async def get_orders(
        self,
        limit: int = 250,
        status: str = "any",
        financial_status: str = None,
        fulfillment_status: str = None,
        created_at_min: datetime = None,
        created_at_max: datetime = None,
        updated_at_min: datetime = None,
        since_id: int = None,
        ids: List[int] = None,
        fields: List[str] = None,
        max_pages: int = None,
    ) -> List[ShopifyOrder]:
        """
        Get all orders with optional filters.
        
        Args:
            limit: Orders per page (max 250)
            status: Order status (open, closed, cancelled, any)
            financial_status: Payment status filter
            fulfillment_status: Fulfillment status filter
            created_at_min: Orders created after this date
            created_at_max: Orders created before this date
            updated_at_min: Orders updated after this date
            since_id: Orders after this ID
            ids: Specific order IDs
            fields: Limit fields returned
            max_pages: Maximum pages to fetch
            
        Returns:
            List of ShopifyOrder models
        """
        params = {"status": status}
        
        if financial_status:
            params["financial_status"] = financial_status
        if fulfillment_status:
            params["fulfillment_status"] = fulfillment_status
        if created_at_min:
            params["created_at_min"] = created_at_min.isoformat()
        if created_at_max:
            params["created_at_max"] = created_at_max.isoformat()
        if updated_at_min:
            params["updated_at_min"] = updated_at_min.isoformat()
        if since_id:
            params["since_id"] = since_id
        if ids:
            params["ids"] = ",".join(str(i) for i in ids)
        if fields:
            params["fields"] = ",".join(fields)
        
        items = await self._paginate(
            "/orders.json",
            "orders",
            params=params,
            limit=limit,
            max_pages=max_pages,
        )
        
        return [ShopifyOrder(**item) for item in items]
    
    async def get_order(self, order_id: int, fields: List[str] = None) -> ShopifyOrder:
        """Get a single order by ID"""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        response = await self._get(f"/orders/{order_id}.json", params=params)
        return ShopifyOrder(**response.get("order", {}))
    
    async def get_order_count(self, status: str = "any") -> int:
        """Get total order count"""
        response = await self._get("/orders/count.json", params={"status": status})
        return response.get("count", 0)
    
    async def close_order(self, order_id: int) -> ShopifyOrder:
        """Close an order"""
        response = await self._post(f"/orders/{order_id}/close.json", {})
        return ShopifyOrder(**response.get("order", {}))
    
    async def cancel_order(self, order_id: int, reason: str = None, email: bool = True) -> ShopifyOrder:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            reason: Cancellation reason (customer, fraud, inventory, declined, other)
            email: Send cancellation email to customer
        """
        data = {"email": email}
        if reason:
            data["reason"] = reason
        
        response = await self._post(f"/orders/{order_id}/cancel.json", data)
        return ShopifyOrder(**response.get("order", {}))
    
    # =========================================================================
    # Customers API
    # =========================================================================
    
    async def get_customers(
        self,
        limit: int = 250,
        created_at_min: datetime = None,
        updated_at_min: datetime = None,
        since_id: int = None,
        ids: List[int] = None,
        fields: List[str] = None,
        max_pages: int = None,
    ) -> List[ShopifyCustomer]:
        """
        Get all customers with optional filters.
        
        Args:
            limit: Customers per page (max 250)
            created_at_min: Customers created after this date
            updated_at_min: Customers updated after this date
            since_id: Customers after this ID
            ids: Specific customer IDs
            fields: Limit fields returned
            max_pages: Maximum pages to fetch
            
        Returns:
            List of ShopifyCustomer models
        """
        params = {}
        
        if created_at_min:
            params["created_at_min"] = created_at_min.isoformat()
        if updated_at_min:
            params["updated_at_min"] = updated_at_min.isoformat()
        if since_id:
            params["since_id"] = since_id
        if ids:
            params["ids"] = ",".join(str(i) for i in ids)
        if fields:
            params["fields"] = ",".join(fields)
        
        items = await self._paginate(
            "/customers.json",
            "customers",
            params=params,
            limit=limit,
            max_pages=max_pages,
        )
        
        return [ShopifyCustomer(**item) for item in items]
    
    async def get_customer(self, customer_id: int, fields: List[str] = None) -> ShopifyCustomer:
        """Get a single customer by ID"""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        response = await self._get(f"/customers/{customer_id}.json", params=params)
        return ShopifyCustomer(**response.get("customer", {}))
    
    async def get_customer_count(self) -> int:
        """Get total customer count"""
        response = await self._get("/customers/count.json")
        return response.get("count", 0)
    
    async def search_customers(self, query: str, limit: int = 250) -> List[ShopifyCustomer]:
        """
        Search customers by query.
        
        Args:
            query: Search query (email, name, etc.)
            limit: Max results
            
        Returns:
            List of matching customers
        """
        response = await self._get("/customers/search.json", params={"query": query, "limit": limit})
        customers = response.get("customers", [])
        return [ShopifyCustomer(**c) for c in customers]
    
    # =========================================================================
    # Blog/Content API
    # =========================================================================
    
    async def get_blogs(self) -> List[ShopifyBlog]:
        """Get all blogs"""
        response = await self._get("/blogs.json")
        blogs = response.get("blogs", [])
        return [ShopifyBlog(**b) for b in blogs]
    
    async def get_blog(self, blog_id: int) -> ShopifyBlog:
        """Get a single blog by ID"""
        response = await self._get(f"/blogs/{blog_id}.json")
        return ShopifyBlog(**response.get("blog", {}))
    
    async def get_articles(
        self,
        blog_id: int,
        limit: int = 250,
        published_status: str = None,
        max_pages: int = None,
    ) -> List[ShopifyArticle]:
        """
        Get all articles for a blog.
        
        Args:
            blog_id: Blog ID
            limit: Articles per page
            published_status: Filter (published, unpublished, any)
            max_pages: Maximum pages to fetch
        """
        params = {}
        if published_status:
            params["published_status"] = published_status
        
        items = await self._paginate(
            f"/blogs/{blog_id}/articles.json",
            "articles",
            params=params,
            limit=limit,
            max_pages=max_pages,
        )
        
        return [ShopifyArticle(**item) for item in items]
    
    async def get_article(self, blog_id: int, article_id: int) -> ShopifyArticle:
        """Get a single article"""
        response = await self._get(f"/blogs/{blog_id}/articles/{article_id}.json")
        return ShopifyArticle(**response.get("article", {}))
    
    async def create_blog_article(self, blog_id: int, article: ArticleCreateRequest) -> ShopifyArticle:
        """
        Create a new blog article.
        
        Args:
            blog_id: Blog ID to create article in
            article: Article data
            
        Returns:
            Created ShopifyArticle model
        """
        response = await self._post(
            f"/blogs/{blog_id}/articles.json",
            {"article": article.model_dump(exclude_none=True)}
        )
        return ShopifyArticle(**response.get("article", {}))
    
    async def update_article(
        self,
        blog_id: int,
        article_id: int,
        updates: Dict[str, Any]
    ) -> ShopifyArticle:
        """Update an existing article"""
        updates["id"] = article_id
        response = await self._put(
            f"/blogs/{blog_id}/articles/{article_id}.json",
            {"article": updates}
        )
        return ShopifyArticle(**response.get("article", {}))
    
    async def delete_article(self, blog_id: int, article_id: int) -> bool:
        """Delete an article"""
        await self._delete(f"/blogs/{blog_id}/articles/{article_id}.json")
        return True
    
    # =========================================================================
    # Policies API
    # =========================================================================
    
    async def get_policies(self) -> List[ShopifyPolicy]:
        """Get store policies (refund, privacy, terms of service, etc.)"""
        response = await self._get("/policies.json")
        policies = response.get("policies", [])
        return [ShopifyPolicy(**p) for p in policies]
    
    # =========================================================================
    # Webhooks API
    # =========================================================================
    
    async def get_webhooks(self) -> List[ShopifyWebhook]:
        """Get all registered webhooks"""
        response = await self._get("/webhooks.json")
        webhooks = response.get("webhooks", [])
        return [ShopifyWebhook(**w) for w in webhooks]
    
    async def get_webhook(self, webhook_id: int) -> ShopifyWebhook:
        """Get a single webhook"""
        response = await self._get(f"/webhooks/{webhook_id}.json")
        return ShopifyWebhook(**response.get("webhook", {}))
    
    async def create_webhook(self, webhook: WebhookCreateRequest) -> ShopifyWebhook:
        """
        Create a new webhook.
        
        Args:
            webhook: Webhook configuration
            
        Returns:
            Created ShopifyWebhook model
        """
        data = {
            "topic": webhook.topic.value,
            "address": str(webhook.address),
            "format": webhook.format,
        }
        response = await self._post("/webhooks.json", {"webhook": data})
        return ShopifyWebhook(**response.get("webhook", {}))
    
    async def delete_webhook(self, webhook_id: int) -> bool:
        """Delete a webhook"""
        await self._delete(f"/webhooks/{webhook_id}.json")
        return True
    
    # =========================================================================
    # Inventory API
    # =========================================================================
    
    async def get_inventory_levels(
        self,
        inventory_item_ids: List[int] = None,
        location_ids: List[int] = None,
        limit: int = 250,
    ) -> List[Dict[str, Any]]:
        """
        Get inventory levels.
        
        Args:
            inventory_item_ids: Filter by inventory item IDs
            location_ids: Filter by location IDs
            limit: Max results per page
        """
        params = {"limit": limit}
        
        if inventory_item_ids:
            params["inventory_item_ids"] = ",".join(str(i) for i in inventory_item_ids)
        if location_ids:
            params["location_ids"] = ",".join(str(i) for i in location_ids)
        
        response = await self._get("/inventory_levels.json", params=params)
        return response.get("inventory_levels", [])
    
    async def set_inventory_level(
        self,
        inventory_item_id: int,
        location_id: int,
        available: int,
    ) -> Dict[str, Any]:
        """
        Set inventory level for an item at a location.
        
        Args:
            inventory_item_id: Inventory item ID
            location_id: Location ID
            available: New available quantity
        """
        response = await self._post("/inventory_levels/set.json", {
            "inventory_item_id": inventory_item_id,
            "location_id": location_id,
            "available": available,
        })
        return response.get("inventory_level", {})
    
    async def adjust_inventory_level(
        self,
        inventory_item_id: int,
        location_id: int,
        adjustment: int,
    ) -> Dict[str, Any]:
        """
        Adjust inventory level by a delta.
        
        Args:
            inventory_item_id: Inventory item ID
            location_id: Location ID
            adjustment: Amount to adjust (positive or negative)
        """
        response = await self._post("/inventory_levels/adjust.json", {
            "inventory_item_id": inventory_item_id,
            "location_id": location_id,
            "available_adjustment": adjustment,
        })
        return response.get("inventory_level", {})
    
    # =========================================================================
    # Locations API
    # =========================================================================
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """Get all locations"""
        response = await self._get("/locations.json")
        return response.get("locations", [])
    
    async def get_location(self, location_id: int) -> Dict[str, Any]:
        """Get a single location"""
        response = await self._get(f"/locations/{location_id}.json")
        return response.get("location", {})
    
    # =========================================================================
    # Fulfillment API
    # =========================================================================
    
    async def get_fulfillments(self, order_id: int) -> List[Dict[str, Any]]:
        """Get fulfillments for an order"""
        response = await self._get(f"/orders/{order_id}/fulfillments.json")
        return response.get("fulfillments", [])
    
    async def create_fulfillment(
        self,
        order_id: int,
        location_id: int,
        tracking_number: str = None,
        tracking_company: str = None,
        tracking_url: str = None,
        line_items: List[Dict[str, Any]] = None,
        notify_customer: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a fulfillment for an order.
        
        Args:
            order_id: Order ID
            location_id: Fulfillment location ID
            tracking_number: Tracking number
            tracking_company: Shipping carrier name
            tracking_url: Tracking URL
            line_items: Specific line items to fulfill
            notify_customer: Send notification email
        """
        data = {
            "location_id": location_id,
            "notify_customer": notify_customer,
        }
        
        if tracking_number:
            data["tracking_number"] = tracking_number
        if tracking_company:
            data["tracking_company"] = tracking_company
        if tracking_url:
            data["tracking_url"] = tracking_url
        if line_items:
            data["line_items"] = line_items
        
        response = await self._post(
            f"/orders/{order_id}/fulfillments.json",
            {"fulfillment": data}
        )
        return response.get("fulfillment", {})
    
    # =========================================================================
    # Metafields API
    # =========================================================================
    
    async def get_product_metafields(self, product_id: int) -> List[Dict[str, Any]]:
        """Get metafields for a product"""
        response = await self._get(f"/products/{product_id}/metafields.json")
        return response.get("metafields", [])
    
    async def create_product_metafield(
        self,
        product_id: int,
        namespace: str,
        key: str,
        value: Any,
        value_type: str = "string",
    ) -> Dict[str, Any]:
        """
        Create a metafield for a product.
        
        Args:
            product_id: Product ID
            namespace: Metafield namespace
            key: Metafield key
            value: Metafield value
            value_type: Value type (string, integer, json, etc.)
        """
        response = await self._post(f"/products/{product_id}/metafields.json", {
            "metafield": {
                "namespace": namespace,
                "key": key,
                "value": value,
                "type": value_type,
            }
        })
        return response.get("metafield", {})
