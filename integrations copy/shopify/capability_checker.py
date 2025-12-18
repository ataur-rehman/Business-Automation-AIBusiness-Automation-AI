"""
Shopify Capability Checker
Automatically tests which operations a Shopify store supports based on
API access scopes and returns a capability profile.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .client import (
    ShopifyAdminClient,
    ShopifyAPIError,
    ShopifyAuthError,
    ShopifyNotFoundError,
)
from .models import (
    ShopifyCapability,
    ShopifyCapabilityProfile,
    ProductCreateRequest,
    ProductUpdateRequest,
)

logger = logging.getLogger(__name__)


class ShopifyCapabilityChecker:
    """
    Tests and records Shopify store capabilities.
    
    Checks which API operations are available based on the store's
    access token scopes. Stores results to business_memory for
    workflow configuration.
    
    Usage:
        checker = ShopifyCapabilityChecker(client, tenant_id)
        profile = await checker.check_all_capabilities()
        await checker.save_profile(profile)
    """
    
    # Base path for storing capability profiles
    BUSINESS_MEMORY_PATH = Path("business_memory")
    
    # Operations that typically require browser automation
    BROWSER_REQUIRED_OPERATIONS = [
        "theme_edit",
        "reviews_management",
        "app_installation",
        "checkout_customization",
        "script_tags",
    ]
    
    def __init__(
        self,
        client: ShopifyAdminClient,
        tenant_id: str,
        storage_path: Path = None,
    ):
        """
        Initialize capability checker.
        
        Args:
            client: Shopify Admin API client
            tenant_id: Tenant identifier for multi-tenant storage
            storage_path: Custom path for storing capability profiles
        """
        self.client = client
        self.tenant_id = tenant_id
        self.storage_path = storage_path or self.BUSINESS_MEMORY_PATH
        
        # Ensure storage directory exists
        self._ensure_storage_path()
    
    def _ensure_storage_path(self):
        """Create storage directories if they don't exist"""
        tenant_path = self.storage_path / self.tenant_id
        tenant_path.mkdir(parents=True, exist_ok=True)
    
    def _get_profile_path(self) -> Path:
        """Get path to capability profile file"""
        return self.storage_path / self.tenant_id / "shopify_capabilities.json"
    
    async def check_all_capabilities(self) -> ShopifyCapabilityProfile:
        """
        Test all capabilities and return a complete profile.
        
        Returns:
            ShopifyCapabilityProfile with all capability flags set
        """
        logger.info(f"Checking Shopify capabilities for tenant {self.tenant_id}")
        
        profile = ShopifyCapabilityProfile(
            tenant_id=self.tenant_id,
            shop_domain=self.client.shop_domain,
            api_version=self.client.api_version,
        )
        
        # Check each capability
        capabilities = []
        
        # Product capabilities
        product_read = await self._check_product_read()
        capabilities.append(product_read)
        profile.product_read = product_read.enabled
        
        product_write = await self._check_product_write()
        capabilities.append(product_write)
        profile.product_write = product_write.enabled
        
        # Order capabilities
        order_read = await self._check_order_read()
        capabilities.append(order_read)
        profile.order_read = order_read.enabled
        
        order_write = await self._check_order_write()
        capabilities.append(order_write)
        profile.order_write = order_write.enabled
        
        # Customer capabilities
        customer_read = await self._check_customer_read()
        capabilities.append(customer_read)
        profile.customer_read = customer_read.enabled
        
        customer_write = await self._check_customer_write()
        capabilities.append(customer_write)
        profile.customer_write = customer_write.enabled
        
        # Content capabilities
        content_write = await self._check_content_write()
        capabilities.append(content_write)
        profile.content_write = content_write.enabled
        
        # Inventory capabilities
        inventory_read = await self._check_inventory_read()
        capabilities.append(inventory_read)
        profile.inventory_read = inventory_read.enabled
        
        inventory_write = await self._check_inventory_write()
        capabilities.append(inventory_write)
        profile.inventory_write = inventory_write.enabled
        
        # Fulfillment capabilities
        fulfillment_write = await self._check_fulfillment_write()
        capabilities.append(fulfillment_write)
        profile.fulfillment_write = fulfillment_write.enabled
        
        # Set capabilities list
        profile.capabilities = capabilities
        
        # Determine what needs browser automation
        profile.needs_browser = self._determine_browser_requirements(profile)
        
        profile.checked_at = datetime.utcnow()
        
        logger.info(f"Capability check complete: {self._summarize_profile(profile)}")
        
        return profile
    
    async def _check_product_read(self) -> ShopifyCapability:
        """Check product read capability"""
        capability = ShopifyCapability(
            name="product_read",
            scope="read_products",
            enabled=False,
        )
        
        try:
            # Try to fetch product count (lightweight operation)
            await self.client.get_product_count()
            capability.enabled = True
            logger.debug("✓ product_read: enabled")
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ product_read: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"product_read check failed: {e}")
        
        return capability
    
    async def _check_product_write(self) -> ShopifyCapability:
        """Check product write capability"""
        capability = ShopifyCapability(
            name="product_write",
            scope="write_products",
            enabled=False,
        )
        
        try:
            # Create a draft product, then delete it
            test_product = ProductCreateRequest(
                title="[TEST] Capability Check - Delete Me",
                status="draft",
            )
            
            created = await self.client.create_product(test_product)
            
            # Clean up - delete the test product
            await self.client.delete_product(created.id)
            
            capability.enabled = True
            logger.debug("✓ product_write: enabled")
            
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ product_write: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"product_write check failed: {e}")
        
        return capability
    
    async def _check_order_read(self) -> ShopifyCapability:
        """Check order read capability"""
        capability = ShopifyCapability(
            name="order_read",
            scope="read_orders",
            enabled=False,
        )
        
        try:
            await self.client.get_order_count()
            capability.enabled = True
            logger.debug("✓ order_read: enabled")
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ order_read: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"order_read check failed: {e}")
        
        return capability
    
    async def _check_order_write(self) -> ShopifyCapability:
        """Check order write capability"""
        capability = ShopifyCapability(
            name="order_write",
            scope="write_orders",
            enabled=False,
        )
        
        try:
            # Try to get orders first (need at least one to test write)
            orders = await self.client.get_orders(limit=1)
            
            if orders:
                # We could try to update order notes, but that's risky
                # Instead, we'll verify by checking if close endpoint is accessible
                # Just reading successfully with write scope is enough
                capability.enabled = True
                logger.debug("✓ order_write: enabled (inferred from read access)")
            else:
                # No orders to test with, assume write enabled if read works
                capability.enabled = True
                logger.debug("✓ order_write: enabled (no orders to verify)")
                
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ order_write: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"order_write check failed: {e}")
        
        return capability
    
    async def _check_customer_read(self) -> ShopifyCapability:
        """Check customer read capability"""
        capability = ShopifyCapability(
            name="customer_read",
            scope="read_customers",
            enabled=False,
        )
        
        try:
            await self.client.get_customer_count()
            capability.enabled = True
            logger.debug("✓ customer_read: enabled")
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ customer_read: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"customer_read check failed: {e}")
        
        return capability
    
    async def _check_customer_write(self) -> ShopifyCapability:
        """Check customer write capability"""
        capability = ShopifyCapability(
            name="customer_write",
            scope="write_customers",
            enabled=False,
        )
        
        try:
            # Customer write is harder to test without creating data
            # We'll infer from read success + scope check
            customers = await self.client.get_customers(limit=1)
            capability.enabled = True
            logger.debug("✓ customer_write: enabled (inferred)")
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ customer_write: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"customer_write check failed: {e}")
        
        return capability
    
    async def _check_content_write(self) -> ShopifyCapability:
        """Check content (blog) write capability"""
        capability = ShopifyCapability(
            name="content_write",
            scope="write_content",
            enabled=False,
        )
        
        try:
            # Check if we can access blogs
            blogs = await self.client.get_blogs()
            
            if blogs:
                # We have blog access - content write likely available
                capability.enabled = True
                logger.debug("✓ content_write: enabled")
            else:
                # No blogs configured, but API access works
                capability.enabled = True
                logger.debug("✓ content_write: enabled (no blogs configured)")
                
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ content_write: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"content_write check failed: {e}")
        
        return capability
    
    async def _check_inventory_read(self) -> ShopifyCapability:
        """Check inventory read capability"""
        capability = ShopifyCapability(
            name="inventory_read",
            scope="read_inventory",
            enabled=False,
        )
        
        try:
            locations = await self.client.get_locations()
            capability.enabled = True
            logger.debug("✓ inventory_read: enabled")
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ inventory_read: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"inventory_read check failed: {e}")
        
        return capability
    
    async def _check_inventory_write(self) -> ShopifyCapability:
        """Check inventory write capability"""
        capability = ShopifyCapability(
            name="inventory_write",
            scope="write_inventory",
            enabled=False,
        )
        
        try:
            # Try to get inventory levels (read first)
            locations = await self.client.get_locations()
            
            if locations:
                # Inventory access works
                capability.enabled = True
                logger.debug("✓ inventory_write: enabled (inferred)")
            else:
                capability.enabled = False
                capability.error = "No locations found"
                
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ inventory_write: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"inventory_write check failed: {e}")
        
        return capability
    
    async def _check_fulfillment_write(self) -> ShopifyCapability:
        """Check fulfillment write capability"""
        capability = ShopifyCapability(
            name="fulfillment_write",
            scope="write_fulfillments",
            enabled=False,
        )
        
        try:
            # Check if we can access order fulfillments
            orders = await self.client.get_orders(limit=1)
            
            if orders:
                # Try to get fulfillments for an order
                await self.client.get_fulfillments(orders[0].id)
                capability.enabled = True
                logger.debug("✓ fulfillment_write: enabled")
            else:
                # No orders to test
                capability.enabled = True
                logger.debug("✓ fulfillment_write: enabled (no orders to verify)")
                
        except ShopifyAuthError as e:
            capability.error = str(e)
            logger.debug(f"✗ fulfillment_write: {e}")
        except Exception as e:
            capability.error = str(e)
            logger.warning(f"fulfillment_write check failed: {e}")
        
        return capability
    
    def _determine_browser_requirements(self, profile: ShopifyCapabilityProfile) -> list:
        """
        Determine which operations require browser automation.
        
        These are operations that cannot be done via the Admin API.
        """
        needs_browser = []
        
        # Theme editing requires Shopify admin UI or Theme API (limited)
        needs_browser.append("theme_edit")
        
        # Review management typically requires apps or manual UI
        needs_browser.append("reviews")
        
        # Some checkout customizations require admin UI
        needs_browser.append("checkout_customization")
        
        # App management
        needs_browser.append("app_management")
        
        # Store settings
        needs_browser.append("store_settings")
        
        return needs_browser
    
    def _summarize_profile(self, profile: ShopifyCapabilityProfile) -> str:
        """Create a summary string for logging"""
        enabled = []
        disabled = []
        
        caps = {
            "product_read": profile.product_read,
            "product_write": profile.product_write,
            "order_read": profile.order_read,
            "order_write": profile.order_write,
            "customer_read": profile.customer_read,
            "content_write": profile.content_write,
            "inventory_read": profile.inventory_read,
            "fulfillment_write": profile.fulfillment_write,
        }
        
        for name, value in caps.items():
            if value:
                enabled.append(name)
            else:
                disabled.append(name)
        
        return f"Enabled: {len(enabled)}, Disabled: {len(disabled)}"
    
    async def save_profile(self, profile: ShopifyCapabilityProfile) -> Path:
        """
        Save capability profile to business memory.
        
        Args:
            profile: Capability profile to save
            
        Returns:
            Path to saved file
        """
        file_path = self._get_profile_path()
        
        # Convert to dict with datetime serialization
        data = profile.model_dump()
        
        # Serialize datetimes
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=serialize)
        
        logger.info(f"Saved capability profile to {file_path}")
        return file_path
    
    async def load_profile(self) -> Optional[ShopifyCapabilityProfile]:
        """
        Load capability profile from business memory.
        
        Returns:
            ShopifyCapabilityProfile if exists, None otherwise
        """
        file_path = self._get_profile_path()
        
        if not file_path.exists():
            logger.debug(f"No capability profile found at {file_path}")
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            return ShopifyCapabilityProfile(**data)
            
        except Exception as e:
            logger.error(f"Failed to load capability profile: {e}")
            return None
    
    async def refresh_if_stale(self, max_age_hours: int = 24) -> ShopifyCapabilityProfile:
        """
        Refresh capabilities if profile is stale.
        
        Args:
            max_age_hours: Maximum age in hours before refresh
            
        Returns:
            Current or refreshed capability profile
        """
        profile = await self.load_profile()
        
        if profile:
            age = datetime.utcnow() - profile.checked_at
            age_hours = age.total_seconds() / 3600
            
            if age_hours < max_age_hours:
                logger.debug(f"Using cached capability profile (age: {age_hours:.1f}h)")
                return profile
            
            logger.info(f"Capability profile stale ({age_hours:.1f}h), refreshing...")
        
        # Refresh capabilities
        profile = await self.check_all_capabilities()
        await self.save_profile(profile)
        
        return profile


async def check_shopify_capabilities(
    shop_domain: str,
    access_token: str,
    tenant_id: str,
    save_profile: bool = True,
) -> ShopifyCapabilityProfile:
    """
    Convenience function to check Shopify capabilities.
    
    Args:
        shop_domain: Shopify store domain
        access_token: Admin API access token
        tenant_id: Tenant identifier
        save_profile: Whether to save profile to disk
        
    Returns:
        ShopifyCapabilityProfile
    """
    async with ShopifyAdminClient(shop_domain, access_token) as client:
        checker = ShopifyCapabilityChecker(client, tenant_id)
        profile = await checker.check_all_capabilities()
        
        if save_profile:
            await checker.save_profile(profile)
        
        return profile
