"""
UI Components Package for Shopify Platform
Premium Dark Theme - Unified Design System
"""

from .theme import (
    get_custom_css,
    COLORS,
    SPACING,
    RADIUS,
)

from .widgets import (
    # Icon System
    ICONS,
    
    # Header Components
    render_main_header,
    render_page_header,
    render_section_header,
    
    # Metric Cards
    render_metrics_grid,
    render_metric_card,
    render_metric_row,
    
    # Status Components
    render_status_row,
    render_status_card,
    render_badge,
    render_connection_status,
    
    # Card Components
    render_card,
    render_info_card,
    render_feature_card,
    render_feature_grid,
    
    # Empty States
    render_empty_state,
    
    # Activity Feed
    render_activity_item,
    render_activity_feed,
    render_timeline,
    
    # Capability Grid
    render_capability_grid,
    
    # Progress
    render_progress_bar,
    render_progress_card,
    
    # Dividers
    render_divider,
    render_section_divider,
    
    # Data Helpers
    get_status_badge_html,
    
    # Loading States
    render_skeleton,
    render_skeleton_cards,
    
    # Toast
    show_toast,
    
    # Legacy
    render_quick_actions,
)

__all__ = [
    # Theme
    "get_custom_css",
    "COLORS",
    "SPACING",
    "RADIUS",
    
    # Icons
    "ICONS",
    
    # Headers
    "render_main_header",
    "render_page_header",
    "render_section_header",
    
    # Metrics
    "render_metrics_grid",
    "render_metric_card",
    "render_metric_row",
    
    # Status
    "render_status_row",
    "render_status_card",
    "render_badge",
    "render_connection_status",
    
    # Cards
    "render_card",
    "render_info_card",
    "render_feature_card",
    "render_feature_grid",
    
    # Empty
    "render_empty_state",
    
    # Activity
    "render_activity_item",
    "render_activity_feed",
    "render_timeline",
    
    # Capability
    "render_capability_grid",
    
    # Progress
    "render_progress_bar",
    "render_progress_card",
    
    # Dividers
    "render_divider",
    "render_section_divider",
    
    # Data
    "get_status_badge_html",
    
    # Loading
    "render_skeleton",
    "render_skeleton_cards",
    
    # Toast
    "show_toast",
    
    # Legacy
    "render_quick_actions",
]
