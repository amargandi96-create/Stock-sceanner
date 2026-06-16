"""
screener.py
-----------
Modul inti untuk logika screening saham berbasis kriteria Value Investing.
Semua ambang batas (threshold) filter dapat dikonfigurasi melalui SCREENER_CONFIG
tanpa harus menyentuh logika utama.
"""

import pandas as pd
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION - Ubah nilai di sini untuk mengatur threshold filter
# =============================================================================
@dataclass
class ScreenerConfig:
    """
    Konfigurasi terpusat untuk semua filter Value Investing.
    Ubah nilai di sini tanpa perlu menyentuh logika screening.

    Semua field bersifat Optional — jika None, filter tersebut dinonaktifkan.
    """
    # --- Valuation Filters ---
    max_pe_ratio:        Optional[float] = 15.0    # P/E Ratio maksimum
    max_pb_ratio:        Optional[float] = 1.5     # P/B Ratio maksimum

    # --- Profitability Filters ---
    min_roe:             Optional[float] = 15.0    # ROE minimum (dalam %)

    # --- Financial Health Filters ---
    max_debt_to_equity:  Optional[float] = 1.0     # Debt/Equity maksimum

    # --- Size Filters (opsional) ---
    min_market_cap_b:    Optional[float] = None    # Market Cap minimum (Miliar USD), None = tidak difilter

    # --- Dividend Filter (opsional) ---
    min_dividend_yield:  Optional[float] = None    # Dividend Yield minimum (%), None = tidak difilter

    # --- Growth Filter (opsional) ---
    min_revenue_growth:  Optional[float] = None    # Revenue Growth minimum (%), None = tidak difilter


# Instance default yang digunakan oleh fungsi screening
DEFAULT_CONFIG = ScreenerConfig()


# =============================================================================
# SCORING ENGINE - Memberikan skor komposit untuk ranking saham
# =============================================================================

def compute_value_score(row: pd.Series) -> float:
    """
    Menghitung skor komposit Value Investing untuk satu baris data saham.
    Skor lebih tinggi = saham lebih menarik secara value.

    Formula:
        - P/E rendah  → skor tinggi
        - P/B rendah  → skor tinggi
        - ROE tinggi  → skor tinggi
        - D/E rendah  → skor tinggi

    Parameters
    ----------
    row : pd.Series
        Satu baris dari DataFrame hasil fetch.

    Returns
    -------
    float
        Skor komposit (0–100 scale approximation).
    """
    score = 0.0

    try:
        pe  = row.get("P/E Ratio")
        pb  = row.get("P/B Ratio")
        roe = row.get("ROE (%)")
        de  = row.get("Debt/Equity")

        # P/E: semakin rendah semakin baik (cap di 50 untuk normalisasi)
        if pe and pe > 0:
            score += max(0, (50 - pe) / 50) * 25

        # P/B: semakin rendah semakin baik (cap di 5)
        if pb and pb > 0:
            score += max(0, (5 - pb) / 5) * 25

        # ROE: semakin tinggi semakin baik (cap di 50%)
        if roe is not None:
            score += min(roe / 50, 1.0) * 30

        # D/E: semakin rendah semakin baik (cap di 3)
        if de is not None:
            score += max(0, (3 - de) / 3) * 20

    except Exception as e:
        logger.debug(f"Tidak bisa menghitung skor untuk {row.get('Ticker', '?')}: {e}")

    return round(score, 2)


# =============================================================================
# MAIN SCREENING LOGIC
# =============================================================================

def apply_filters(df: pd.DataFrame, config: ScreenerConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """
    Memfilter DataFrame saham berdasarkan kriteria Value Investing dari config.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame hasil dari data_fetcher.fetch_multiple_tickers()
    config : ScreenerConfig
        Objek konfigurasi berisi threshold filter.

    Returns
    -------
    pd.DataFrame
        DataFrame yang sudah difilter, diurutkan berdasarkan Value Score (tertinggi dulu).
    """
    if df.empty:
        logger.warning("DataFrame kosong, tidak ada yang bisa difilter.")
        return df

    filtered = df.copy()
    initial_count = len(filtered)

    # Definisikan semua filter yang akan diterapkan
    filter_rules = [
        ("P/E Ratio",      config.max_pe_ratio,        "<="),
        ("P/B Ratio",      config.max_pb_ratio,        "<="),
        ("ROE (%)",        config.min_roe,             ">="),
        ("Debt/Equity",    config.max_debt_to_equity,  "<="),
        ("Market Cap (B)", config.min_market_cap_b,    ">="),
        ("Dividend Yield (%)", config.min_dividend_yield, ">="),
        ("Revenue Growth (%)", config.min_revenue_growth, ">="),
    ]

    for col, threshold, operator in filter_rules:
        if threshold is None:
            continue  # Filter dinonaktifkan
        if col not in filtered.columns:
            logger.warning(f"Kolom '{col}' tidak ditemukan, filter dilewati.")
            continue

        before = len(filtered)

        # Hapus baris dengan nilai NaN di kolom yang difilter
        filtered = filtered.dropna(subset=[col])

        if operator == "<=":
            filtered = filtered[filtered[col] <= threshold]
        elif operator == ">=":
            filtered = filtered[filtered[col] >= threshold]

        after = len(filtered)
        logger.info(f"Filter [{col} {operator} {threshold}]: {before} → {after} saham")

    # Tambahkan kolom Value Score untuk ranking
    if not filtered.empty:
        filtered["Value Score"] = filtered.apply(compute_value_score, axis=1)
        filtered = filtered.sort_values("Value Score", ascending=False)
        filtered = filtered.reset_index(drop=True)
        filtered.index += 1  # Mulai index dari 1 (Rank)
        filtered.index.name = "Rank"

    final_count = len(filtered)
    logger.info(
        f"Screening selesai: {initial_count} ticker masuk → {final_count} lolos filter."
    )

    return filtered


def get_filter_summary(config: ScreenerConfig) -> dict:
    """
    Menghasilkan ringkasan filter yang aktif untuk ditampilkan di dashboard.

    Parameters
    ----------
    config : ScreenerConfig

    Returns
    -------
    dict
        Dictionary berisi nama filter dan nilai threshold-nya.
    """
    return {
        "P/E Ratio ≤":          config.max_pe_ratio,
        "P/B Ratio ≤":          config.max_pb_ratio,
        "ROE (%) ≥":            config.min_roe,
        "Debt/Equity ≤":        config.max_debt_to_equity,
        "Market Cap (B) ≥":     config.min_market_cap_b,
        "Dividend Yield (%) ≥": config.min_dividend_yield,
        "Revenue Growth (%) ≥": config.min_revenue_growth,
    }
