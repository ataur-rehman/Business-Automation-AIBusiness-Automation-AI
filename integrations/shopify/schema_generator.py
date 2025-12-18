"""
Shopify Schema Generator
Generates structured schemas for Shopify product and order data.
Used by the Schema Generator service to create Shopify-specific data schemas.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ShopifyFieldDefinition(BaseModel):
    """Definition of a Shopify data field"""
    name: str
    type: str  # string, number, boolean, array, object, enum
    description: str
    required: bool = False
    nullable: bool = True
    example: Optional[Any] = None
    enum_values: Optional[List[str]] = None
    array_item_type: Optional[str] = None
    nested_fields: Optional[List["ShopifyFieldDefinition"]] = None


class ShopifySchema(BaseModel):
    """Complete schema for a Shopify entity"""
    schema_name: str
    schema_version: str = "1.0"
    entity_type: str  # product, order, customer, variant, etc.
    description: str
    fields: List[ShopifyFieldDefinition]
    source: str = "shopify_admin_api"
    api_version: str = "2025-10"
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ShopifySchemaGenerator:
    """
    Generates structured schemas for Shopify data.
    
    Produces consistent, normalized schemas that can be used by:
    - RAG systems for knowledge retrieval
    - Support agents for answering queries
    - Content agents for generating descriptions
    - Analytics systems for reporting
    """
    
    API_VERSION = "2025-10"
    
    @classmethod
    def generate_product_schema(cls) -> ShopifySchema:
        """Generate schema for Shopify products"""
        return ShopifySchema(
            schema_name="shopify_product",
            entity_type="product",
            description="Shopify product schema with variants, options, and images",
            api_version=cls.API_VERSION,
            fields=[
                ShopifyFieldDefinition(
                    name="id",
                    type="number",
                    description="Unique Shopify product ID",
                    required=True,
                    nullable=False,
                    example=7654321098765
                ),
                ShopifyFieldDefinition(
                    name="title",
                    type="string",
                    description="Product title/name",
                    required=True,
                    nullable=False,
                    example="Premium Wireless Headphones"
                ),
                ShopifyFieldDefinition(
                    name="handle",
                    type="string",
                    description="URL-friendly product handle",
                    required=True,
                    nullable=False,
                    example="premium-wireless-headphones"
                ),
                ShopifyFieldDefinition(
                    name="body_html",
                    type="string",
                    description="Product description in HTML format",
                    required=False,
                    nullable=True,
                    example="<p>High-quality wireless headphones...</p>"
                ),
                ShopifyFieldDefinition(
                    name="vendor",
                    type="string",
                    description="Product vendor/brand",
                    required=False,
                    nullable=True,
                    example="AudioTech"
                ),
                ShopifyFieldDefinition(
                    name="product_type",
                    type="string",
                    description="Product type/category",
                    required=False,
                    nullable=True,
                    example="Electronics"
                ),
                ShopifyFieldDefinition(
                    name="status",
                    type="enum",
                    description="Product publication status",
                    required=True,
                    nullable=False,
                    enum_values=["active", "archived", "draft"],
                    example="active"
                ),
                ShopifyFieldDefinition(
                    name="tags",
                    type="string",
                    description="Comma-separated list of product tags",
                    required=False,
                    nullable=True,
                    example="wireless, bluetooth, headphones"
                ),
                ShopifyFieldDefinition(
                    name="variants",
                    type="array",
                    description="Array of product variants",
                    required=True,
                    array_item_type="object",
                    nested_fields=[
                        ShopifyFieldDefinition(
                            name="id", type="number", description="Variant ID", required=True
                        ),
                        ShopifyFieldDefinition(
                            name="title", type="string", description="Variant title", required=True
                        ),
                        ShopifyFieldDefinition(
                            name="price", type="string", description="Variant price", required=True
                        ),
                        ShopifyFieldDefinition(
                            name="sku", type="string", description="Stock keeping unit", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="inventory_quantity", type="number", description="Available stock", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="option1", type="string", description="First option value (e.g., Size)", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="option2", type="string", description="Second option value (e.g., Color)", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="option3", type="string", description="Third option value", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="weight", type="number", description="Weight in weight_unit", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="weight_unit", type="string", description="Weight unit (kg, g, lb, oz)", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="barcode", type="string", description="Product barcode (UPC, EAN, etc.)", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="compare_at_price", type="string", description="Original price for sale display", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="requires_shipping", type="boolean", description="Whether variant requires shipping", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="taxable", type="boolean", description="Whether variant is taxable", required=False
                        ),
                    ]
                ),
                ShopifyFieldDefinition(
                    name="options",
                    type="array",
                    description="Product options (Size, Color, etc.)",
                    required=False,
                    array_item_type="object",
                    nested_fields=[
                        ShopifyFieldDefinition(
                            name="id", type="number", description="Option ID", required=True
                        ),
                        ShopifyFieldDefinition(
                            name="name", type="string", description="Option name", required=True
                        ),
                        ShopifyFieldDefinition(
                            name="values", type="array", description="Available option values", array_item_type="string", required=True
                        ),
                    ]
                ),
                ShopifyFieldDefinition(
                    name="images",
                    type="array",
                    description="Product images",
                    required=False,
                    array_item_type="object",
                    nested_fields=[
                        ShopifyFieldDefinition(
                            name="id", type="number", description="Image ID", required=True
                        ),
                        ShopifyFieldDefinition(
                            name="src", type="string", description="Image URL", required=True
                        ),
                        ShopifyFieldDefinition(
                            name="alt", type="string", description="Alt text", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="position", type="number", description="Display position", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="width", type="number", description="Image width in pixels", required=False
                        ),
                        ShopifyFieldDefinition(
                            name="height", type="number", description="Image height in pixels", required=False
                        ),
                    ]
                ),
                ShopifyFieldDefinition(
                    name="created_at",
                    type="string",
                    description="Product creation timestamp (ISO 8601)",
                    required=False,
                    example="2024-01-15T10:30:00Z"
                ),
                ShopifyFieldDefinition(
                    name="updated_at",
                    type="string",
                    description="Product last update timestamp (ISO 8601)",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="published_at",
                    type="string",
                    description="Product publication timestamp (ISO 8601)",
                    required=False
                ),
            ]
        )
    
    @classmethod
    def generate_order_schema(cls) -> ShopifySchema:
        """Generate schema for Shopify orders"""
        return ShopifySchema(
            schema_name="shopify_order",
            entity_type="order",
            description="Shopify order schema with line items, addresses, and fulfillment",
            api_version=cls.API_VERSION,
            fields=[
                ShopifyFieldDefinition(
                    name="id",
                    type="number",
                    description="Unique Shopify order ID",
                    required=True,
                    example=5678901234567
                ),
                ShopifyFieldDefinition(
                    name="name",
                    type="string",
                    description="Order number (e.g., #1001)",
                    required=True,
                    example="#1001"
                ),
                ShopifyFieldDefinition(
                    name="order_number",
                    type="number",
                    description="Numeric order number",
                    required=True,
                    example=1001
                ),
                ShopifyFieldDefinition(
                    name="email",
                    type="string",
                    description="Customer email",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="phone",
                    type="string",
                    description="Customer phone",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="created_at",
                    type="string",
                    description="Order creation timestamp (ISO 8601)",
                    required=True
                ),
                ShopifyFieldDefinition(
                    name="currency",
                    type="string",
                    description="Order currency code",
                    required=True,
                    example="USD"
                ),
                ShopifyFieldDefinition(
                    name="total_price",
                    type="string",
                    description="Total order price",
                    required=True,
                    example="99.99"
                ),
                ShopifyFieldDefinition(
                    name="subtotal_price",
                    type="string",
                    description="Subtotal before tax/shipping",
                    required=True
                ),
                ShopifyFieldDefinition(
                    name="total_tax",
                    type="string",
                    description="Total tax amount",
                    required=True,
                    example="8.50"
                ),
                ShopifyFieldDefinition(
                    name="total_discounts",
                    type="string",
                    description="Total discount amount",
                    required=True,
                    example="10.00"
                ),
                ShopifyFieldDefinition(
                    name="financial_status",
                    type="enum",
                    description="Payment status",
                    required=True,
                    enum_values=["pending", "authorized", "partially_paid", "paid", "partially_refunded", "refunded", "voided"]
                ),
                ShopifyFieldDefinition(
                    name="fulfillment_status",
                    type="enum",
                    description="Fulfillment status",
                    required=False,
                    enum_values=["fulfilled", "partial", "unfulfilled", "restocked"]
                ),
                ShopifyFieldDefinition(
                    name="gateway",
                    type="string",
                    description="Payment gateway used",
                    required=False,
                    example="shopify_payments"
                ),
                ShopifyFieldDefinition(
                    name="test",
                    type="boolean",
                    description="Whether this is a test order",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="note",
                    type="string",
                    description="Customer notes on order",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="tags",
                    type="string",
                    description="Comma-separated order tags",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="line_items",
                    type="array",
                    description="Ordered items",
                    required=True,
                    array_item_type="object",
                    nested_fields=[
                        ShopifyFieldDefinition(name="id", type="number", description="Line item ID", required=True),
                        ShopifyFieldDefinition(name="product_id", type="number", description="Product ID", required=False),
                        ShopifyFieldDefinition(name="variant_id", type="number", description="Variant ID", required=False),
                        ShopifyFieldDefinition(name="title", type="string", description="Product title", required=True),
                        ShopifyFieldDefinition(name="variant_title", type="string", description="Variant title", required=False),
                        ShopifyFieldDefinition(name="sku", type="string", description="SKU", required=False),
                        ShopifyFieldDefinition(name="quantity", type="number", description="Quantity ordered", required=True),
                        ShopifyFieldDefinition(name="price", type="string", description="Unit price", required=True),
                        ShopifyFieldDefinition(name="total_discount", type="string", description="Line item discount", required=False),
                        ShopifyFieldDefinition(name="fulfillment_status", type="string", description="Line item fulfillment", required=False),
                    ]
                ),
                ShopifyFieldDefinition(
                    name="shipping_address",
                    type="object",
                    description="Shipping address",
                    required=False,
                    nested_fields=[
                        ShopifyFieldDefinition(name="first_name", type="string", description="First name", required=False),
                        ShopifyFieldDefinition(name="last_name", type="string", description="Last name", required=False),
                        ShopifyFieldDefinition(name="company", type="string", description="Company name", required=False),
                        ShopifyFieldDefinition(name="address1", type="string", description="Street address line 1", required=False),
                        ShopifyFieldDefinition(name="address2", type="string", description="Street address line 2", required=False),
                        ShopifyFieldDefinition(name="city", type="string", description="City", required=False),
                        ShopifyFieldDefinition(name="province", type="string", description="State/Province", required=False),
                        ShopifyFieldDefinition(name="province_code", type="string", description="State/Province code", required=False),
                        ShopifyFieldDefinition(name="country", type="string", description="Country", required=False),
                        ShopifyFieldDefinition(name="country_code", type="string", description="Country code (ISO)", required=False),
                        ShopifyFieldDefinition(name="zip", type="string", description="Postal/ZIP code", required=False),
                        ShopifyFieldDefinition(name="phone", type="string", description="Phone number", required=False),
                    ]
                ),
                ShopifyFieldDefinition(
                    name="fulfillments",
                    type="array",
                    description="Fulfillment records",
                    required=False,
                    array_item_type="object",
                    nested_fields=[
                        ShopifyFieldDefinition(name="id", type="number", description="Fulfillment ID", required=True),
                        ShopifyFieldDefinition(name="status", type="string", description="Fulfillment status", required=True),
                        ShopifyFieldDefinition(name="tracking_number", type="string", description="Tracking number", required=False),
                        ShopifyFieldDefinition(name="tracking_company", type="string", description="Carrier name", required=False),
                        ShopifyFieldDefinition(name="tracking_url", type="string", description="Tracking URL", required=False),
                        ShopifyFieldDefinition(name="created_at", type="string", description="Fulfillment timestamp", required=False),
                    ]
                ),
                ShopifyFieldDefinition(
                    name="cancelled_at",
                    type="string",
                    description="Cancellation timestamp if cancelled",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="cancel_reason",
                    type="string",
                    description="Reason for cancellation",
                    required=False
                ),
            ]
        )
    
    @classmethod
    def generate_customer_schema(cls) -> ShopifySchema:
        """Generate schema for Shopify customers"""
        return ShopifySchema(
            schema_name="shopify_customer",
            entity_type="customer",
            description="Shopify customer schema with addresses and order statistics",
            api_version=cls.API_VERSION,
            fields=[
                ShopifyFieldDefinition(
                    name="id",
                    type="number",
                    description="Unique Shopify customer ID",
                    required=True
                ),
                ShopifyFieldDefinition(
                    name="email",
                    type="string",
                    description="Customer email address",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="phone",
                    type="string",
                    description="Customer phone number",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="first_name",
                    type="string",
                    description="Customer first name",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="last_name",
                    type="string",
                    description="Customer last name",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="accepts_marketing",
                    type="boolean",
                    description="Marketing opt-in status",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="verified_email",
                    type="boolean",
                    description="Email verification status",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="state",
                    type="enum",
                    description="Customer account state",
                    enum_values=["enabled", "disabled", "invited", "declined"],
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="orders_count",
                    type="number",
                    description="Total number of orders",
                    required=False,
                    example=5
                ),
                ShopifyFieldDefinition(
                    name="total_spent",
                    type="string",
                    description="Total amount spent",
                    required=False,
                    example="499.95"
                ),
                ShopifyFieldDefinition(
                    name="currency",
                    type="string",
                    description="Customer currency",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="note",
                    type="string",
                    description="Customer notes",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="tags",
                    type="string",
                    description="Comma-separated customer tags",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="tax_exempt",
                    type="boolean",
                    description="Tax exemption status",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="default_address",
                    type="object",
                    description="Default shipping address",
                    required=False,
                    nested_fields=[
                        ShopifyFieldDefinition(name="address1", type="string", description="Street address", required=False),
                        ShopifyFieldDefinition(name="city", type="string", description="City", required=False),
                        ShopifyFieldDefinition(name="province", type="string", description="State/Province", required=False),
                        ShopifyFieldDefinition(name="country", type="string", description="Country", required=False),
                        ShopifyFieldDefinition(name="zip", type="string", description="Postal code", required=False),
                        ShopifyFieldDefinition(name="phone", type="string", description="Phone", required=False),
                    ]
                ),
                ShopifyFieldDefinition(
                    name="addresses",
                    type="array",
                    description="All customer addresses",
                    required=False,
                    array_item_type="object"
                ),
                ShopifyFieldDefinition(
                    name="created_at",
                    type="string",
                    description="Customer creation timestamp",
                    required=False
                ),
                ShopifyFieldDefinition(
                    name="updated_at",
                    type="string",
                    description="Last update timestamp",
                    required=False
                ),
            ]
        )
    
    @classmethod
    def generate_all_schemas(cls) -> Dict[str, ShopifySchema]:
        """Generate all Shopify schemas"""
        return {
            "product": cls.generate_product_schema(),
            "order": cls.generate_order_schema(),
            "customer": cls.generate_customer_schema(),
        }
    
    @classmethod
    def to_json_schema(cls, schema: ShopifySchema) -> Dict[str, Any]:
        """Convert ShopifySchema to JSON Schema format"""
        properties = {}
        required = []
        
        for field in schema.fields:
            field_schema = cls._field_to_json_schema(field)
            properties[field.name] = field_schema
            
            if field.required:
                required.append(field.name)
        
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": schema.schema_name,
            "description": schema.description,
            "type": "object",
            "properties": properties,
            "required": required if required else None,
        }
    
    @classmethod
    def _field_to_json_schema(cls, field: ShopifyFieldDefinition) -> Dict[str, Any]:
        """Convert a field definition to JSON Schema format"""
        type_mapping = {
            "string": "string",
            "number": "number",
            "boolean": "boolean",
            "array": "array",
            "object": "object",
            "enum": "string",
        }
        
        schema: Dict[str, Any] = {
            "type": type_mapping.get(field.type, "string"),
            "description": field.description,
        }
        
        if field.example is not None:
            schema["examples"] = [field.example]
        
        if field.type == "enum" and field.enum_values:
            schema["enum"] = field.enum_values
        
        if field.type == "array":
            if field.nested_fields:
                items_properties = {}
                items_required = []
                for nested in field.nested_fields:
                    items_properties[nested.name] = cls._field_to_json_schema(nested)
                    if nested.required:
                        items_required.append(nested.name)
                
                schema["items"] = {
                    "type": "object",
                    "properties": items_properties,
                }
                if items_required:
                    schema["items"]["required"] = items_required
            elif field.array_item_type:
                schema["items"] = {"type": field.array_item_type}
        
        if field.type == "object" and field.nested_fields:
            nested_properties = {}
            nested_required = []
            for nested in field.nested_fields:
                nested_properties[nested.name] = cls._field_to_json_schema(nested)
                if nested.required:
                    nested_required.append(nested.name)
            
            schema["properties"] = nested_properties
            if nested_required:
                schema["required"] = nested_required
        
        if field.nullable:
            schema["nullable"] = True
        
        return schema


def get_shopify_product_schema_summary() -> str:
    """Get a text summary of the Shopify product schema for prompts"""
    return """
Product Schema (Shopify):
- title: string (required) - Product name
- sku: string - Stock keeping unit
- price: number - Product price
- variants: list - Product variants with price/sku/inventory
- options: list - Variant options (Size, Color, Material)
- tags: list - Product tags for categorization
- images: list - Product image URLs
- inventory_quantity: number - Available stock
- vendor: string - Brand/vendor name
- status: string (active/archived/draft) - Publication status
- body_html: string - Product description (HTML)
- handle: string - URL slug
- product_type: string - Category/type
"""


def get_shopify_order_schema_summary() -> str:
    """Get a text summary of the Shopify order schema for prompts"""
    return """
Order Schema (Shopify):
- order_id: string (required) - Unique order identifier
- name: string - Order number (#1001)
- line_items: list - Ordered products with quantity/price
- shipping_address: object - Delivery address
- billing_address: object - Payment address
- financial_status: string - Payment status (pending/paid/refunded)
- fulfillment_status: string - Shipping status (unfulfilled/partial/fulfilled)
- total_price: number - Order total
- subtotal_price: number - Subtotal before tax/shipping
- total_tax: number - Tax amount
- total_discounts: number - Discount amount
- currency: string - Currency code (USD)
- gateway: string - Payment method
- created_at: string - Order timestamp
- customer: object - Customer info
- tracking_number: string - Shipment tracking
- note: string - Order notes
"""
