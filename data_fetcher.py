"""
core/data_fetcher.py
--------------------
Modul pengambilan data fundamental saham dari Yahoo Finance.
Menggunakan requests langsung (tanpa yfinance/pandas/numpy).
"""

import json
import logging
import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

PCT_FIELDS   = {"roe", "div_yield", "rev_growth", "gross_margin"}
ROUND2       = {"pe", "pb", "de", "price", "eps"}

FIELD_MAP = {
    "trailingPE":     "pe",
    "priceToBook":    "pb",
    "returnOnEquity": "roe",
    "debtToEquity":   "de",
    "marketCap":      "mktcap",
    "currentPrice":   "price",
    "shortName":      "company",
    "sector":         "sector",
    "dividendYield":  "div_yield",
    "revenueGrowth":  "rev_growth",
    "grossMargins":   "gross_margin",
    "trailingEps":    "eps",
}


def fetch_ticker(ticker: str) -> dict | None:
    """
    Ambil data fundamental satu ticker dari Yahoo Finance API.
    Return dict atau None jika gagal.
    """
    try:
        url = (
            f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"
            f"?modules=summaryDetail,defaultKeyStatistics,financialData,assetProfile,price"
        )
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        qs   = data.get("quoteSummary", {})
        if qs.get("error") or not qs.get("result"):
            logger.warning(f"[{ticker}] Data tidak tersedia.")
            return None

        # Gabungkan semua modul jadi satu dict datar
        info = {}
        for module in qs["result"][0].values():
            if isinstance(module, dict):
                for k, v in module.items():
                    # Yahoo v10 membungkus nilai dalam {"raw": ..., "fmt": ...}
                    if isinstance(v, dict) and "raw" in v:
                        info[k] = v["raw"]
                    else:
                        info[k] = v

        if "currentPrice" not in info and "regularMarketPrice" not in info:
            logger.warning(f"[{ticker}] Tidak ada harga.")
            return None

        result = {"ticker": ticker.upper()}
        for yf_key, our_key in FIELD_MAP.items():
            val = info.get(yf_key)
            if val is None:
                result[our_key] = None
                continue
            try:
                val = float(val)
            except (TypeError, ValueError):
                result[our_key] = val
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
    Ambil data banyak ticker.
    Returns (data_list, failed_list)
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
