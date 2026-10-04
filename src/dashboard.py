import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# ======================== PAGE SETUP ========================
st.set_page_config(
    page_title="E-Commerce | Analytics Studio",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv()

# ======================== STYLING ===========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp {
  background: radial-gradient(circle at 80% 0%, rgba(103,80,255,.13), transparent 28%),
              linear-gradient(135deg,#080f20 0%,#0b1428 55%,#101a31 100%);
  color:#eef2ff;
}
[data-testid="stHeader"] { background:rgba(8,15,32,.88); }
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#111e3a 0%,#0c162c 58%,#111b35 100%);
  border-right:1px solid rgba(151,167,255,.2);
}
[data-testid="stSidebar"] > div:first-child { padding:1.1rem .85rem 1.4rem; }
.brand-card {
  padding:18px 15px 20px; border-radius:20px; margin-bottom:22px;
  background:linear-gradient(145deg,rgba(76,101,237,.25),rgba(128,70,235,.13));
  border:1px solid rgba(160,174,255,.25);
  box-shadow:0 12px 28px rgba(0,0,0,.15);
}
.brand-icon { font-size:2.15rem; line-height:1.2; }
.brand-name { color:#fff; font-size:1.28rem; font-weight:800; letter-spacing:-.5px; margin-top:8px; }
.brand-sub { color:#aebdf1; font-size:.68rem; font-weight:800; letter-spacing:2px; margin-top:5px; }
.sidebar-section { color:#7f92c3; font-size:.68rem; font-weight:800; letter-spacing:2px; margin:16px 0 10px 8px; }
[data-testid="stSidebar"] div[role="radiogroup"] { gap:7px; }
[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding:10px 12px; min-height:42px; border-radius:12px;
  background:rgba(255,255,255,.025); border:1px solid rgba(155,173,235,.08);
  transition:all .18s ease-in-out;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background:rgba(104,91,255,.15); border-color:rgba(139,130,255,.45);
}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background:linear-gradient(100deg,#4c65ed 0%,#7548ed 100%);
  border:1px solid rgba(186,190,255,.55);
  box-shadow:0 7px 20px rgba(73,77,230,.28);
}
[data-testid="stSidebar"] div[role="radiogroup"] label p {
  color:#e9edff !important; font-size:.9rem; font-weight:600;
}
[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display:none; }
.sidebar-status {
  margin-top:20px; padding:14px; border-radius:15px;
  background:linear-gradient(135deg,rgba(45,72,135,.28),rgba(103,65,170,.16));
  border:1px solid rgba(142,157,240,.2);
}
.status-label { color:#aebeff; font-size:.67rem; font-weight:800; letter-spacing:1.5px; }
.status-main { color:#f1f4ff; font-size:.86rem; font-weight:700; margin-top:8px; }
.status-detail { color:#aab9dc; font-size:.76rem; line-height:1.6; margin-top:5px; }
.status-dot { color:#43e6a1; font-weight:800; }
.sidebar-footer { color:#7485b2; font-size:.69rem; text-align:center; margin-top:18px; }
.hero {
  padding:25px 28px; border:1px solid rgba(143,160,235,.2); border-radius:22px;
  background:linear-gradient(110deg,rgba(27,43,78,.92),rgba(30,26,73,.72));
  box-shadow:0 14px 35px rgba(0,0,0,.16); margin-bottom:20px;
}
.hero-kicker { color:#a9b8ff; font-size:.72rem; font-weight:800; letter-spacing:2.2px; margin-bottom:7px; }
.hero h1 { color:#fff; font-size:clamp(1.8rem,3vw,2.65rem); line-height:1.12; letter-spacing:-1.2px; margin:0; font-weight:800; }
.hero h1 span { background:linear-gradient(90deg,#91a8ff,#d09cff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hero p { color:#bac7e8; font-size:.95rem; margin:10px 0 0; }
.section-title { font-size:1.1rem; font-weight:800; color:#f4f6ff; margin:12px 0; }
.metric-card { padding:17px 18px; border-radius:17px; border:1px solid rgba(151,168,235,.2); min-height:112px; box-shadow:0 8px 24px rgba(0,0,0,.13); }
.metric-label { color:#d3dcf8; font-size:.79rem; font-weight:600; margin-bottom:9px; }
.metric-value { color:#fff; font-size:1.65rem; font-weight:800; letter-spacing:-.6px; }
.metric-icon { float:right; font-size:1.4rem; }
.metric-blue { background:linear-gradient(135deg,rgba(35,91,190,.65),rgba(29,49,105,.8)); }
.metric-green { background:linear-gradient(135deg,rgba(0,142,116,.55),rgba(13,65,74,.82)); }
.metric-purple { background:linear-gradient(135deg,rgba(112,52,194,.63),rgba(55,35,106,.85)); }
.metric-pink { background:linear-gradient(135deg,rgba(179,48,92,.6),rgba(88,30,66,.82)); }
.metric-gold { background:linear-gradient(135deg,rgba(175,115,29,.62),rgba(87,62,30,.84)); }
.panel { background:rgba(17,29,51,.78); border:1px solid rgba(143,160,225,.17); border-radius:17px; padding:15px 17px 7px; margin-bottom:15px; }
.stButton > button {
  border-radius:10px; border:1px solid rgba(163,174,255,.32);
  background:linear-gradient(100deg,#4c65ed,#7847e8); color:white; font-weight:700;
}
.stButton > button:hover { border-color:#b6baff; color:white; box-shadow:0 6px 20px rgba(91,82,255,.25); }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
  background-color:#172440; border-color:rgba(149,164,226,.28); border-radius:10px;
}
[data-testid="stDataFrame"] { border:1px solid rgba(143,160,225,.18); border-radius:12px; overflow:hidden; }
.small-note { color:#93a3ca; font-size:.8rem; }
</style>
""", unsafe_allow_html=True)

# ======================== DATABASE ==========================
@st.cache_data(ttl=60)
def load_data():
    required = ["DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError("Missing database settings in .env: " + ", ".join(missing))

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            data = pd.read_sql_query("SELECT * FROM products", conn)
    finally:
        engine.dispose()
    return data

try:
    df = load_data()
except Exception as exc:
    st.error("Could not load products from PostgreSQL.")
    st.code(str(exc))
    st.info("Check that PostgreSQL is running and the DB_* values in your .env file are correct.")
    st.stop()

if df.empty:
    st.warning("The products table is empty. Run `python src/load_product.py` first.")
    st.stop()

# Normalize optional columns and numeric values
for col in ["price", "rating", "stock", "discountPercentage"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
if "brand" not in df.columns:
    df["brand"] = "Unknown"
if "category" not in df.columns:
    df["category"] = "Uncategorized"
if "title" not in df.columns:
    df["title"] = "Untitled product"
if "availabilityStatus" not in df.columns:
    df["availabilityStatus"] = "Unknown"
for col in ["brand", "category", "title", "availabilityStatus"]:
    df[col] = df[col].fillna("Unknown").astype(str)

def money(value):
    return f"${value:,.2f}" if pd.notna(value) else "—"

def chart_theme(fig, height=320):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce5ff", family="Inter, sans-serif"),
        margin=dict(l=12, r=12, t=20, b=12),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(150,170,220,.12)", zerolinecolor="rgba(150,170,220,.12)"),
        yaxis=dict(gridcolor="rgba(150,170,220,.12)", zerolinecolor="rgba(150,170,220,.12)"),
    )
    return fig

# ======================== SIDEBAR ===========================
with st.sidebar:
    st.markdown("""
    <div class="brand-card">
      <div class="brand-icon">🛒</div>
      <div class="brand-name">E-Commerce</div>
      <div class="brand-sub">ANALYTICS STUDIO</div>
    </div>
    <div class="sidebar-section">WORKSPACE NAVIGATION</div>
    """, unsafe_allow_html=True)

    pages = [
        "✨  Dashboard",
        "🛍️  Products",
        "▦  Category Analysis",
        "↗️  Price Analysis",
        "⭐  Rating Analysis",
        "📦  Stock Analysis",
        "🔎  Data Explorer",
        "ⓘ  About",
    ]
    selected_page = st.radio(
        "Navigation",
        pages,
        index=0,
        label_visibility="collapsed",
        key="navigation_page",
    )

    st.markdown(f"""
    <div class="sidebar-status">
      <div class="status-label">DATA CONNECTION</div>
      <div class="status-main">🗄️ DummyJSON → PostgreSQL</div>
      <div class="status-detail"><span class="status-dot">● Connected</span><br>
      {len(df):,} products available<br>
      Database: {os.getenv("DB_NAME", "learning_db")}</div>
    </div>
    <div class="sidebar-status">
      <div class="status-label">CURRENT SESSION</div>
      <div class="status-main">🕒 {datetime.now().strftime("%d %b %Y")}</div>
      <div class="status-detail">Updated at {datetime.now().strftime("%I:%M %p")}<br>Refresh data to reload from PostgreSQL.</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄  Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div class="sidebar-footer">BUILT WITH PYTHON · PANDAS · PLOTLY<br>POSTGRESQL · STREAMLIT</div>', unsafe_allow_html=True)

# ======================== GLOBAL FILTERS ====================
st.markdown("""
<div class="hero">
  <div class="hero-kicker">PRODUCT INTELLIGENCE · LIVE DATA</div>
  <h1>🛍️ E-Commerce <span>Analytics Studio</span></h1>
  <p>Turn product data into clear insights. Explore categories, pricing, ratings, discounts and inventory.</p>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="section-title">🎛️ Explore your dataset</div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([1.15, 1.15, 1.7, 1.15])
    categories = ["All categories"] + sorted(df["category"].dropna().unique().tolist())
    brands = ["All brands"] + sorted(df["brand"].dropna().unique().tolist())
    statuses = ["All statuses"] + sorted(df["availabilityStatus"].dropna().unique().tolist())
    with f1:
        category_filter = st.selectbox("Category", categories)
    with f2:
        brand_filter = st.selectbox("Brand", brands)
    min_price = float(df["price"].min()) if "price" in df and df["price"].notna().any() else 0.0
    max_price = float(df["price"].max()) if "price" in df and df["price"].notna().any() else 1000.0
    if max_price <= min_price:
        max_price = min_price + 1.0
    with f3:
        price_range = st.slider("Price range ($)", min_value=min_price, max_value=max_price,
                                value=(min_price, max_price))
    with f4:
        status_filter = st.selectbox("Availability", statuses)

filtered = df.copy()
if category_filter != "All categories":
    filtered = filtered[filtered["category"] == category_filter]
if brand_filter != "All brands":
    filtered = filtered[filtered["brand"] == brand_filter]
if status_filter != "All statuses":
    filtered = filtered[filtered["availabilityStatus"] == status_filter]
if "price" in filtered.columns:
    filtered = filtered[filtered["price"].between(price_range[0], price_range[1], inclusive="both")]

page = selected_page.split("  ", 1)[-1].strip()

# ======================== METRICS ===========================
total_products = len(filtered)
avg_price = filtered["price"].mean() if "price" in filtered else float("nan")
avg_rating = filtered["rating"].mean() if "rating" in filtered else float("nan")
total_stock = filtered["stock"].sum() if "stock" in filtered else float("nan")
avg_discount = filtered["discountPercentage"].mean() if "discountPercentage" in filtered else float("nan")

if page == "Dashboard":
    st.markdown('<div class="section-title">📊 Your product performance at a glance</div>', unsafe_allow_html=True)
    metrics = [
        ("TOTAL PRODUCTS", f"{total_products:,}", "🛍️", "metric-blue"),
        ("AVERAGE PRICE", money(avg_price), "💳", "metric-green"),
        ("AVERAGE RATING", f"{avg_rating:.2f} / 5" if pd.notna(avg_rating) else "—", "⭐", "metric-purple"),
        ("TOTAL STOCK UNITS", f"{int(total_stock):,}" if pd.notna(total_stock) else "—", "📦", "metric-pink"),
        ("AVERAGE DISCOUNT", f"{avg_discount:.2f}%" if pd.notna(avg_discount) else "—", "🏷️", "metric-gold"),
    ]
    metric_cols = st.columns(5)
    for col, (label, value, icon, color_class) in zip(metric_cols, metrics):
        with col:
            st.markdown(f'<div class="metric-card {color_class}"><div class="metric-icon">{icon}</div><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">📈 Visual insights</div>', unsafe_allow_html=True)
    left, middle, right = st.columns([1.15, 1.25, 1.15])
    with left:
        st.markdown('<div class="panel"><b>Products by category</b></div>', unsafe_allow_html=True)
        cat_counts = filtered["category"].value_counts().rename_axis("Category").reset_index(name="Products")
        fig = px.bar(cat_counts, x="Category", y="Products", color="Category",
                     color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Products")
        st.plotly_chart(chart_theme(fig, 330), use_container_width=True)
    with middle:
        st.markdown('<div class="panel"><b>Price distribution</b></div>', unsafe_allow_html=True)
        if "price" in filtered:
            fig = px.histogram(filtered.dropna(subset=["price"]), x="price", nbins=28,
                               color_discrete_sequence=["#8b5cf6"])
            fig.update_layout(xaxis_title="Price ($)", yaxis_title="Number of products")
            st.plotly_chart(chart_theme(fig, 330), use_container_width=True)
    with right:
        st.markdown('<div class="panel"><b>Average rating by category</b></div>', unsafe_allow_html=True)
        if "rating" in filtered:
            rating_cat = filtered.groupby("category", as_index=False)["rating"].mean().sort_values("rating")
            fig = px.bar(rating_cat, x="rating", y="category", orientation="h",
                         color="rating", color_continuous_scale=["#4776e6", "#c471ed", "#f64f59"])
            fig.update_layout(xaxis_title="Average rating", yaxis_title="", coloraxis_showscale=False,
                              xaxis_range=[0, 5])
            st.plotly_chart(chart_theme(fig, 330), use_container_width=True)

    bottom_left, bottom_right = st.columns([1.35, 1])
    with bottom_left:
        st.markdown('<div class="panel"><b>🏆 Top 10 products by rating</b></div>', unsafe_allow_html=True)
        display_cols = [c for c in ["title", "category", "brand", "price", "rating", "stock"] if c in filtered.columns]
        top = filtered.sort_values("rating", ascending=False) if "rating" in filtered else filtered
        if display_cols:
            st.dataframe(top[display_cols].head(10), use_container_width=True, hide_index=True)
    with bottom_right:
        st.markdown('<div class="panel"><b>🍩 Category share</b></div>', unsafe_allow_html=True)
        share = filtered["category"].value_counts().rename_axis("Category").reset_index(name="Products")
        fig = px.pie(share, names="Category", values="Products", hole=.58,
                     color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_layout(legend=dict(orientation="v", yanchor="middle", y=.5, xanchor="left", x=1))
        st.plotly_chart(chart_theme(fig, 330), use_container_width=True)

    p1, p2 = st.columns(2)
    with p1:
        st.markdown('<div class="panel"><b>💰 Price vs rating</b></div>', unsafe_allow_html=True)
        if "price" in filtered and "rating" in filtered:
            fig = px.scatter(filtered, x="price", y="rating", color="category",
                             hover_name="title", hover_data=["brand", "stock"])
            fig.update_layout(xaxis_title="Price ($)", yaxis_title="Rating")
            st.plotly_chart(chart_theme(fig, 300), use_container_width=True)
    with p2:
        st.markdown('<div class="panel"><b>📦 Stock distribution</b></div>', unsafe_allow_html=True)
        if "stock" in filtered:
            fig = px.histogram(filtered.dropna(subset=["stock"]), x="stock", nbins=25,
                               color_discrete_sequence=["#32c5ff"])
            fig.update_layout(xaxis_title="Stock units", yaxis_title="Number of products")
            st.plotly_chart(chart_theme(fig, 300), use_container_width=True)

elif page == "Products":
    st.markdown('<div class="section-title">🛍️ Product catalogue</div>', unsafe_allow_html=True)
    search = st.text_input("Search product title or brand", placeholder="Try a product name or brand...")
    products_view = filtered.copy()
    if search:
        products_view = products_view[
            products_view["title"].str.contains(search, case=False, na=False)
            | products_view["brand"].str.contains(search, case=False, na=False)
        ]
    st.caption(f"Showing {len(products_view):,} products")
    st.dataframe(products_view, use_container_width=True, hide_index=True)

elif page == "Category Analysis":
    st.markdown('<div class="section-title">▦ Category analysis</div>', unsafe_allow_html=True)
    cat = filtered.groupby("category", as_index=False).agg(
        product_count=("id", "count") if "id" in filtered else ("title", "count"),
        average_price=("price", "mean") if "price" in filtered else ("title", "count"),
        average_rating=("rating", "mean") if "rating" in filtered else ("title", "count"),
    )
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(cat, x="category", y="product_count", color="category",
                     color_discrete_sequence=px.colors.qualitative.Vivid, title="Products per category")
        st.plotly_chart(chart_theme(fig, 380), use_container_width=True)
    with c2:
        if "price" in filtered:
            fig = px.bar(cat, x="category", y="average_price", color="average_price",
                         color_continuous_scale="Purples", title="Average listed price by category")
            st.plotly_chart(chart_theme(fig, 380), use_container_width=True)
    st.dataframe(cat.round(2), use_container_width=True, hide_index=True)

elif page == "Price Analysis":
    st.markdown('<div class="section-title">↗️ Price analysis</div>', unsafe_allow_html=True)
    if "price" in filtered:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(filtered, x="price", nbins=30, title="Price distribution",
                               color_discrete_sequence=["#8b5cf6"])
            st.plotly_chart(chart_theme(fig, 380), use_container_width=True)
        with c2:
            price_cat = filtered.groupby("category", as_index=False)["price"].mean().sort_values("price", ascending=False)
            fig = px.bar(price_cat, x="category", y="price", color="price",
                         color_continuous_scale="Purples", title="Average price by category")
            st.plotly_chart(chart_theme(fig, 380), use_container_width=True)
        st.markdown("#### Highest-priced products")
        st.dataframe(filtered.sort_values("price", ascending=False).head(20), use_container_width=True, hide_index=True)

elif page == "Rating Analysis":
    st.markdown('<div class="section-title">⭐ Rating analysis</div>', unsafe_allow_html=True)
    if "rating" in filtered:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(filtered, x="rating", nbins=20, title="Rating distribution",
                               color_discrete_sequence=["#f4b942"])
            st.plotly_chart(chart_theme(fig, 370), use_container_width=True)
        with c2:
            rate = filtered.groupby("category", as_index=False)["rating"].mean().sort_values("rating", ascending=False)
            fig = px.bar(rate, x="category", y="rating", color="rating",
                         color_continuous_scale=["#4776e6", "#c471ed", "#f64f59"],
                         title="Average rating by category")
            st.plotly_chart(chart_theme(fig, 370), use_container_width=True)
        st.markdown("#### Highest-rated products")
        st.dataframe(filtered.sort_values("rating", ascending=False).head(20), use_container_width=True, hide_index=True)

elif page == "Stock Analysis":
    st.markdown('<div class="section-title">📦 Inventory and stock analysis</div>', unsafe_allow_html=True)
    if "stock" in filtered:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(filtered, x="stock", nbins=28, title="Stock quantity distribution",
                               color_discrete_sequence=["#22c99a"])
            st.plotly_chart(chart_theme(fig, 370), use_container_width=True)
        with c2:
            low = filtered.sort_values("stock").head(15)
            fig = px.bar(low, x="stock", y="title", orientation="h", color="stock",
                         color_continuous_scale="RdYlGn_r", title="Products with lowest stock")
            st.plotly_chart(chart_theme(fig, 370), use_container_width=True)
        st.dataframe(filtered.sort_values("stock").head(25), use_container_width=True, hide_index=True)

elif page == "Data Explorer":
    st.markdown('<div class="section-title">🔎 Data explorer</div>', unsafe_allow_html=True)
    st.write("Inspect the records currently matching the filters above.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data as CSV", data=csv,
                       file_name="ecommerce_products_filtered.csv", mime="text/csv")

elif page == "About":
    st.markdown('<div class="section-title">ⓘ About this project</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="panel">
      <h3>🛒 E-Commerce Analytics Studio</h3>
      <p>This project demonstrates a simple data pipeline and analytics dashboard built with:</p>
      <ul>
        <li><b>Python</b> for data processing</li>
        <li><b>DummyJSON API</b> as a source of sample product catalogue data</li>
        <li><b>PostgreSQL</b> to store product records</li>
        <li><b>Pandas</b> for analysis</li>
        <li><b>Plotly</b> for interactive charts</li>
        <li><b>Streamlit</b> for the dashboard interface</li>
      </ul>
      <p><b>Important:</b> the source contains sample product-catalogue data, not actual orders, revenue, or customer transactions.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="small-note">E-Commerce Analytics Studio · Python + Pandas + Plotly + PostgreSQL · Sample product data</div>', unsafe_allow_html=True)
