"""
Shopify Integration Module
Provides Shopify Admin API client, capability detection, data ingestion,
and webhook handlers for multi-tenant e-commerce automation.
"""

from .client import ShopifyAdminClient, ShopifyAPIError, ShopifyAuthError, ShopifyNotFoundError
from .service import ShopifyService, create_shopify_service
from .capability_checker import ShopifyCapabilityChecker, check_shopify_capabilities
from .schema_generator import ShopifySchemaGenerator, get_shopify_product_schema_summary, get_shopify_order_schema_summary

# Lazy import for routes to avoid loading heavy FastAPI/database dependencies
# when only the client is needed (e.g., in Streamlit UI)
def get_shopify_router():
    """Lazy load shopify router to avoid import errors in non-FastAPI contexts."""
    from .routes import shopify_router
    return shopify_router

def get_configure_shopify_routes():
    """Lazy load configure_shopify_routes to avoid import errors in non-FastAPI contexts."""
    from .routes import configure_shopify_routes
    return configure_shopify_routes

__all__ = [
    # Client
    "ShopifyAdminClient",
    "ShopifyAPIError",
    "ShopifyAuthError",
    "ShopifyNotFoundError",
    # Service
    "ShopifyService",
    "create_shopify_service",
    # Capability
    "ShopifyCapabilityChecker",
    "check_shopify_capabilities",
    # Schema
    "ShopifySchemaGenerator",
    "get_shopify_product_schema_summary",
    "get_shopify_order_schema_summary",
    # Routes (lazy loaders)
    "get_shopify_router",
    "get_configure_shopify_routes",
]
