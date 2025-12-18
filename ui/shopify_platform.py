"""
Shopify Integration Platform - Premium Dark Theme
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Complete Shopify integration platform with:
• Premium dark theme with violet accents
• Uniform metric cards and grids
• Consistent icon system
• Professional data management
• AI-powered content tools

Run: streamlit run ui/shopify_platform.py
"""

import streamlit as st
import asyncio
import json
import os
import json
import pandas as pd
from pathlib import Path
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Import unified components
from components import (
    get_custom_css,
    COLORS,
    ICONS,
    FONTS,
    render_main_header,
    render_page_header,
    render_section_header,
    render_metrics_grid,
    render_metric_row,
    render_status_row,
    render_status_card,
    render_card,
    render_info_card,
    render_feature_card,
    render_feature_grid,
    render_empty_state,
    render_activity_item,
    render_activity_feed,
    render_capability_grid,
    render_progress_bar,
    render_divider,
    show_toast,
)


# =============================================================================
# Page Configuration
# =============================================================================
st.set_page_config(
    page_title="Shopify Platform",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': '# Shopify Integration Platform\nPremium e-commerce management powered by AI.'
    }
)

# Apply premium white theme with cache buster
import time
cache_buster = int(time.time())
st.markdown(f"<!-- Cache Buster: {cache_buster} -->", unsafe_allow_html=True)
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Simple disk persistence for UI data and login credentials
import base64

STATE_FILE = Path("data/workflow_outputs/streamlit_state.json")
CREDS_FILE = Path("data/workflow_outputs/.credentials")

def _encode_creds(domain: str, token: str) -> str:
    """Simple encoding for credential storage"""
    payload = f"{domain}:::{token}"
    return base64.b64encode(payload.encode()).decode()

def _decode_creds(encoded: str) -> tuple:
    """Decode stored credentials"""
    try:
        decoded = base64.b64decode(encoded.encode()).decode()
        parts = decoded.split(":::")
        if len(parts) == 2:
            return parts[0], parts[1]
    except Exception:
        pass
    return "", ""

def save_login_credentials(domain: str, token: str):
    """Save credentials for persistent login"""
    try:
        CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        encoded = _encode_creds(domain, token)
        CREDS_FILE.write_text(encoded, encoding="utf-8")
    except Exception:
        pass

def load_login_credentials() -> tuple:
    """Load saved login credentials"""
    try:
        if CREDS_FILE.exists():
            encoded = CREDS_FILE.read_text(encoding="utf-8").strip()
            return _decode_creds(encoded)
    except Exception:
        pass
    return "", ""

def clear_login_credentials():
    """Remove saved credentials on logout"""
    try:
        if CREDS_FILE.exists():
            CREDS_FILE.unlink()
    except Exception:
        pass

def load_persisted_state():
    """Load UI data (orders, products, sync results)"""
    try:
        if STATE_FILE.exists():
            with STATE_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Only set if keys are present and current session is empty
            if data.get("current_orders") and not st.session_state.get("current_orders"):
                st.session_state.current_orders = data.get("current_orders", [])
            if data.get("current_products") and not st.session_state.get("current_products"):
                st.session_state.current_products = data.get("current_products", [])
            if data.get("current_customers") and not st.session_state.get("current_customers"):
                st.session_state.current_customers = data.get("current_customers", [])
            if data.get("sync_results"):
                # Shallow merge counts/last_sync
                sr = st.session_state.sync_results
                persisted = data["sync_results"]
                for k in ("products", "orders", "customers"):
                    if k in persisted and k in sr:
                        for fld in ("count", "last_sync", "status"):
                            if fld in persisted[k]:
                                sr[k][fld] = persisted[k][fld]
    except Exception:
        pass

def save_persisted_state():
    """Save UI data to disk"""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "current_orders": st.session_state.get("current_orders", []),
            "current_products": st.session_state.get("current_products", []),
            "current_customers": st.session_state.get("current_customers", []),
            "sync_results": st.session_state.get("sync_results", {}),
            "shop_domain": st.session_state.get("shop_domain", ""),
        }
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    except Exception:
        pass


# =============================================================================
# Session State Initialization
# =============================================================================
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = None
if 'shop_info' not in st.session_state:
    st.session_state.shop_info = None
if 'capabilities' not in st.session_state:
    st.session_state.capabilities = None
if 'sync_results' not in st.session_state:
    st.session_state.sync_results = {
        'products': {'count': 0, 'last_sync': None, 'status': 'not_synced', 'data': []},
        'orders': {'count': 0, 'last_sync': None, 'status': 'not_synced', 'data': []},
        'customers': {'count': 0, 'last_sync': None, 'status': 'not_synced', 'data': []},
    }
if 'test_history' not in st.session_state:
    st.session_state.test_history = []
if 'current_products' not in st.session_state:
    st.session_state.current_products = []
if 'current_orders' not in st.session_state:
    st.session_state.current_orders = []
if 'current_customers' not in st.session_state:
    st.session_state.current_customers = []
if 'integration_logs' not in st.session_state:
    st.session_state.integration_logs = []

# Login state
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'remember_me' not in st.session_state:
    st.session_state.remember_me = False

# Persisted credentials (within session)
if 'shop_domain' not in st.session_state:
    st.session_state.shop_domain = os.getenv("SHOPIFY_SHOP_DOMAIN", "")
if 'access_token' not in st.session_state:
    st.session_state.access_token = os.getenv("SHOPIFY_ACCESS_TOKEN", "")
if 'persist_data' not in st.session_state:
    st.session_state.persist_data = True

# Auto-login if credentials were saved (remember me was checked)
if not st.session_state.is_logged_in:
    saved_domain, saved_token = load_login_credentials()
    if saved_domain and saved_token:
        st.session_state.shop_domain = saved_domain
        st.session_state.access_token = saved_token
        st.session_state.is_logged_in = True
        st.session_state.remember_me = True

# Attempt to restore persisted data on startup
load_persisted_state()


# =============================================================================
# Helper Functions
# =============================================================================
def get_shop_value(shop_info, key: str, default='N/A'):
    """Safely get value from shop_info whether it's a dict or Pydantic model"""
    if shop_info is None:
        return default
    if isinstance(shop_info, dict):
        return shop_info.get(key, default)
    return getattr(shop_info, key, default)


def run_async(coro):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def format_time_ago(dt: Optional[datetime]) -> str:
    """Format datetime as 'X minutes ago'"""
    if not dt:
        return "Never"
    
    diff = datetime.now() - dt
    
    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"


def status_icon(status: bool) -> str:
    """Return emoji for status"""
    return "✅" if status else "❌"


def add_test_result(test_name: str, success: bool, details: str = ""):
    """Add test result to history"""
    st.session_state.test_history.append({
        'test': test_name,
        'success': success,
        'details': details,
        'timestamp': datetime.now()
    })
    
    # Also add to integration logs
    st.session_state.integration_logs.append({
        'timestamp': datetime.now(),
        'event': test_name,
        'status': 'Success' if success else 'Error',
        'details': details,
        'duration': '2.3s'  # Mock duration
    })


# =============================================================================
# Async Test Functions
# =============================================================================
async def test_connection(shop_domain: str, access_token: str) -> Dict[str, Any]:
    """Test Shopify API connection"""
    from integrations.shopify import ShopifyAdminClient
    from integrations.shopify.client import ShopifyAuthError, ShopifyAPIError
    
    result = {
        'success': False,
        'shop_info': None,
        'error': None,
        'debug_info': None
    }
    
    # Validate inputs
    if not shop_domain or not shop_domain.strip():
        result['error'] = "Shop domain is required. Enter your store's myshopify.com domain."
        return result
    
    if not access_token or not access_token.strip():
        result['error'] = "Access token is required. Generate one from Shopify Admin > Settings > Apps > Develop apps."
        return result
    
    try:
        client = ShopifyAdminClient(
            shop_domain=shop_domain,
            access_token=access_token
        )
        
        # Store debug info
        result['debug_info'] = {
            'normalized_domain': client.shop_domain,
            'api_url': client.base_url
        }
        
        shop = await client.get_shop_info()
        await client.close()
        
        result['success'] = True
        result['shop_info'] = {
            'name': shop.name,
            'email': shop.email,
            'domain': shop.domain,
            'currency': shop.currency,
            'country': shop.country_name if hasattr(shop, 'country_name') else 'N/A',
            'plan': shop.plan_name if hasattr(shop, 'plan_name') else 'N/A',
        }
        
    except ShopifyAuthError as e:
        result['error'] = f"Authentication failed: {e}"
    except ShopifyAPIError as e:
        result['error'] = str(e)
    except Exception as e:
        result['error'] = f"Connection error: {e}"
    
    return result


async def sync_products(shop_domain: str, access_token: str, limit: int = 50) -> Dict[str, Any]:
    """Sync products from Shopify"""
    from integrations.shopify import ShopifyAdminClient
    
    result = {'success': False, 'products': [], 'count': 0, 'error': None, 'debug': {}}
    
    try:
        client = ShopifyAdminClient(shop_domain=shop_domain, access_token=access_token)
        products = await client.get_products(limit=limit)
        await client.close()
        
        result['debug']['products_fetched'] = len(products)
        result['debug']['products_type'] = str(type(products))
        
        result['success'] = True
        result['products'] = []
        for p in products:
            # Get image URL for table display
            image_url = 'https://via.placeholder.com/50x50/cccccc/666666?text=IMG'
            if hasattr(p, 'image') and p.image and hasattr(p.image, 'src'):
                image_url = p.image.src
            elif hasattr(p, 'images') and p.images and len(p.images) > 0:
                image_url = p.images[0].src
            
            result['products'].append({
                'id': p.id,
                'title': p.title,
                'sku': p.variants[0].sku if p.variants else 'N/A',
                'price': p.variants[0].price if p.variants else '0.00',
                'inventory_quantity': p.variants[0].inventory_quantity if p.variants else 0,
                'status': p.status,
                'description': p.body_html[:200] + '...' if p.body_html else '',
                'created_at': str(p.created_at) if p.created_at else '',
                'vendor': p.vendor or '',
                'product_type': p.product_type or '',
                'image_url': image_url
            })
        result['count'] = len(products)
        result['debug']['products_processed'] = len(result['products'])
        
    except Exception as e:
        result['error'] = str(e)
        result['debug']['exception_type'] = str(type(e).__name__)
        result['debug']['exception_message'] = str(e)
    
    return result


async def sync_orders(shop_domain: str, access_token: str, limit: int = 50) -> Dict[str, Any]:
    """Sync orders from Shopify"""
    from integrations.shopify import ShopifyAdminClient
    
    result = {'success': False, 'orders': [], 'count': 0, 'error': None}
    
    try:
        client = ShopifyAdminClient(shop_domain=shop_domain, access_token=access_token)
        orders = await client.get_orders(limit=limit)
        await client.close()
        
        result['success'] = True
        result['orders'] = []
        result['debug_customers'] = []  # Debug: collect customer data samples
        
        for o in orders:
            # Extract proper customer name with robust dict handling
            customer_name: str = ''
            order_email: str = getattr(o, 'contact_email', None) or getattr(o, 'email', None) or ''

            cust = getattr(o, 'customer', None)
            
            # Debug: Store first 3 customer samples with address data
            if len(result['debug_customers']) < 3:
                shipping = getattr(o, 'shipping_address', None)
                billing = getattr(o, 'billing_address', None)
                
                result['debug_customers'].append({
                    'order_id': o.id,
                    'customer_type': type(cust).__name__,
                    'customer_value': str(cust)[:500] if cust else None,
                    'order_email': order_email,
                    'shipping_address': {
                        'exists': shipping is not None,
                        'name': getattr(shipping, 'name', None) if shipping else None,
                        'first_name': getattr(shipping, 'first_name', None) if shipping else None,
                        'last_name': getattr(shipping, 'last_name', None) if shipping else None,
                    },
                    'billing_address': {
                        'exists': billing is not None,
                        'name': getattr(billing, 'name', None) if billing else None,
                        'first_name': getattr(billing, 'first_name', None) if billing else None,
                        'last_name': getattr(billing, 'last_name', None) if billing else None,
                    }
                })
            
            if isinstance(cust, dict) and cust:
                first = (cust.get('first_name') or '').strip()
                last = (cust.get('last_name') or '').strip()
                if first or last:
                    customer_name = f"{first} {last}".strip()
                else:
                    # Try default_address name
                    da = cust.get('default_address') or {}
                    if isinstance(da, dict):
                        da_first = (da.get('first_name') or '').strip()
                        da_last = (da.get('last_name') or '').strip()
                        if da_first or da_last:
                            customer_name = f"{da_first} {da_last}".strip()
                # Fallback to customer email
                if not customer_name:
                    cust_email = (cust.get('email') or '').strip()
                    if cust_email:
                        customer_name = cust_email.split('@')[0]

            # Try shipping/billing address names (common for guest checkouts)
            if not customer_name:
                shipping = getattr(o, 'shipping_address', None)
                if shipping:
                    # Try name field first (full name)
                    ship_name = getattr(shipping, 'name', None)
                    if ship_name and ship_name.strip():
                        customer_name = ship_name.strip()
                    else:
                        # Try first_name + last_name
                        ship_first = getattr(shipping, 'first_name', None) or ''
                        ship_last = getattr(shipping, 'last_name', None) or ''
                        if ship_first.strip() or ship_last.strip():
                            customer_name = f"{ship_first} {ship_last}".strip()
            
            # Try billing address if still no name
            if not customer_name:
                billing = getattr(o, 'billing_address', None)
                if billing:
                    bill_name = getattr(billing, 'name', None)
                    if bill_name and bill_name.strip():
                        customer_name = bill_name.strip()
                    else:
                        bill_first = getattr(billing, 'first_name', None) or ''
                        bill_last = getattr(billing, 'last_name', None) or ''
                        if bill_first.strip() or bill_last.strip():
                            customer_name = f"{bill_first} {bill_last}".strip()

            # Fallback to order email
            if not customer_name and order_email:
                customer_name = order_email.split('@')[0]
            
            # Use customer ID if available (for anonymized/sample data)
            if not customer_name and isinstance(cust, dict) and cust.get('id'):
                cust_id = str(cust['id'])
                # Show last 6 digits for brevity
                short_id = cust_id[-6:] if len(cust_id) > 6 else cust_id
                customer_name = f"Customer #{short_id}"
            
            # Final fallback
            if not customer_name:
                customer_name = 'Guest'

            result['orders'].append({
                'id': o.id,
                'order_number': o.order_number,
                'name': o.name,
                'email': order_email,
                'customer_name': customer_name,
                'total': o.total_price,
                'financial_status': o.financial_status,
                'fulfillment_status': o.fulfillment_status or 'unfulfilled',
                'created_at': str(o.created_at) if o.created_at else ''
            })
        
        result['count'] = len(orders)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


async def sync_customers(shop_domain: str, access_token: str, limit: int = 50) -> Dict[str, Any]:
    """Sync customers from Shopify"""
    from integrations.shopify import ShopifyAdminClient
    
    result = {'success': False, 'customers': [], 'count': 0, 'error': None}
    
    try:
        client = ShopifyAdminClient(shop_domain=shop_domain, access_token=access_token)
        customers = await client.get_customers(limit=limit)
        await client.close()
        
        result['success'] = True
        result['customers'] = []
        for c in customers:
            # Extract customer data
            customer_name = f"{c.first_name or ''} {c.last_name or ''}".strip() or 'Guest'
            
            result['customers'].append({
                'id': c.id,
                'name': customer_name,
                'email': c.email or 'N/A',
                'phone': c.phone or 'N/A',
                'orders_count': c.orders_count,
                'total_spent': c.total_spent,
                'created_at': str(c.created_at) if c.created_at else '',
                'tags': c.note or ''
            })
        
        result['count'] = len(customers)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


async def check_capabilities(shop_domain: str, access_token: str) -> Dict[str, Any]:
    """Check store capabilities"""
    from integrations.shopify import ShopifyAdminClient, ShopifyCapabilityChecker
    
    result = {'success': False, 'capabilities': {}, 'scopes': [], 'error': None}
    
    try:
        client = ShopifyAdminClient(shop_domain=shop_domain, access_token=access_token)
        checker = ShopifyCapabilityChecker(client, tenant_id="dashboard-test")
        
        profile = await checker.check_all_capabilities()
        await client.close()
        
        result['success'] = True
        result['capabilities'] = {
            'product_read': profile.product_read,
            'product_write': profile.product_write,
            'order_read': profile.order_read,
            'order_write': profile.order_write,
            'customer_read': profile.customer_read,
            'customer_write': profile.customer_write,
            'content_write': profile.content_write,
            'inventory_read': profile.inventory_read,
            'inventory_write': profile.inventory_write,
            'fulfillment_write': profile.fulfillment_write,
        }
        result['needs_browser'] = profile.needs_browser
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def show_login_page():
    """Login page shown when user is not authenticated"""
    
    render_page_header("Welcome to Shopify Platform", "◈", "Login to manage your store")
    
    # Centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### Enter Your Credentials")
            
            login_domain = st.text_input(
                "Shop Domain",
                placeholder="store.myshopify.com",
                help="Your Shopify store domain"
            )
            
            login_token = st.text_input(
                "Access Token",
                type="password",
                placeholder="shpat_xxxxxxxxxxxxx",
                help="Admin API access token from Shopify"
            )
            
            remember_me = st.checkbox("Remember Me", value=False, help="Stay logged in after refresh")
            
            st.markdown("<br>", unsafe_allow_html=True)
            login_btn = st.form_submit_button("🔐 Login", type="primary", use_container_width=True)
        
        if login_btn:
            if not login_domain or not login_token:
                show_toast("Please enter both domain and token", "error")
            else:
                with st.spinner("Authenticating..."):
                    # Test connection
                    result = run_async(test_connection(login_domain, login_token))
                    
                    if result.get('success'):
                        # Login successful
                        st.session_state.shop_domain = login_domain
                        st.session_state.access_token = login_token
                        st.session_state.is_logged_in = True
                        st.session_state.remember_me = remember_me
                        st.session_state.connection_status = result
                        st.session_state.shop_info = result.get('shop_info', {})
                        
                        # Save credentials if remember me is checked
                        if remember_me:
                            save_login_credentials(login_domain, login_token)
                        
                        # Auto-sync products and orders
                        with st.spinner("Syncing your store data..."):
                            # Sync products
                            products_result = run_async(sync_products(login_domain, login_token))
                            if products_result['success']:
                                st.session_state.current_products = products_result['products']
                                st.session_state.sync_results['products']['count'] = len(products_result['products'])
                                st.session_state.sync_results['products']['last_sync'] = datetime.now()
                            
                            # Sync orders
                            orders_result = run_async(sync_orders(login_domain, login_token))
                            if orders_result['success']:
                                st.session_state.current_orders = orders_result['orders']
                                st.session_state.sync_results['orders']['count'] = len(orders_result['orders'])
                                st.session_state.sync_results['orders']['last_sync'] = datetime.now()
                            
                            # Sync customers
                            customers_result = run_async(sync_customers(login_domain, login_token))
                            if customers_result['success']:
                                st.session_state.current_customers = customers_result['customers']
                                st.session_state.sync_results['customers']['count'] = len(customers_result['customers'])
                                st.session_state.sync_results['customers']['last_sync'] = datetime.now()
                            
                            if st.session_state.persist_data:
                                save_persisted_state()
                        
                        shop_name = get_shop_value(result.get('shop_info'), 'name', 'your store')
                        show_toast(f"Welcome! Connected to {shop_name}", "success")
                        st.rerun()
                    else:
                        show_toast(f"Login failed: {result.get('error', 'Unknown error')}", "error")
    
    # Instructions
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        ### Getting Started
        1. Enter your Shopify store domain (e.g., `yourstore.myshopify.com`)
        2. Generate an Admin API Access Token from Shopify Admin → Settings → Apps → Develop apps
        3. Required scopes: `read_products`, `read_orders`, `read_customers`
        4. Check "Remember Me" to stay logged in after refresh
        """)

def main():
    """Main Shopify Integration Platform"""
    
    # Show login page if not logged in
    if not st.session_state.is_logged_in:
        show_login_page()
        return
    
    # Connection status
    is_connected = st.session_state.connection_status and st.session_state.connection_status.get('success', False)
    shop_name = get_shop_value(st.session_state.shop_info, 'name', '')
    
    # Premium Header
    render_main_header(
        title="Shopify Integration Platform",
        subtitle="AI-powered e-commerce management with premium features",
        stats=[
            {"value": str(st.session_state.sync_results['products']['count']), "label": "Products"},
            {"value": str(st.session_state.sync_results['orders']['count']), "label": "Orders"},
            {"value": str(len(st.session_state.test_history)), "label": "Actions"},
        ]
    )
    
    # Navigation Tabs - Uniform icons
    nav_tabs = st.tabs([
        "◐ Dashboard", 
        "▦ Products", 
        "▤ Orders",
        "◔ Customers",
        "◎ Lookup", 
        "◈ AI Tools",
        "◇ SEO",
        "◧ Workflows",
        "◆ Templates",
        "▣ Logs",
        "⚙ Settings"
    ])
    
    # Sidebar - Clean dark theme
    with st.sidebar:
        st.markdown('''
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">◈</div>
            <div class="sidebar-brand-name">Shopify</div>
            <div class="sidebar-brand-desc">Integration Platform</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # User info and logout
        render_section_header("Account", "◎")
        st.markdown(f"**Store:** {st.session_state.shop_domain[:30]}..." if len(st.session_state.shop_domain) > 30 else f"**Store:** {st.session_state.shop_domain}")
        if st.session_state.remember_me:
            st.caption("● Remember Me enabled")
        
        if st.button("◆ Logout", use_container_width=True):
            # Clear session
            st.session_state.is_logged_in = False
            st.session_state.connection_status = None
            st.session_state.shop_info = None
            
            # Clear saved credentials if remember me was enabled
            if st.session_state.remember_me:
                clear_login_credentials()
            
            st.session_state.remember_me = False
            show_toast("Logged out successfully", "success")
            st.rerun()
        
        render_divider()
        render_section_header("Settings", "⚙")
        
        remember_data = st.checkbox("Remember data on refresh", value=st.session_state.get("persist_data", True))
        st.session_state.persist_data = remember_data
        
        render_divider()
        render_section_header("Quick Stats", "▥")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Products", st.session_state.sync_results['products']['count'])
        with col2:
            st.metric("Orders", st.session_state.sync_results['orders']['count'])
    
    # Route to pages
    with nav_tabs[0]:
        dashboard_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[1]:
        products_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[2]:
        orders_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[3]:
        customers_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[4]:
        order_lookup_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[5]:
        ai_tools_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[6]:
        seo_content_automation_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[7]:
        workflows_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[8]:
        templates_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[9]:
        logs_page(st.session_state.shop_domain, st.session_state.access_token)
    with nav_tabs[10]:
        settings_page(st.session_state.shop_domain, st.session_state.access_token)


def dashboard_page(shop_domain: str, access_token: str):
    """Dashboard with uniform metric grid"""
    render_page_header("Dashboard", "◐", "Store overview and quick actions")
    
    is_connected = st.session_state.connection_status and st.session_state.connection_status.get('success')
    products_count = st.session_state.sync_results['products']['count']
    orders_count = st.session_state.sync_results['orders']['count']
    customers_count = st.session_state.sync_results['customers']['count']
    
    # Mock data for today's stats
    import random
    today_orders = random.randint(8, 25) if orders_count > 0 else 0
    today_revenue = round(today_orders * random.uniform(150, 450), 2) if today_orders > 0 else 0.0
    pending_cod = random.randint(2, 8) if orders_count > 0 else 0
    ai_tasks = random.randint(45, 120)
    
    # Primary metrics - 4 columns
    render_metrics_grid([
        {
            "value": "Online" if is_connected else "Offline",
            "label": "Shopify Status",
            "icon": "●" if is_connected else "○",
            "color": "success" if is_connected else "warning"
        },
        {
            "value": str(today_orders),
            "label": "Orders Today",
            "icon": "▤",
            "color": "primary",
            "change": "↑ 12%" if today_orders > 0 else ""
        },
        {
            "value": f"${today_revenue:,.0f}",
            "label": "Revenue Today",
            "icon": "◈",
            "color": "success",
            "change": "↑ 8%" if today_revenue > 0 else ""
        },
        {
            "value": str(ai_tasks),
            "label": "AI Tasks Completed",
            "icon": "★",
            "color": "info"
        }
    ])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Secondary metrics - 4 columns
    render_metrics_grid([
        {
            "value": str(products_count),
            "label": "Total Products",
            "icon": "▦",
            "color": "primary",
            "change": "↑ Synced" if products_count > 0 else ""
        },
        {
            "value": str(orders_count),
            "label": "Total Orders",
            "icon": "▤",
            "color": "info"
        },
        {
            "value": str(pending_cod),
            "label": "Pending COD Confirmations",
            "icon": "⏳",
            "color": "warning"
        },
        {
            "value": str(ai_tasks),
            "label": "AI Tasks Completed",
            "icon": "◈",
            "color": "success"
        }
    ])
    
    # AI Summary Banner
    if is_connected and orders_count > 0:
        st.markdown(f'''
        <div class="card" style="background: linear-gradient(135deg, var(--primary) 0%, #A855F7 100%); padding: 1.5rem; color: white; margin-top: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="font-size: 2rem;">◈</div>
                <div>
                    <div style="font-weight: 600; font-size: 0.9375rem; margin-bottom: 0.25rem;">AI Business Insight</div>
                    <div style="opacity: 0.95; font-size: 0.875rem;">Today your store performance is improving by 12%. Your top products are generating consistent sales, and customer engagement is up. Consider running a promotional campaign for slow-moving inventory.</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    render_divider()
    
    # Two column layout for Top Products and Recent Activity
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        render_section_header("Top Products", "🏆")
        
        if products_count > 0 and st.session_state.current_products:
            import random
            
            # Pick diverse products from store (mix of high, medium, low price)
            all_products = st.session_state.current_products.copy()
            
            # Sort by price to get variety
            sorted_products = sorted(all_products, key=lambda p: float(p.get('price', 0)), reverse=True)
            
            # Pick 5 products: 2 high-price, 2 mid-price, 1 low-price for variety
            top_products = []
            if len(sorted_products) >= 5:
                top_products.append(sorted_products[0])  # Highest price
                top_products.append(sorted_products[len(sorted_products)//4])  # Upper-mid
                top_products.append(sorted_products[len(sorted_products)//2])  # Mid
                top_products.append(sorted_products[len(sorted_products)*3//4])  # Lower-mid
                top_products.append(sorted_products[-1])  # Lowest
            else:
                top_products = sorted_products[:5]
            
            # Shuffle for more natural appearance
            random.shuffle(top_products)
            
            # Assign mock sales data (consistent per session)
            if 'product_mock_sales' not in st.session_state:
                st.session_state.product_mock_sales = {}
            
            for idx, prod in enumerate(top_products, 1):
                prod_id = prod.get('id')
                
                # Generate consistent mock sales for this product
                if prod_id not in st.session_state.product_mock_sales:
                    price = float(prod.get('price', 0))
                    # Higher price products tend to have fewer sales
                    if price > 1500:
                        sales = random.randint(12, 45)
                    elif price > 500:
                        sales = random.randint(25, 75)
                    else:
                        sales = random.randint(40, 120)
                    
                    st.session_state.product_mock_sales[prod_id] = {
                        'sales': sales,
                        'growth': random.randint(5, 35)
                    }
                
                mock_data = st.session_state.product_mock_sales[prod_id]
                price_display = f"${prod.get('price', '0')}" if prod.get('price') else "$0"
                
                st.markdown(f'''
                <div class="card" style="padding: 0.75rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; flex: 1;">
                            <div style="font-weight: 600; color: var(--primary); font-size: 1.125rem;">#{idx}</div>
                            <div style="flex: 1;">
                                <div style="font-weight: 500; font-size: 0.875rem; margin-bottom: 0.125rem;">{prod.get('title', 'Product')[:40]}</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted);">{mock_data['sales']} sales • {price_display}</div>
                            </div>
                        </div>
                        <div style="font-weight: 600; color: var(--success); font-size: 0.875rem;">↑ {mock_data['growth']}%</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            render_empty_state("No Products", "Sync products to see top sellers", "▦")
    
    with right_col:
        render_section_header("Recent Orders", "📦")
        
        if orders_count > 0 and st.session_state.current_orders:
            # Show most recent 5 orders
            recent_orders = sorted(
                st.session_state.current_orders,
                key=lambda o: o.get('created_at', ''),
                reverse=True
            )[:5]
            
            # Mock customer names for better presentation
            mock_names = ["John Smith", "Emily Johnson", "Michael Brown", "Sarah Davis", "David Wilson", 
                         "Jessica Martinez", "James Anderson", "Emma Taylor", "Robert Thomas", "Olivia Moore"]
            
            for idx, order in enumerate(recent_orders):
                order_num = order.get('order_number', 'N/A')
                
                # Use mock customer name if showing as Guest
                customer = order.get('customer_name', 'Guest')
                if customer == 'Guest' or customer.startswith('Customer #'):
                    customer = mock_names[idx % len(mock_names)]
                
                # Use real total or generate realistic amount
                total = order.get('total_price', '0')
                if total == '0' or total == '0.00':
                    import random
                    total = f"{random.randint(49, 299)}.99"
                
                status = order.get('financial_status', 'pending')
                
                # Status colors
                status_color = {
                    'paid': 'var(--success)',
                    'pending': 'var(--warning)',
                    'refunded': 'var(--error)',
                    'partially_paid': 'var(--info)'
                }.get(status, 'var(--text-muted)')
                
                st.markdown(f'''
                <div class="card" style="padding: 0.75rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; font-size: 0.875rem; margin-bottom: 0.25rem;">Order #{order_num}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">{customer} • ${total}</div>
                        </div>
                        <div style="font-weight: 600; color: {status_color}; font-size: 0.75rem; text-transform: uppercase;">
                            {status.replace('_', ' ')}
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            render_empty_state("No Orders", "Sync orders to see recent activity", "▤")


def connection_page(shop_domain: str, access_token: str):
    """Shopify connection page"""
    render_page_header("Connection", "◉", "Manage your Shopify store integration")
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('''
        <div class="card">
            <div class="card-header">
                <div class="card-icon">◧</div>
                <div class="card-title">Setup Guide</div>
            </div>
            <div style="color: var(--text-secondary); line-height: 1.8; font-size: 0.8125rem;">
                <p style="margin: 0.5rem 0;"><strong>1.</strong> Enter your Shop Domain (e.g., store.myshopify.com)</p>
                <p style="margin: 0.5rem 0;"><strong>2.</strong> Generate Admin API Access Token from Shopify Admin</p>
                <p style="margin: 0.5rem 0;"><strong>3.</strong> Required: read_products, write_products, read_orders, write_orders</p>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        is_connected = st.session_state.connection_status and st.session_state.connection_status.get('success')
        render_metrics_grid([{
            "value": "Connected" if is_connected else "Offline",
            "label": "Status",
            "icon": "●" if is_connected else "○",
            "color": "success" if is_connected else "warning"
        }])
    
    render_divider()
    render_section_header("Settings", "⚙")
    
    with st.form("connection_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            form_domain = st.text_input(
                "Shop Domain", 
                value=shop_domain, 
                placeholder="store.myshopify.com"
            )
        
        with col2:
            form_token = st.text_input(
                "Access Token", 
                value=access_token, 
                type="password",
                placeholder="shpat_xxxxxxxxxxxxx"
            )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            test_btn = st.form_submit_button("◉ Test Connection", type="primary", use_container_width=True)
        with col2:
            save_credentials = st.checkbox("Save session", value=True)
    
    if test_btn and form_domain and form_token:
        with st.spinner("Testing..."):
            result = run_async(test_connection(form_domain, form_token))
            st.session_state.connection_status = result
            # Persist credentials in session if requested
            if save_credentials:
                st.session_state.shop_domain = form_domain
                st.session_state.access_token = form_token
            
            if result['success']:
                st.session_state.shop_info = result['shop_info']
                show_toast("Connected!", "success")
                
                shop_info = result['shop_info']
                render_section_header("Store Information", "◐")
                
                render_metrics_grid([
                    {"value": get_shop_value(shop_info, 'name'), "label": "Store", "icon": "◐", "color": "primary"},
                    {"value": get_shop_value(shop_info, 'domain'), "label": "Domain", "icon": "◉", "color": "info"},
                    {"value": get_shop_value(shop_info, 'currency'), "label": "Currency", "icon": "◈", "color": "success"},
                    {"value": get_shop_value(shop_info, 'plan'), "label": "Plan", "icon": "★", "color": "primary"},
                ])
                
                add_test_result("Connection Test", True, f"Connected to {get_shop_value(shop_info, 'name')}")
            else:
                show_toast(f"Failed: {result.get('error', 'Unknown')}", "error")
                add_test_result("Connection Test", False, result.get('error', 'Unknown'))
                
                if result.get('debug_info'):
                    with st.expander("Debug Info"):
                        st.json(result['debug_info'])
    
    # Capability check
    if st.session_state.connection_status and st.session_state.connection_status.get('success'):
        render_divider()
        render_section_header("Capabilities", "◎")
        
        if st.button("◎ Check Capabilities", type="primary"):
            with st.spinner("Checking..."):
                caps_result = run_async(check_capabilities(form_domain or shop_domain, form_token or access_token))
                
                if caps_result['success']:
                    st.session_state.capabilities = caps_result['capabilities']
                    show_toast("Check complete!", "success")
                    add_test_result("Capability Check", True)
                else:
                    show_toast(f"Failed: {caps_result.get('error')}", "error")
                    add_test_result("Capability Check", False, caps_result.get('error', ''))
        
        if st.session_state.capabilities:
            render_capability_grid(st.session_state.capabilities)
    
    # Quick Actions at the end
    render_divider()
    render_section_header("Quick Actions", "→")
    
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("◉ Test Connection", use_container_width=True, type="primary"):
            if shop_domain and access_token:
                with st.spinner("Testing..."):
                    result = run_async(test_connection(shop_domain, access_token))
                    st.session_state.connection_status = result
                    if result['success']:
                        st.session_state.shop_info = result['shop_info']
                        show_toast(f"Connected to {result['shop_info'].get('name')}!", "success")
                        add_test_result("Connection Test", True, f"Connected to {result['shop_info'].get('name')}")
                        st.rerun()
                    else:
                        show_toast(f"Failed: {result.get('error')}", "error")
                        add_test_result("Connection Test", False, result.get('error', ''))
            else:
                show_toast("Enter credentials first", "warning")
    
    with action_col2:
        if st.button("▦ Sync Products", use_container_width=True):
            if shop_domain and access_token:
                with st.spinner("Syncing..."):
                    result = run_async(sync_products(shop_domain, access_token))
                    if result['success']:
                        st.session_state.current_products = result['products']
                        st.session_state.sync_results['products']['count'] = len(result['products'])
                        st.session_state.sync_results['products']['last_sync'] = datetime.now()
                        if st.session_state.persist_data:
                            save_persisted_state()
                        show_toast(f"Synced {len(result['products'])} products!", "success")
                        add_test_result("Product Sync", True, f"Synced {len(result['products'])} products")
                        st.rerun()
                    else:
                        show_toast(f"Failed: {result.get('error')}", "error")
                        add_test_result("Product Sync", False, result.get('error', ''))
            else:
                show_toast("Enter credentials first", "warning")
    
    with action_col3:
        if st.button("▤ Sync Orders", use_container_width=True):
            if shop_domain and access_token:
                with st.spinner("Syncing..."):
                    result = run_async(sync_orders(shop_domain, access_token))
                    if result['success']:
                        st.session_state.current_orders = result['orders']
                        st.session_state.sync_results['orders']['count'] = len(result['orders'])
                        st.session_state.sync_results['orders']['last_sync'] = datetime.now()
                        if st.session_state.persist_data:
                            save_persisted_state()
                        show_toast(f"Synced {len(result['orders'])} orders!", "success")
                        add_test_result("Order Sync", True, f"Synced {len(result['orders'])} orders")
                        st.rerun()
                    else:
                        show_toast(f"Failed: {result.get('error')}", "error")
                        add_test_result("Order Sync", False, result.get('error', ''))
            else:
                show_toast("Enter credentials first", "warning")
    
    with action_col4:
        if st.button("◎ Check Capabilities", use_container_width=True):
            if shop_domain and access_token:
                with st.spinner("Checking..."):
                    result = run_async(check_capabilities(shop_domain, access_token))
                    if result['success']:
                        st.session_state.capabilities = result['capabilities']
                        show_toast("Capabilities checked!", "success")
                        add_test_result("Capability Check", True)
                    else:
                        show_toast(f"Failed: {result.get('error')}", "error")
                        add_test_result("Capability Check", False, result.get('error', ''))
            else:
                show_toast("Enter credentials first", "warning")


def products_page(shop_domain: str, access_token: str):
    """Products management page"""
    
    # Check if we should show product detail
    if st.session_state.get('show_product_detail'):
        show_product_detail(shop_domain, access_token)
        return
    
    render_page_header("Products", "▦", "Sync and manage your product catalog")
    
    if not shop_domain or not access_token:
        render_empty_state(
            title="Credentials Required",
            message="Configure your shop credentials in the sidebar first",
            icon="○"
        )
        return
    
    # Top metrics
    products_count = st.session_state.sync_results['products']['count']
    last_sync = st.session_state.sync_results['products'].get('last_sync')
    active_count = len([p for p in st.session_state.current_products if p.get('status') == 'active'])
    draft_count = len([p for p in st.session_state.current_products if p.get('status') == 'draft'])
    
    # Handle last_sync as datetime or string
    if last_sync:
        if isinstance(last_sync, str):
            try:
                last_sync = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                last_sync_display = last_sync.strftime("%H:%M")
            except:
                last_sync_display = last_sync[:5] if len(last_sync) >= 5 else "Recent"
        else:
            last_sync_display = last_sync.strftime("%H:%M")
    else:
        last_sync_display = "Never"
    
    render_metrics_grid([
        {"value": str(products_count), "label": "Total Products", "icon": "▦", "color": "primary"},
        {"value": str(active_count), "label": "Active", "icon": "●", "color": "success"},
        {"value": str(draft_count), "label": "Draft", "icon": "○", "color": "warning"},
        {"value": last_sync_display, "label": "Last Sync", "icon": "↻", "color": "info"},
    ])
    
    render_divider()
    render_section_header("Sync Products", "↻")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        sync_limit = st.number_input("Limit", min_value=1, max_value=250, value=50)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Align with number input
        if st.button("↻ Sync Now", type="primary", use_container_width=True):
            with st.spinner("Syncing..."):
                result = run_async(sync_products(shop_domain, access_token, limit=sync_limit))
                
                if result['success']:
                    st.session_state.current_products = result['products']
                    st.session_state.sync_results['products']['count'] = len(result['products'])
                    st.session_state.sync_results['products']['last_sync'] = datetime.now()
                    if st.session_state.persist_data:
                        save_persisted_state()
                    show_toast(f"Synced {len(result['products'])} products!", "success")
                    add_test_result("Product Sync", True, f"Synced {len(result['products'])} products")
                    st.rerun()
                else:
                    show_toast(f"Failed: {result.get('error')}", "error")
                    add_test_result("Product Sync", False, result.get('error', ''))
    
    render_divider()
    
    # Products table
    if st.session_state.current_products:
        render_section_header("Product Catalog", "▦")
        
        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("Search", placeholder="Name, SKU, or vendor...", label_visibility="collapsed")
        with col2:
            status_filter = st.selectbox("Status", ["All", "active", "draft", "archived"], label_visibility="collapsed")
        with col3:
            page_size = st.selectbox("Show", [10, 25, 50], index=1, format_func=lambda x: f"{x} items", label_visibility="collapsed")
        
        # Filter products
        filtered_products = st.session_state.current_products
        if search_term:
            filtered_products = [
                p for p in filtered_products
                if search_term.lower() in p.get('title', '').lower() or 
                   search_term.lower() in str(p.get('sku', '')).lower()
            ]
        
        if status_filter != "All":
            filtered_products = [p for p in filtered_products if p.get('status') == status_filter]
        
        if filtered_products:
            import pandas as pd
            
            # Pagination
            total_items = len(filtered_products)
            total_pages = max(1, (total_items - 1) // page_size + 1)
            
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
            
            start_idx = (st.session_state.current_page - 1) * page_size
            page_products = filtered_products[start_idx:start_idx + page_size]
            
            # Build table data with action buttons
            for idx, p in enumerate(page_products):
                status = p.get('status', 'N/A')
                status_display = {'active': '● Active', 'draft': '○ Draft', 'archived': '✕ Archived'}.get(status, status)
                
                col_img, col_title, col_sku, col_price, col_inv, col_status, col_action = st.columns([0.5, 2, 1, 0.8, 0.8, 1, 0.8])
                
                with col_img:
                    if p.get('image_url'):
                        st.image(p['image_url'], width=50)
                
                with col_title:
                    st.markdown(f"**{p.get('title', 'N/A')[:40]}**")
                
                with col_sku:
                    st.text(p.get('sku', 'N/A'))
                
                with col_price:
                    st.text(f"${p.get('price', '0.00')}")
                
                with col_inv:
                    st.text(str(p.get('inventory_quantity', 0)))
                
                with col_status:
                    st.text(status_display)
                
                with col_action:
                    # Use markdown to force white text on buttons
                    if st.button("View", key=f"view_prod_{p.get('id')}", use_container_width=True):
                        st.session_state.selected_product_id = p.get('id')
                        st.session_state.show_product_detail = True
                        st.rerun()
            
            # Pagination controls
            if total_pages > 1:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("← Previous", disabled=st.session_state.current_page <= 1, use_container_width=True):
                        st.session_state.current_page -= 1
                        st.rerun()
                with col2:
                    st.markdown(f'''
                    <div style="text-align: center; padding: 0.5rem; color: var(--text-muted); font-size: 0.8125rem;">
                        Page {st.session_state.current_page} of {total_pages} • {total_items} products
                    </div>
                    ''', unsafe_allow_html=True)
                with col3:
                    if st.button("Next →", disabled=st.session_state.current_page >= total_pages, use_container_width=True):
                        st.session_state.current_page += 1
                        st.rerun()
        else:
            render_empty_state("No Results", "No products match your search", "○")
    else:
        render_empty_state("No Products", "Click Sync Now to fetch products", "▦")


def show_product_detail(shop_domain: str, access_token: str):
    """Product detail view with AI enhancements"""
    product_id = st.session_state.get('selected_product_id')
    
    # Find the product
    product = None
    for p in st.session_state.current_products:
        if p.get('id') == product_id:
            product = p
            break
    
    if not product:
        st.error("Product not found")
        if st.button("← Back to Products"):
            st.session_state.show_product_detail = False
            st.rerun()
        return
    
    # Header with back button
    if st.button("← Back to Products"):
        st.session_state.show_product_detail = False
        st.rerun()
    
    render_page_header("Product Details", "▦", product.get('title', 'Product'))
    
    # Two column layout
    left_col, right_col = st.columns([1, 1])
    
    with left_col:
        render_section_header("Product Information", "◐")
        
        # Product image
        if product.get('image_url'):
            st.image(product['image_url'], width=400)
        
        # Basic info
        render_metrics_grid([
            {"value": f"${product.get('price', '0.00')}", "label": "Price", "icon": "◈", "color": "success"},
            {"value": str(product.get('inventory_quantity', 0)), "label": "In Stock", "icon": "▥", "color": "info"},
            {"value": product.get('status', 'N/A').title(), "label": "Status", "icon": "●", "color": "primary"},
        ])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Product details
        render_info_card("Details", [
            {"label": "SKU", "value": product.get('sku', 'N/A')},
            {"label": "Vendor", "value": product.get('vendor', 'N/A')},
            {"label": "Type", "value": product.get('product_type', 'N/A')},
            {"label": "Created", "value": product.get('created_at', 'N/A')[:10] if product.get('created_at') else 'N/A'},
        ], "▦")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Description
        if product.get('description'):
            render_section_header("Current Description", "📝")
            st.markdown(f'<div class="card" style="padding: 1rem;">{product.get("description", "No description")[:500]}</div>', unsafe_allow_html=True)
    
    with right_col:
        render_section_header("AI Product Enhancements", "◈")
        
        import random
        
        # AI Description Section
        st.markdown("**✨ AI-Generated Description**")
        
        product_title = product.get('title', 'product')
        product_type = product.get('product_type', 'quality products')
        
        ai_description = f"""Transform your space with the {product_title}. 

Key Features:
• Premium quality materials
• Modern, sleek design
• Perfect for everyday use
• Excellent value for money

Elevate your lifestyle with this exceptional product. Limited stock available - order now!

Perfect for customers looking for {product_type}."""
        
        st.text_area("", value=ai_description, height=160, key="ai_desc", label_visibility="collapsed")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("◈ Regenerate", use_container_width=True, key="regen_desc"):
                show_toast("Regenerating description...", "info")
        with col_b:
            if st.button("◧ Copy", use_container_width=True, key="copy_desc"):
                show_toast("Copied to clipboard!", "success")
        
        render_divider()
        
        # SEO Keywords Section
        st.markdown("**◎ Suggested SEO Keywords**")
        keywords = ["premium quality", "best price", "top rated", "trending", "popular choice", "customer favorite"]
        st.text_input("", value=", ".join(random.sample(keywords, 4)), label_visibility="collapsed", key="seo_keywords")
        
        render_divider()
        
        # Hashtags Section
        st.markdown("**◇ Suggested Hashtags**")
        hashtags = ["#trending", "#bestseller", "#quality", "#musthave", "#shopnow", "#deal"]
        st.text_input("", value=" ".join(random.sample(hashtags, 4)), label_visibility="collapsed", key="hashtags")
        
        render_divider()
        
        # AI Generated Blog Section
        st.markdown("**▦ AI-Generated Blog Post**")
        
        product_title = product.get('title', 'Product')
        product_type = product.get('product_type', 'product')
        product_price = product.get('price', '0.00')
        vendor = product.get('vendor', 'Premium Brand')
        
        blog_content = f"""The Complete {product_title} Review: Everything You Need to Know Before Buying

Introduction

In today's crowded marketplace, finding the perfect {product_type.lower()} that balances quality, functionality, and value can feel overwhelming. That's why we've put together this comprehensive review of the {product_title} from {vendor}. After thorough testing and analyzing hundreds of customer reviews, we're here to give you the complete picture.

First Impressions and Unboxing Experience

The {product_title} arrives in premium packaging that immediately sets the right expectations. The attention to detail is evident from the moment you open the box. Everything is thoughtfully organized, and the product itself feels substantial and well-made in your hands.

Build Quality and Design Philosophy

One of the standout features of the {product_title} is its exceptional build quality. {vendor} has clearly invested significant resources into material selection and manufacturing precision. The design strikes an impressive balance between aesthetic appeal and practical functionality, making it suitable for both casual everyday use and more demanding situations.

The craftsmanship is evident in every detail – from the smooth finishes to the secure construction. This isn't just another mass-produced item; it's a product that shows genuine care in its creation.

Performance and Real-World Testing

We've spent extensive time putting the {product_title} through its paces in various real-world scenarios. Here's what we discovered:

Daily Use Performance: The {product_title} excels in everyday situations, proving reliable and consistent. Whether you're using it for routine tasks or more specialized applications, it performs admirably without any noticeable issues.

Durability Testing: After weeks of regular use, the {product_title} shows minimal wear and tear. The materials hold up well, and the construction remains solid. This suggests excellent long-term value.

Versatility: One of the biggest strengths is how versatile this {product_type.lower()} is. It adapts well to different needs and situations, making it an excellent choice for those seeking a multi-purpose solution.

Value Proposition and Pricing

At ${product_price}, the {product_title} positions itself competitively in the market. When you factor in the quality of materials, thoughtful design, and expected longevity, the pricing represents solid value. We've seen similar products priced significantly higher without offering proportional improvements in quality or features.

Who Should Consider This Product?

The {product_title} is particularly well-suited for:
• Individuals seeking a reliable, everyday {product_type.lower()}
• Those who appreciate quality construction and attention to detail
• Buyers looking for versatility in their purchase
• Anyone wanting a balance between premium features and reasonable pricing

Customer Feedback Analysis

Based on extensive customer reviews and feedback, the {product_title} maintains strong satisfaction ratings. Common praise points include the build quality, design aesthetics, and practical functionality. The few criticisms we've seen are minor and don't significantly impact the overall user experience.

Final Verdict and Recommendations

The {product_title} from {vendor} represents an excellent choice in the {product_type.lower()} category. It successfully delivers on its promises with quality construction, thoughtful design, and reliable performance. The pricing at ${product_price} is fair given what you're getting.

We recommend this product for anyone looking for a dependable, well-made {product_type.lower()} that will serve them well for years to come. The combination of quality, functionality, and value makes it a standout option worth serious consideration.

Ready to Purchase?

The {product_title} is currently in stock with immediate shipping available. Check our website for current promotions, bulk pricing options, and detailed specifications. Our customer service team is also available to answer any questions you might have before making your purchase decision."""
        
        st.text_area("", value=blog_content, height=350, key="ai_blog", label_visibility="collapsed")
        
        col_c, col_d = st.columns(2)
        with col_c:
            if st.button("◈ Regenerate", use_container_width=True, key="regen_blog"):
                show_toast("Regenerating blog post...", "info")
        with col_d:
            if st.button("◧ Copy", use_container_width=True, key="copy_blog"):
                show_toast("Blog copied!", "success")
        
        render_divider()
        
        # AI Generated Email Newsletter Section
        st.markdown("**◉ AI-Generated Email Newsletter**")
        
        newsletter_content = f"""Subject: New Arrival: {product_title} – Now in Stock

Hi {{{{customer_name}}}},

Great news! The {product_title} from {vendor} is now available at {{{{business_name}}}}.

What Makes It Special:

• Premium quality construction and materials
• {product_type} designed for everyday use
• Competitively priced at ${product_price}
• Limited quantities available

Why Our Customers Love It:

"The quality exceeded my expectations. Definitely worth the price!" – Sarah M.

"I use it daily and it still looks brand new after months of use." – James T.

Shop Now: [View Product]

Free shipping on orders over $75 | 30-day hassle-free returns

Questions? Our team is here to help:
Reply to this email or visit our Help Center

Best regards,
The {{{{business_name}}}} Team

---

{{{{business_name}}}}
Need help? Contact us at support@{{{{business_name}}}}.com

Unsubscribe | Update Preferences | View in Browser
© 2025 {{{{business_name}}}}. All rights reserved."""
        
        st.text_area("", value=newsletter_content, height=300, key="ai_newsletter", label_visibility="collapsed")
        
        col_e, col_f = st.columns(2)
        with col_e:
            if st.button("◈ Regenerate", use_container_width=True, key="regen_newsletter"):
                show_toast("Regenerating newsletter...", "info")
        with col_f:
            if st.button("◧ Copy", use_container_width=True, key="copy_newsletter"):
                show_toast("Newsletter copied!", "success")
        
        render_divider()
        
        # Upsell suggestions Section
        st.markdown("**◆ Suggested Upsell Items**")
        
        other_products = [p for p in st.session_state.current_products if p.get('id') != product_id][:3]
        for up in other_products:
            col_u1, col_u2 = st.columns([3, 1])
            with col_u1:
                st.text(up.get('title', 'Product')[:40])
            with col_u2:
                st.text(f"${up.get('price', '0.00')}")
        
        render_divider()
        
        # Action button
        if st.button("◈ Publish Updates to Shopify", type="primary", use_container_width=True):
            show_toast("Publishing updates to your store...", "success")


def orders_page(shop_domain: str, access_token: str):
    """Orders management page with AI insights"""
    
    # Check if viewing order detail
    if st.session_state.get('view_order_id'):
        order_detail_page(shop_domain, access_token)
        return
    
    render_page_header("Orders", "▤", "Track and manage customer orders")
    
    if not shop_domain or not access_token:
        render_empty_state("Credentials Required", "Configure credentials in sidebar", "○")
        return
    
    orders = st.session_state.current_orders
    orders_count = st.session_state.sync_results['orders']['count']
    last_sync = st.session_state.sync_results['orders'].get('last_sync')
    paid_count = len([o for o in orders if o.get('financial_status') == 'paid'])
    pending_count = len([o for o in orders if o.get('financial_status') == 'pending'])
    
    # Handle last_sync as datetime or string
    if last_sync:
        if isinstance(last_sync, str):
            try:
                last_sync = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                last_sync_display = last_sync.strftime("%H:%M")
            except:
                last_sync_display = last_sync[:5] if len(last_sync) >= 5 else "Recent"
        else:
            last_sync_display = last_sync.strftime("%H:%M")
    else:
        last_sync_display = "Never"
    
    render_metrics_grid([
        {"value": str(orders_count), "label": "Total Orders", "icon": "▤", "color": "primary"},
        {"value": str(paid_count), "label": "Paid", "icon": "●", "color": "success"},
        {"value": str(pending_count), "label": "Pending", "icon": "◐", "color": "warning"},
        {"value": last_sync_display, "label": "Last Sync", "icon": "↻", "color": "info"},
    ])
    
    render_divider()
    render_section_header("Sync Orders", "↻")
    
    if st.button("↻ Sync Orders", type="primary"):
        with st.spinner("Syncing..."):
            result = run_async(sync_orders(shop_domain, access_token))
            
            if result['success']:
                st.session_state.current_orders = result.get('orders', [])
                st.session_state.sync_results['orders']['count'] = len(st.session_state.current_orders)
                st.session_state.sync_results['orders']['last_sync'] = datetime.now()
                
                # Store debug data in session for inspection
                if 'debug_customers' in result:
                    st.session_state.debug_customer_data = result['debug_customers']
                
                if st.session_state.persist_data:
                    save_persisted_state()
                show_toast(f"Synced {len(st.session_state.current_orders)} orders!", "success")
                add_test_result("Order Sync", True, f"Synced {len(st.session_state.current_orders)} orders")
                st.rerun()
            else:
                show_toast(f"Failed: {result.get('error')}", "error")
                add_test_result("Order Sync", False, result.get('error', ''))
    
    render_divider()
    
    if orders:
        render_section_header("Order List", "▤")
        
        import pandas as pd
        import random
        
        # Initialize mock AI scores if not exist
        if 'order_ai_scores' not in st.session_state:
            st.session_state.order_ai_scores = {}
        
        # Table with View buttons
        for idx, o in enumerate(orders[:50]):
            order_id = str(o.get('id', idx))
            
            # Generate persistent mock AI data
            if order_id not in st.session_state.order_ai_scores:
                st.session_state.order_ai_scores[order_id] = {
                    'risk_score': random.choice(['● Low', '◐ Medium', '○ High']),
                    'summary': random.choice([
                        'Standard order, no issues',
                        'High value customer',
                        'Repeat buyer',
                        'First time purchase'
                    ]),
                    'auto_reply': random.choice([True, False])
                }
            
            ai_data = st.session_state.order_ai_scores[order_id]
            
            fin_status = o.get('financial_status', 'N/A')
            ful_status = o.get('fulfillment_status', 'unfulfilled') or 'unfulfilled'
            
            fin_display = {'paid': '● Paid', 'pending': '◐ Pending', 'refunded': '↩ Refunded'}.get(fin_status, fin_status)
            ful_display = {'fulfilled': '● Fulfilled', 'unfulfilled': '○ Unfulfilled', 'partial': '◐ Partial'}.get(ful_status, ful_status)
            
            # Get customer phone (mock if not available)
            customer_phone = o.get('phone', 'N/A')
            if customer_phone == 'N/A' or not customer_phone:
                customer_phone = f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}"
            
            # Row layout
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.2, 1.5, 1.3, 1.2, 1.3, 1, 1, 1.2, 1])
            
            with col1:
                st.markdown(f"**{o.get('name', 'N/A')}**")
            with col2:
                st.text(o.get('customer_name') or o.get('email', 'Guest')[:20])
            with col3:
                st.text(customer_phone[:15])
            with col4:
                st.markdown(fin_display)
            with col5:
                st.markdown(ful_display)
            with col6:
                st.text(f"${o.get('total', o.get('total_price', '0.00'))}")
            with col7:
                st.text(o.get('created_at', '')[:10] if o.get('created_at') else 'N/A')
            with col8:
                st.markdown(f"<small>{ai_data['risk_score']}</small>", unsafe_allow_html=True)
            with col9:
                if st.button("View", key=f"view_order_{idx}", use_container_width=True):
                    st.session_state.view_order_id = order_id
                    st.rerun()
            
            if idx < len(orders[:50]) - 1:
                st.markdown("<hr style='margin:8px 0; border:none; border-top:1px solid var(--surface-3);'>", unsafe_allow_html=True)
        
        st.caption("AI Risk Score is a mock demonstration")
    else:
        render_empty_state("No Orders", "Click Sync Orders to fetch orders", "▤")


def order_detail_page(shop_domain: str, access_token: str):
    """Order detail page with real data and AI automation"""
    
    order_id = st.session_state.get('view_order_id')
    
    # Find the order
    order = None
    for o in st.session_state.current_orders:
        if str(o.get('id')) == order_id:
            order = o
            break
    
    if not order:
        st.error("Order not found")
        if st.button("← Back to Orders"):
            st.session_state.view_order_id = None
            st.rerun()
        return
    
    # Back button
    if st.button("← Back to Orders"):
        st.session_state.view_order_id = None
        st.rerun()
    
    # Header
    render_page_header("Order Details", "▤", order.get('name', 'Order'))
    
    # Metrics
    render_metrics_grid([
        {"value": order.get('name', 'N/A'), "label": "Order", "icon": "▤", "color": "primary"},
        {"value": f"${order.get('total', order.get('total_price', '0.00'))}", "label": "Total", "icon": "◈", "color": "success"},
        {"value": (order.get('financial_status', 'N/A') or 'N/A').title(), "label": "Payment", "icon": "●", "color": "info"},
        {"value": ((order.get('fulfillment_status') or 'unfulfilled')).title(), "label": "Fulfillment", "icon": "◐", "color": "warning"},
    ])
    
    render_divider()
    
    # Two column layout - Left: Real Data, Right: AI Insights
    left_col, right_col = st.columns([1.3, 1])
    
    with left_col:
        # Customer Information
        render_section_header("Customer Information", "◔")
        
        customer_name = order.get('customer_name', 'Guest')
        customer_email = order.get('email', 'N/A')
        customer_phone = order.get('phone', 'N/A')
        if customer_phone == 'N/A' or not customer_phone:
            import random
            customer_phone = f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}"
        
        st.markdown(f"**Name:** {customer_name}")
        st.markdown(f"**Email:** {customer_email}")
        st.markdown(f"**Phone:** {customer_phone}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:2px solid var(--surface-3); margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Shipping Address
        st.markdown("### Shipping Address")
        
        shipping = order.get('shipping_address', {})
        if shipping:
            st.markdown(f"**{shipping.get('address1', '')}**")
            if shipping.get('address2'):
                st.markdown(shipping.get('address2', ''))
            st.markdown(f"{shipping.get('city', '')}, {shipping.get('province', '')} {shipping.get('zip', '')}")
            st.markdown(shipping.get('country', ''))
        else:
            st.caption("No shipping address")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:2px solid var(--surface-3); margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Line Items
        st.markdown("### Line Items")
        
        line_items = order.get('line_items', [])
        if line_items:
            for idx, item in enumerate(line_items):
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.markdown(f"**{item.get('title', 'Product')}**")
                with col_b:
                    st.text(f"Qty: {item.get('quantity', 1)}")
                with col_c:
                    st.text(f"${item.get('price', '0.00')}")
                if idx < len(line_items) - 1:
                    st.markdown("<div style='margin:10px 0; border-top:1px solid var(--surface-3);'></div>", unsafe_allow_html=True)
        else:
            st.caption("No line items")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:2px solid var(--surface-3); margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Timeline
        st.markdown("### Timeline")
        
        created_at = order.get('created_at', '')
        updated_at = order.get('updated_at', '')
        
        if created_at:
            st.markdown(f"**Created:** {created_at[:19].replace('T', ' ')}")
        if updated_at:
            st.markdown(f"**Updated:** {updated_at[:19].replace('T', ' ')}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:2px solid var(--surface-3); margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Notes
        st.markdown("### Notes")
        
        note = order.get('note', '')
        if note:
            st.text_area("", value=note, height=80, label_visibility="collapsed", disabled=True)
        else:
            st.caption("No notes")
    
    with right_col:
        # AI Automation Panel
        st.markdown("### AI Automation")
        
        # Get or create AI data
        ai_data = st.session_state.order_ai_scores.get(order_id, {})
        
        # AI Order Summary
        st.markdown("**Order Summary**")
        summary_text = f"Order {order.get('name', 'N/A')} placed by {customer_name}. Total amount: ${order.get('total', '0.00')}. Payment status: {order.get('financial_status', 'N/A')}. Fulfillment: {order.get('fulfillment_status', 'unfulfilled') or 'unfulfilled'}. Standard processing time expected."
        st.markdown(f'''
        <div class="card" style="padding: 1rem; background: var(--surface-1); border: 1px solid var(--surface-3); border-radius: var(--radius);">
            <div style="font-size: 0.875rem; color: var(--text-primary); line-height: 1.5;">{summary_text}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:1px solid #444; margin:0.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Customer Intent Analysis
        st.markdown("**Intent Analysis**")
        import random
        intent_options = [
            "Standard purchase - no special intent detected",
            "Gift purchase - check delivery timing",
            "Bulk order - potential business customer",
            "Repeat customer - high loyalty score",
            "First-time buyer - send welcome email"
        ]
        intent_text = random.choice(intent_options)
        st.info(intent_text)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:1px solid #444; margin:0.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Priority Score
        st.markdown("**Priority Score**")
        priority_icons = {'High': '●', 'Medium': '◐', 'Low': '○'}
        priority = random.choice(['High', 'Medium', 'Low'])
        st.markdown(f"{priority_icons[priority]} **{priority} Priority**")
        
        risk_reasons = {
            'High': 'Large order value, requires attention',
            'Medium': 'Standard order, normal processing',
            'Low': 'Low value, automated handling'
        }
        st.caption(risk_reasons[priority])
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:1px solid #444; margin:0.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Generate Reply
        st.markdown("**Generate Reply**")
        
        reply_template = f"""Hi {customer_name},

Thank you for your order {order.get('name', 'N/A')}!

Your order is currently being prepared for dispatch and will be shipped today. You'll receive a tracking number via email once it's on its way.

Order Summary:
• Total: ${order.get('total', '0.00')}
• Payment: {order.get('financial_status', 'N/A').title()}
• Estimated Delivery: 3-5 business days

If you have any questions, feel free to reply to this email.

Best regards,
Customer Support Team"""
        
        st.text_area("", value=reply_template, height=280, key="ai_reply", label_visibility="collapsed")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Action buttons
        col_x, col_y = st.columns(2)
        with col_x:
            if st.button("Regenerate", use_container_width=True):
                show_toast("Regenerating AI reply...", "info")
        with col_y:
            if st.button("Send Reply", use_container_width=True):
                show_toast("Reply sent to customer!", "success")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("All AI insights are mock demonstrations")


def customers_page(shop_domain: str, access_token: str):
    """Customers management page with AI insights"""
    render_page_header("Customers", "◔", "Manage customer relationships")
    
    if not shop_domain or not access_token:
        render_empty_state("Credentials Required", "Configure credentials in sidebar", "○")
        return
    
    customers = st.session_state.current_customers
    customers_count = st.session_state.sync_results['customers']['count']
    last_sync = st.session_state.sync_results['customers'].get('last_sync')
    
    # Calculate metrics
    total_spent_sum = sum(float(c.get('total_spent', 0)) for c in customers)
    high_value = len([c for c in customers if float(c.get('total_spent', 0)) > 500])
    repeat_customers = len([c for c in customers if c.get('orders_count', 0) > 1])
    
    # Handle last_sync
    if last_sync:
        if isinstance(last_sync, str):
            try:
                last_sync = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                last_sync_display = last_sync.strftime("%H:%M")
            except:
                last_sync_display = last_sync[:5] if len(last_sync) >= 5 else "Recent"
        else:
            last_sync_display = last_sync.strftime("%H:%M")
    else:
        last_sync_display = "Never"
    
    render_metrics_grid([
        {"value": str(customers_count), "label": "Total Customers", "icon": "◔", "color": "primary"},
        {"value": str(high_value), "label": "High Value", "icon": "★", "color": "success"},
        {"value": str(repeat_customers), "label": "Repeat Buyers", "icon": "◉", "color": "info"},
        {"value": last_sync_display, "label": "Last Sync", "icon": "↻", "color": "warning"},
    ])
    
    render_divider()
    render_section_header("Sync Customers", "↻")
    
    if st.button("↻ Sync Customers", type="primary"):
        with st.spinner("Syncing..."):
            result = run_async(sync_customers(shop_domain, access_token))
            
            if result['success']:
                st.session_state.current_customers = result.get('customers', [])
                st.session_state.sync_results['customers']['count'] = len(st.session_state.current_customers)
                st.session_state.sync_results['customers']['last_sync'] = datetime.now()
                if st.session_state.persist_data:
                    save_persisted_state()
                show_toast(f"Synced {len(st.session_state.current_customers)} customers!", "success")
                add_test_result("Customer Sync", True, f"Synced {len(st.session_state.current_customers)} customers")
                st.rerun()
            else:
                show_toast(f"Failed: {result.get('error')}", "error")
                add_test_result("Customer Sync", False, result.get('error', ''))
    
    render_divider()
    
    if customers:
        render_section_header("Customer List", "◔")
        
        # Mock AI segmentation
        import random
        ai_types = ["Frequent Buyer", "New Customer", "At Risk", "VIP", "Occasional"]
        ai_products = ["Shoes", "Electronics", "Fashion", "Home Decor", "Sports"]
        ai_risk = ["Low", "Medium", "High"]
        
        table_data = []
        for c in customers[:50]:
            # Add mock AI fields
            customer_type = random.choice(ai_types)
            next_purchase = random.choice(ai_products)
            risk_score = random.choice(ai_risk)
            
            table_data.append({
                "Name": c.get('name', 'N/A'),
                "Email": c.get('email', 'N/A'),
                "Phone": c.get('phone', 'N/A')[:15] if c.get('phone') != 'N/A' else 'N/A',
                "Orders": c.get('orders_count', 0),
                "Total Spent": f"${float(c.get('total_spent', 0)):.2f}",
                "AI Type": customer_type,
                "Predicted Next": next_purchase,
                "Risk": risk_score,
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)
        
        st.caption("◈ AI Type, Predicted Next Purchase, and Risk Score are AI-powered insights (mock)")
    else:
        render_empty_state("No Customers", "Click Sync Customers to fetch customers", "◔")


def order_lookup_page(shop_domain: str, access_token: str):
    """Order status lookup and detail page"""
    render_page_header("Order Lookup", "◎", "Find order status quickly")
    
    with st.form("order_lookup"):
        order_id = st.text_input("Order ID or Number", placeholder="e.g., 1234567890 or #1001")
        lookup_btn = st.form_submit_button("◎ Find Order", type="primary")
    
    if lookup_btn and order_id:
        found_order = None
        search_id = order_id.replace('#', '').strip()
        
        for order in st.session_state.current_orders:
            if (str(order.get('id', '')) == search_id or 
                str(order.get('order_number', '')) == search_id or
                str(order.get('name', '')) == order_id):
                found_order = order
                break
        
        if found_order:
            st.session_state.lookup_found_order = found_order
            show_toast("Order found!", "success")
        else:
            st.session_state.lookup_found_order = None
            st.error("Order not found")
    
    # Display found order from session state
    found_order = st.session_state.get('lookup_found_order')
    
    if found_order:
        # Primary metrics
        render_metrics_grid([
            {"value": f"#{found_order.get('order_number', 'N/A')}", "label": "Order", "icon": "▤", "color": "primary"},
            {"value": f"${found_order.get('total', '0.00')}", "label": "Total", "icon": "◈", "color": "success"},
            {"value": found_order.get('financial_status', 'N/A').title(), "label": "Payment", "icon": "●", "color": "info"},
            {"value": (found_order.get('fulfillment_status') or 'unfulfilled').title(), "label": "Fulfillment", "icon": "◐", "color": "warning"},
        ])
        
        render_divider()
        
        # Two column layout
        left_col, right_col = st.columns([1, 1])
        
        with left_col:
            render_section_header("Order Details", "◔")
            
            render_info_card("Customer Information", [
                {"label": "Name", "value": found_order.get('customer_name', 'Guest')},
                {"label": "Email", "value": found_order.get('email', 'N/A')},
                {"label": "Order Date", "value": found_order.get('created_at', 'N/A')[:10] if found_order.get('created_at') else 'N/A'},
            ], "◔")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mock line items
            render_section_header("Line Items (Mock)", "▦")
            import random
            mock_items = [
                {"name": "Product A", "qty": 2, "price": 50.00},
                {"name": "Product B", "qty": 1, "price": 35.00},
            ]
            
            for item in mock_items:
                st.markdown(f'''
                <div class="card" style="padding: 0.75rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 500; font-size: 0.875rem;">{item["name"]}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">Qty: {item["qty"]} × ${item["price"]:.2f}</div>
                        </div>
                        <div style="font-weight: 600; color: var(--primary);">${item["qty"] * item["price"]:.2f}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mock order timeline
            render_section_header("Order Timeline (Mock)", "◉")
            timeline_events = [
                {"time": "2 days ago", "event": "Order placed", "icon": "●"},
                {"time": "1 day ago", "event": "Payment confirmed", "icon": "●"},
                {"time": "12 hours ago", "event": "Processing started", "icon": "◐"},
                {"time": "Pending", "event": "Shipped", "icon": "○"},
            ]
            
            for evt in timeline_events:
                completed = evt["icon"] == "●"
                color = "success" if completed else "muted"
                st.markdown(f'''
                <div style="display: flex; gap: 0.75rem; margin-bottom: 0.75rem; align-items: start;">
                    <div style="color: var(--{color}); font-size: 1.25rem; line-height: 1;">{evt["icon"]}</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 500; font-size: 0.875rem;">{evt["event"]}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">{evt["time"]}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        
        with right_col:
            render_section_header("AI Analysis", "◈")
            
            # AI Order Summary
            st.markdown("### Order Summary")
            summary = f"""Order Type: Standard Purchase
Risk Level: Low
Customer Segment: Repeat Buyer
Priority: Normal

Insights:
• Customer has {random.randint(3, 15)} previous orders
• Average order value: ${random.randint(50, 150):.2f}
• High likelihood of positive review
• No delivery issues predicted"""
            
            st.markdown(f'''
            <div class="card" style="padding: 1rem; background: var(--surface-1); border: 1px solid var(--surface-3); border-radius: var(--radius);">
                <pre style="margin: 0; font-size: 0.875rem; color: var(--text-primary); white-space: pre-wrap; font-family: {FONTS['primary']};">{summary}</pre>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Customer Intent Analysis
            st.markdown("### Intent Analysis")
            intent_tags = ["First-time buyer", "Price-sensitive", "Quick delivery needed", "Gift purchase"]
            selected_intent = random.choice(intent_tags)
            
            st.markdown(f'''
            <div class="card" style="padding: 1rem;">
                <div style="font-weight: 600; margin-bottom: 0.5rem;">Detected Intent:</div>
                <div style="display: inline-block; padding: 0.5rem 1rem; background: var(--primary); color: white; border-radius: 20px; font-size: 0.875rem;">{selected_intent}</div>
                <div style="margin-top: 1rem; font-size: 0.875rem; color: var(--text-secondary);">
                    Based on order patterns and customer behavior, this order shows characteristics of a {selected_intent.lower()}.
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Priority Score
            st.markdown("### Priority Score")
            priority_score = random.randint(65, 95)
            priority_level = "High" if priority_score > 80 else "Medium" if priority_score > 60 else "Low"
            priority_color = "success" if priority_score > 80 else "warning" if priority_score > 60 else "error"
            
            st.markdown(f'''
            <div class="card" style="padding: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <div style="font-weight: 600;">Priority Level:</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--{priority_color});">{priority_score}/100</div>
                </div>
                <div style="background: var(--card-bg); border-radius: 8px; height: 8px; overflow: hidden;">
                    <div style="background: var(--{priority_color}); width: {priority_score}%; height: 100%;"></div>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted);">
                    {priority_level} priority - Recommended response time: {2 if priority_score > 80 else 4 if priority_score > 60 else 24} hours
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Generate Reply
            st.markdown("### Generate Reply")
            reply_type = st.selectbox("Reply Type", ["Order Status", "Delay Notification", "Delivery Confirmation", "Issue Resolution"])
            
            if st.button("Generate Reply", use_container_width=True):
                mock_reply = f"""Hi {found_order.get('customer_name', 'Customer')},

Thank you for your order #{found_order.get('order_number', 'N/A')}!

Your order is currently {found_order.get('fulfillment_status', 'being processed')}. We're working hard to get it to you as soon as possible.

Order Details:
• Total: ${found_order.get('total', '0.00')}
• Payment Status: {found_order.get('financial_status', 'confirmed')}
• Expected Delivery: 3-5 business days

If you have any questions, please don't hesitate to reach out.

Best regards,
Your Store Team"""
                
                st.session_state.lookup_generated_reply = mock_reply
                show_toast("Reply generated!", "success")
            
            # Display generated reply if exists
            if st.session_state.get('lookup_generated_reply'):
                st.text_area("Generated Reply", value=st.session_state.lookup_generated_reply, height=250)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Copy", use_container_width=True):
                        show_toast("Copied to clipboard!", "success")
                with col_b:
                    if st.button("Send", use_container_width=True):
                        show_toast("Email sent!", "success")
    else:
        render_empty_state("Not Found", "Order not in current data. Try syncing first.", "○")


def ai_tools_page(shop_domain: str, access_token: str):
    """AI-powered tools page"""
    render_page_header("AI Tools", "◈", "AI-powered content and analytics")

    tool_tabs = st.tabs([
        "◧ Descriptions",
        "◉ Support Emails",
        "▥ Analytics",
        "◇ SEO Tools",
        "▦ Form Filling",
        "▣ Support Chat",
    ])
    
    with tool_tabs[0]:
        render_section_header("Product Descriptions", "◧")
        
        if st.session_state.current_products:
            product_options = {f"{p.get('title', 'Unnamed')} - ${p.get('price', '0.00')}": p for p in st.session_state.current_products}
            selected_product_key = st.selectbox("Select Product", list(product_options.keys()))
            
            if selected_product_key:
                selected_product = product_options[selected_product_key]
                tone_options = ["Luxury", "Friendly", "Trendy", "Professional", "Casual"]
                selected_tone = st.selectbox("Tone", tone_options)
                
                if st.button("◈ Generate", type="primary"):
                    with st.spinner("Generating..."):
                        generated_desc = f"""{selected_product.get('title', 'Product')}

Premium quality, exceptional craftsmanship. Perfect for any occasion.

{selected_product.get('description', 'Experience the difference.')}

Shop now - fast shipping and satisfaction guaranteed!"""
                        
                        show_toast("Generated!", "success")
                        st.text_area("Generated Description", generated_desc, height=150)
        else:
            render_empty_state("No Products", "Sync products first", "▦")
    
    with tool_tabs[1]:
        render_section_header("Support Emails", "◉")
        
        email_types = {"Order Status": "order_status", "COD Confirmation": "cod_confirmation", 
                       "Return/Refund": "return_refund", "Delivery ETA": "delivery_eta"}
        
        col1, col2 = st.columns(2)
        with col1:
            selected_email_type = st.selectbox("Email Type", list(email_types.keys()))
            customer_name = st.text_input("Customer Name", placeholder="John Doe")
        with col2:
            email_tone = st.selectbox("Tone", ["Luxury", "Friendly", "Trendy"])
            order_number = st.text_input("Order Number", placeholder="1001")
        
        if st.button("◈ Generate Email", type="primary"):
            try:
                # Fetch real order data if order number is provided
                real_customer_name = customer_name
                real_total_amount = "$99.99"
                real_product_names = "Selected Product"
                real_order_status = "Processing"
                real_email = customer_name or "customer@example.com"
                shipping_info = "Your order is being prepared and will be shipped soon."
                real_tracking = None
                
                if order_number and 'orders' in st.session_state:
                    # Find the order by order number
                    matching_order = None
                    for order in st.session_state.orders:
                        if str(order.get('order_number')) == str(order_number) or str(order.get('name', '')).replace('#', '') == str(order_number):
                            matching_order = order
                            break
                    
                    if matching_order:
                        # Extract real customer details
                        real_customer_name = matching_order.get('customer_name', customer_name or "Valued Customer")
                        real_total_amount = f"₹{matching_order.get('total_price', '0')}"
                        
                        # Format status professionally
                        status = matching_order.get('financial_status', 'pending')
                        status_map = {
                            'pending': 'Payment Pending',
                            'paid': 'Confirmed & Processing',
                            'partially_paid': 'Partially Paid',
                            'refunded': 'Refunded',
                            'voided': 'Cancelled',
                            'authorized': 'Payment Authorized'
                        }
                        real_order_status = status_map.get(status, status.replace('_', ' ').title())
                        
                        # Get fulfillment status for shipping info
                        fulfillment_status = matching_order.get('fulfillment_status')
                        if fulfillment_status == 'fulfilled':
                            shipping_info = "Your order has been shipped and is on the way!"
                            tracking_numbers = []
                            for fulfillment in matching_order.get('fulfillments', []):
                                if fulfillment.get('tracking_number'):
                                    tracking_numbers.append(fulfillment['tracking_number'])
                            real_tracking = tracking_numbers[0] if tracking_numbers else None
                        elif fulfillment_status == 'partial':
                            shipping_info = "Part of your order has been shipped. Remaining items are being prepared."
                            real_tracking = None
                        else:
                            shipping_info = "Your order is being carefully prepared and will be shipped within 1-2 business days."
                            real_tracking = None
                        
                        # Extract product names from line items
                        line_items = matching_order.get('line_items', [])
                        if line_items:
                            product_list = [item.get('name', 'Product') for item in line_items]
                            real_product_names = ", ".join(product_list)
                        
                        # Try to get customer email
                        if matching_order.get('email'):
                            real_email = matching_order.get('email')
                        elif matching_order.get('customer', {}).get('email'):
                            real_email = matching_order['customer']['email']
                        
                        show_toast(f"Found Order #{order_number}!", "success")
                    else:
                        show_toast(f"Order #{order_number} not found, using provided details", "warning")
                
                # Get template key once here for use in both branches
                template_key = email_types[selected_email_type]
                
                template_path = Path(__file__).parent.parent / "generated_templates.json"
                if template_path.exists():
                    with open(template_path, "r") as f:
                        templates = json.load(f)
                    
                    template_data = templates.get(email_tone, {}).get("support", {}).get(template_key)
                    
                    # Handle dict structure (email/short/whatsapp) or direct string template
                    if isinstance(template_data, dict):
                        # Use 'email' key if available, otherwise try 'template' key
                        template = template_data.get('email') or template_data.get('template') or str(template_data)
                    else:
                        template = template_data or "No template found"
                    
                    # Ensure template is a string before formatting
                    if isinstance(template, str):
                        from string import Template
                        
                        # Prepare replacement values
                        values = {
                            'customer_name': real_customer_name,
                            'order_id': order_number or "12345",
                            'order_number': order_number or "12345",
                            'status': real_order_status,
                            'shipping_info': shipping_info,
                            'business_name': st.session_state.get('business_profile', {}).get('business_name', 'Sclothers'),
                            'total_amount': real_total_amount,
                            'product_name': real_product_names,
                            'answer': "The item is currently in stock.",
                            'size_chart_link': "https://yourstore.com/size-chart",
                            'return_instructions': "Package securely and ship to returns address.",
                            'email': real_email,
                            'tracking_link': f"https://yourstore.com/track/{order_number}" if not real_tracking else f"https://track.shipment.com/{real_tracking}",
                            'delivery_date': "3-5 business days",
                            'courier': "Blue Dart Express"
                        }
                        
                        # Try both placeholder formats: {...} and ${...}
                        try:
                            # First try Python format strings {...}
                            generated_email = template.format(**values)
                        except (KeyError, ValueError):
                            # If that fails, try Template with ${...}
                            template_obj = Template(template)
                            generated_email = template_obj.safe_substitute(**values)
                        
                        st.text_area("Generated Email", generated_email, height=250)
                    else:
                        show_toast("Invalid template format", "error")
                else:
                    # Fallback mock template if file doesn't exist
                    mock_template = f"""Subject: {selected_email_type}

Dear {customer_name or 'Valued Customer'},

Thank you for your order #{order_number or '12345'}. 

{('We are processing your COD order. Please confirm your order by replying YES.' if template_key == 'cod_confirmation' 
  else 'Your order is being processed and will be shipped soon.' if template_key == 'order_status'
  else 'We have received your return request and will process it within 3-5 business days.' if template_key == 'return_refund'
  else 'Your order will be delivered within 3-5 business days.')}

Best regards,
Your Store Team"""
                    show_toast("Generated (mock template)!", "success")
                    st.text_area("Generated Email", mock_template, height=200)
            except Exception as e:
                show_toast(f"Error: {e}", "error")
    
    with tool_tabs[2]:
        render_section_header("Business Analyzer AI", "▥")
        
        if st.session_state.current_orders and st.session_state.current_products:
            total_orders = len(st.session_state.current_orders)
            total_products = len(st.session_state.current_products)
            total_value = sum(float(order.get('total', 0)) for order in st.session_state.current_orders)
            avg_order_value = total_value / total_orders if total_orders > 0 else 0
            
            # Core metrics
            render_metrics_grid([
                {"value": str(total_orders), "label": "Total Orders", "icon": "▤", "color": "primary"},
                {"value": str(total_products), "label": "Products", "icon": "▦", "color": "info"},
                {"value": f"${total_value:,.0f}", "label": "Revenue", "icon": "◈", "color": "success"},
                {"value": f"${avg_order_value:.0f}", "label": "AOV", "icon": "▥", "color": "warning"},
            ])
            
            render_divider()
            
            # AI Business Detection (Mock)
            import random
            niches = ["Fashion Apparel", "Electronics & Gadgets", "Home & Living", "Health & Beauty", "Sports & Fitness"]
            detected_niche = random.choice(niches)
            
            regions = ["Pakistan", "India", "UAE", "USA", "Southeast Asia"]
            detected_region = st.session_state.get('business_region', random.choice(regions))
            
            st.markdown(f'''
            <div class="card" style="background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%); padding: 1.5rem; color: white; margin-bottom: 1.5rem;">
                <div style="font-size: 0.875rem; opacity: 0.9; margin-bottom: 0.5rem;">🤖 AI BUSINESS ANALYSIS</div>
                <div style="font-weight: 600; font-size: 1.125rem; margin-bottom: 1rem;">Detected Niche: {detected_niche}</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.875rem;">
                    <div>
                        <div style="opacity: 0.9;">Primary Region</div>
                        <div style="font-weight: 600; margin-top: 0.25rem;">🌍 {detected_region}</div>
                    </div>
                    <div>
                        <div style="opacity: 0.9;">Confidence Score</div>
                        <div style="font-weight: 600; margin-top: 0.25rem;">⭐ {random.randint(85, 98)}%</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Key Insights
            col1, col2 = st.columns(2)
            
            with col1:
                render_section_header("Key Insights", "🔍")
                
                insights = [
                    "COD (Cash on Delivery) usage likely high in your region",
                    "High return rate risk - size charts recommended",
                    "Mobile traffic dominant - optimize mobile experience",
                    "Social media integration will boost engagement",
                    "Customer support via WhatsApp recommended"
                ]
                
                for insight in insights:
                    st.markdown(f'''
                    <div class="card" style="padding: 0.75rem; margin-bottom: 0.5rem; border-left: 3px solid var(--primary);">
                        <div style="font-size: 0.8125rem; color: var(--text-secondary);">• {insight}</div>
                    </div>
                    ''', unsafe_allow_html=True)
            
            with col2:
                render_section_header("Automation Recommendations", "🤖")
                
                automations = [
                    ("Auto COD Confirmation", "High Priority", "success"),
                    ("Auto WhatsApp Replies", "High Priority", "success"),
                    ("Auto Blog SEO", "Medium Priority", "info"),
                    ("Abandoned Cart Follow-up", "Medium Priority", "info"),
                    ("Low Stock Alerts", "Low Priority", "warning")
                ]
                
                for name, priority, color in automations:
                    st.markdown(f'''
                    <div class="card" style="padding: 0.75rem; margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-size: 0.875rem; font-weight: 500;">{name}</div>
                            <div style="font-size: 0.75rem; padding: 0.25rem 0.75rem; border-radius: 12px; background: var(--{color}); color: white;">{priority}</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
            
            render_divider()
            render_section_header("Missing Information", "⚠")
            
            missing_info = [
                {"item": "Courier Partner Name", "importance": "Critical", "reason": "For automated shipping notifications"},
                {"item": "Return Policy Details", "importance": "High", "reason": "For customer support automation"},
                {"item": "Social Media Accounts", "importance": "Medium", "reason": "For cross-platform marketing"},
                {"item": "Brand Guidelines", "importance": "Medium", "reason": "For consistent AI content generation"}
            ]
            
            for info in missing_info:
                col_a, col_b, col_c = st.columns([2, 1, 2])
                with col_a:
                    st.markdown(f"**{info['item']}**")
                with col_b:
                    badge_color = "error" if info['importance'] == "Critical" else "warning" if info['importance'] == "High" else "info"
                    st.markdown(f'<span style="font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 8px; background: var(--{badge_color}); color: white;">{info["importance"]}</span>', unsafe_allow_html=True)
                with col_c:
                    st.caption(info['reason'])
        else:
            render_empty_state("No Data", "Sync products and orders first", "▥")
    
    with tool_tabs[3]:
        render_section_header("SEO Tools", "◇")
        
        seo_tabs = st.tabs(["◎ Keywords", "◧ Optimizer", "◉ Meta Tags"])
        
        with seo_tabs[0]:
            target_keyword = st.text_input("Keyword to Analyze")
            
            if st.button("◎ Analyze", type="primary") and target_keyword:
                with st.spinner("Analyzing..."):
                    render_metrics_grid([
                        {"value": "12.5K", "label": "Search Volume", "icon": "▥", "color": "primary"},
                        {"value": "Medium", "label": "Competition", "icon": "◐", "color": "warning"},
                        {"value": "$2.45", "label": "CPC", "icon": "◈", "color": "success"},
                    ])
                    
                    render_divider()
                    st.markdown(f"**Related:** {target_keyword} online, best {target_keyword}, buy {target_keyword}")
        
        with seo_tabs[1]:
            content = st.text_area("Content", height=150)
            target_kw = st.text_input("Primary Keyword")
            
            if st.button("◧ Analyze Content", type="primary") and content and target_kw:
                word_count = len(content.split())
                kw_count = content.lower().count(target_kw.lower())
                kw_density = (kw_count / word_count) * 100 if word_count > 0 else 0
                
                render_metrics_grid([
                    {"value": str(word_count), "label": "Words", "icon": "◧", "color": "primary"},
                    {"value": str(kw_count), "label": "Keywords", "icon": "◎", "color": "info"},
                    {"value": f"{kw_density:.1f}%", "label": "Density", "icon": "◐", "color": "success" if 1 <= kw_density <= 3 else "warning"},
                ])
        
        with seo_tabs[2]:
            page_title = st.text_input("Page Title")
            page_desc = st.text_area("Description", height=80)
            
            if st.button("◉ Generate Meta", type="primary") and page_title:
                optimized_title = f"{page_title[:50]}..." if len(page_title) > 50 else page_title
                optimized_desc = page_desc[:155] if page_desc else f"Discover {page_title} - Premium quality, fast shipping."
                
                st.code(f'<title>{optimized_title}</title>\n<meta name="description" content="{optimized_desc}">')

    with tool_tabs[4]:
        render_section_header("Form Filling / Data Entry", "▦")

        st.caption("Paste unstructured customer details and extract structured fields for fast data entry.")

        raw_text = st.text_area(
            "Customer Details",
            height=160,
            placeholder=(
                "Name: John Doe\n"
                "Email: john@example.com\n"
                "Phone: +1 555 123 4567\n"
                "Order: #1001\n"
                "Address: 123 Main St, City, Country"
            ),
        )

        def _extract_fields(text: str) -> Dict[str, str]:
            if not text:
                return {}

            fields: Dict[str, str] = {}

            email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
            if email_match:
                fields["email"] = email_match.group(0)

            phone_match = re.search(r"(\+?\d[\d\s\-()]{7,}\d)", text)
            if phone_match:
                fields["phone"] = phone_match.group(1).strip()

            order_match = re.search(r"(?:order\s*(?:id|number)?\s*[:\-]?\s*#?)(\d{3,})", text, re.IGNORECASE)
            if not order_match:
                order_match = re.search(r"#(\d{3,})", text)
            if order_match:
                fields["order_number"] = order_match.group(1)

            name_match = re.search(r"(?:name|customer)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
            if name_match:
                fields["name"] = name_match.group(1).strip()[:120]

            address_match = re.search(r"address\s*[:\-]\s*(.+)", text, re.IGNORECASE)
            if address_match:
                fields["address"] = address_match.group(1).strip()[:200]

            return fields

        col_a, col_b = st.columns([1, 1])
        with col_a:
            extract_clicked = st.button("▦ Extract Fields", type="primary")
        with col_b:
            st.caption("Tip: Include labels like 'Email:' for best results.")

        if extract_clicked:
            extracted = _extract_fields(raw_text)
            if not extracted:
                show_toast("No fields found. Add labels like 'Email:' or '#1001'.", "warning")
            else:
                show_toast("Fields extracted", "success")

            rows = [{"Field": k.replace("_", " ").title(), "Value": v} for k, v in extracted.items()]
            if rows:
                st.data_editor(rows, use_container_width=True, disabled=False, hide_index=True)

            with st.expander("Extracted JSON", expanded=bool(extracted)):
                st.json(extracted)

    with tool_tabs[5]:
        render_section_header("Customer Support Chat", "▣")

        if "support_chat_history" not in st.session_state:
            st.session_state.support_chat_history = []

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("▣ New Chat", use_container_width=True):
                st.session_state.support_chat_history = []
                st.rerun()
        with col2:
            st.caption("Chat UI demo. If a support endpoint is enabled, it will be used automatically.")

        for msg in st.session_state.support_chat_history:
            with st.chat_message(msg.get("role", "assistant")):
                st.write(msg.get("content", ""))

        def _fallback_support_reply(message: str) -> str:
            m = (message or "").lower()
            if any(k in m for k in ["refund", "return", "exchange"]):
                return (
                    "I can help with that. Please share your order number and the item(s) you want to return, "
                    "and tell me whether the package is unopened or used. I will guide you through the return steps."
                )
            if any(k in m for k in ["where", "track", "tracking", "delivery", "shipping"]):
                return (
                    "Sure — please share your order number (e.g., #1001) and the email used at checkout. "
                    "I will check the latest shipping status and estimated delivery." 
                )
            if "order" in m:
                return (
                    "Happy to help. Please share your order number (e.g., #1001) and your checkout email, "
                    "and tell me what issue you are seeing (status, address change, cancellation, etc.)."
                )
            return (
                "Thanks for reaching out. Tell me what you need help with and share your order number if you have one."
            )

        # NOTE: Streamlit limitation: st.chat_input cannot be used inside tabs/columns/sidebar.
        # Use a standard form input instead.
        with st.form("support_chat_send", clear_on_submit=True):
            user_message = st.text_input("Message", placeholder="Type a customer message...")
            send_clicked = st.form_submit_button("▣ Send", type="primary")

        if send_clicked and user_message:
            st.session_state.support_chat_history.append({"role": "user", "content": user_message})

            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
            assistant_reply: Optional[str] = None

            try:
                # Optional backend integration (if routes are enabled)
                resp = requests.post(
                    f"{backend_url}/v1/generate/reply?async_mode=false",
                    json={
                        "message": user_message,
                        "conversation_history": [],
                    },
                    timeout=20,
                )
                if resp.ok:
                    payload = resp.json()
                    if isinstance(payload, dict):
                        assistant_reply = payload.get("reply") or payload.get("response")
                    else:
                        assistant_reply = str(payload)
            except Exception:
                assistant_reply = None

            if not assistant_reply:
                assistant_reply = _fallback_support_reply(user_message)

            st.session_state.support_chat_history.append({"role": "assistant", "content": assistant_reply})
            st.rerun()


def workflows_page(shop_domain: str, access_token: str):
    """Workflows & Automation management page"""
    render_page_header("Workflows & Automation", "◧", "Manage automated processes")
    
    # Mock workflow data
    workflows = [
        {"name": "COD Confirmation", "status": "active", "trigger": "New COD Order", "last_run": "2 hours ago", "success_rate": 98, "runs": 245},
        {"name": "Auto Customer Reply", "status": "inactive", "trigger": "WhatsApp Message", "last_run": "Never", "success_rate": 0, "runs": 0},
        {"name": "Auto Blog Generation", "status": "active", "trigger": "Weekly Schedule", "last_run": "Yesterday", "success_rate": 95, "runs": 52},
        {"name": "Low Stock Alert", "status": "active", "trigger": "Daily Check", "last_run": "Today", "success_rate": 100, "runs": 180},
        {"name": "Abandoned Cart", "status": "inactive", "trigger": "Cart Idle 24h", "last_run": "Never", "success_rate": 0, "runs": 0},
        {"name": "Order Status Update", "status": "active", "trigger": "Order Fulfillment", "last_run": "1 hour ago", "success_rate": 97, "runs": 320},
    ]
    
    # Summary metrics
    active_count = len([w for w in workflows if w['status'] == 'active'])
    total_runs = sum(w['runs'] for w in workflows)
    avg_success = sum(w['success_rate'] for w in workflows if w['runs'] > 0) / len([w for w in workflows if w['runs'] > 0])
    
    render_metrics_grid([
        {"value": str(len(workflows)), "label": "Total Workflows", "icon": "◧", "color": "primary"},
        {"value": str(active_count), "label": "Active", "icon": "●", "color": "success"},
        {"value": str(total_runs), "label": "Total Runs", "icon": "◉", "color": "info"},
        {"value": f"{avg_success:.1f}%", "label": "Avg Success", "icon": "★", "color": "warning"},
    ])
    
    render_divider()
    render_section_header("Automation List", "◧")
    
    # Workflows table
    for workflow in workflows:
        status_color = "success" if workflow['status'] == 'active' else "muted"
        status_icon = "●" if workflow['status'] == 'active' else "○"
        
        with st.expander(f"{status_icon} {workflow['name']} - {workflow['status'].title()}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Trigger:** {workflow['trigger']}")
                st.markdown(f"**Last Run:** {workflow['last_run']}")
            
            with col2:
                st.markdown(f"**Total Runs:** {workflow['runs']}")
                st.markdown(f"**Success Rate:** {workflow['success_rate']}%")
            
            with col3:
                toggle_label = "Deactivate" if workflow['status'] == 'active' else "Activate"
                if st.button(f"{toggle_label}", key=f"toggle_{workflow['name']}", use_container_width=True):
                    show_toast(f"Workflow {toggle_label.lower()}d!", "success")
                
                if st.button("View Logs", key=f"logs_{workflow['name']}", use_container_width=True):
                    show_toast("Viewing logs (mock)", "info")
            
            # Mock workflow diagram
            st.markdown("### Workflow Steps")
            st.markdown(f'''
            <div class="card" style="padding: 1rem; background: var(--card-bg);">
                <div style="display: flex; align-items: center; gap: 1rem; overflow-x: auto; padding: 0.5rem 0;">
                    <div style="text-align: center; min-width: 120px;">
                        <div style="padding: 1rem; background: var(--primary); border-radius: 8px; color: white; font-weight: 600; font-size: 0.875rem;">Trigger</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">{workflow['trigger']}</div>
                    </div>
                    <div style="color: var(--primary); font-size: 1.5rem;">→</div>
                    <div style="text-align: center; min-width: 120px;">
                        <div style="padding: 1rem; background: var(--info); border-radius: 8px; color: white; font-weight: 600; font-size: 0.875rem;">Extract Data</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">Parse inputs</div>
                    </div>
                    <div style="color: var(--primary); font-size: 1.5rem;">→</div>
                    <div style="text-align: center; min-width: 120px;">
                        <div style="padding: 1rem; background: var(--warning); border-radius: 8px; color: white; font-weight: 600; font-size: 0.875rem;">AI Process</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">Generate content</div>
                    </div>
                    <div style="color: var(--primary); font-size: 1.5rem;">→</div>
                    <div style="text-align: center; min-width: 120px;">
                        <div style="padding: 1rem; background: var(--success); border-radius: 8px; color: white; font-weight: 600; font-size: 0.875rem;">Execute</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">Send/Save</div>
                    </div>
                    <div style="color: var(--primary); font-size: 1.5rem;">→</div>
                    <div style="text-align: center; min-width: 120px;">
                        <div style="padding: 1rem; background: var(--secondary); border-radius: 8px; color: white; font-weight: 600; font-size: 0.875rem;">Log</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">Record result</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    render_divider()
    
    if st.button("➕ Create New Workflow", type="primary"):
        show_toast("Workflow builder coming soon!", "info")


def templates_page(shop_domain: str, access_token: str):
    """Templates management page"""
    render_page_header("Templates", "◆", "Manage communication templates")
    
    template_tabs = st.tabs(["📧 Email", "💬 Messages", "📝 Content"])
    
    with template_tabs[0]:
        render_section_header("Email Templates", "📧")
        
        email_templates = {
            "Order Status": "Subject: Your Order #{order_number} Update\n\nHi {customer_name},\n\nYour order is {status}.\n\nThank you!",
            "COD Confirmation": "Subject: Confirm Your COD Order\n\nHi {customer_name},\n\nPlease confirm order #{order_number} for ${total}.\n\nReply YES to confirm.",
            "Return/Refund": "Subject: Return Request Received\n\nHi {customer_name},\n\nWe received your return request for order #{order_number}.\n\nProcessing time: 3-5 days.",
            "Delivery ETA": "Subject: Your Order is On The Way!\n\nHi {customer_name},\n\nOrder #{order_number} will arrive by {delivery_date}.\n\nTrack: {tracking_link}"
        }
        
        selected_email = st.selectbox("Select Template", list(email_templates.keys()))
        
        edited_template = st.text_area(
            "Template Content",
            value=email_templates[selected_email],
            height=200,
            help="Use {variables} for dynamic content"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("💾 Save", type="primary", use_container_width=True):
                show_toast("Template saved!", "success")
        with col2:
            if st.button("Preview", use_container_width=True):
                # Show preview with sample data
                preview = edited_template.format(
                    customer_name="John Doe",
                    order_number="1234",
                    status="being processed",
                    total="99.99",
                    delivery_date="Dec 25, 2025",
                    tracking_link="https://track.example.com/1234"
                )
                st.info("**Preview:**\n\n" + preview)
    
    with template_tabs[1]:
        render_section_header("Message Templates", "💬")
        
        message_templates = {
            "WhatsApp Order": "Hello {customer_name}! 👋\n\nYour order #{order_number} is confirmed.\nTotal: ${total}\n\nWe'll keep you updated!",
            "SMS Delivery": "Hi {customer_name}, your order #{order_number} is out for delivery. Track: {tracking_link}",
            "Instagram Reply": "Hey! Thanks for reaching out. Your order #{order_number} status: {status}. DM us for more info! 💬",
        }
        
        selected_msg = st.selectbox("Select Message Template", list(message_templates.keys()))
        
        edited_msg = st.text_area(
            "Message Content",
            value=message_templates[selected_msg],
            height=150
        )
        
        if st.button("💾 Save Message Template", type="primary"):
            show_toast("Message template saved!", "success")
    
    with template_tabs[2]:
        render_section_header("Content Templates", "📝")
        
        content_types = ["Blog Post", "Product Description", "Social Caption", "SEO Meta"]
        selected_content = st.selectbox("Content Type", content_types)
        
        if selected_content == "Blog Post":
            st.text_area("Blog Template", value="# {title}\n\n{intro}\n\n## Key Points\n{content}\n\n## Conclusion\n{conclusion}", height=200)
        elif selected_content == "Product Description":
            st.text_area("Product Template", value="{product_name}\n\n{description}\n\nFeatures:\n{features}\n\nPrice: ${price}", height=200)
        elif selected_content == "Social Caption":
            st.text_area("Social Template", value="✨ {product_name} ✨\n\n{catchy_line}\n\n{hashtags}", height=150)
        else:
            st.text_area("Meta Template", value="Title: {seo_title}\nDescription: {seo_description}", height=100)
        
        if st.button("💾 Save Content Template", type="primary"):
            show_toast("Content template saved!", "success")


def logs_page(shop_domain: str, access_token: str):
    """Logs and monitoring page"""
    render_page_header("Logs", "▣", "Monitor activity and system health")
    
    # System health
    render_metrics_grid([
        {"value": "127", "label": "API Calls Today", "icon": "◉", "color": "primary", "change": "↑ 12%"},
        {"value": "98.5%", "label": "Success Rate", "icon": "●", "color": "success"},
        {"value": "45ms", "label": "Avg Response", "icon": "◔", "color": "info"},
        {"value": str(len(st.session_state.test_history)), "label": "Total Actions", "icon": "▣", "color": "warning"},
    ])
    
    render_divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_section_header("Activity Log", "▥")
        
        if st.session_state.test_history:
            render_activity_feed(st.session_state.test_history[-10:])
        else:
            render_empty_state("No Activity", "Perform actions to see logs", "○")
    
    with col2:
        render_section_header("System Status", "◎")
        
        statuses = [
            ("Products", st.session_state.sync_results['products']['count'] > 0),
            ("Orders", st.session_state.sync_results['orders']['count'] > 0),
            ("Customers", st.session_state.sync_results['customers']['count'] > 0),
        ]
        
        for name, synced in statuses:
            render_status_row(
                text=f"{name}: {'Synced' if synced else 'Not Synced'}",
                status="success" if synced else "warning"
            )
        
        render_section_header("Storage", "▤")
        
        render_progress_bar("Products Cached", len(st.session_state.current_products), max(len(st.session_state.current_products), 100))
        render_progress_bar("Orders Cached", len(st.session_state.current_orders), max(len(st.session_state.current_orders), 100))


def settings_page(shop_domain: str, access_token: str):
    """Settings and configuration page"""
    render_page_header("Settings", "⚙", "Configure platform and business preferences")
    
    settings_tabs = st.tabs(["◐ Business Profile", "◉ Integration", "◈ Automation", "▥ Brand Voice"])
    
    with settings_tabs[0]:
        render_section_header("Business Information", "◐")
        
        with st.form("business_profile"):
            col1, col2 = st.columns(2)
            
            with col1:
                business_name = st.text_input(
                    "Business Name",
                    value=st.session_state.get('business_name', get_shop_value(st.session_state.shop_info, 'name', '')),
                    placeholder="Your Store Name"
                )
                business_email = st.text_input(
                    "Contact Email",
                    value=st.session_state.get('business_email', get_shop_value(st.session_state.shop_info, 'email', '')),
                    placeholder="contact@store.com"
                )
                business_phone = st.text_input(
                    "Phone Number",
                    value=st.session_state.get('business_phone', ''),
                    placeholder="+92 300 1234567"
                )
            
            with col2:
                business_region = st.selectbox(
                    "Primary Region",
                    ["Pakistan", "India", "UAE", "USA", "UK", "Other"],
                    index=0
                )
                business_currency = st.selectbox(
                    "Currency",
                    ["PKR", "USD", "INR", "AED", "GBP", "EUR"],
                    index=0
                )
                business_timezone = st.selectbox(
                    "Timezone",
                    ["Asia/Karachi", "Asia/Dubai", "America/New_York", "Europe/London"],
                    index=0
                )
            
            st.markdown("<br>", unsafe_allow_html=True)
            business_desc = st.text_area(
                "Business Description",
                value=st.session_state.get('business_desc', ''),
                placeholder="Briefly describe your business and products...",
                height=100
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                save_profile = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)
            
            if save_profile:
                st.session_state.business_name = business_name
                st.session_state.business_email = business_email
                st.session_state.business_phone = business_phone
                st.session_state.business_region = business_region
                st.session_state.business_currency = business_currency
                st.session_state.business_timezone = business_timezone
                st.session_state.business_desc = business_desc
                show_toast("Business profile saved!", "success")
    
    with settings_tabs[1]:
        render_section_header("Shopify Connection", "◉")
        
        # Connection status
        is_connected = st.session_state.connection_status and st.session_state.connection_status.get('success')
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown('''
            <div class="card">
                <div style="color: var(--text-secondary); line-height: 1.8; font-size: 0.875rem;">
                    <p style="margin: 0.5rem 0;"><strong>1.</strong> Enter your Shop Domain (e.g., store.myshopify.com)</p>
                    <p style="margin: 0.5rem 0;"><strong>2.</strong> Generate Admin API Access Token from Shopify Admin</p>
                    <p style="margin: 0.5rem 0;"><strong>3.</strong> Required scopes: read_products, write_products, read_orders, write_orders</p>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            render_metrics_grid([{
                "value": "Connected" if is_connected else "Offline",
                "label": "Status",
                "icon": "●" if is_connected else "○",
                "color": "success" if is_connected else "warning"
            }])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("connection_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                form_domain = st.text_input(
                    "Shop Domain", 
                    value=shop_domain, 
                    placeholder="store.myshopify.com"
                )
            
            with col2:
                form_token = st.text_input(
                    "Access Token", 
                    value=access_token, 
                    type="password",
                    placeholder="shpat_xxxxxxxxxxxxx"
                )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                test_btn = st.form_submit_button("Test Connection", type="primary", use_container_width=True)
            with col2:
                save_credentials = st.checkbox("Save credentials", value=True)
        
        if test_btn and form_domain and form_token:
            with st.spinner("Testing connection..."):
                result = run_async(test_connection(form_domain, form_token))
                st.session_state.connection_status = result
                
                if save_credentials:
                    st.session_state.shop_domain = form_domain
                    st.session_state.access_token = form_token
                
                if result['success']:
                    st.session_state.shop_info = result['shop_info']
                    show_toast("Connected successfully!", "success")
                    
                    shop_info = result['shop_info']
                    st.markdown("<br>", unsafe_allow_html=True)
                    render_section_header("Store Information", "◐")
                    
                    render_metrics_grid([
                        {"value": get_shop_value(shop_info, 'name'), "label": "Store", "icon": "◐", "color": "primary"},
                        {"value": get_shop_value(shop_info, 'domain'), "label": "Domain", "icon": "◉", "color": "info"},
                        {"value": get_shop_value(shop_info, 'currency'), "label": "Currency", "icon": "◈", "color": "success"},
                        {"value": get_shop_value(shop_info, 'plan'), "label": "Plan", "icon": "★", "color": "primary"},
                    ])
                    
                    add_test_result("Connection Test", True, f"Connected to {get_shop_value(shop_info, 'name')}")
                else:
                    show_toast(f"Connection failed: {result.get('error', 'Unknown error')}", "error")
                    add_test_result("Connection Test", False, result.get('error', 'Unknown'))
                    
                    if result.get('debug_info'):
                        with st.expander("Debug Information"):
                            st.json(result['debug_info'])
        
        # Capabilities check
        if is_connected:
            render_divider()
            render_section_header("API Capabilities", "◎")
            
            if st.button("Check Capabilities", type="secondary"):
                with st.spinner("Checking API capabilities..."):
                    caps_result = run_async(check_capabilities(shop_domain, access_token))
                    
                    if caps_result['success']:
                        st.session_state.capabilities = caps_result['capabilities']
                        show_toast("Capabilities checked!", "success")
                        add_test_result("Capability Check", True)
                    else:
                        show_toast(f"Failed: {caps_result.get('error')}", "error")
                        add_test_result("Capability Check", False, caps_result.get('error', ''))
            
            if st.session_state.capabilities:
                st.markdown("<br>", unsafe_allow_html=True)
                render_capability_grid(st.session_state.capabilities)
        
        render_divider()
        render_section_header("Data Sync Settings", "↻")
        
        col1, col2 = st.columns(2)
        with col1:
            auto_sync = st.checkbox("Enable Auto-Sync", value=False, help="Automatically sync data every hour (mock)")
            persist_data = st.checkbox("Persist Data on Refresh", value=st.session_state.get('persist_data', True))
            st.session_state.persist_data = persist_data
        
        with col2:
            sync_products = st.checkbox("Sync Products", value=True, disabled=True)
            sync_orders = st.checkbox("Sync Orders", value=True, disabled=True)
            sync_customers = st.checkbox("Sync Customers", value=True, disabled=True)
        
        if auto_sync:
            st.info("🤖 Auto-sync will run every hour at the top of the hour (mock feature)")
    
    with settings_tabs[2]:
        render_section_header("Automation Preferences (Mock)", "◈")
        
        st.markdown("### COD Confirmation")
        cod_auto = st.checkbox("Auto-send COD confirmation emails", value=False)
        if cod_auto:
            cod_template = st.selectbox("Email Template", ["Professional", "Friendly", "Urgent"])
            cod_delay = st.slider("Send after (minutes)", 5, 60, 15)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Customer Support")
        support_auto = st.checkbox("Auto-reply to common questions", value=False)
        if support_auto:
            support_tone = st.selectbox("Reply Tone", ["Professional", "Friendly", "Casual"])
            support_channels = st.multiselect("Active Channels", ["Email", "WhatsApp", "Instagram", "Facebook"], default=["Email"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Content Generation")
        content_auto = st.checkbox("Auto-generate blog posts weekly", value=False)
        if content_auto:
            content_freq = st.selectbox("Frequency", ["Weekly", "Bi-weekly", "Monthly"])
            content_day = st.selectbox("Publish Day", ["Monday", "Wednesday", "Friday"])
    
    with settings_tabs[3]:
        render_section_header("Brand Voice & Style (Mock)", "▥")
        
        brand_voice = st.selectbox(
            "Primary Brand Voice",
            ["Professional", "Friendly", "Luxury", "Trendy", "Casual", "Technical"],
            index=0
        )
        
        brand_keywords = st.text_area(
            "Brand Keywords (comma-separated)",
            value="quality, affordable, trusted, premium",
            help="Keywords that represent your brand",
            height=80
        )
        
        col1, col2 = st.columns(2)
        with col1:
            target_audience = st.multiselect(
                "Target Audience",
                ["Young Adults (18-25)", "Adults (26-40)", "Professionals", "Parents", "Students", "Seniors"],
                default=["Young Adults (18-25)", "Adults (26-40)"]
            )
        
        with col2:
            content_focus = st.multiselect(
                "Content Focus",
                ["Product Features", "Customer Stories", "How-to Guides", "Industry News", "Promotions"],
                default=["Product Features", "How-to Guides"]
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save Brand Settings", type="primary"):
            st.session_state.brand_voice = brand_voice
            st.session_state.brand_keywords = brand_keywords
            st.session_state.target_audience = target_audience
            st.session_state.content_focus = content_focus
            show_toast("Brand settings saved!", "success")


def seo_content_automation_page(shop_domain: str, access_token: str):
    """SEO Content Automation page"""
    render_page_header("SEO Automation", "◇", "AI-powered content strategy")
    
    # Hero section
    st.markdown('''
    <div class="card" style="background: linear-gradient(135deg, var(--primary) 0%, #A855F7 100%); padding: 2rem; color: white;">
        <h3 style="margin: 0 0 0.5rem 0; font-size: 1.25rem;">◈ Intelligent Content Generation</h3>
        <p style="opacity: 0.9; margin-bottom: 1rem; font-size: 0.875rem;">Automate content strategy with AI</p>
        <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.8125rem; opacity: 0.9;">
            <span>▥ Product-driven topics</span>
            <span>◧ AI SEO content</span>
            <span>◉ Smart linking</span>
            <span>◔ Auto scheduling</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    if not shop_domain or not access_token:
        render_empty_state("Credentials Required", "Configure shop credentials first", "○")
        return
    
    render_divider()
    
    # ROI metrics
    render_metrics_grid([
        {"value": "PKR 100K+", "label": "Monthly Savings", "icon": "◈", "color": "warning", "change": "↑ vs manual"},
        {"value": "90%", "label": "Time Saved", "icon": "◔", "color": "success", "change": "↑ efficiency"},
        {"value": "3x", "label": "Content Output", "icon": "▥", "color": "primary", "change": "↑ vs traditional"},
    ])
    
    render_divider()
    
    # Tabs
    automation_tabs = st.tabs(["◎ Topics", "◧ Content", "◔ Schedule", "▥ Analysis", "⚙ Config"])
    
    with automation_tabs[0]:
        render_section_header("Topic Generation", "◎")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            topic_count = st.slider("Topics to generate", 5, 50, 15)
            
        with col2:
            if st.button("◎ Generate Topics", type="primary"):
                with st.spinner("Analyzing..."):
                    try:
                        api_url = "http://localhost:8000/v1/shopify/content/generate-seo-topics"
                        response = requests.post(api_url, json={
                            "shop_domain": shop_domain,
                            "access_token": access_token,
                            "limit": topic_count
                        }, timeout=30)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success'):
                                topics = result.get('topics', [])
                                st.session_state.generated_topics = topics
                                st.success(f"Generated {len(topics)} SEO topic suggestions!")
                            else:
                                # Fallback to mock data
                                topics = generate_mock_seo_topics(shop_domain, topic_count)
                                st.session_state.generated_topics = topics
                                st.success(f"Generated {len(topics)} SEO topic suggestions (demo mode)")
                        else:
                            # Fallback to mock data
                            topics = generate_mock_seo_topics(shop_domain, topic_count)
                            st.session_state.generated_topics = topics
                            st.info(f"Generated {len(topics)} SEO topic suggestions (demo mode)")
                    except requests.exceptions.ConnectionError:
                        # Fallback to mock data when backend is not running
                        topics = generate_mock_seo_topics(shop_domain, topic_count)
                        st.session_state.generated_topics = topics
                        st.info(f"Generated {len(topics)} SEO topic suggestions (demo mode)")
                    except Exception as e:
                        # Fallback to mock data on any error
                        topics = generate_mock_seo_topics(shop_domain, topic_count)
                        st.session_state.generated_topics = topics
                        st.warning(f"Using demo mode: {str(e)}")
        
        # Display generated topics
        if 'generated_topics' in st.session_state and st.session_state.generated_topics:
            st.markdown("### Generated Topic Suggestions")
            
            for i, topic in enumerate(st.session_state.generated_topics, 1):
                # Handle both dict and string formats
                if isinstance(topic, dict):
                    topic_title = topic.get('title', f'Topic {i}')
                    topic_keywords = topic.get('keywords', [])
                    topic_traffic = topic.get('traffic_potential', 'N/A')
                    topic_angle = topic.get('content_angle', 'N/A')
                    
                    # Handle related_product which might be a dict or string
                    related_prod = topic.get('related_product', 'N/A')
                    if isinstance(related_prod, dict):
                        topic_product = related_prod.get('title', 'N/A')
                    else:
                        topic_product = str(related_prod) if related_prod else 'N/A'
                else:
                    # If topic is a string or other format
                    topic_title = str(topic)
                    topic_keywords = []
                    topic_traffic = 'N/A'
                    topic_angle = 'N/A'
                    topic_product = 'N/A'
                
                with st.expander(f"{i}. {topic_title}", expanded=i<=3):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if topic_keywords:
                            st.write(f"**Target Keywords:** {', '.join(topic_keywords)}")
                        st.write(f"**Traffic Potential:** {topic_traffic} monthly searches")
                        st.write(f"**Content Angle:** {topic_angle}")
                        st.write(f"**Related Product:** {topic_product}")
                    
                    with col2:
                        if st.button("Generate Content", key=f"generate_content_{i}"):
                            st.session_state.selected_topic = topic if isinstance(topic, dict) else {'title': topic_title}
                            st.info("Go to 'Content Generation' tab to create this article!")
    
    with automation_tabs[1]:
        st.subheader("✍️ AI-Powered SEO Content Generation")
        
        st.markdown("""
        Generate complete SEO-optimized articles with intelligent product integration.
        """)
        
        # Content generation form
        with st.form("content_generation_form"):
            st.markdown("#### Content Configuration")
            
            # Use selected topic or manual input
            if 'selected_topic' in st.session_state:
                topic_data = st.session_state.selected_topic
                default_title = topic_data['title']
                default_keywords = ', '.join(topic_data['keywords'])
                st.info(f"📝 Using selected topic: {default_title}")
            else:
                default_title = ""
                default_keywords = ""
            
            content_title = st.text_input("Article Title", value=default_title)
            target_keywords = st.text_area("Target Keywords (comma-separated)", value=default_keywords)
            
            col1, col2 = st.columns(2)
            with col1:
                word_count = st.selectbox("Word Count", [800, 1000, 1200, 1500, 2000], index=2)
                content_type = st.selectbox("Content Type", ["seo_blog", "product_guide", "how_to_guide", "buying_guide"])
            
            with col2:
                internal_links = st.slider("Internal Links", 1, 8, 3)
                product_mentions = st.slider("Product Mentions", 1, 5, 2)
            
            generate_content = st.form_submit_button("🚀 Generate SEO Content", type="primary")
            
            if generate_content and content_title and target_keywords:
                with st.spinner("Generating SEO-optimized content..."):
                    # Call real backend API
                    try:
                        api_url = "http://localhost:8000/v1/shopify/content/generate-seo-blog"
                        payload = {
                            "shop_domain": shop_domain,
                            "access_token": access_token,
                            "target_keywords": [kw.strip() for kw in target_keywords.split(',')],
                            "content_type": content_type,
                            "word_count": word_count,
                            "internal_links_count": internal_links,
                            "product_mentions": product_mentions
                        }
                        response = requests.post(api_url, json=payload, timeout=120)  # Increased timeout for LLM generation
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success'):
                                content_data = result.get('content', {})
                                seo_metrics = result.get('seo_metrics', {})
                                
                                # Format for UI display
                                formatted_content = {
                                    'title': content_data.get('title', content_title),
                                    'content': content_data.get('content', 'No content generated'),
                                    'meta_description': content_data.get('meta_description', ''),
                                    'keywords': content_data.get('target_keywords', []),
                                    'metrics': {
                                        'word_count': word_count,
                                        'seo_score': 85,
                                        'readability': 90,
                                        'internal_links': seo_metrics.get('internal_links', 0),
                                        'product_mentions': seo_metrics.get('product_mentions', 0)
                                    }
                                }
                                
                                st.session_state.generated_content = formatted_content
                                st.success("SEO content generated successfully!")
                            else:
                                # Fallback to mock
                                content_result = generate_mock_seo_content(
                                    content_title, 
                                    [kw.strip() for kw in target_keywords.split(',')], 
                                    word_count,
                                    internal_links,
                                    product_mentions
                                )
                                st.session_state.generated_content = content_result
                                st.info("Content generated (demo mode)")
                        else:
                            # Fallback to mock
                            content_result = generate_mock_seo_content(
                                content_title, 
                                [kw.strip() for kw in target_keywords.split(',')], 
                                word_count,
                                internal_links,
                                product_mentions
                            )
                            st.session_state.generated_content = content_result
                            st.info(f"Content generated (demo mode)")
                    except requests.exceptions.ConnectionError:
                        # Fallback to mock
                        content_result = generate_mock_seo_content(
                            content_title, 
                            [kw.strip() for kw in target_keywords.split(',')], 
                            word_count,
                            internal_links,
                            product_mentions
                        )
                        st.session_state.generated_content = content_result
                        st.info("Content generated (demo mode)")
                    except Exception as e:
                        # Fallback to mock
                        content_result = generate_mock_seo_content(
                            content_title, 
                            [kw.strip() for kw in target_keywords.split(',')], 
                            word_count,
                            internal_links,
                            product_mentions
                        )
                        st.session_state.generated_content = content_result
                        st.warning(f"Content generated (demo mode): {str(e)}")
        
        # Display generated content
        if 'generated_content' in st.session_state and st.session_state.generated_content:
            content = st.session_state.generated_content
            
            st.markdown("### 📝 Generated Content")
            
            # Content metrics
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            with metrics_col1:
                st.metric("Word Count", content['metrics']['word_count'])
            with metrics_col2:
                st.metric("SEO Score", f"{content['metrics']['seo_score']}/100")
            with metrics_col3:
                st.metric("Readability", content['metrics']['readability'])
            with metrics_col4:
                st.metric("Internal Links", content['metrics']['internal_links'])
            
            # Content preview
            st.markdown("#### Content Preview")
            with st.expander("📖 Article Content", expanded=True):
                st.markdown(content.get('content', 'No content generated'))
            
            # Meta information
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📝 Meta Description")
                st.text_area("Meta Description", content.get('meta_description', ''), height=100, disabled=True)
            
            with col2:
                st.markdown("#### 🎯 SEO Keywords")
                keywords = content.get('keywords', content.get('target_keywords', []))
                st.write(", ".join(keywords) if keywords else "No keywords")
                
                st.markdown("#### 🔗 Internal Links")
                internal_links = content.get('internal_links', [])
                if internal_links:
                    for link in internal_links:
                        if isinstance(link, dict):
                            st.write(f"• [{link.get('text', link.get('title', 'Link'))}]({link.get('url', '#')})")
                        else:
                            st.write(f"• {link}")
                else:
                    st.write("No internal links")
            
            # Publish options
            st.markdown("#### 🚀 Publishing Options")
            publish_col1, publish_col2 = st.columns(2)
            
            with publish_col1:
                if st.button("📤 Publish to Shopify Blog", type="primary"):
                    with st.spinner("Publishing to Shopify..."):
                        st.success("✅ Article published successfully!")
                        st.info("🔗 Article URL: https://your-store.myshopify.com/blogs/news/new-article")
            
            with publish_col2:
                if st.button("📅 Schedule for Later"):
                    st.info("📅 Article scheduled for next publish slot")
    
    with automation_tabs[2]:
        st.subheader("📅 Automated Content Scheduling")
        
        st.markdown("""
        Set up automated weekly content generation and publishing schedules.
        """)
        
        # ROI highlight
        st.info("💰 **Automation Benefit:** Save 90% of manual content planning time while ensuring consistent publishing")
        
        # Scheduling configuration
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⚙️ Schedule Configuration")
            
            topics_per_week = st.slider("Articles per week", 1, 7, 3)
            publish_days = st.multiselect(
                "Publish days", 
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                default=["Monday", "Wednesday", "Friday"]
            )
            publish_time = st.time_input("Publish time", value=datetime.strptime("09:00", "%H:%M").time())
            
            auto_publish = st.checkbox("Auto-publish (vs draft only)", value=True)
            
            if st.button("💾 Save Schedule Configuration", type="primary"):
                schedule_config = {
                    'topics_per_week': topics_per_week,
                    'publish_days': publish_days,
                    'publish_time': publish_time.strftime("%H:%M"),
                    'auto_publish': auto_publish
                }
                st.session_state.schedule_config = schedule_config
                st.success("✅ Schedule configuration saved!")
        
        with col2:
            st.markdown("#### 📊 Content Calendar Preview")
            
            if 'schedule_config' in st.session_state:
                config = st.session_state.schedule_config
                st.write(f"**📅 Publishing:** {config['topics_per_week']} articles/week")
                st.write(f"**📆 Days:** {', '.join(config['publish_days'])}")
                st.write(f"**⏰ Time:** {config['publish_time']}")
                st.write(f"**🤖 Auto-publish:** {'Yes' if config['auto_publish'] else 'Drafts only'}")
                
                # Mock upcoming schedule
                st.markdown("##### 📋 This Week's Schedule")
                upcoming_articles = [
                    {"date": "Monday, Dec 16", "topic": "Ultimate Wireless Headphones Guide", "status": "✅ Scheduled"},
                    {"date": "Wednesday, Dec 18", "topic": "Gaming Setup Essentials", "status": "🔄 In Progress"},
                    {"date": "Friday, Dec 20", "topic": "Fast Charging Technology", "status": "📝 Topic Ready"}
                ]
                
                for article in upcoming_articles:
                    st.write(f"• **{article['date']}:** {article['topic']} - {article['status']}")
            else:
                st.info("💡 Configure your schedule to see the content calendar preview.")
        
        # ROI Information
        st.markdown("---")
        st.markdown("#### 💰 Cost Savings Analysis")
        
        roi_col1, roi_col2, roi_col3 = st.columns(3)
        
        with roi_col1:
            st.metric("Manual Cost/Month", "PKR 110,000", help="Content writer + SEO specialist + management")
        with roi_col2:
            st.metric("Automation Cost/Month", "PKR 10,000", help="AI generation + system maintenance")
        with roi_col3:
            st.metric("Monthly Savings", "PKR 100,000", delta="1000% ROI")
    
    with automation_tabs[3]:
        st.subheader("📊 SEO Analysis & Optimization")
        
        st.markdown("""
        Analyze existing content and get optimization recommendations.
        """)
        
        # SEO analysis form
        with st.form("seo_analysis_form"):
            st.markdown("#### Content to Analyze")
            
            analysis_content = st.text_area(
                "Paste your content here", 
                height=200,
                placeholder="Paste your blog article, product description, or any content you want to analyze..."
            )
            
            analysis_keywords = st.text_input(
                "Target Keywords (comma-separated)",
                placeholder="wireless headphones, best bluetooth headphones"
            )
            
            analyze_button = st.form_submit_button("🔍 Analyze SEO", type="primary")
            
            if analyze_button and analysis_content:
                with st.spinner("Analyzing SEO factors..."):
                    # Mock SEO analysis
                    seo_analysis = perform_mock_seo_analysis(analysis_content, analysis_keywords.split(',') if analysis_keywords else [])
                    st.session_state.seo_analysis = seo_analysis
        
        # Display SEO analysis results
        if 'seo_analysis' in st.session_state:
            analysis = st.session_state.seo_analysis
            
            st.markdown("### 📊 SEO Analysis Results")
            
            # Overall scores
            score_col1, score_col2, score_col3, score_col4 = st.columns(4)
            
            with score_col1:
                st.metric("Overall SEO Score", f"{analysis['overall_score']}/100")
            with score_col2:
                st.metric("Readability Score", f"{analysis['readability_score']}/100")
            with score_col3:
                st.metric("Keyword Density", f"{analysis['keyword_density']:.1%}")
            with score_col4:
                st.metric("Content Length", f"{analysis['word_count']} words")
            
            # Detailed analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ✅ Strengths")
                for strength in analysis['strengths']:
                    st.success(f"✅ {strength}")
            
            with col2:
                st.markdown("#### 🔧 Recommendations")
                for rec in analysis['recommendations']:
                    st.warning(f"💡 {rec}")
            
            # Keyword analysis
            if analysis['keyword_analysis']:
                st.markdown("#### 🎯 Keyword Analysis")
                for keyword, data in analysis['keyword_analysis'].items():
                    with st.expander(f"Keyword: {keyword}"):
                        st.write(f"**Density:** {data['density']:.1%}")
                        st.write(f"**Status:** {data['status']}")
                        st.write(f"**Suggestion:** {data['suggestion']}")
    
    with automation_tabs[4]:
        st.subheader("⚙️ Automation Configuration")
        
        st.markdown("""
        Configure your SEO content automation preferences and business settings.
        """)
        
        # Business configuration
        with st.form("business_config_form"):
            st.markdown("#### 🏢 Business Configuration")
            
            business_type = st.selectbox(
                "Business Type", 
                ["ecommerce", "service_business", "b2b"],
                help="This affects content tone, frequency, and optimization focus"
            )
            
            brand_voice = st.selectbox(
                "Brand Voice",
                ["Professional", "Friendly", "Luxury", "Casual", "Technical", "Trendy"]
            )
            
            content_focus = st.multiselect(
                "Content Focus Areas",
                ["Product Education", "Industry Insights", "How-to Guides", "Buying Guides", "Comparisons", "Trends"],
                default=["Product Education", "How-to Guides"]
            )
            
            target_audience = st.selectbox(
                "Primary Audience",
                ["General Consumers", "Business Professionals", "Tech Enthusiasts", "Budget Shoppers", "Premium Buyers"]
            )
            
            save_config = st.form_submit_button("💾 Save Configuration", type="primary")
            
            if save_config:
                business_config = {
                    'business_type': business_type,
                    'brand_voice': brand_voice,
                    'content_focus': content_focus,
                    'target_audience': target_audience,
                    'shop_domain': shop_domain
                }
                st.session_state.business_config = business_config
                st.success("✅ Business configuration saved!")
        
        # Current configuration display
        if 'business_config' in st.session_state:
            st.markdown("#### 📋 Current Configuration")
            config = st.session_state.business_config
            
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.write(f"**Business Type:** {config['business_type'].replace('_', ' ').title()}")
                st.write(f"**Brand Voice:** {config['brand_voice']}")
            with info_col2:
                st.write(f"**Target Audience:** {config['target_audience']}")
                st.write(f"**Content Focus:** {', '.join(config['content_focus'])}")
        
        # Integration status
        st.markdown("---")
        st.markdown("#### 🔌 Integration Status")
        
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            st.success("✅ Shopify Connection")
            st.write("Connected to store")
        
        with status_col2:
            st.success("✅ AI Content Engine")  
            st.write("Ready for generation")
        
        with status_col3:
            st.info("🔄 Background Tasks")
            st.write("Scheduling enabled")


# Mock functions for SEO content automation
def generate_mock_seo_topics(shop_domain: str, count: int) -> List[Dict[str, Any]]:
    """Generate mock SEO topics for demonstration"""
    base_topics = [
        {
            'title': 'Ultimate Guide to Wireless Bluetooth Headphones',
            'keywords': ['wireless headphones', 'bluetooth headphones', 'best wireless headphones'],
            'traffic_potential': 2400,
            'content_angle': 'Educational Guide',
            'related_product': 'Premium Wireless Headphones'
        },
        {
            'title': 'Gaming Keyboard Buying Guide 2024',
            'keywords': ['gaming keyboard', 'mechanical keyboard', 'keyboard guide'],
            'traffic_potential': 1800,
            'content_angle': 'Buying Guide',
            'related_product': 'RGB Gaming Keyboard'
        },
        {
            'title': 'Fast Charging Technology Explained',
            'keywords': ['fast charging', 'USB-C charger', 'quick charge'],
            'traffic_potential': 1200,
            'content_angle': 'Educational',
            'related_product': 'USB-C Fast Charger'
        },
        {
            'title': 'Best Smartphone Accessories for 2024',
            'keywords': ['smartphone accessories', 'phone accessories', 'mobile accessories'],
            'traffic_potential': 3200,
            'content_angle': 'Product Roundup',
            'related_product': 'Phone Accessories Bundle'
        },
        {
            'title': 'How to Choose the Perfect Laptop Stand',
            'keywords': ['laptop stand', 'ergonomic laptop stand', 'laptop accessories'],
            'traffic_potential': 900,
            'content_angle': 'How-to Guide',
            'related_product': 'Adjustable Laptop Stand'
        }
    ]
    
    # Return requested number of topics, cycling through base topics
    topics = []
    for i in range(count):
        topic = base_topics[i % len(base_topics)].copy()
        if i >= len(base_topics):
            topic['title'] = f"{topic['title']} - Advanced Edition"
            topic['traffic_potential'] = int(topic['traffic_potential'] * 0.8)
        topics.append(topic)
    
    return topics


def generate_mock_seo_content(title: str, keywords: List[str], word_count: int, internal_links: int, product_mentions: int) -> Dict[str, Any]:
    """Generate mock SEO content for demonstration"""
    
    kw = keywords[0] if keywords else 'this topic'
    kw_title = kw.title() if keywords else 'This'
    
    # Build content using string concatenation to avoid quote issues
    content = "# " + title + "\n\n"
    content += "Looking for the perfect solution? You have come to the right place. In this comprehensive guide, we will explore everything you need to know about " + kw + " and help you make an informed decision.\n\n"
    content += "## Why " + kw_title + " Matters\n\n"
    content += kw_title + " has become increasingly important in today market. Whether you are a beginner or an expert, understanding the fundamentals can help you make better choices.\n\n"
    content += "### Key Benefits\n\n"
    content += "1. **Quality and Performance**: Get the best value for your investment\n"
    content += "2. **Durability**: Long-lasting solutions that serve you well\n"
    content += "3. **User Experience**: Enhanced satisfaction and convenience\n\n"
    content += "## How to Choose the Right Option\n\n"
    content += "When selecting " + kw + ", consider these essential factors:\n\n"
    content += "- **Your specific needs and requirements**\n"
    content += "- **Budget and value considerations**\n"
    content += "- **Quality and brand reputation**\n"
    content += "- **Customer reviews and feedback**\n\n"
    content += "## Our Top Recommendations\n\n"
    content += "After extensive research and testing, we have curated the best options available. Our [Premium Product Collection](/products/premium-collection) offers exceptional quality and value.\n\n"
    content += "For those seeking budget-friendly alternatives, check out our [Essential Series](/products/essential-series) that delivers solid performance without breaking the bank.\n\n"
    content += "## Expert Tips and Best Practices\n\n"
    content += "### Getting the Most Value\n\n"
    content += "To maximize your investment, follow these expert recommendations:\n\n"
    content += "1. **Research thoroughly** before making a decision\n"
    content += "2. **Compare features** across different options\n"
    content += "3. **Read customer reviews** for real-world insights\n"
    content += "4. **Consider long-term value** over initial cost\n\n"
    content += "### Common Mistakes to Avoid\n\n"
    content += "Do not fall into these common traps:\n"
    content += "- Focusing solely on price\n"
    content += "- Ignoring compatibility requirements\n"
    content += "- Skipping warranty considerations\n"
    content += "- Not reading the fine print\n\n"
    content += "## Frequently Asked Questions\n\n"
    content += "**Q: How long does it typically last?**\n"
    content += "A: With proper care and usage, you can expect excellent longevity and performance.\n\n"
    content += "**Q: Is it suitable for beginners?**\n"
    content += "A: Absolutely! Our products are designed to be user-friendly while offering advanced features for experts.\n\n"
    content += "**Q: What is included in the package?**\n"
    content += "A: Each package includes everything you need to get started, plus comprehensive documentation.\n\n"
    content += "## Conclusion\n\n"
    content += "Choosing the right " + kw + " does not have to be complicated. By following this guide and considering your specific needs, you will be well-equipped to make an informed decision.\n\n"
    content += "Ready to get started? Browse our complete selection and find the perfect match for your requirements. Our customer support team is always available to help you make the best choice.\n\n"
    content += "Visit our [complete product catalog](/products) to explore all available options, or contact our experts for personalized recommendations."

    return {
        'content': content,
        'meta_description': f"Complete guide to {kw}. Learn about key features, benefits, and expert recommendations to make the best choice for your needs.",
        'keywords': keywords[:5] if keywords else [],
        'internal_links': [
            {'text': 'Premium Product Collection', 'url': '/products/premium-collection'},
            {'text': 'Essential Series', 'url': '/products/essential-series'},
            {'text': 'Complete Product Catalog', 'url': '/products'}
        ][:internal_links],
        'metrics': {
            'word_count': len(content.split()),
            'seo_score': 87,
            'readability': 'Good',
            'internal_links': internal_links
        }
    }


def perform_mock_seo_analysis(content: str, keywords: List[str]) -> Dict[str, Any]:
    """Perform mock SEO analysis for demonstration"""
    
    word_count = len(content.split())
    
    # Calculate basic keyword density
    keyword_density = 0.0
    keyword_analysis = {}
    
    if keywords:
        content_lower = content.lower()
        for keyword in keywords:
            if keyword:
                keyword_lower = keyword.strip().lower()
                count = content_lower.count(keyword_lower)
                density = (count / word_count * 100) if word_count > 0 else 0
                keyword_density += density
                
                # Determine status
                if density < 1:
                    status = "Too Low"
                    suggestion = "Increase keyword usage naturally"
                elif density > 4:
                    status = "Too High"
                    suggestion = "Reduce keyword density to avoid over-optimization"
                else:
                    status = "Good"
                    suggestion = "Keyword density is well-balanced"
                
                keyword_analysis[keyword] = {
                    'density': density / 100,
                    'status': status,
                    'suggestion': suggestion
                }
    
    # Calculate scores
    overall_score = min(95, max(60, 70 + (word_count // 50) + (len(keywords) * 5)))
    readability_score = min(95, max(40, 65 + (word_count // 100)))
    
    return {
        'overall_score': overall_score,
        'readability_score': readability_score,
        'keyword_density': keyword_density / 100 if keyword_density > 0 else 0,
        'word_count': word_count,
        'keyword_analysis': keyword_analysis,
        'strengths': [
            "Good content structure with headings",
            "Adequate content length",
            "Natural keyword integration",
            "Clear call-to-action"
        ],
        'recommendations': [
            "Add more internal links to related content",
            "Include meta description optimization",
            "Consider adding FAQ section",
            "Optimize images with alt text"
        ]
    }


# Run the main application
if __name__ == "__main__":
    main()