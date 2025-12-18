"""
Shopify Data Ingestion Service
Syncs products, orders, customers, and policies from Shopify to local database
and RAG index for AI-powered workflows.
"""

from __future__ import annotations  # Enable forward references for type hints

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from .client import ShopifyAdminClient, ShopifyAPIError
from .capability_checker import ShopifyCapabilityChecker
from .models import (
    ShopifyProduct,
    ShopifyOrder,
    ShopifyCustomer,
    ShopifyPolicy,
    ShopifyCapabilityProfile,
    SyncType,
    SyncStatus,
    SyncResult,
)

# Import database models
from backend.models.product import Product, ProductStatus
from backend.models.order import Order, OrderStatus, PaymentStatus, FulfillmentStatus
from backend.models.customer import Customer, CustomerStatus

# Try importing RAG integration
try:
    from agents.data_scraper.rag_integration import RAGIntegration, LLAMAINDEX_AVAILABLE
except ImportError:
    RAGIntegration = None  # type: ignore
    LLAMAINDEX_AVAILABLE = False

logger = logging.getLogger(__name__)


class ShopifyService:
    """
    Shopify data synchronization service.
    
    Handles:
    - Product sync from Shopify to local DB + RAG
    - Order sync for tracking and automation
    - Customer sync for support and personalization
    - Policy sync for support agent context
    
    Supports multi-tenant architecture via tenant_id.
    
    Usage:
        service = ShopifyService(db_session, client, tenant_id)
        result = await service.sync_products()
    """
    
    PLATFORM_NAME = "shopify"
    
    def __init__(
        self,
        db: AsyncSession,
        client: ShopifyAdminClient,
        tenant_id: str,
        rag_integration: Optional[Any] = None,
    ):
        """
        Initialize Shopify service.
        
        Args:
            db: SQLAlchemy async session
            client: Shopify Admin API client
            tenant_id: Tenant identifier for multi-tenant isolation
            rag_integration: Optional RAGIntegration instance for vector indexing
        """
        self.db = db
        self.client = client
        self.tenant_id = tenant_id
        self.rag = rag_integration
        
        # Initialize RAG if available and not provided
        if self.rag is None and LLAMAINDEX_AVAILABLE and RAGIntegration:
            try:
                self.rag = RAGIntegration(
                    persist_dir=f"./data/rag_indices/{tenant_id}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize RAG: {e}")
        
        logger.info(f"ShopifyService initialized for tenant {tenant_id}")
    
    # =========================================================================
    # Product Sync
    # =========================================================================
    
    async def sync_products(
        self,
        full_sync: bool = False,
        since_updated: datetime = None,
        max_products: int = None,
        push_to_rag: bool = True,
    ) -> SyncResult:
        """
        Sync products from Shopify to local database.
        
        Args:
            full_sync: If True, sync all products. If False, only updated ones.
            since_updated: Only sync products updated after this date
            max_products: Maximum number of products to sync
            push_to_rag: Whether to push products to RAG index
            
        Returns:
            SyncResult with sync statistics
        """
        result = SyncResult(
            sync_type=SyncType.PRODUCTS,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )
        
        try:
            logger.info(f"Starting product sync for tenant {self.tenant_id}")
            
            # Fetch products from Shopify
            params = {}
            if not full_sync and since_updated:
                params["updated_at_min"] = since_updated
            
            max_pages = (max_products // 250) + 1 if max_products else None
            
            shopify_products = await self.client.get_products(
                limit=250,
                max_pages=max_pages,
                **params
            )
            
            if max_products:
                shopify_products = shopify_products[:max_products]
            
            logger.info(f"Fetched {len(shopify_products)} products from Shopify")
            
            # Process each product
            synced_count = 0
            failed_count = 0
            
            for shopify_product in shopify_products:
                try:
                    await self._upsert_product(shopify_product)
                    synced_count += 1
                    
                    # Push to RAG
                    if push_to_rag and self.rag and self.rag.is_available:
                        await self._push_product_to_rag(shopify_product)
                        
                except Exception as e:
                    logger.error(f"Failed to sync product {shopify_product.id}: {e}")
                    result.errors.append(f"Product {shopify_product.id}: {str(e)}")
                    failed_count += 1
            
            # Commit all changes
            await self.db.commit()
            
            result.status = SyncStatus.COMPLETED if failed_count == 0 else SyncStatus.PARTIAL
            result.items_synced = synced_count
            result.items_failed = failed_count
            result.completed_at = datetime.utcnow()
            
            logger.info(f"Product sync complete: {synced_count} synced, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Product sync failed: {e}", exc_info=True)
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()
            await self.db.rollback()
        
        return result
    
    async def _upsert_product(self, shopify_product: ShopifyProduct) -> Product:
        """Insert or update a product in the database"""
        
        # Check if product exists
        stmt = select(Product).where(
            and_(
                Product.tenant_id == self.tenant_id,
                Product.external_id == str(shopify_product.id),
                Product.is_deleted == False,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        # Normalize product data
        normalized = self._normalize_product(shopify_product)
        
        if existing:
            # Update existing product
            for key, value in normalized.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            logger.debug(f"Updated product: {shopify_product.title}")
            return existing
        else:
            # Create new product
            product = Product(
                tenant_id=self.tenant_id,
                **normalized
            )
            self.db.add(product)
            logger.debug(f"Created product: {shopify_product.title}")
            return product
    
    def _normalize_product(self, shopify_product: ShopifyProduct) -> Dict[str, Any]:
        """Convert Shopify product to normalized DB format"""
        
        # Get primary variant for price/sku
        primary_variant = shopify_product.variants[0] if shopify_product.variants else None
        
        # Build image list
        images = [img.src for img in shopify_product.images] if shopify_product.images else []
        
        # Map status
        status_map = {
            "active": ProductStatus.ACTIVE,
            "archived": ProductStatus.DISCONTINUED,
            "draft": ProductStatus.DRAFT,
        }
        
        return {
            "external_id": str(shopify_product.id),
            "name": shopify_product.title,
            "slug": shopify_product.handle,
            "sku": primary_variant.sku if primary_variant else None,
            "description": self._strip_html(shopify_product.body_html) if shopify_product.body_html else None,
            "long_description": shopify_product.body_html,
            "category": shopify_product.product_type,
            "tags": shopify_product.tags_list,
            "price": float(primary_variant.price) if primary_variant else None,
            "currency": "USD",  # Shopify stores price in shop currency
            "stock_quantity": primary_variant.inventory_quantity if primary_variant else None,
            "images": images,
            "primary_image_url": images[0] if images else None,
            "status": status_map.get(shopify_product.status.value, ProductStatus.ACTIVE),
            "external_url": f"https://{self.client.shop_domain}/products/{shopify_product.handle}",
            "specifications": {
                "vendor": shopify_product.vendor,
                "variants_count": len(shopify_product.variants),
                "options": [opt.name for opt in shopify_product.options] if shopify_product.options else [],
            },
            "custom_fields": {
                "shopify_created_at": shopify_product.created_at.isoformat() if shopify_product.created_at else None,
                "shopify_updated_at": shopify_product.updated_at.isoformat() if shopify_product.updated_at else None,
                "published_at": shopify_product.published_at.isoformat() if shopify_product.published_at else None,
            },
            "is_active": shopify_product.status == "active",
        }
    
    async def _push_product_to_rag(self, shopify_product: ShopifyProduct):
        """Push product to RAG index for semantic search"""
        if not self.rag:
            return
        
        try:
            # Create document-like structure for RAG
            from scraper.models import ProductData
            
            product_data = ProductData(
                name=shopify_product.title,
                price=float(shopify_product.variants[0].price) if shopify_product.variants else None,
                currency="USD",
                url=f"https://{self.client.shop_domain}/products/{shopify_product.handle}",
                image_url=shopify_product.images[0].src if shopify_product.images else None,
                description=self._strip_html(shopify_product.body_html) if shopify_product.body_html else None,
                sku=shopify_product.variants[0].sku if shopify_product.variants else None,
                category=shopify_product.product_type,
                brand=shopify_product.vendor,
                in_stock=shopify_product.variants[0].inventory_quantity > 0 if shopify_product.variants else True,
            )
            
            # Push to RAG
            self.rag._product_to_document(product_data, self.tenant_id)
            
        except Exception as e:
            logger.warning(f"Failed to push product to RAG: {e}")
    
    # =========================================================================
    # Order Sync
    # =========================================================================
    
    async def sync_orders(
        self,
        full_sync: bool = False,
        since_created: datetime = None,
        status: str = "any",
        max_orders: int = None,
    ) -> SyncResult:
        """
        Sync orders from Shopify to local database.
        
        Args:
            full_sync: If True, sync all orders. If False, only recent ones.
            since_created: Only sync orders created after this date
            status: Order status filter (open, closed, cancelled, any)
            max_orders: Maximum number of orders to sync
            
        Returns:
            SyncResult with sync statistics
        """
        result = SyncResult(
            sync_type=SyncType.ORDERS,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )
        
        try:
            logger.info(f"Starting order sync for tenant {self.tenant_id}")
            
            # Fetch orders from Shopify
            max_pages = (max_orders // 250) + 1 if max_orders else 10  # Default to 10 pages
            
            shopify_orders = await self.client.get_orders(
                limit=250,
                status=status,
                created_at_min=since_created,
                max_pages=max_pages,
            )
            
            if max_orders:
                shopify_orders = shopify_orders[:max_orders]
            
            logger.info(f"Fetched {len(shopify_orders)} orders from Shopify")
            
            # Process each order
            synced_count = 0
            failed_count = 0
            
            for shopify_order in shopify_orders:
                try:
                    await self._upsert_order(shopify_order)
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync order {shopify_order.id}: {e}")
                    result.errors.append(f"Order {shopify_order.id}: {str(e)}")
                    failed_count += 1
            
            # Commit all changes
            await self.db.commit()
            
            result.status = SyncStatus.COMPLETED if failed_count == 0 else SyncStatus.PARTIAL
            result.items_synced = synced_count
            result.items_failed = failed_count
            result.completed_at = datetime.utcnow()
            
            logger.info(f"Order sync complete: {synced_count} synced, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Order sync failed: {e}", exc_info=True)
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()
            await self.db.rollback()
        
        return result
    
    async def _upsert_order(self, shopify_order: ShopifyOrder) -> Order:
        """Insert or update an order in the database"""
        
        # Check if order exists
        stmt = select(Order).where(
            and_(
                Order.tenant_id == self.tenant_id,
                Order.external_id == str(shopify_order.id),
                Order.is_deleted == False,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        # Normalize order data
        normalized = self._normalize_order(shopify_order)
        
        if existing:
            # Update existing order
            for key, value in normalized.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            logger.debug(f"Updated order: {shopify_order.name}")
            return existing
        else:
            # Create new order
            order = Order(
                tenant_id=self.tenant_id,
                **normalized
            )
            self.db.add(order)
            logger.debug(f"Created order: {shopify_order.name}")
            return order
    
    def _normalize_order(self, shopify_order: ShopifyOrder) -> Dict[str, Any]:
        """Convert Shopify order to normalized DB format"""
        
        # Map payment status
        payment_status_map = {
            "pending": PaymentStatus.PENDING,
            "authorized": PaymentStatus.AUTHORIZED,
            "paid": PaymentStatus.PAID,
            "partially_paid": PaymentStatus.PARTIALLY_PAID,
            "partially_refunded": PaymentStatus.PARTIALLY_REFUNDED,
            "refunded": PaymentStatus.REFUNDED,
            "voided": PaymentStatus.VOIDED,
        }
        
        # Map fulfillment status
        fulfillment_status_map = {
            "fulfilled": FulfillmentStatus.FULFILLED,
            "partial": FulfillmentStatus.PARTIAL,
            "unfulfilled": FulfillmentStatus.UNFULFILLED,
            "restocked": FulfillmentStatus.RESTOCKED,
            None: FulfillmentStatus.UNFULFILLED,
        }
        
        # Determine order status
        if shopify_order.cancelled_at:
            order_status = OrderStatus.CANCELLED
        elif shopify_order.fulfillment_status and shopify_order.fulfillment_status.value == "fulfilled":
            order_status = OrderStatus.DELIVERED
        elif shopify_order.fulfillment_status and shopify_order.fulfillment_status.value == "partial":
            order_status = OrderStatus.SHIPPED
        elif shopify_order.financial_status.value == "paid":
            order_status = OrderStatus.PROCESSING
        else:
            order_status = OrderStatus.PENDING
        
        # Normalize line items
        line_items = []
        for item in shopify_order.line_items:
            line_items.append({
                "id": item.id,
                "product_id": str(item.product_id) if item.product_id else None,
                "variant_id": str(item.variant_id) if item.variant_id else None,
                "title": item.title,
                "variant_title": item.variant_title,
                "sku": item.sku,
                "quantity": item.quantity,
                "price": item.price,
                "total_discount": item.total_discount,
            })
        
        # Check if COD
        is_cod = shopify_order.gateway and "cod" in shopify_order.gateway.lower()
        
        return {
            "external_id": str(shopify_order.id),
            "order_number": shopify_order.name,
            "platform": self.PLATFORM_NAME,
            "customer_email": shopify_order.email,
            "customer_phone": shopify_order.phone,
            "customer_name": shopify_order.shipping_address.name if shopify_order.shipping_address else None,
            "status": order_status,
            "payment_status": payment_status_map.get(
                shopify_order.financial_status.value,
                PaymentStatus.PENDING
            ),
            "fulfillment_status": fulfillment_status_map.get(
                shopify_order.fulfillment_status.value if shopify_order.fulfillment_status else None,
                FulfillmentStatus.UNFULFILLED
            ),
            "currency": shopify_order.currency,
            "subtotal": float(shopify_order.subtotal_price),
            "total_tax": float(shopify_order.total_tax),
            "total_discounts": float(shopify_order.total_discounts),
            "total_price": float(shopify_order.total_price),
            "payment_method": shopify_order.gateway,
            "is_cod": is_cod,
            "line_items": line_items,
            "shipping_address": shopify_order.shipping_address.model_dump() if shopify_order.shipping_address else None,
            "billing_address": shopify_order.billing_address.model_dump() if shopify_order.billing_address else None,
            "fulfillments": shopify_order.fulfillments,
            "order_date": shopify_order.created_at,
            "cancelled_at": shopify_order.cancelled_at,
            "note": shopify_order.note,
            "tags": shopify_order.tags.split(",") if shopify_order.tags else [],
            "discount_codes": shopify_order.discount_codes,
            "refunds": shopify_order.refunds,
            "is_test": shopify_order.test,
            "requires_confirmation": is_cod,
            "custom_fields": {
                "shopify_order_number": shopify_order.order_number,
                "buyer_accepts_marketing": shopify_order.buyer_accepts_marketing,
            },
        }
    
    # =========================================================================
    # Customer Sync
    # =========================================================================
    
    async def sync_customers(
        self,
        full_sync: bool = False,
        since_updated: datetime = None,
        max_customers: int = None,
    ) -> SyncResult:
        """
        Sync customers from Shopify to local database.
        
        Args:
            full_sync: If True, sync all customers
            since_updated: Only sync customers updated after this date
            max_customers: Maximum number of customers to sync
            
        Returns:
            SyncResult with sync statistics
        """
        result = SyncResult(
            sync_type=SyncType.CUSTOMERS,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )
        
        try:
            logger.info(f"Starting customer sync for tenant {self.tenant_id}")
            
            # Fetch customers from Shopify
            max_pages = (max_customers // 250) + 1 if max_customers else 10
            
            shopify_customers = await self.client.get_customers(
                limit=250,
                updated_at_min=since_updated if not full_sync else None,
                max_pages=max_pages,
            )
            
            if max_customers:
                shopify_customers = shopify_customers[:max_customers]
            
            logger.info(f"Fetched {len(shopify_customers)} customers from Shopify")
            
            # Process each customer
            synced_count = 0
            failed_count = 0
            
            for shopify_customer in shopify_customers:
                try:
                    await self._upsert_customer(shopify_customer)
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync customer {shopify_customer.id}: {e}")
                    result.errors.append(f"Customer {shopify_customer.id}: {str(e)}")
                    failed_count += 1
            
            # Commit all changes
            await self.db.commit()
            
            result.status = SyncStatus.COMPLETED if failed_count == 0 else SyncStatus.PARTIAL
            result.items_synced = synced_count
            result.items_failed = failed_count
            result.completed_at = datetime.utcnow()
            
            logger.info(f"Customer sync complete: {synced_count} synced, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Customer sync failed: {e}", exc_info=True)
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()
            await self.db.rollback()
        
        return result
    
    async def _upsert_customer(self, shopify_customer: ShopifyCustomer) -> Customer:
        """Insert or update a customer in the database"""
        
        # Check if customer exists
        stmt = select(Customer).where(
            and_(
                Customer.tenant_id == self.tenant_id,
                Customer.external_id == str(shopify_customer.id),
                Customer.is_deleted == False,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        # Normalize customer data
        normalized = self._normalize_customer(shopify_customer)
        
        if existing:
            # Update existing customer
            for key, value in normalized.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            logger.debug(f"Updated customer: {shopify_customer.email}")
            return existing
        else:
            # Create new customer
            customer = Customer(
                tenant_id=self.tenant_id,
                **normalized
            )
            self.db.add(customer)
            logger.debug(f"Created customer: {shopify_customer.email}")
            return customer
    
    def _normalize_customer(self, shopify_customer: ShopifyCustomer) -> Dict[str, Any]:
        """Convert Shopify customer to normalized DB format"""
        
        # Map status
        status_map = {
            "enabled": CustomerStatus.ACTIVE,
            "disabled": CustomerStatus.DISABLED,
            "invited": CustomerStatus.INVITED,
            "declined": CustomerStatus.DECLINED,
        }
        
        return {
            "external_id": str(shopify_customer.id),
            "platform": self.PLATFORM_NAME,
            "email": shopify_customer.email,
            "phone": shopify_customer.phone,
            "first_name": shopify_customer.first_name,
            "last_name": shopify_customer.last_name,
            "status": status_map.get(shopify_customer.state, CustomerStatus.ACTIVE),
            "accepts_marketing": shopify_customer.accepts_marketing,
            "marketing_opt_in_date": shopify_customer.accepts_marketing_updated_at,
            "verified_email": shopify_customer.verified_email,
            "default_address": shopify_customer.default_address.model_dump() if shopify_customer.default_address else None,
            "addresses": [addr.model_dump() for addr in shopify_customer.addresses] if shopify_customer.addresses else [],
            "total_orders": shopify_customer.orders_count,
            "total_spent": float(shopify_customer.total_spent),
            "currency": shopify_customer.currency,
            "note": shopify_customer.note,
            "tags": shopify_customer.tags.split(",") if shopify_customer.tags else [],
            "tax_exempt": shopify_customer.tax_exempt,
            "custom_fields": {
                "shopify_created_at": shopify_customer.created_at.isoformat() if shopify_customer.created_at else None,
                "shopify_updated_at": shopify_customer.updated_at.isoformat() if shopify_customer.updated_at else None,
            },
        }
    
    # =========================================================================
    # Policy Sync
    # =========================================================================
    
    async def sync_policies(self) -> SyncResult:
        """
        Sync store policies from Shopify.
        Policies are stored in business memory for support agent context.
        
        Returns:
            SyncResult with sync statistics
        """
        result = SyncResult(
            sync_type=SyncType.POLICIES,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.utcnow(),
        )
        
        try:
            logger.info(f"Starting policy sync for tenant {self.tenant_id}")
            
            # Fetch policies from Shopify
            policies = await self.client.get_policies()
            
            logger.info(f"Fetched {len(policies)} policies from Shopify")
            
            # Store policies in business memory
            policy_data = {}
            for policy in policies:
                policy_data[policy.handle or policy.title.lower().replace(" ", "_")] = {
                    "title": policy.title,
                    "body": policy.body,
                    "url": policy.url,
                    "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
                }
            
            # Save to business memory
            await self._save_policies_to_memory(policy_data)
            
            # Push to RAG for support agent
            if self.rag and self.rag.is_available:
                await self._push_policies_to_rag(policies)
            
            result.status = SyncStatus.COMPLETED
            result.items_synced = len(policies)
            result.completed_at = datetime.utcnow()
            
            logger.info(f"Policy sync complete: {len(policies)} policies synced")
            
        except Exception as e:
            logger.error(f"Policy sync failed: {e}", exc_info=True)
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.utcnow()
        
        return result
    
    async def _save_policies_to_memory(self, policy_data: Dict[str, Any]):
        """Save policies to business memory"""
        import json
        
        memory_path = Path("business_memory") / self.tenant_id
        memory_path.mkdir(parents=True, exist_ok=True)
        
        policies_file = memory_path / "store_policies.json"
        
        with open(policies_file, "w") as f:
            json.dump({
                "tenant_id": self.tenant_id,
                "platform": self.PLATFORM_NAME,
                "shop_domain": self.client.shop_domain,
                "policies": policy_data,
                "synced_at": datetime.utcnow().isoformat(),
            }, f, indent=2)
        
        logger.debug(f"Saved policies to {policies_file}")
    
    async def _push_policies_to_rag(self, policies: List[ShopifyPolicy]):
        """Push policies to RAG for support agent context"""
        if not self.rag:
            return
        
        try:
            from scraper.models import PolicyData
            
            for policy in policies:
                policy_data = PolicyData(
                    title=policy.title,
                    content=policy.body,
                    url=policy.url,
                    policy_type=policy.handle or "general",
                )
                
                self.rag._policy_to_document(policy_data, self.tenant_id)
                
        except Exception as e:
            logger.warning(f"Failed to push policies to RAG: {e}")
    
    # =========================================================================
    # Full Sync
    # =========================================================================
    
    async def sync_all(
        self,
        full_sync: bool = False,
        push_to_rag: bool = True,
    ) -> Dict[str, SyncResult]:
        """
        Perform full data sync: products, orders, customers, policies.
        
        Args:
            full_sync: If True, sync all data. If False, only recent updates.
            push_to_rag: Whether to push data to RAG index
            
        Returns:
            Dictionary of SyncResults keyed by sync type
        """
        logger.info(f"Starting full sync for tenant {self.tenant_id}")
        
        results = {}
        
        # Sync products
        results["products"] = await self.sync_products(
            full_sync=full_sync,
            push_to_rag=push_to_rag,
        )
        
        # Sync orders
        results["orders"] = await self.sync_orders(full_sync=full_sync)
        
        # Sync customers
        results["customers"] = await self.sync_customers(full_sync=full_sync)
        
        # Sync policies
        results["policies"] = await self.sync_policies()
        
        # Log summary
        total_synced = sum(r.items_synced for r in results.values())
        total_failed = sum(r.items_failed for r in results.values())
        
        logger.info(
            f"Full sync complete for tenant {self.tenant_id}: "
            f"{total_synced} items synced, {total_failed} failed"
        )
        
        return results
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def _strip_html(self, html: str) -> str:
        """Remove HTML tags from string"""
        import re
        if not html:
            return ""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html).strip()
    
    async def get_sync_stats(self) -> Dict[str, Any]:
        """Get current sync statistics for the tenant"""
        
        # Count products
        product_count = await self.db.execute(
            select(Product).where(
                and_(
                    Product.tenant_id == self.tenant_id,
                    Product.is_deleted == False,
                )
            )
        )
        
        # Count orders
        order_count = await self.db.execute(
            select(Order).where(
                and_(
                    Order.tenant_id == self.tenant_id,
                    Order.is_deleted == False,
                )
            )
        )
        
        # Count customers
        customer_count = await self.db.execute(
            select(Customer).where(
                and_(
                    Customer.tenant_id == self.tenant_id,
                    Customer.is_deleted == False,
                )
            )
        )
        
        return {
            "tenant_id": self.tenant_id,
            "platform": self.PLATFORM_NAME,
            "shop_domain": self.client.shop_domain,
            "products_count": len(product_count.scalars().all()),
            "orders_count": len(order_count.scalars().all()),
            "customers_count": len(customer_count.scalars().all()),
            "rag_available": self.rag.is_available if self.rag else False,
        }


async def create_shopify_service(
    db: AsyncSession,
    shop_domain: str,
    access_token: str,
    tenant_id: str,
) -> ShopifyService:
    """
    Factory function to create ShopifyService instance.
    
    Args:
        db: SQLAlchemy async session
        shop_domain: Shopify store domain
        access_token: Admin API access token
        tenant_id: Tenant identifier
        
    Returns:
        Configured ShopifyService instance
    """
    client = ShopifyAdminClient(shop_domain, access_token)
    return ShopifyService(db, client, tenant_id)
