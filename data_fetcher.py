"""
data_fetcher.py
---------------
Modul untuk mengambil data fundamental saham dari Yahoo Finance menggunakan yfinance.
Dirancang untuk digunakan sebagai bagian dari sistem Value Investing Stock Screener.
"""

import yfinance as yf
import pandas as pd
import logging
from typing import Optional

# Setup logging untuk debugging dan monitoring
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# FIELD MAPPING - Pemetaan field dari yfinance ke nama kolom sistem kita
# =============================================================================
FUNDAMENTAL_FIELDS = {
    "trailingPE":          "P/E Ratio",
    "priceToBook":         "P/B Ratio",
    "returnOnEquity":      "ROE (%)",
    "debtToEquity":        "Debt/Equity",
    "marketCap":           "Market Cap (B)",
    "currentPrice":        "Price",
    "sector":              "Sector",
    "shortName":           "Company",
    "dividendYield":       "Dividend Yield (%)",
    "revenueGrowth":       "Revenue Growth (%)",
    "grossMargins":        "Gross Margin (%)",
}


def fetch_ticker_info(ticker: str) -> Optional[dict]:
    """
    Mengambil data fundamental untuk satu ticker dari Yahoo Finance.

    Parameters
    ----------
    ticker : str
        Simbol saham (contoh: 'AAPL', 'BBCA.JK')

    Returns
    -------
    dict | None
        Dictionary berisi data fundamental, atau None jika gagal.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Validasi: pastikan data tidak kosong
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            logger.warning(f"[{ticker}] Data tidak tersedia atau ticker tidak valid.")
            return None

        result = {"Ticker": ticker.upper()}

        for yf_field, display_name in FUNDAMENTAL_FIELDS.items():
            raw_value = info.get(yf_field)

            # Normalisasi nilai persentase (yfinance mengembalikan desimal, ubah ke %)
            if display_name in ("ROE (%)", "Dividend Yield (%)", "Revenue Growth (%)", "Gross Margin (%)"):
                result[display_name] = round(raw_value * 100, 2) if raw_value is not None else None
            # Normalisasi Market Cap ke Miliar
            elif display_name == "Market Cap (B)":
                result[display_name] = round(raw_value / 1e9, 2) if raw_value is not None else None
            else:
                result[display_name] = round(raw_value, 2) if isinstance(raw_value, float) else raw_value

        logger.info(f"[{ticker}] Data berhasil diambil.")
        return result

    except Exception as e:
        logger.error(f"[{ticker}] Gagal mengambil data: {e}")
        return None


def fetch_multiple_tickers(tickers: list[str]) -> pd.DataFrame:
    """
    Mengambil data fundamental untuk banyak ticker sekaligus.

    Parameters
    ----------
    tickers : list[str]
        Daftar simbol saham.

    Returns
    -------
    pd.DataFrame
        DataFrame berisi data fundamental semua ticker yang berhasil diambil.
        Ticker yang gagal akan dilewati dengan log peringatan.
    """
    all_data = []
    failed_tickers = []

    logger.info(f"Memulai pengambilan data untuk {len(tickers)} ticker...")

    for ticker in tickers:
        data = fetch_ticker_info(ticker.strip().upper())
        if data:
            all_data.append(data)
        else:
            failed_tickers.append(ticker)

    if failed_tickers:
        logger.warning(f"Ticker yang gagal diambil datanya: {failed_tickers}")

    if not all_data:
        logger.error("Tidak ada data yang berhasil diambil dari semua ticker.")
        return pd.DataFrame()

    df = pd.DataFrame(all_data)

    # Atur urutan kolom agar mudah dibaca
    column_order = [
        "Ticker", "Company", "Sector", "Price",
        "P/E Ratio", "P/B Ratio", "ROE (%)", "Debt/Equity",
        "Market Cap (B)", "Dividend Yield (%)", "Revenue Growth (%)", "Gross Margin (%)"
    ]
    df = df.reindex(columns=[c for c in column_order if c in df.columns])

    logger.info(f"Pengambilan data selesai. {len(all_data)} ticker berhasil, {len(failed_tickers)} gagal.")
    return df
