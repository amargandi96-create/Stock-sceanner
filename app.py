"""
app.py
------
Dashboard Streamlit untuk Value Investing Stock Screener.
Menampilkan hasil filter secara interaktif dengan sorting, konfigurasi threshold,
dan visualisasi metrik utama.

Cara menjalankan:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import time

from data_fetcher import fetch_multiple_tickers
from screener import ScreenerConfig, apply_filters, get_filter_summary

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Value Investing Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM CSS - Styling profesional dan bersih
# =============================================================================
st.markdown("""
<style>
    /* Base font */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Header utama */
    .main-header {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        opacity: 0.75;
        font-size: 0.95rem;
        margin: 0;
    }

    /* Metric cards */
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e40af;
    }
    .metric-card .label {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.2rem;
    }

    /* Filter summary tags */
    .filter-tag {
        display: inline-block;
        background: #dbeafe;
        color: #1e40af;
        border-radius: 20px;
        padding: 0.2rem 0.75rem;
        font-size: 0.8rem;
        margin: 0.2rem;
        font-weight: 500;
    }

    /* Score badge */
    .score-high { color: #16a34a; font-weight: 700; }
    .score-mid  { color: #d97706; font-weight: 700; }
    .score-low  { color: #dc2626; font-weight: 700; }

    /* Sidebar tweaks */
    [data-testid="stSidebar"] {
        background: #f1f5f9;
    }
    [data-testid="stSidebar"] h2 {
        color: #0f172a;
    }

    /* Table styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Divider */
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 1.5rem 0; }

    /* Footer */
    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DEFAULT TICKER LIST
# =============================================================================
DEFAULT_TICKERS_US = "AAPL, MSFT, GOOGL, AMZN, META, BRK-B, JNJ, KO, WMT, PG, V, JPM, BAC, XOM, CVX"
DEFAULT_TICKERS_ID = "BBCA.JK, BBRI.JK, TLKM.JK, ASII.JK, BMRI.JK, UNVR.JK, ICBP.JK, HMSP.JK"


# =============================================================================
# SIDEBAR - KONFIGURASI & INPUT
# =============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Konfigurasi Screener")
    st.markdown("---")

    # --- Input Ticker ---
    st.markdown("### 📋 Daftar Ticker")
    market_choice = st.radio(
        "Pilih Pasar",
        ["🇺🇸 US Stocks", "🇮🇩 IDX Stocks", "✏️ Custom"],
        index=0
    )

    if market_choice == "🇺🇸 US Stocks":
        ticker_input = DEFAULT_TICKERS_US
    elif market_choice == "🇮🇩 IDX Stocks":
        ticker_input = DEFAULT_TICKERS_ID
    else:
        ticker_input = ""

    ticker_text = st.text_area(
        "Masukkan ticker (pisahkan dengan koma):",
        value=ticker_input,
        height=120,
        help="Contoh: AAPL, MSFT, BBCA.JK"
    )

    st.markdown("---")
    st.markdown("### 🎯 Filter Value Investing")

    # --- Valuation ---
    st.markdown("**Valuasi**")
    max_pe = st.slider("P/E Ratio Maks", 1.0, 50.0, 15.0, 0.5,
                       help="Harga saham dibagi EPS. Lebih rendah = lebih murah.")
    max_pb = st.slider("P/B Ratio Maks", 0.1, 5.0, 1.5, 0.1,
                       help="Harga vs nilai buku aset. Di bawah 1.5 = undervalued.")

    # --- Profitability ---
    st.markdown("**Profitabilitas**")
    min_roe = st.slider("ROE Minimum (%)", 0.0, 50.0, 15.0, 1.0,
                        help="Return on Equity. Semakin tinggi semakin efisien.")

    # --- Financial Health ---
    st.markdown("**Kesehatan Keuangan**")
    max_de = st.slider("Debt/Equity Maks", 0.0, 3.0, 1.0, 0.1,
                       help="Rasio utang vs ekuitas. Di bawah 1 = lebih aman.")

    # --- Optional Filters ---
    with st.expander("🔧 Filter Tambahan (Opsional)"):
        use_mktcap = st.checkbox("Aktifkan filter Market Cap")
        min_mktcap = st.number_input("Market Cap Minimum (Miliar $)", 0.0, 5000.0, 1.0) if use_mktcap else None

        use_div = st.checkbox("Aktifkan filter Dividend Yield")
        min_div = st.slider("Dividend Yield Minimum (%)", 0.0, 10.0, 1.0, 0.1) if use_div else None

        use_growth = st.checkbox("Aktifkan filter Revenue Growth")
        min_growth = st.slider("Revenue Growth Minimum (%)", -20.0, 50.0, 5.0, 1.0) if use_growth else None

    st.markdown("---")
    run_button = st.button("🔍 Jalankan Screener", use_container_width=True, type="primary")


# =============================================================================
# MAIN CONTENT
# =============================================================================
st.markdown("""
<div class="main-header">
    <h1>📊 Value Investing Stock Screener</h1>
    <p>Temukan saham undervalued berdasarkan kriteria fundamental Benjamin Graham & Warren Buffett</p>
</div>
""", unsafe_allow_html=True)


# --- State management ---
if "result_df" not in st.session_state:
    st.session_state.result_df = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None


# =============================================================================
# PROSES SCREENING
# =============================================================================
if run_button:
    tickers = [t.strip().upper() for t in ticker_text.split(",") if t.strip()]

    if not tickers:
        st.error("⚠️ Masukkan setidaknya satu ticker saham.")
        st.stop()

    # Buat konfigurasi dari input sidebar
    config = ScreenerConfig(
        max_pe_ratio       = max_pe,
        max_pb_ratio       = max_pb,
        min_roe            = min_roe,
        max_debt_to_equity = max_de,
        min_market_cap_b   = min_mktcap,
        min_dividend_yield = min_div,
        min_revenue_growth = min_growth,
    )

    # Progress bar saat fetch data
    progress_bar = st.progress(0, text="Mengambil data dari Yahoo Finance...")
    status_placeholder = st.empty()

    with st.spinner(""):
        start_time = time.time()
        raw_df = fetch_multiple_tickers(tickers)
        elapsed = round(time.time() - start_time, 1)

    progress_bar.progress(70, text="Menerapkan filter...")
    time.sleep(0.3)

    result_df = apply_filters(raw_df, config)

    progress_bar.progress(100, text="Selesai!")
    time.sleep(0.3)
    progress_bar.empty()
    status_placeholder.empty()

    st.session_state.raw_df    = raw_df
    st.session_state.result_df = result_df
    st.session_state.config    = config
    st.session_state.elapsed   = elapsed

    st.success(f"✅ Data berhasil diambil dalam {elapsed} detik.")


# =============================================================================
# TAMPILKAN HASIL
# =============================================================================
if st.session_state.result_df is not None:
    raw_df    = st.session_state.raw_df
    result_df = st.session_state.result_df
    config    = st.session_state.config

    # --- Summary Metrics ---
    st.markdown("### 📈 Ringkasan Hasil")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{len(raw_df)}</div>
            <div class="label">Ticker Dianalisa</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{len(result_df)}</div>
            <div class="label">Lolos Filter</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        pass_rate = f"{round(len(result_df)/len(raw_df)*100)}%" if len(raw_df) > 0 else "0%"
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{pass_rate}</div>
            <div class="label">Pass Rate</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        top_score = f"{result_df['Value Score'].max():.1f}" if not result_df.empty and "Value Score" in result_df.columns else "—"
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{top_score}</div>
            <div class="label">Skor Tertinggi</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Active Filter Summary ---
    summary = get_filter_summary(config)
    active_filters = {k: v for k, v in summary.items() if v is not None}
    if active_filters:
        filter_tags = " ".join([
            f'<span class="filter-tag">{k} {v}</span>'
            for k, v in active_filters.items()
        ])
        st.markdown(f"**Filter Aktif:** {filter_tags}", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Hasil Filter ---
    tab1, tab2 = st.tabs(["✅ Saham Lolos Filter", "📋 Semua Data Mentah"])

    with tab1:
        if result_df.empty:
            st.warning("⚠️ Tidak ada saham yang lolos semua filter. Coba longgarkan threshold di sidebar.")
        else:
            st.markdown(f"**{len(result_df)} saham lolos semua kriteria Value Investing**, diurutkan berdasarkan Value Score.")

            # Pilih kolom untuk sorting
            sort_col = st.selectbox(
                "Urutkan berdasarkan:",
                options=["Value Score", "P/E Ratio", "P/B Ratio", "ROE (%)", "Debt/Equity", "Market Cap (B)"],
                index=0
            )
            sort_asc = st.radio("Urutan:", ["Tertinggi dulu ↓", "Terendah dulu ↑"], horizontal=True)
            ascending = sort_asc == "Terendah dulu ↑"

            display_df = result_df.sort_values(sort_col, ascending=ascending) if sort_col in result_df.columns else result_df

            # Format angka untuk tampilan
            fmt_df = display_df.copy()
            for col in ["P/E Ratio", "P/B Ratio", "Debt/Equity"]:
                if col in fmt_df.columns:
                    fmt_df[col] = fmt_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
            for col in ["ROE (%)", "Dividend Yield (%)", "Revenue Growth (%)", "Gross Margin (%)"]:
                if col in fmt_df.columns:
                    fmt_df[col] = fmt_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
            if "Market Cap (B)" in fmt_df.columns:
                fmt_df["Market Cap (B)"] = fmt_df["Market Cap (B)"].apply(lambda x: f"${x:.1f}B" if pd.notna(x) else "—")
            if "Value Score" in fmt_df.columns:
                fmt_df["Value Score"] = fmt_df["Value Score"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")

            st.dataframe(fmt_df, use_container_width=True, height=400)

            # Download CSV
            csv = result_df.to_csv(index=True).encode("utf-8")
            st.download_button(
                label="⬇️ Download Hasil (CSV)",
                data=csv,
                file_name="value_screener_results.csv",
                mime="text/csv"
            )

    with tab2:
        st.markdown("Data mentah semua ticker (sebelum difilter).")
        st.dataframe(raw_df, use_container_width=True, height=400)

    # --- Disclaimer ---
    st.markdown("""
    <div class="footer">
        ⚠️ <strong>Disclaimer:</strong> Informasi ini hanya untuk tujuan edukasi dan bukan merupakan saran investasi.
        Lakukan riset mandiri (DYOR) sebelum membuat keputusan investasi. Data bersumber dari Yahoo Finance.
    </div>
    """, unsafe_allow_html=True)

else:
    # --- Landing state (sebelum run) ---
    st.markdown("### 🚀 Cara Menggunakan")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**1. Pilih Pasar**\nPilih US Stocks, IDX, atau masukkan ticker custom di sidebar.")
    with col2:
        st.info("**2. Atur Threshold**\nSesuaikan filter P/E, P/B, ROE, dan Debt/Equity sesuai strategi Anda.")
    with col3:
        st.info("**3. Jalankan Screener**\nKlik tombol 'Jalankan Screener' dan lihat hasilnya.")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 📚 Panduan Kriteria Value Investing")

    criteria_data = {
        "Metrik":        ["P/E Ratio",       "P/B Ratio",      "ROE (%)",          "Debt/Equity"],
        "Default Maks/Min": ["≤ 15",         "≤ 1.5",          "≥ 15%",            "≤ 1.0"],
        "Artinya":       [
            "Saham diperdagangkan tidak lebih dari 15x earnings",
            "Harga tidak lebih dari 1.5x nilai buku aset",
            "Perusahaan menghasilkan return minimal 15% dari ekuitas",
            "Utang tidak melebihi ekuitas pemegang saham"
        ],
        "Sumber":        ["Benjamin Graham", "Benjamin Graham", "Warren Buffett", "Peter Lynch"],
    }
    st.table(pd.DataFrame(criteria_data))
