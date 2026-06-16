"""
core/data_fetcher.py
--------------------
Modul pengambilan data fundamental saham dari Yahoo Finance.
Kompatibel dengan Android via yfinance.
"""

import yfinance as yf
import logging

logger = logging.getLogger(__name__)

# Mapping field yfinance → nama tampilan
FIELD_MAP = {
    "trailingPE":     "pe",
    "priceToBook":    "pb",
    "returnOnEquity": "roe",        # desimal → kita kalikan 100
    "debtToEquity":   "de",
    "marketCap":      "mktcap",     # raw bytes → dibagi 1e9
    "currentPrice":   "price",
    "shortName":      "company",
    "sector":         "sector",
    "dividendYield":  "div_yield",  # desimal → kali 100
    "revenueGrowth":  "rev_growth", # desimal → kali 100
    "grossMargins":   "gross_margin",
    "trailingEps":    "eps",
}

PCT_FIELDS  = {"roe", "div_yield", "rev_growth", "gross_margin"}
ROUND2      = {"pe", "pb", "de", "price", "eps"}


def fetch_ticker(ticker: str) -> dict | None:
    """
    Ambil data fundamental satu ticker.
    Return dict atau None jika gagal.
    """
    try:
        info = yf.Ticker(ticker).info
        if not info or ("currentPrice" not in info and "regularMarketPrice" not in info):
            logger.warning(f"[{ticker}] Data tidak tersedia.")
            return None

        result = {"ticker": ticker.upper()}
        for yf_key, our_key in FIELD_MAP.items():
            val = info.get(yf_key)
            if val is None:
                result[our_key] = None
                continue
            if our_key in PCT_FIELDS:
                result[our_key] = round(val * 100, 2)
            elif our_key == "mktcap":
                result[our_key] = round(val / 1e9, 2)
            elif our_key in ROUND2 or isinstance(val, float):
                result[our_key] = round(val, 2)
            else:
                result[our_key] = val

        logger.info(f"[{ticker}] OK")
        return result

    except Exception as e:
        logger.error(f"[{ticker}] Error: {e}")
        return None


def fetch_multiple(tickers: list[str],
                   on_progress=None) -> tuple[list[dict], list[str]]:
    """
    Ambil data banyak ticker. Memanggil callback on_progress(done, total)
    setelah setiap ticker selesai (untuk update progress bar di UI).

    Returns
    -------
    (data_list, failed_list)
    """
    results, failed = [], []
    total = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        data = fetch_ticker(ticker.strip().upper())
        if data:
            results.append(data)
        else:
            failed.append(ticker)
        if on_progress:
            on_progress(i, total)

    return results, failed
