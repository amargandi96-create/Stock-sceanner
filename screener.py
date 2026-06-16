"""
core/screener.py
----------------
Logika filter dan scoring Value Investing.
Semua threshold dikonfigurasi via ScreenerConfig.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScreenerConfig:
    """
    Konfigurasi threshold filter Value Investing.
    Set nilai None untuk menonaktifkan filter tersebut.
    """
    max_pe:    Optional[float] = 15.0
    max_pb:    Optional[float] = 1.5
    min_roe:   Optional[float] = 15.0
    max_de:    Optional[float] = 1.0
    min_mktcap: Optional[float] = None   # Miliar USD


def compute_score(s: dict) -> float:
    """
    Skor komposit 0–100. Lebih tinggi = lebih undervalued.
    Bobot: ROE 30%, P/E 25%, P/B 25%, D/E 20%
    """
    score = 0.0
    pe  = s.get("pe")
    pb  = s.get("pb")
    roe = s.get("roe")
    de  = s.get("de")

    if pe  and pe  > 0: score += max(0, (50 - pe)  / 50) * 25
    if pb  and pb  > 0: score += max(0, (5  - pb)  / 5)  * 25
    if roe is not None: score += min(roe / 50, 1.0)       * 30
    if de  is not None: score += max(0, (3  - de)  / 3)  * 20

    return round(score, 1)


def apply_filters(data: list[dict],
                  cfg: ScreenerConfig) -> list[dict]:
    """
    Filter list saham berdasarkan cfg.
    Return list diurutkan berdasarkan Value Score (tertinggi dulu).
    """
    out = []
    for s in data:
        if cfg.max_pe    is not None and (s.get("pe")     is None or s["pe"]     > cfg.max_pe):    continue
        if cfg.max_pb    is not None and (s.get("pb")     is None or s["pb"]     > cfg.max_pb):    continue
        if cfg.min_roe   is not None and (s.get("roe")    is None or s["roe"]    < cfg.min_roe):   continue
        if cfg.max_de    is not None and (s.get("de")     is None or s["de"]     > cfg.max_de):    continue
        if cfg.min_mktcap is not None and (s.get("mktcap") is None or s["mktcap"] < cfg.min_mktcap): continue

        scored = {**s, "score": compute_score(s)}
        out.append(scored)

    return sorted(out, key=lambda x: x["score"], reverse=True)
