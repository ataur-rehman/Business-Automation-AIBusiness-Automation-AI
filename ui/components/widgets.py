"""
Premium UI Components for Shopify Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strict Design Rules:
• All icons: 40×40px containers, 8px radius
• All spacing: 1.5rem (cards), 1rem (elements)
• All radius: 0.75rem (cards), 0.5rem (small)
• All text: 0.8125rem body, 0.75rem caption
• Uniform grid: 4 columns for metrics
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


# =============================================================================
# UNIFIED ICON SYSTEM - Minimal geometric symbols only
# =============================================================================
ICONS = {
    # Core Navigation
    "dashboard": "◐",
    "connect": "◉",
    "products": "▦",
    "orders": "▤",
    "search": "◎",
    "ai": "◈",
    "seo": "◇",
    "logs": "▣",
    "settings": "⚙",
    "sync": "↻",
    
    # Actions
    "check": "✓",
    "close": "✕",
    "add": "+",
    "remove": "−",
    "edit": "◧",
    "view": "◉",
    "arrow_right": "→",
    "arrow_up": "↑",
    "arrow_down": "↓",
    
    # Status
    "success": "●",
    "warning": "●",
    "error": "●",
    "info": "●",
    "active": "●",
    "inactive": "○",
    
    # Data
    "chart": "▥",
    "money": "◈",
    "users": "◔",
    "time": "◔",
    "storage": "▤",
    "api": "◉",
    "star": "★",
    "empty": "○",
}


# =============================================================================
# HEADER COMPONENTS
# =============================================================================

def render_main_header(
    title: str,
    subtitle: str = "",
    stats: Optional[List[Dict[str, str]]] = None,
    show_connection: bool = False,
    is_connected: bool = False
) -> None:
    """Premium header with optional stats row"""
    
    stats_html = ""
    if stats:
        items = ""
        for s in stats:
            stat_value = s.get("value", "0")
            stat_label = s.get("label", "")
            items += f'''<div class="header-stat">
                <div class="header-stat-value">{stat_value}</div>
                <div class="header-stat-label">{stat_label}</div>
            </div>'''
        stats_html = f'<div class="header-stats">{items}</div>'
    
    st.markdown(f'''
    <div class="premium-header">
        <div class="premium-header-title">{title}</div>
        <div class="premium-header-subtitle">{subtitle}</div>
        {stats_html}
    </div>
    ''', unsafe_allow_html=True)


def render_page_header(title: str, icon: str = "◐", description: str = "") -> None:
    """Page title with icon - use at top of each page"""
    st.markdown(f'''
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
        <div style="width: 40px; height: 40px; border-radius: 8px; background: var(--primary-muted); 
             display: flex; align-items: center; justify-content: center; color: var(--primary); font-size: 1rem;">{icon}</div>
        <div>
            <div style="font-size: 1.125rem; font-weight: 700; color: var(--text-primary);">{title}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">{description}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_section_header(title: str, icon: str = "◐", subtitle: str = "") -> None:
    """Section header with consistent styling"""
    st.markdown(f'''
    <div class="section-header">
        <div class="section-icon">{icon}</div>
        <div class="section-title">{title}</div>
    </div>
    ''', unsafe_allow_html=True)


# =============================================================================
# METRIC CARDS - Strict 4-column grid
# =============================================================================

def render_metrics_grid(metrics: List[Dict[str, Any]]) -> None:
    """Render metrics as Streamlit-native cards (no raw HTML in UI)."""

    if not metrics:
        return

    # Render in rows of 4 for consistent layout
    chunk_size = 4
    for start in range(0, len(metrics), chunk_size):
        row = metrics[start : start + chunk_size]
        cols = st.columns(len(row))

        for col, m in zip(cols, row):
            icon = m.get("icon", "◐")
            value = m.get("value", "0")
            label = m.get("label", "")
            change = m.get("change", "")
            color = m.get("color", "primary")

            # Use st.metric delta for changes (keeps a11y + avoids HTML)
            delta = change if change else None

            # Add icon + keep a small semantic class hook via label prefix
            display_label = f"{icon} {label}" if label else str(icon)

            with col:
                # Wrap in a container to allow CSS to style the block consistently
                with st.container():
                    st.metric(label=display_label, value=value, delta=delta)
                    # Store desired semantic color for CSS hooks via data attribute using markdown comment
                    # (No visible output; used only for debugging / future CSS targeting if needed)
                    st.markdown(f"<!-- metric-color:{color} -->", unsafe_allow_html=True)


def render_metric_card(
    value: Union[str, int, float],
    label: str,
    icon: str = "◐",
    icon_color: str = "primary",
    change: Optional[str] = None,
    change_positive: bool = True
) -> None:
    """Single metric card - use render_metrics_grid for multiple"""
    render_metrics_grid([{
        "value": value,
        "label": label,
        "icon": icon,
        "color": icon_color,
        "change": change if change else ""
    }])


def render_metric_row(metrics: List[Dict[str, Any]]) -> None:
    """Render metrics in a row - alias for render_metrics_grid"""
    render_metrics_grid(metrics)


# =============================================================================
# STATUS COMPONENTS
# =============================================================================

def render_status_row(text: str, status: str = "info", meta: str = "") -> None:
    """Single status row with dot indicator"""
    st.markdown(f'''
    <div class="status-row">
        <div class="status-dot {status}"></div>
        <div class="status-text">{text}</div>
        <div class="status-meta">{meta}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_status_card(message: str, status: str = "info", icon: Optional[str] = None) -> None:
    """Status card - alias for render_status_row"""
    render_status_row(text=message, status=status)


def render_connection_status(is_connected: bool, store_name: str = "") -> None:
    """Connection status badge"""
    if is_connected:
        text = f"Connected{' • ' + store_name if store_name else ''}"
        render_status_row(text=text, status="success")
    else:
        render_status_row(text="Not Connected", status="error")


def render_badge(text: str, variant: str = "primary") -> str:
    """Return inline badge HTML"""
    return f'<span style="color: var(--{variant}); font-weight: 500; font-size: 0.75rem;">{text}</span>'


# =============================================================================
# CARD COMPONENTS
# =============================================================================

def render_card(title: str, content: str = "", icon: str = "◐") -> None:
    """Uniform card with title and content"""
    st.markdown(f'''
    <div class="card">
        <div class="card-header">
            <div class="card-icon">{icon}</div>
            <div class="card-title">{title}</div>
        </div>
        <div class="card-content">{content}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_info_card(title: str, items: List[Dict[str, str]], icon: str = "◐") -> None:
    """Card with key-value pairs"""
    rows = ""
    for i in items:
        item_label = i.get("label", "")
        item_value = i.get("value", "")
        rows += f'''<div style="display: flex; justify-content: space-between; padding: 0.75rem 0; 
             border-bottom: 1px solid var(--surface-3);">
            <span style="color: var(--text-muted); font-size: 0.8125rem;">{item_label}</span>
            <span style="color: var(--text-primary); font-weight: 500; font-size: 0.8125rem;">{item_value}</span>
        </div>'''
    
    st.markdown(f'''
    <div class="card">
        <div class="card-header">
            <div class="card-icon">{icon}</div>
            <div class="card-title">{title}</div>
        </div>
        {rows}
    </div>
    ''', unsafe_allow_html=True)


def render_feature_card(title: str, description: str, icon: str = "◐") -> None:
    """Feature highlight card"""
    st.markdown(f'''
    <div class="card" style="text-align: center; padding: 1.5rem;">
        <div style="width: 40px; height: 40px; border-radius: 8px; background: var(--primary-muted); 
             display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; 
             color: var(--primary); font-size: 1rem;">{icon}</div>
        <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 0.8125rem; color: var(--text-muted); line-height: 1.5;">{description}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_feature_grid(features: List[Dict[str, str]], columns: int = 3) -> None:
    """Render uniform feature cards grid"""
    cards = "".join([
        f'''<div class="card" style="text-align: center; padding: 1.5rem;">
            <div style="width: 40px; height: 40px; border-radius: 8px; background: var(--primary-muted); 
                 display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; 
                 color: var(--primary); font-size: 1rem;">{f.get("icon", "◐")}</div>
            <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">{f.get("title", "")}</div>
            <div style="font-size: 0.8125rem; color: var(--text-muted); line-height: 1.5;">{f.get("description", "")}</div>
        </div>'''
        for f in features
    ])
    
    st.markdown(f'''
    <div style="display: grid; grid-template-columns: repeat({columns}, 1fr); gap: 1rem;">
        {cards}
    </div>
    ''', unsafe_allow_html=True)


# =============================================================================
# EMPTY STATE
# =============================================================================

def render_empty_state(title: str, message: str, icon: str = "○", action_text: Optional[str] = None) -> bool:
    """Uniform empty state display"""
    st.markdown(f'''
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{message}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    if action_text:
        return st.button(action_text, type="primary", use_container_width=True)
    return False


# =============================================================================
# ACTIVITY FEED
# =============================================================================

def render_activity_item(title: str, meta: str, status: str = "success") -> None:
    """Single activity item"""
    icon = "✓" if status == "success" else "✕"
    st.markdown(f'''
    <div class="activity-item">
        <div class="activity-icon {status}">{icon}</div>
        <div class="activity-content">
            <div class="activity-title">{title}</div>
            <div class="activity-meta">{meta}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_activity_feed(activities: List[Dict[str, Any]], limit: int = 5) -> None:
    """Render activity feed list"""
    st.markdown('<div class="card" style="padding: 0.75rem 1.5rem;">', unsafe_allow_html=True)
    
    for activity in activities[:limit]:
        timestamp = activity.get("timestamp", datetime.now())
        time_str = timestamp.strftime("%H:%M") if isinstance(timestamp, datetime) else str(timestamp)
        
        status = "success" if activity.get("success", False) else "error"
        title = activity.get("test", activity.get("event", "Activity"))
        details = activity.get("details", "")
        
        meta = time_str + (f" • {details[:30]}..." if details else "")
        render_activity_item(title=title, meta=meta, status=status)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_timeline(events: List[Dict[str, Any]]) -> None:
    """Render timeline - alias for activity feed"""
    activities = [{
        "test": e.get("content", ""),
        "timestamp": e.get("time", ""),
        "success": e.get("status", "") == "success"
    } for e in events]
    render_activity_feed(activities)


# =============================================================================
# CAPABILITY GRID
# =============================================================================

def render_capability_grid(capabilities: Dict[str, bool]) -> None:
    """Uniform capability indicator grid"""
    labels = {
        "product_read": "Read Products",
        "product_write": "Write Products",
        "order_read": "Read Orders",
        "order_write": "Write Orders",
        "customer_read": "Read Customers",
        "customer_write": "Write Customers",
        "content_write": "Write Content",
        "inventory_read": "Read Inventory",
        "inventory_write": "Write Inventory",
        "fulfillment_write": "Fulfillment",
    }
    
    items = ""
    for key, enabled in capabilities.items():
        label = labels.get(key, key.replace("_", " ").title())
        icon = "✓" if enabled else "✕"
        state = "enabled" if enabled else "disabled"
        
        items += f'''
        <div class="capability-item {state}">
            <span>{icon}</span>
            <span>{label}</span>
        </div>
        '''
    
    st.markdown(f'<div class="capability-grid">{items}</div>', unsafe_allow_html=True)


# =============================================================================
# PROGRESS INDICATORS
# =============================================================================

def render_progress_bar(label: str, current: int, total: int) -> None:
    """Uniform progress bar"""
    pct = (current / total * 100) if total > 0 else 0
    
    st.markdown(f'''
    <div style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-size: 0.8125rem; color: var(--text-secondary);">{label}</span>
            <span style="font-size: 0.8125rem; color: var(--text-primary); font-weight: 500;">{current}/{total}</span>
        </div>
        <div class="progress-container">
            <div class="progress-bar" style="width: {pct}%;"></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_progress_card(title: str, current: int, total: int, icon: str = "◐") -> None:
    """Progress card - alias for render_progress_bar"""
    render_progress_bar(title, current, total)


# =============================================================================
# DIVIDERS
# =============================================================================

def render_divider() -> None:
    """Consistent divider line"""
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


def render_section_divider() -> None:
    """Alias for render_divider"""
    render_divider()


# =============================================================================
# DATA DISPLAY HELPERS
# =============================================================================

def get_status_badge_html(status: str) -> str:
    """Get inline status badge HTML"""
    status_map = {
        "active": ("● Active", "success"),
        "draft": ("● Draft", "warning"),
        "archived": ("○ Archived", "error"),
        "paid": ("● Paid", "success"),
        "pending": ("● Pending", "warning"),
        "cancelled": ("○ Cancelled", "error"),
        "refunded": ("↩ Refunded", "info"),
        "fulfilled": ("● Fulfilled", "success"),
        "unfulfilled": ("○ Unfulfilled", "warning"),
        "partial": ("◐ Partial", "info"),
    }
    
    text, color = status_map.get(status.lower(), (status.title(), "info"))
    return f'<span style="color: var(--{color}); font-size: 0.75rem; font-weight: 500;">{text}</span>'


# =============================================================================
# LOADING STATES
# =============================================================================

def render_skeleton(height: str = "1rem", width: str = "100%") -> None:
    """Skeleton loading placeholder"""
    st.markdown(f'''
    <div style="height: {height}; width: {width}; background: var(--surface-2); 
         border-radius: 0.5rem; animation: pulse 1.5s infinite;"></div>
    ''', unsafe_allow_html=True)


def render_skeleton_cards(count: int = 4) -> None:
    """Skeleton metric cards"""
    cols = st.columns(count)
    for col in cols:
        with col:
            st.markdown('''
            <div class="metric-card">
                <div style="width: 40px; height: 40px; background: var(--surface-2); 
                     border-radius: 8px; margin-bottom: 1rem;"></div>
                <div style="width: 60%; height: 1.5rem; background: var(--surface-2); 
                     border-radius: 4px; margin-bottom: 0.5rem;"></div>
                <div style="width: 80%; height: 0.75rem; background: var(--surface-2); 
                     border-radius: 4px;"></div>
            </div>
            ''', unsafe_allow_html=True)


# =============================================================================
# TOAST NOTIFICATIONS
# =============================================================================

def show_toast(message: str, type: str = "info") -> None:
    """Show toast using Streamlit native"""
    if type == "success":
        st.success(message)
    elif type == "error":
        st.error(message)
    elif type == "warning":
        st.warning(message)
    else:
        st.info(message)


# =============================================================================
# DEPRECATED / LEGACY ALIASES
# =============================================================================

def render_quick_actions(actions: List[Dict[str, str]]) -> None:
    """Deprecated - use native buttons"""
    pass
