import streamlit as st
from datetime import datetime, timedelta, timezone

from data.database import get_active_tickers_db, add_active_ticker_db, remove_active_ticker_db
from data.data_single_asset import get_price_history # Need simple fetch for tape price

def render_theme_toggle():
    if 'is_dark_mode' not in st.session_state:
        st.session_state['is_dark_mode'] = False
    
    btn_icon = "☀️" if st.session_state['is_dark_mode'] else "🌙"
    if st.button(btn_icon, key="theme_toggle_btn", help="Toggle Day/Night Mode"):
        st.session_state['is_dark_mode'] = not st.session_state['is_dark_mode']
        st.rerun()
    return st.session_state['is_dark_mode']

def apply_theme_and_css(is_dark_mode):
    # --- COULEURS ---
    if is_dark_mode:
        c_bg_main = "#0e1117"
        c_bg_card = "#262730"
        c_text    = "#fafafa"
        c_border  = "#414449"
        c_accent  = "#ff4b4b"
        c_float_bg = "#262730"
        c_float_tx = "#ffffff"
        c_tape_bg = "#1f2229"
        c_tape_tx = "#00FF00"
    else:
        c_bg_main = "#ffffff"
        c_bg_card = "#f0f2f6"
        c_text    = "#31333F"
        c_border  = "#d6d6d6"
        c_accent  = "#ff4b4b"
        c_float_bg = "#ffffff"
        c_float_tx = "#31333F"
        c_tape_bg = "#e9ecef"
        c_tape_tx = "#000000"

    css = f"""
    <style>
    :root {{
        --primary-color: {c_accent};
        --background-color: {c_bg_main};
        --secondary-background-color: {c_bg_card};
        --text-color: {c_text};
    }}
    .stApp {{ background-color: {c_bg_main}; color: {c_text}; }}

    /* ELEMENTS FLOTTANTS */
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"], div[data-baseweb="input"] {{
        background-color: {c_bg_card} !important; border: 1px solid {c_border} !important; color: {c_text} !important;
    }}
    div[data-baseweb="select"] span, input {{ color: {c_text} !important; }}
    
    div[data-testid="stPopoverBody"], div[data-baseweb="popover"] > div, ul[data-testid="stSelectboxVirtualDropdown"], li[role="option"] {{
        background-color: {c_float_bg} !important; color: {c_text} !important;
    }}
    li[role="option"]:hover {{ background-color: {c_accent} !important; color: white !important; }}
    div[data-testid="stTooltipContent"] {{ background-color: {c_float_bg} !important; color: {c_float_tx} !important; border: 1px solid {c_border} !important; }}
    div[data-testid="stToast"] {{ background-color: {c_float_bg} !important; border: 1px solid {c_border} !important; color: {c_text} !important; }}
    
    /* BOUTONS */
    button, div[data-testid="stButton"] > button {{
        background-color: {c_bg_card} !important; color: {c_text} !important; border: 1px solid {c_border} !important;
    }}
    button:hover {{
        border-color: {c_accent} !important; color: {c_accent} !important;
    }}

    /* ============================================================
       EFFET TILT (CSS PUR - Version Stable)
       ============================================================ */
    .tilt-card {{
        transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease;
        background-color: rgba(128,128,128,0.05);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .tilt-card:hover {{
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        z-index: 10;
    }}

    /* RESTE DU CSS */
    .big-add-button button {{ background-color: {c_bg_card} !important; border: 2px dashed {c_border} !important; color: gray !important; }}
    .big-add-button button:hover {{ border-color: {c_accent} !important; color: {c_accent} !important; }}
    h1, h2, h3, h4, p, label, span {{ color: {c_text} !important; }}
    .ticker-container {{ background-color: {c_tape_bg}; border-left: 4px solid {c_accent}; border-radius: 4px; padding: 10px 15px; display: flex; flex-wrap: wrap; gap: 20px; align-items: center; }}
    .ticker-item {{ font-family: 'Courier New', monospace; font-weight: bold; color: {c_tape_tx}; }}
    .footer {{ background-color: {c_bg_card}; border-top: 1px solid {c_border}; color: {c_text}; position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; padding: 5px; font-size: 0.75rem; z-index: 9999; }}
    header[data-testid="stHeader"] {{ background-color: {c_bg_main} !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_ticker_tape(prices_dict):
    if not prices_dict:
        html_content = '<div class="ticker-container"><div class="ticker-item">Loading data...</div></div>'
    else:
        items_html = ""
        for ticker, price in prices_dict.items():
            sym = ticker.replace("^", "")
            items_html += f'<div class="ticker-item">{sym}: {price:.2f}</div>'
        html_content = f'<div class="ticker-container">{items_html}</div>'
    st.markdown(html_content, unsafe_allow_html=True)

def render_footer():
    now = datetime.now(timezone.utc) + timedelta(hours=1)
    time_str = now.strftime("%Y-%m-%d %H:%M:%S UTC+1")
    st.markdown(f'<div class="footer">David WANG and Kylian POUTEAU - Last refresh: {time_str}</div>', unsafe_allow_html=True)

def render_ticker_tape_db():
    # 1. Fetch symbols from DB
    tickers = get_active_tickers_db()
    
    # 2. Get LIVE prices (simple last close)
    # Optimization: Fetch in bulk if possible, or loop fast
    prices = {}
    if tickers:
        # Batch fetch via yfinance is faster but keeping structure simple:
        for t in tickers:
            try:
                # Fetch 1 day
                df = get_price_history(t, years=0.1) 
                if not df.empty:
                    prices[t] = df['Close'].iloc[-1]
            except:
                prices[t] = 0.0

    # 3. Render HTML
    if not prices:
        html_content = '<div class="ticker-container"><div class="ticker-item">No active tickers. Add one!</div></div>'
    else:
        items_html = ""
        for ticker, price in prices.items():
            sym = ticker.replace("^", "")
            items_html += f'<div class="ticker-item">{sym}: {price:.2f}</div>'
        html_content = f'<div class="ticker-container">{items_html}</div>'
    st.markdown(html_content, unsafe_allow_html=True)
    return tickers

def render_manage_tickers_ui():
    """UI in sidebar/expander to add/remove."""
    st.markdown("### Manage Tickers")
    
    c1, c2 = st.columns([0.7, 0.3])
    with c1: new_t = st.text_input("Symbol", placeholder="AAPL", label_visibility="collapsed")
    with c2: 
        if st.button("Add"):
            if new_t:
                ok, msg = add_active_ticker_db(new_t.upper())
                if ok: st.success(msg)
                else: st.error(msg)
                st.rerun()

    current = get_active_tickers_db()
    if current:
        st.write("Active:")
        cols = st.columns(3)
        for i, t in enumerate(current):
            if cols[i%3].button(f"❌ {t}", key=f"del_{t}"):
                remove_active_ticker_db(t)
                st.rerun()