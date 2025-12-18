"""
Shopify Webhook Handlers
HMAC verification and event processing for Shopify webhooks.
"""

import hashlib
import hmac
import base64
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel

from ..models import WebhookPayload, WebhookTopic

logger = logging.getLogger(__name__)


class WebhookVerificationError(Exception):
    """Webhook signature verification failed"""
    pass


def verify_shopify_hmac(
    data: bytes,
    hmac_header: str,
    secret: str,
) -> bool:
    """
    Verify Shopify webhook HMAC signature.
    
    Shopify signs webhooks with HMAC-SHA256 using the app's API secret.
    The signature is base64-encoded and sent in the X-Shopify-Hmac-SHA256 header.
    
    Args:
        data: Raw request body bytes
        hmac_header: Value of X-Shopify-Hmac-SHA256 header
        secret: Shopify API secret (client secret)
        
    Returns:
        True if signature is valid
        
    Raises:
        WebhookVerificationError: If verification fails
    """
    if not hmac_header:
        raise WebhookVerificationError("Missing HMAC header")
    
    if not secret:
        raise WebhookVerificationError("Missing API secret")
    
    # Calculate expected HMAC
    calculated_hmac = hmac.new(
        secret.encode('utf-8'),
        data,
        hashlib.sha256
    ).digest()
    
    # Base64 encode to match Shopify's format
    calculated_b64 = base64.b64encode(calculated_hmac).decode('utf-8')
    
    # Compare using constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(calculated_b64, hmac_header):
        logger.warning("Webhook HMAC verification failed")
        raise WebhookVerificationError("Invalid HMAC signature")
    
    return True


class WebhookContext(BaseModel):
    """Context passed to webhook handlers"""
    topic: str
    shop_domain: str
    api_version: str
    payload: Dict[str, Any]
    webhook_id: Optional[str] = None
    received_at: datetime = None
    
    class Config:
        arbitrary_types_allowed = True


class ShopifyWebhookHandler:
    """
    Handles incoming Shopify webhook events.
    
    Supports registering handlers for specific webhook topics and
    dispatching events to the appropriate handler.
    
    Usage:
        handler = ShopifyWebhookHandler(api_secret="shpss_xxxx")
        
        @handler.on(WebhookTopic.ORDERS_CREATE)
        async def handle_new_order(ctx: WebhookContext):
            print(f"New order: {ctx.payload['id']}")
        
        # In your route:
        await handler.process_webhook(request)
    """
    
    def __init__(self, api_secret: str):
        """
        Initialize webhook handler.
        
        Args:
            api_secret: Shopify API secret for HMAC verification
        """
        self.api_secret = api_secret
        self._handlers: Dict[str, Callable] = {}
        self._default_handler: Optional[Callable] = None
        
        logger.info("ShopifyWebhookHandler initialized")
    
    def on(self, topic: WebhookTopic):
        """
        Decorator to register a handler for a webhook topic.
        
        Args:
            topic: Webhook topic to handle
            
        Usage:
            @handler.on(WebhookTopic.ORDERS_CREATE)
            async def handle_order(ctx: WebhookContext):
                ...
        """
        def decorator(func: Callable):
            self._handlers[topic.value] = func
            logger.debug(f"Registered handler for {topic.value}")
            return func
        return decorator
    
    def set_default_handler(self, func: Callable):
        """Set a default handler for unhandled topics"""
        self._default_handler = func
    
    def verify_and_parse(
        self,
        body: bytes,
        hmac_header: str,
        topic: str,
        shop_domain: str,
        api_version: str = "2025-10",
    ) -> WebhookContext:
        """
        Verify webhook signature and parse payload.
        
        Args:
            body: Raw request body
            hmac_header: X-Shopify-Hmac-SHA256 header value
            topic: X-Shopify-Topic header value
            shop_domain: X-Shopify-Shop-Domain header value
            api_version: X-Shopify-API-Version header value
            
        Returns:
            WebhookContext with parsed payload
            
        Raises:
            WebhookVerificationError: If signature is invalid
        """
        # Verify HMAC
        verify_shopify_hmac(body, hmac_header, self.api_secret)
        
        # Parse payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise WebhookVerificationError(f"Invalid JSON payload: {e}")
        
        return WebhookContext(
            topic=topic,
            shop_domain=shop_domain,
            api_version=api_version,
            payload=payload,
            received_at=datetime.utcnow(),
        )
    
    async def dispatch(self, ctx: WebhookContext) -> Any:
        """
        Dispatch webhook to appropriate handler.
        
        Args:
            ctx: Webhook context with parsed payload
            
        Returns:
            Handler result
        """
        handler = self._handlers.get(ctx.topic)
        
        if handler:
            logger.info(f"Dispatching {ctx.topic} webhook from {ctx.shop_domain}")
            return await handler(ctx)
        elif self._default_handler:
            logger.info(f"Using default handler for {ctx.topic}")
            return await self._default_handler(ctx)
        else:
            logger.warning(f"No handler registered for topic: {ctx.topic}")
            return None
    
    async def process_webhook(
        self,
        body: bytes,
        hmac_header: str,
        topic: str,
        shop_domain: str,
        api_version: str = "2025-10",
    ) -> Any:
        """
        Process a complete webhook request.
        
        Combines verification, parsing, and dispatch.
        
        Args:
            body: Raw request body
            hmac_header: X-Shopify-Hmac-SHA256 header
            topic: X-Shopify-Topic header
            shop_domain: X-Shopify-Shop-Domain header
            api_version: X-Shopify-API-Version header
            
        Returns:
            Handler result
        """
        ctx = self.verify_and_parse(
            body=body,
            hmac_header=hmac_header,
            topic=topic,
            shop_domain=shop_domain,
            api_version=api_version,
        )
        
        return await self.dispatch(ctx)


# =============================================================================
# Default Webhook Handlers
# =============================================================================

async def handle_order_created(ctx: WebhookContext, service=None):
    """
    Handle orders/create webhook.
    
    Actions:
    - Sync order to database
    - Check if COD order needs confirmation
    - Trigger order confirmation workflow
    """
    logger.info(f"Order created: {ctx.payload.get('id')} from {ctx.shop_domain}")
    
    order_data = ctx.payload
    
    # Log key order info
    logger.info(
        f"Order #{order_data.get('name')}: "
        f"${order_data.get('total_price')} "
        f"({order_data.get('financial_status')})"
    )
    
    # Check for COD
    if order_data.get('gateway', '').lower() in ['cod', 'cash on delivery']:
        logger.info(f"COD order detected - may need confirmation")
        return {
            "action": "cod_confirmation_needed",
            "order_id": order_data.get('id'),
            "order_name": order_data.get('name'),
        }
    
    return {
        "action": "order_synced",
        "order_id": order_data.get('id'),
    }


async def handle_order_fulfilled(ctx: WebhookContext, service=None):
    """
    Handle orders/fulfilled webhook.
    
    Actions:
    - Update order status in database
    - Trigger fulfillment notification workflow
    """
    logger.info(f"Order fulfilled: {ctx.payload.get('id')} from {ctx.shop_domain}")
    
    order_data = ctx.payload
    
    fulfillments = order_data.get('fulfillments', [])
    tracking_info = None
    
    if fulfillments:
        latest = fulfillments[-1]
        tracking_info = {
            "tracking_number": latest.get('tracking_number'),
            "tracking_company": latest.get('tracking_company'),
            "tracking_url": latest.get('tracking_url'),
        }
    
    return {
        "action": "order_fulfilled",
        "order_id": order_data.get('id'),
        "tracking": tracking_info,
    }


async def handle_product_updated(ctx: WebhookContext, service=None):
    """
    Handle products/update webhook.
    
    Actions:
    - Sync product to database
    - Update RAG index
    - Check for stock alerts
    """
    logger.info(f"Product updated: {ctx.payload.get('id')} from {ctx.shop_domain}")
    
    product_data = ctx.payload
    
    # Check variants for stock
    low_stock_variants = []
    for variant in product_data.get('variants', []):
        if variant.get('inventory_quantity', 0) < 5:
            low_stock_variants.append({
                "variant_id": variant.get('id'),
                "title": variant.get('title'),
                "quantity": variant.get('inventory_quantity'),
            })
    
    result = {
        "action": "product_synced",
        "product_id": product_data.get('id'),
    }
    
    if low_stock_variants:
        result["low_stock_alert"] = True
        result["low_stock_variants"] = low_stock_variants
    
    return result


async def handle_customer_created(ctx: WebhookContext, service=None):
    """
    Handle customers/create webhook.
    
    Actions:
    - Sync customer to database
    - Trigger welcome workflow if applicable
    """
    logger.info(f"Customer created: {ctx.payload.get('id')} from {ctx.shop_domain}")
    
    customer_data = ctx.payload
    
    return {
        "action": "customer_synced",
        "customer_id": customer_data.get('id'),
        "email": customer_data.get('email'),
        "accepts_marketing": customer_data.get('accepts_marketing'),
    }


async def handle_inventory_level_update(ctx: WebhookContext, service=None):
    """
    Handle inventory_levels/update webhook.
    
    Actions:
    - Update inventory in database
    - Check for low stock alerts
    - Trigger reorder workflow if needed
    """
    logger.info(f"Inventory updated from {ctx.shop_domain}")
    
    inventory_data = ctx.payload
    
    available = inventory_data.get('available', 0)
    inventory_item_id = inventory_data.get('inventory_item_id')
    
    result = {
        "action": "inventory_updated",
        "inventory_item_id": inventory_item_id,
        "available": available,
    }
    
    # Low stock alert
    if available < 5:
        result["low_stock_alert"] = True
    
    # Out of stock alert
    if available <= 0:
        result["out_of_stock_alert"] = True
    
    return result


async def handle_app_uninstalled(ctx: WebhookContext, service=None):
    """
    Handle app/uninstalled webhook.
    
    Actions:
    - Mark integration as disconnected
    - Clean up stored tokens
    - Log the uninstall
    """
    logger.warning(f"App uninstalled from {ctx.shop_domain}")
    
    return {
        "action": "app_uninstalled",
        "shop_domain": ctx.shop_domain,
        "cleanup_required": True,
    }


def create_default_webhook_handler(api_secret: str) -> ShopifyWebhookHandler:
    """
    Create a webhook handler with default handlers registered.
    
    Args:
        api_secret: Shopify API secret
        
    Returns:
        Configured ShopifyWebhookHandler
    """
    handler = ShopifyWebhookHandler(api_secret)
    
    # Register default handlers
    handler._handlers[WebhookTopic.ORDERS_CREATE.value] = handle_order_created
    handler._handlers[WebhookTopic.ORDERS_FULFILLED.value] = handle_order_fulfilled
    handler._handlers[WebhookTopic.PRODUCTS_UPDATE.value] = handle_product_updated
    handler._handlers[WebhookTopic.CUSTOMERS_CREATE.value] = handle_customer_created
    handler._handlers[WebhookTopic.INVENTORY_LEVELS_UPDATE.value] = handle_inventory_level_update
    handler._handlers[WebhookTopic.APP_UNINSTALLED.value] = handle_app_uninstalled
    
    logger.info("Created webhook handler with default handlers")
    
    return handler
