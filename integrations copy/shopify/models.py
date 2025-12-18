"""
Shopify Integration Models
Pydantic models for Shopify API requests, responses, and internal data structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


# =============================================================================
# Enums
# =============================================================================

class ShopifyFulfillmentStatus(str, Enum):
    """Shopify order fulfillment status"""
    FULFILLED = "fulfilled"
    PARTIAL = "partial"
    UNFULFILLED = "unfulfilled"
    RESTOCKED = "restocked"


class ShopifyFinancialStatus(str, Enum):
    """Shopify order financial status"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    VOIDED = "voided"


class ShopifyProductStatus(str, Enum):
    """Shopify product status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


# =============================================================================
# Shop Models
# =============================================================================

class ShopInfo(BaseModel):
    """Shopify shop information"""
    id: int
    name: str
    email: str
    domain: str
    myshopify_domain: str
    shop_owner: Optional[str] = None
    phone: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    province_code: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    zip: Optional[str] = None
    currency: str = "USD"
    money_format: Optional[str] = None
    timezone: Optional[str] = None
    plan_name: Optional[str] = None
    plan_display_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# Product Models
# =============================================================================

class ShopifyProductVariant(BaseModel):
    """Shopify product variant"""
    id: int
    product_id: int
    title: str
    price: str
    sku: Optional[str] = None
    position: int = 1
    inventory_policy: str = "deny"
    compare_at_price: Optional[str] = None
    fulfillment_service: str = "manual"
    inventory_management: Optional[str] = None
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    taxable: bool = True
    barcode: Optional[str] = None
    grams: int = 0
    image_id: Optional[int] = None
    weight: float = 0.0
    weight_unit: str = "kg"
    inventory_item_id: Optional[int] = None
    inventory_quantity: int = 0
    old_inventory_quantity: Optional[int] = None
    requires_shipping: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ShopifyProductImage(BaseModel):
    """Shopify product image"""
    id: int
    product_id: int
    position: int = 1
    src: str
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    variant_ids: List[int] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ShopifyProductOption(BaseModel):
    """Shopify product option (e.g., Size, Color)"""
    id: int
    product_id: int
    name: str
    position: int = 1
    values: List[str] = Field(default_factory=list)


class ShopifyProduct(BaseModel):
    """Shopify product"""
    id: int
    title: str
    body_html: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    handle: str
    status: ShopifyProductStatus = ShopifyProductStatus.ACTIVE
    published_scope: str = "web"
    tags: str = ""
    template_suffix: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    variants: List[ShopifyProductVariant] = Field(default_factory=list)
    options: List[ShopifyProductOption] = Field(default_factory=list)
    images: List[ShopifyProductImage] = Field(default_factory=list)
    image: Optional[ShopifyProductImage] = None

    @property
    def tags_list(self) -> List[str]:
        """Convert comma-separated tags to list"""
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class ProductCreateRequest(BaseModel):
    """Request model for creating a product"""
    title: str
    body_html: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    tags: Optional[str] = None
    status: ShopifyProductStatus = ShopifyProductStatus.DRAFT
    variants: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[Dict[str, Any]] = Field(default_factory=list)


class ProductUpdateRequest(BaseModel):
    """Request model for updating a product"""
    title: Optional[str] = None
    body_html: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[ShopifyProductStatus] = None
    variants: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[Dict[str, Any]]] = None


# =============================================================================
# Order Models
# =============================================================================

class ShopifyAddress(BaseModel):
    """Shopify address (shipping/billing)"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    province_code: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ShopifyLineItem(BaseModel):
    """Shopify order line item"""
    id: int
    variant_id: Optional[int] = None
    product_id: Optional[int] = None
    title: str
    variant_title: Optional[str] = None
    sku: Optional[str] = None
    vendor: Optional[str] = None
    quantity: int
    price: str
    total_discount: str = "0.00"
    fulfillment_service: str = "manual"
    fulfillment_status: Optional[str] = None
    gift_card: bool = False
    grams: int = 0
    taxable: bool = True
    tax_lines: List[Dict[str, Any]] = Field(default_factory=list)
    properties: List[Dict[str, Any]] = Field(default_factory=list)
    requires_shipping: bool = True
    name: Optional[str] = None


class ShopifyOrder(BaseModel):
    """Shopify order"""
    id: int
    name: str  # Order number like "#1001"
    order_number: int
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_email: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    currency: str = "USD"
    total_price: str
    subtotal_price: str
    total_tax: str = "0.00"
    total_discounts: str = "0.00"
    total_shipping_price_set: Optional[Dict[str, Any]] = None
    taxes_included: bool = False
    financial_status: ShopifyFinancialStatus = ShopifyFinancialStatus.PENDING
    fulfillment_status: Optional[ShopifyFulfillmentStatus] = None
    cancel_reason: Optional[str] = None
    gateway: Optional[str] = None
    test: bool = False
    confirmed: bool = True
    buyer_accepts_marketing: bool = False
    note: Optional[str] = None
    note_attributes: List[Dict[str, Any]] = Field(default_factory=list)
    tags: str = ""
    line_items: List[ShopifyLineItem] = Field(default_factory=list)
    shipping_address: Optional[ShopifyAddress] = None
    billing_address: Optional[ShopifyAddress] = None
    customer: Optional[Dict[str, Any]] = None
    discount_codes: List[Dict[str, Any]] = Field(default_factory=list)
    fulfillments: List[Dict[str, Any]] = Field(default_factory=list)
    refunds: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Customer Models
# =============================================================================

class ShopifyCustomer(BaseModel):
    """Shopify customer"""
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    accepts_marketing: bool = False
    accepts_marketing_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    orders_count: int = 0
    total_spent: str = "0.00"
    note: Optional[str] = None
    state: str = "disabled"
    verified_email: bool = False
    tax_exempt: bool = False
    tags: str = ""
    currency: str = "USD"
    default_address: Optional[ShopifyAddress] = None
    addresses: List[ShopifyAddress] = Field(default_factory=list)

    @property
    def full_name(self) -> str:
        """Get customer full name"""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or "Unknown"


# =============================================================================
# Blog/Content Models
# =============================================================================

class ShopifyBlog(BaseModel):
    """Shopify blog"""
    id: int
    handle: str
    title: str
    commentable: str = "no"
    feedburner: Optional[str] = None
    feedburner_location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    template_suffix: Optional[str] = None
    tags: str = ""


class ShopifyArticle(BaseModel):
    """Shopify blog article"""
    id: int
    blog_id: int
    title: str
    author: str
    body_html: str
    handle: str
    summary_html: Optional[str] = None
    template_suffix: Optional[str] = None
    tags: str = ""
    published: bool = True
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    image: Optional[Dict[str, Any]] = None


class ArticleCreateRequest(BaseModel):
    """Request model for creating a blog article"""
    title: str
    author: str
    body_html: str
    tags: Optional[str] = None
    summary_html: Optional[str] = None
    published: bool = False
    image: Optional[Dict[str, Any]] = None


# =============================================================================
# Policy Models
# =============================================================================

class ShopifyPolicy(BaseModel):
    """Shopify store policy"""
    title: str
    body: str
    url: Optional[str] = None
    handle: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# Capability Models
# =============================================================================

class ShopifyCapability(BaseModel):
    """Individual capability check result"""
    name: str
    enabled: bool
    scope: Optional[str] = None
    error: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class ShopifyCapabilityProfile(BaseModel):
    """Complete capability profile for a Shopify store"""
    tenant_id: str
    shop_domain: str
    product_read: bool = False
    product_write: bool = False
    order_read: bool = False
    order_write: bool = False
    customer_read: bool = False
    customer_write: bool = False
    content_write: bool = False
    inventory_read: bool = False
    inventory_write: bool = False
    fulfillment_write: bool = False
    needs_browser: List[str] = Field(default_factory=list)
    capabilities: List[ShopifyCapability] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    api_version: str = "2025-10"

    def to_summary(self) -> Dict[str, Any]:
        """Convert to summary dict for Business Analyzer"""
        return {
            "product_read": self.product_read,
            "product_write": self.product_write,
            "order_read": self.order_read,
            "order_write": self.order_write,
            "customer_read": self.customer_read,
            "customer_write": self.customer_write,
            "content_write": self.content_write,
            "inventory_read": self.inventory_read,
            "inventory_write": self.inventory_write,
            "fulfillment_write": self.fulfillment_write,
            "needs_browser": self.needs_browser,
        }


# =============================================================================
# Webhook Models
# =============================================================================

class WebhookTopic(str, Enum):
    """Supported Shopify webhook topics"""
    ORDERS_CREATE = "orders/create"
    ORDERS_UPDATED = "orders/updated"
    ORDERS_FULFILLED = "orders/fulfilled"
    ORDERS_CANCELLED = "orders/cancelled"
    ORDERS_PAID = "orders/paid"
    PRODUCTS_CREATE = "products/create"
    PRODUCTS_UPDATE = "products/update"
    PRODUCTS_DELETE = "products/delete"
    CUSTOMERS_CREATE = "customers/create"
    CUSTOMERS_UPDATE = "customers/update"
    CUSTOMERS_DELETE = "customers/delete"
    INVENTORY_LEVELS_UPDATE = "inventory_levels/update"
    APP_UNINSTALLED = "app/uninstalled"


class ShopifyWebhook(BaseModel):
    """Shopify webhook configuration"""
    id: int
    address: HttpUrl
    topic: str
    format: str = "json"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    api_version: str = "2025-10"


class WebhookCreateRequest(BaseModel):
    """Request model for creating a webhook"""
    topic: WebhookTopic
    address: HttpUrl
    format: str = "json"


class WebhookPayload(BaseModel):
    """Incoming webhook payload wrapper"""
    topic: str
    shop_domain: str
    api_version: str
    payload: Dict[str, Any]
    hmac_header: str
    received_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Sync Status Models
# =============================================================================

class SyncType(str, Enum):
    """Types of data sync"""
    PRODUCTS = "products"
    ORDERS = "orders"
    CUSTOMERS = "customers"
    POLICIES = "policies"
    FULL = "full"


class SyncStatus(str, Enum):
    """Sync operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncResult(BaseModel):
    """Result of a sync operation"""
    sync_type: SyncType
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    items_synced: int = 0
    items_failed: int = 0
    errors: List[str] = Field(default_factory=list)
    next_cursor: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# =============================================================================
# API Response Wrappers
# =============================================================================

class PaginatedResponse(BaseModel):
    """Paginated API response wrapper"""
    items: List[Any]
    has_next_page: bool = False
    next_page_cursor: Optional[str] = None
    total_count: Optional[int] = None


class ShopifyAPIResponse(BaseModel):
    """Generic Shopify API response wrapper"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_max: Optional[int] = None
