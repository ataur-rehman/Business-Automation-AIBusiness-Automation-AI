"""
Premium Theme System for Shopify Platform
Professional white theme with sophisticated contrast colors.
"""

# =============================================================================
# Color Palette - Premium White Theme with Professional Blue
# =============================================================================
COLORS = {
    # Primary Brand Colors - Deep Professional Blue
    "primary": "#1E40AF",           # Deep Blue
    "primary_hover": "#1E3A8A",
    "primary_muted": "#1E40AF15",
    
    # Surface Colors (White Theme)
    "surface_0": "#FFFFFF",         # White - Page bg
    "surface_1": "#F9FAFB",         # Light gray - Cards
    "surface_2": "#F3F4F6",         # Elevated cards
    "surface_3": "#E5E7EB",         # Borders, dividers
    
    # Text Colors
    "text_primary": "#111827",
    "text_secondary": "#4B5563",
    "text_muted": "#9CA3AF",
    
    # Semantic Colors
    "success": "#059669",
    "success_muted": "#05966915",
    "warning": "#D97706",
    "warning_muted": "#D9770615",
    "error": "#DC2626",
    "error_muted": "#DC262615",
    "info": "#2563EB",
    "info_muted": "#2563EB15",
}

# =============================================================================
# Design Tokens - Strict Consistency
# =============================================================================
SPACING = {
    "xs": "0.5rem",     # 8px
    "sm": "0.75rem",    # 12px
    "md": "1rem",       # 16px
    "lg": "1.5rem",     # 24px
    "xl": "2rem",       # 32px
    "2xl": "3rem",      # 48px
}

RADIUS = {
    "sm": "0.5rem",     # 8px
    "md": "0.75rem",    # 12px
    "lg": "1rem",       # 16px
}

FONTS = {
    "primary": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    "mono": "'JetBrains Mono', monospace",
}


def get_custom_css() -> str:
    """Generate premium white theme CSS with professional contrast"""
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ===========================================
       CSS Variables - White Theme
       =========================================== */
    :root {{
        --primary: {COLORS['primary']};
        --primary-hover: {COLORS['primary_hover']};
        --primary-muted: {COLORS['primary_muted']};
        --surface-0: {COLORS['surface_0']};
        --surface-1: {COLORS['surface_1']};
        --surface-2: {COLORS['surface_2']};
        --surface-3: {COLORS['surface_3']};
        --text-primary: {COLORS['text_primary']};
        --text-secondary: {COLORS['text_secondary']};
        --text-muted: {COLORS['text_muted']};
        --success: {COLORS['success']};
        --warning: {COLORS['warning']};
        --error: {COLORS['error']};
        --info: {COLORS['info']};
        --radius: {RADIUS['md']};
        --spacing: {SPACING['lg']};
    }}
    
    /* ===========================================
       Global Reset & Base - White Theme
       =========================================== */
    .stApp {{
        background: var(--surface-0);
        font-family: {FONTS['primary']};
    }}
    
    .stApp > header {{
        background: transparent;
    }}
    
    .main .block-container {{
        padding: 2rem 3rem;
        max-width: 1400px;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header[data-testid="stHeader"] {{
        display: none;
    }}
    
    /* Force Streamlit text to be visible on white background */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div,
    .stText, .element-container, [data-testid="stMarkdownContainer"],
    .stButton button, label, .stTextInput label, .stSelectbox label {{
        color: var(--text-primary) !important;
    }}
    
    /* Streamlit native components - white theme overrides */
    .stButton > button {{
        background-color: var(--primary) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }}
    
    /* Secondary buttons - lighter style */
    .stButton > button[kind="secondary"] {{
        background-color: #6B7280 !important;
        color: #FFFFFF !important;
        border: 1px solid #9CA3AF !important;
    }}
    
    .stButton > button:hover {{
        background-color: var(--primary-hover) !important;
        color: #FFFFFF !important;
    }}
    
    .stButton > button[kind="secondary"]:hover {{
        background-color: #4B5563 !important;
        color: #FFFFFF !important;
    }}
    
    /* Ultra-aggressive button text fix - target everything */
    .stButton button,
    .stButton button *,
    .stButton button span, 
    .stButton button div,
    .stButton button p,
    button[data-testid="baseButton-primary"],
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] *,
    button[data-testid="baseButton-secondary"] *,
    [data-testid="stButton"] button,
    [data-testid="stButton"] button * {{
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        background: transparent !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}
    
    /* Button background - keep it blue */
    .stButton > button,
    button[data-testid="baseButton-primary"],
    [data-testid="stButton"] > button {{
        background-color: var(--primary) !important;
        background: var(--primary) !important;
    }}
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {{
        background: white !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--surface-3) !important;
    }}
    
    /* Password visibility toggle button fix */
    button[kind="icon"], button[title*="Show"], button[title*="Hide"] {{
        background: transparent !important;
        color: var(--text-secondary) !important;
        border: none !important;
        padding: 0.25rem !important;
        min-width: auto !important;
        width: auto !important;
    }}
    
    button[kind="icon"]:hover {{
        color: var(--text-primary) !important;
        background: var(--surface-2) !important;
    }}
    
    button[kind="icon"] svg {{
        fill: var(--text-secondary) !important;
        stroke: var(--text-secondary) !important;
        color: var(--text-secondary) !important;
        width: 20px !important;
        height: 20px !important;
        display: block !important;
    }}
    
    button[kind="icon"]:hover svg {{
        fill: var(--text-primary) !important;
        stroke: var(--text-primary) !important;
    }}
    
    /* Fix for Streamlit's eye icon specifically */
    [data-testid="stTextInput"] button[kind="icon"] {{
        background: white !important;
        border: 1px solid var(--surface-3) !important;
        border-radius: 4px !important;
    }}

    /* ===========================================
       Streamlit Metric Cards (native)
       =========================================== */
    div[data-testid="stMetric"] {{
        background: var(--surface-1);
        border: 1px solid var(--surface-3);
        border-radius: var(--radius);
        padding: 1.25rem 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }}

    div[data-testid="stMetric"]:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.10), 0 4px 6px -2px rgba(0, 0, 0, 0.06);
        transform: translateY(-1px);
        transition: box-shadow 160ms ease, transform 160ms ease;
    }}

    div[data-testid="stMetricLabel"] p {{
        color: var(--text-secondary) !important;
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }}

    div[data-testid="stMetricDelta"] {{
        color: var(--text-secondary) !important;
        font-size: 0.75rem !important;
    }}
    
    /* Professional shadows for depth */
    .shadow-sm {{ box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }}
    .shadow {{ box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); }}
    .shadow-md {{ box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }}
    .shadow-lg {{ box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }}
    
    /* ===========================================
       Typography - Consistent Hierarchy
       =========================================== */
    h1, h2, h3, h4, h5, h6, p, span, div {{
        font-family: {FONTS['primary']};
    }}
    
    /* ===========================================
       Premium Header - White Theme
       =========================================== */
    .premium-header {{
        background: var(--surface-1);
        border: 1px solid var(--surface-3);
        border-radius: var(--radius);
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }}
    
    .premium-header-title {{
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }}
    
    .premium-header-subtitle {{
        font-size: 0.9375rem;
        color: var(--text-secondary);
        margin: 0;
    }}
    
    .header-stats {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-top: 1.5rem;
    }}
    
    .header-stat {{
        background: var(--surface-2);
        padding: 1rem;
        border-radius: calc(var(--radius) - 4px);
        text-align: center;
    }}
    
    .header-stat-value {{
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }}
    
    .header-stat-label {{
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }}
    
    /* ===========================================
       Metric Cards - Uniform Grid
       =========================================== */
    .metrics-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }}
    
    .metric-card {{
        background: var(--surface-1);
        border: 1px solid var(--surface-3);
        border-radius: var(--radius);
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        transition: all 0.2s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-2px);
        border-color: var(--primary);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}
    
    .metric-card-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    
    .metric-icon {{
        width: 40px;
        height: 40px;
        border-radius: calc(var(--radius) - 4px);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.125rem;
    }}
    
    .metric-icon.primary {{ background: var(--primary-muted); }}
    .metric-icon.success {{ background: {COLORS['success_muted']}; }}
    .metric-icon.warning {{ background: {COLORS['warning_muted']}; }}
    .metric-icon.error {{ background: {COLORS['error_muted']}; }}
    .metric-icon.info {{ background: {COLORS['info_muted']}; }}
    
    .metric-badge {{
        font-size: 0.6875rem;
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    
    .metric-badge.up {{
        background: {COLORS['success_muted']};
        color: var(--success);
    }}
    
    .metric-badge.down {{
        background: {COLORS['error_muted']};
        color: var(--error);
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
    }}
    
    .metric-label {{
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text-muted);
    }}
    
    /* ===========================================
       Section Headers - Consistent
       =========================================== */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--surface-3);
    }}
    
    .section-icon {{
        width: 32px;
        height: 32px;
        border-radius: calc(var(--radius) - 4px);
        background: var(--primary-muted);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.875rem;
    }}
    
    .section-title {{
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }}
    
    .section-subtitle {{
        font-size: 0.8125rem;
        color: var(--text-muted);
        margin-left: auto;
    }}
    
    /* ===========================================
       Cards - Uniform Styling with Shadows
       =========================================== */
    .card {{
        background: var(--surface-1);
        border: 1px solid var(--surface-3);
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        transition: all 0.2s ease;
    }}
    
    .card:hover {{
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}
    
    .card-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }}
    
    .card-icon {{
        width: 36px;
        height: 36px;
        border-radius: calc(var(--radius) - 4px);
        background: var(--primary-muted);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }}
    
    .card-title {{
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--text-primary);
    }}
    
    .card-content {{
        font-size: 0.875rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }}
    
    /* ===========================================
       Status Indicators - Uniform
       =========================================== */
    .status-row {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.875rem 1rem;
        background: var(--surface-2);
        border-radius: calc(var(--radius) - 4px);
        margin-bottom: 0.5rem;
    }}
    
    .status-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }}
    
    .status-dot.success {{ background: var(--success); }}
    .status-dot.warning {{ background: var(--warning); }}
    .status-dot.error {{ background: var(--error); }}
    .status-dot.info {{ background: var(--info); }}
    
    .status-text {{
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
        flex: 1;
    }}
    
    .status-meta {{
        font-size: 0.75rem;
        color: var(--text-muted);
    }}
    
    /* ===========================================
       Buttons - Consistent Styling
       =========================================== */
    .stButton > button {{
        font-family: {FONTS['primary']};
        font-weight: 600;
        font-size: 0.875rem;
        border-radius: calc(var(--radius) - 4px);
        padding: 0.625rem 1rem;
        transition: all 0.15s ease;
        border: none;
    }}
    
    .stButton > button[kind="primary"] {{
        background: var(--primary);
        color: white;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background: var(--primary-hover);
    }}
    
    .stButton > button[kind="secondary"] {{
        background: var(--surface-2);
        color: var(--text-secondary);
        border: 1px solid var(--surface-3);
    }}
    
    /* ===========================================
       Inputs - Uniform Styling
       =========================================== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {{
        font-family: {FONTS['primary']};
        background: var(--surface-2);
        border: 1px solid var(--surface-3);
        border-radius: calc(var(--radius) - 4px);
        color: var(--text-primary);
        font-size: 0.875rem;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--primary);
        box-shadow: 0 0 0 2px var(--primary-muted);
    }}
    
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {{
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 0.8125rem;
    }}
    
    /* ===========================================
       Tabs - Premium Styling
       =========================================== */
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--surface-1);
        border: 1px solid var(--surface-3);
        border-radius: var(--radius);
        padding: 0.375rem;
        gap: 0.25rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        font-family: {FONTS['primary']};
        font-weight: 500;
        font-size: 0.8125rem;
        border-radius: calc(var(--radius) - 4px);
        padding: 0.625rem 1rem;
        color: var(--text-muted);
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--text-secondary);
        background: var(--surface-2);
    }}
    
    .stTabs [aria-selected="true"] {{
        background: var(--primary);
        color: white;
    }}
    
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none;
    }}
    
    .stTabs [data-baseweb="tab-border"] {{
        display: none;
    }}
    
    /* ===========================================
       Sidebar - Premium
       =========================================== */
    section[data-testid="stSidebar"] {{
        background: var(--surface-1);
        border-right: 1px solid var(--surface-3);
    }}
    
    section[data-testid="stSidebar"] .block-container {{
        padding: 1.5rem;
    }}
    
    .sidebar-brand {{
        padding: 1rem;
        background: var(--surface-2);
        border-radius: var(--radius);
        margin-bottom: 1.5rem;
        text-align: center;
    }}
    
    .sidebar-brand-icon {{
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }}
    
    .sidebar-brand-name {{
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary);
    }}
    
    .sidebar-brand-desc {{
        font-size: 0.75rem;
        color: var(--text-muted);
    }}
    
    /* ===========================================
       Expanders - Uniform
       =========================================== */
    .streamlit-expanderHeader {{
        font-family: {FONTS['primary']};
        font-weight: 600;
        font-size: 0.875rem;
        background: var(--surface-2);
        border: 1px solid var(--surface-3);
        border-radius: var(--radius);
        color: var(--text-primary);
    }}
    
    .streamlit-expanderContent {{
        background: var(--surface-1);
        border: 1px solid var(--surface-3);
        border-top: none;
        border-radius: 0 0 var(--radius) var(--radius);
    }}
    
    /* ===========================================
       Data Tables - Premium
       =========================================== */
    .stDataFrame {{
        border: 1px solid var(--surface-3);
        border-radius: var(--radius);
        overflow: hidden;
    }}
    
    .stDataFrame [data-testid="stDataFrameResizable"] {{
        background: var(--surface-1);
    }}
    
    /* ===========================================
       Metrics (Native) - Override
       =========================================== */
    [data-testid="stMetricValue"] {{
        font-family: {FONTS['primary']};
        font-weight: 700;
        color: var(--text-primary);
    }}
    
    [data-testid="stMetricLabel"] {{
        font-family: {FONTS['primary']};
        color: var(--text-muted);
        font-weight: 500;
    }}
    
    /* ===========================================
       Dividers
       =========================================== */
    .divider {{
        height: 1px;
        background: var(--surface-3);
        margin: 2rem 0;
    }}
    
    /* ===========================================
       Empty State
       =========================================== */
    .empty-state {{
        text-align: center;
        padding: 3rem 2rem;
        background: var(--surface-1);
        border: 1px dashed var(--surface-3);
        border-radius: var(--radius);
    }}
    
    .empty-state-icon {{
        width: 64px;
        height: 64px;
        border-radius: var(--radius);
        background: var(--surface-2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin: 0 auto 1rem auto;
    }}
    
    .empty-state-title {{
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }}
    
    .empty-state-text {{
        font-size: 0.875rem;
        color: var(--text-muted);
    }}
    
    /* ===========================================
       Activity List
       =========================================== */
    .activity-item {{
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.875rem 0;
        border-bottom: 1px solid var(--surface-3);
    }}
    
    .activity-item:last-child {{
        border-bottom: none;
    }}
    
    .activity-icon {{
        width: 32px;
        height: 32px;
        border-radius: calc(var(--radius) - 4px);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.875rem;
        flex-shrink: 0;
    }}
    
    .activity-icon.success {{ background: {COLORS['success_muted']}; }}
    .activity-icon.error {{ background: {COLORS['error_muted']}; }}
    
    .activity-content {{
        flex: 1;
        min-width: 0;
    }}
    
    .activity-title {{
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
    }}
    
    .activity-meta {{
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.125rem;
    }}
    
    /* ===========================================
       Capability Grid
       =========================================== */
    .capability-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.5rem;
    }}
    
    .capability-item {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.625rem 0.75rem;
        background: var(--surface-2);
        border-radius: calc(var(--radius) - 4px);
        font-size: 0.8125rem;
        color: var(--text-secondary);
    }}
    
    .capability-item.enabled {{
        color: var(--success);
    }}
    
    .capability-item.disabled {{
        color: var(--text-muted);
    }}
    
    /* ===========================================
       Progress Bar
       =========================================== */
    .progress-container {{
        background: var(--surface-2);
        border-radius: 9999px;
        height: 6px;
        overflow: hidden;
    }}
    
    .progress-bar {{
        height: 100%;
        background: var(--primary);
        border-radius: 9999px;
        transition: width 0.3s ease;
    }}
    
    /* ===========================================
       Responsive Grid
       =========================================== */
    @media (max-width: 1024px) {{
        .metrics-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
        
        .header-stats {{
            grid-template-columns: repeat(2, 1fr);
        }}
    }}
    
    @media (max-width: 640px) {{
        .metrics-grid {{
            grid-template-columns: 1fr;
        }}
        
        .header-stats {{
            grid-template-columns: 1fr;
        }}
        
        .main .block-container {{
            padding: 1rem;
        }}
    }}
</style>
"""


def get_dark_mode_css() -> str:
    """Additional dark mode styles (already dark by default)"""
    return ""

