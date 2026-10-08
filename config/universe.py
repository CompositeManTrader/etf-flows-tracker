"""ETF universe definition: ETFs categorized by asset class and theme, plus a GICS sector map."""
from __future__ import annotations

ETF_UNIVERSE: dict[str, dict[str, str]] = {
    # US Equity Broad (8)
    "SPY":  {"category": "US Equity Broad", "subcategory": "Broad",          "issuer": "SPDR",     "name": "SPDR S&P 500"},
    "IVV":  {"category": "US Equity Broad", "subcategory": "Broad",          "issuer": "iShares",  "name": "iShares Core S&P 500"},
    "VOO":  {"category": "US Equity Broad", "subcategory": "Broad",          "issuer": "Vanguard", "name": "Vanguard S&P 500"},
    "VTI":  {"category": "US Equity Broad", "subcategory": "Broad",          "issuer": "Vanguard", "name": "Vanguard Total Stock Market"},
    "QQQ":  {"category": "US Equity Broad", "subcategory": "Nasdaq",         "issuer": "Invesco",  "name": "Invesco QQQ Trust"},
    "QQQM": {"category": "US Equity Broad", "subcategory": "Nasdaq",         "issuer": "Invesco",  "name": "Invesco Nasdaq 100"},
    "IWM":  {"category": "US Equity Broad", "subcategory": "Small Cap",      "issuer": "iShares",  "name": "iShares Russell 2000"},
    "DIA":  {"category": "US Equity Broad", "subcategory": "Dow",            "issuer": "SPDR",     "name": "SPDR Dow Jones Industrial"},

    # US Sectors SPDR (11)
    "XLK":  {"category": "US Sectors",      "subcategory": "Technology",          "issuer": "SPDR", "name": "Technology Select Sector SPDR"},
    "XLF":  {"category": "US Sectors",      "subcategory": "Financials",          "issuer": "SPDR", "name": "Financial Select Sector SPDR"},
    "XLE":  {"category": "US Sectors",      "subcategory": "Energy",              "issuer": "SPDR", "name": "Energy Select Sector SPDR"},
    "XLV":  {"category": "US Sectors",      "subcategory": "Healthcare",          "issuer": "SPDR", "name": "Health Care Select Sector SPDR"},
    "XLI":  {"category": "US Sectors",      "subcategory": "Industrials",         "issuer": "SPDR", "name": "Industrial Select Sector SPDR"},
    "XLY":  {"category": "US Sectors",      "subcategory": "Cons. Discretionary", "issuer": "SPDR", "name": "Consumer Discretionary Select Sector SPDR"},
    "XLP":  {"category": "US Sectors",      "subcategory": "Cons. Staples",       "issuer": "SPDR", "name": "Consumer Staples Select Sector SPDR"},
    "XLU":  {"category": "US Sectors",      "subcategory": "Utilities",           "issuer": "SPDR", "name": "Utilities Select Sector SPDR"},
    "XLB":  {"category": "US Sectors",      "subcategory": "Materials",           "issuer": "SPDR", "name": "Materials Select Sector SPDR"},
    "XLRE": {"category": "US Sectors",      "subcategory": "Real Estate",         "issuer": "SPDR", "name": "Real Estate Select Sector SPDR"},
    "XLC":  {"category": "US Sectors",      "subcategory": "Communications",      "issuer": "SPDR", "name": "Communication Services Select Sector SPDR"},

    # US Sectors iShares (10) — daily shares from iShares product pages
    "IYW":  {"category": "US Sectors", "subcategory": "Technology",          "issuer": "iShares", "name": "iShares U.S. Technology"},
    "IYF":  {"category": "US Sectors", "subcategory": "Financials",          "issuer": "iShares", "name": "iShares U.S. Financials"},
    "IYE":  {"category": "US Sectors", "subcategory": "Energy",              "issuer": "iShares", "name": "iShares U.S. Energy"},
    "IYH":  {"category": "US Sectors", "subcategory": "Healthcare",          "issuer": "iShares", "name": "iShares U.S. Healthcare"},
    "IYJ":  {"category": "US Sectors", "subcategory": "Industrials",         "issuer": "iShares", "name": "iShares U.S. Industrials"},
    "IYC":  {"category": "US Sectors", "subcategory": "Cons. Discretionary", "issuer": "iShares", "name": "iShares U.S. Consumer Discretionary"},
    "IYK":  {"category": "US Sectors", "subcategory": "Cons. Staples",       "issuer": "iShares", "name": "iShares U.S. Consumer Staples"},
    "IDU":  {"category": "US Sectors", "subcategory": "Utilities",           "issuer": "iShares", "name": "iShares U.S. Utilities"},
    "IYM":  {"category": "US Sectors", "subcategory": "Materials",           "issuer": "iShares", "name": "iShares U.S. Basic Materials"},
    "IYZ":  {"category": "US Sectors", "subcategory": "Communications",      "issuer": "iShares", "name": "iShares U.S. Telecommunications"},

    # US Sectors Vanguard (10) — month-end shares only (Vanguard monthly view)
    "VGT":  {"category": "US Sectors", "subcategory": "Technology",          "issuer": "Vanguard", "name": "Vanguard Information Technology"},
    "VFH":  {"category": "US Sectors", "subcategory": "Financials",          "issuer": "Vanguard", "name": "Vanguard Financials"},
    "VDE":  {"category": "US Sectors", "subcategory": "Energy",              "issuer": "Vanguard", "name": "Vanguard Energy"},
    "VHT":  {"category": "US Sectors", "subcategory": "Healthcare",          "issuer": "Vanguard", "name": "Vanguard Health Care"},
    "VIS":  {"category": "US Sectors", "subcategory": "Industrials",         "issuer": "Vanguard", "name": "Vanguard Industrials"},
    "VCR":  {"category": "US Sectors", "subcategory": "Cons. Discretionary", "issuer": "Vanguard", "name": "Vanguard Consumer Discretionary"},
    "VDC":  {"category": "US Sectors", "subcategory": "Cons. Staples",       "issuer": "Vanguard", "name": "Vanguard Consumer Staples"},
    "VPU":  {"category": "US Sectors", "subcategory": "Utilities",           "issuer": "Vanguard", "name": "Vanguard Utilities"},
    "VAW":  {"category": "US Sectors", "subcategory": "Materials",           "issuer": "Vanguard", "name": "Vanguard Materials"},
    "VOX":  {"category": "US Sectors", "subcategory": "Communications",      "issuer": "Vanguard", "name": "Vanguard Communication Services"},

    # US Industries SPDR (14) — sub-sector detail, all with official daily history
    "KRE":  {"category": "US Industries", "subcategory": "Regional Banks",       "issuer": "SPDR", "name": "SPDR S&P Regional Banking"},
    "KBE":  {"category": "US Industries", "subcategory": "Banks",                "issuer": "SPDR", "name": "SPDR S&P Bank"},
    "KIE":  {"category": "US Industries", "subcategory": "Insurance",            "issuer": "SPDR", "name": "SPDR S&P Insurance"},
    "XOP":  {"category": "US Industries", "subcategory": "Oil & Gas E&P",        "issuer": "SPDR", "name": "SPDR S&P Oil & Gas Exploration & Production"},
    "XES":  {"category": "US Industries", "subcategory": "Oil & Gas Services",   "issuer": "SPDR", "name": "SPDR S&P Oil & Gas Equipment & Services"},
    "XME":  {"category": "US Industries", "subcategory": "Metals & Mining",      "issuer": "SPDR", "name": "SPDR S&P Metals & Mining"},
    "XHB":  {"category": "US Industries", "subcategory": "Homebuilders",         "issuer": "SPDR", "name": "SPDR S&P Homebuilders"},
    "XRT":  {"category": "US Industries", "subcategory": "Retail",               "issuer": "SPDR", "name": "SPDR S&P Retail"},
    "XAR":  {"category": "US Industries", "subcategory": "Aerospace & Defense",  "issuer": "SPDR", "name": "SPDR S&P Aerospace & Defense"},
    "XTN":  {"category": "US Industries", "subcategory": "Transportation",       "issuer": "SPDR", "name": "SPDR S&P Transportation"},
    "XSD":  {"category": "US Industries", "subcategory": "Semiconductors",       "issuer": "SPDR", "name": "SPDR S&P Semiconductor"},
    "XSW":  {"category": "US Industries", "subcategory": "Software & Services",  "issuer": "SPDR", "name": "SPDR S&P Software & Services"},
    "XPH":  {"category": "US Industries", "subcategory": "Pharmaceuticals",      "issuer": "SPDR", "name": "SPDR S&P Pharmaceuticals"},
    "XHE":  {"category": "US Industries", "subcategory": "Health Care Equipment", "issuer": "SPDR", "name": "SPDR S&P Health Care Equipment"},

    # US Factor (10)
    "MTUM": {"category": "US Factor", "subcategory": "Momentum",     "issuer": "iShares", "name": "iShares MSCI USA Momentum"},
    "QUAL": {"category": "US Factor", "subcategory": "Quality",      "issuer": "iShares", "name": "iShares MSCI USA Quality"},
    "USMV": {"category": "US Factor", "subcategory": "Min Vol",      "issuer": "iShares", "name": "iShares MSCI USA Min Vol"},
    "VLUE": {"category": "US Factor", "subcategory": "Value",        "issuer": "iShares", "name": "iShares MSCI USA Value"},
    "SIZE": {"category": "US Factor", "subcategory": "Size",         "issuer": "iShares", "name": "iShares MSCI USA Size"},
    "IWF":  {"category": "US Factor", "subcategory": "Large Growth", "issuer": "iShares", "name": "iShares Russell 1000 Growth"},
    "IWD":  {"category": "US Factor", "subcategory": "Large Value",  "issuer": "iShares", "name": "iShares Russell 1000 Value"},
    "IWN":  {"category": "US Factor", "subcategory": "Small Value",  "issuer": "iShares", "name": "iShares Russell 2000 Value"},
    "IWO":  {"category": "US Factor", "subcategory": "Small Growth", "issuer": "iShares", "name": "iShares Russell 2000 Growth"},
    "MOAT": {"category": "US Factor", "subcategory": "Wide Moat",    "issuer": "VanEck",  "name": "VanEck Morningstar Wide Moat"},

    # Thematic (10)
    "ARKK": {"category": "Thematic", "subcategory": "Disruptive Innov",   "issuer": "ARK",         "name": "ARK Innovation"},
    "ARKG": {"category": "Thematic", "subcategory": "Genomics",           "issuer": "ARK",         "name": "ARK Genomic Revolution"},
    "ARKW": {"category": "Thematic", "subcategory": "Next Gen Internet",  "issuer": "ARK",         "name": "ARK Next Generation Internet"},
    "SMH":  {"category": "Thematic", "subcategory": "Semiconductors",     "issuer": "VanEck",      "name": "VanEck Semiconductor"},
    "SOXX": {"category": "Thematic", "subcategory": "Semiconductors",     "issuer": "iShares",     "name": "iShares Semiconductor"},
    "ICLN": {"category": "Thematic", "subcategory": "Clean Energy",       "issuer": "iShares",     "name": "iShares Global Clean Energy"},
    "KWEB": {"category": "Thematic", "subcategory": "China Internet",     "issuer": "KraneShares", "name": "KraneShares CSI China Internet"},
    "ROBO": {"category": "Thematic", "subcategory": "Robotics & AI",      "issuer": "ROBO Global", "name": "ROBO Global Robotics & Automation"},
    "XBI":  {"category": "Thematic", "subcategory": "Biotech",            "issuer": "SPDR",        "name": "SPDR S&P Biotech"},
    "IBB":  {"category": "Thematic", "subcategory": "Biotech",            "issuer": "iShares",     "name": "iShares Biotechnology"},

    # Volatility (5) — split by direction: inflows to long-vol and short-vol are opposite bets
    "VXX":  {"category": "Volatility Long",  "subcategory": "Long Vol Short-term", "issuer": "Barclays",  "name": "iPath Series B S&P 500 VIX Short-Term"},
    "UVXY": {"category": "Volatility Long",  "subcategory": "Long Vol 1.5x",       "issuer": "ProShares", "name": "ProShares Ultra VIX Short-Term"},
    "SVXY": {"category": "Volatility Short", "subcategory": "Short Vol -0.5x",     "issuer": "ProShares", "name": "ProShares Short VIX Short-Term"},
    "VIXY": {"category": "Volatility Long",  "subcategory": "Long Vol Short-term", "issuer": "ProShares", "name": "ProShares VIX Short-Term"},
    "SVOL": {"category": "Volatility Short", "subcategory": "Short Vol Income",    "issuer": "Simplify",  "name": "Simplify Volatility Premium"},

    # Intl DM (8)
    "EFA":  {"category": "Intl DM", "subcategory": "EAFE",      "issuer": "iShares",  "name": "iShares MSCI EAFE"},
    "IEFA": {"category": "Intl DM", "subcategory": "EAFE Core", "issuer": "iShares",  "name": "iShares Core MSCI EAFE"},
    "VEA":  {"category": "Intl DM", "subcategory": "Developed", "issuer": "Vanguard", "name": "Vanguard FTSE Developed Markets"},
    "VGK":  {"category": "Intl DM", "subcategory": "Europe",    "issuer": "Vanguard", "name": "Vanguard FTSE Europe"},
    "EWJ":  {"category": "Intl DM", "subcategory": "Japan",     "issuer": "iShares",  "name": "iShares MSCI Japan"},
    "EWU":  {"category": "Intl DM", "subcategory": "UK",        "issuer": "iShares",  "name": "iShares MSCI United Kingdom"},
    "EWG":  {"category": "Intl DM", "subcategory": "Germany",   "issuer": "iShares",  "name": "iShares MSCI Germany"},
    "EWQ":  {"category": "Intl DM", "subcategory": "France",    "issuer": "iShares",  "name": "iShares MSCI France"},

    # EM (8)
    "EEM":  {"category": "EM", "subcategory": "Broad EM",     "issuer": "iShares",  "name": "iShares MSCI Emerging Markets"},
    "IEMG": {"category": "EM", "subcategory": "Core EM",      "issuer": "iShares",  "name": "iShares Core MSCI Emerging Markets"},
    "VWO":  {"category": "EM", "subcategory": "Broad EM",     "issuer": "Vanguard", "name": "Vanguard FTSE Emerging Markets"},
    "FXI":  {"category": "EM", "subcategory": "China Large",  "issuer": "iShares",  "name": "iShares China Large-Cap"},
    "MCHI": {"category": "EM", "subcategory": "China Broad",  "issuer": "iShares",  "name": "iShares MSCI China"},
    "EWZ":  {"category": "EM", "subcategory": "Brazil",       "issuer": "iShares",  "name": "iShares MSCI Brazil"},
    "EWW":  {"category": "EM", "subcategory": "Mexico",       "issuer": "iShares",  "name": "iShares MSCI Mexico"},
    "INDA": {"category": "EM", "subcategory": "India",        "issuer": "iShares",  "name": "iShares MSCI India"},

    # US Bonds (10)
    "AGG": {"category": "US Bonds", "subcategory": "Aggregate",       "issuer": "iShares",  "name": "iShares Core US Aggregate Bond"},
    "BND": {"category": "US Bonds", "subcategory": "Aggregate",       "issuer": "Vanguard", "name": "Vanguard Total Bond Market"},
    "TLT": {"category": "US Bonds", "subcategory": "Long Treasury",   "issuer": "iShares",  "name": "iShares 20+ Year Treasury"},
    "IEF": {"category": "US Bonds", "subcategory": "7-10Y Treasury",  "issuer": "iShares",  "name": "iShares 7-10 Year Treasury"},
    "SHY": {"category": "US Bonds", "subcategory": "1-3Y Treasury",   "issuer": "iShares",  "name": "iShares 1-3 Year Treasury"},
    "LQD": {"category": "US Bonds", "subcategory": "IG Corporate",    "issuer": "iShares",  "name": "iShares iBoxx Investment Grade Corporate"},
    "HYG": {"category": "US Bonds", "subcategory": "High Yield",      "issuer": "iShares",  "name": "iShares iBoxx High Yield Corporate"},
    "JNK": {"category": "US Bonds", "subcategory": "High Yield",      "issuer": "SPDR",     "name": "SPDR Bloomberg High Yield Bond"},
    "TIP": {"category": "US Bonds", "subcategory": "TIPS",            "issuer": "iShares",  "name": "iShares TIPS Bond"},
    "MBB": {"category": "US Bonds", "subcategory": "MBS",             "issuer": "iShares",  "name": "iShares MBS"},

    # Intl Bonds (4)
    "EMB":  {"category": "Intl Bonds", "subcategory": "EM USD",          "issuer": "iShares",  "name": "iShares JPM USD Emerging Markets Bond"},
    "EMLC": {"category": "Intl Bonds", "subcategory": "EM Local",        "issuer": "VanEck",   "name": "VanEck JPM EM Local Currency Bond"},
    "BNDX": {"category": "Intl Bonds", "subcategory": "Intl Aggregate",  "issuer": "Vanguard", "name": "Vanguard Total International Bond"},
    "IGOV": {"category": "Intl Bonds", "subcategory": "Intl Treasury",   "issuer": "iShares",  "name": "iShares International Treasury Bond"},

    # Commodities (8)
    "GLD":  {"category": "Commodities", "subcategory": "Gold",         "issuer": "SPDR",    "name": "SPDR Gold Shares"},
    "IAU":  {"category": "Commodities", "subcategory": "Gold",         "issuer": "iShares", "name": "iShares Gold Trust"},
    "SLV":  {"category": "Commodities", "subcategory": "Silver",       "issuer": "iShares", "name": "iShares Silver Trust"},
    "USO":  {"category": "Commodities", "subcategory": "Oil",          "issuer": "USCF",    "name": "United States Oil Fund"},
    "UNG":  {"category": "Commodities", "subcategory": "Natural Gas",  "issuer": "USCF",    "name": "United States Natural Gas Fund"},
    "DBA":  {"category": "Commodities", "subcategory": "Agriculture",  "issuer": "Invesco", "name": "Invesco DB Agriculture"},
    "DBC":  {"category": "Commodities", "subcategory": "Broad Cmdty",  "issuer": "Invesco", "name": "Invesco DB Commodity Index"},
    "PDBC": {"category": "Commodities", "subcategory": "Broad Cmdty",  "issuer": "Invesco", "name": "Invesco Optimum Yield Diversified Commodity"},

    # Real Estate (3)
    "VNQ": {"category": "Real Estate", "subcategory": "US REITs",       "issuer": "Vanguard", "name": "Vanguard Real Estate"},
    "IYR": {"category": "Real Estate", "subcategory": "US REITs",       "issuer": "iShares",  "name": "iShares US Real Estate"},
    "REM": {"category": "Real Estate", "subcategory": "Mortgage REITs", "issuer": "iShares",  "name": "iShares Mortgage Real Estate"},

    # Crypto (5)
    "IBIT": {"category": "Crypto", "subcategory": "Bitcoin Spot",  "issuer": "iShares",  "name": "iShares Bitcoin Trust"},
    "FBTC": {"category": "Crypto", "subcategory": "Bitcoin Spot",  "issuer": "Fidelity", "name": "Fidelity Wise Origin Bitcoin Fund"},
    "ETHA": {"category": "Crypto", "subcategory": "Ethereum Spot", "issuer": "iShares",  "name": "iShares Ethereum Trust"},
    "BITB": {"category": "Crypto", "subcategory": "Bitcoin Spot",  "issuer": "Bitwise",  "name": "Bitwise Bitcoin ETF"},
    "ARKB": {"category": "Crypto", "subcategory": "Bitcoin Spot",  "issuer": "ARK",      "name": "ARK 21Shares Bitcoin ETF"},

    # Defensive (5)
    "HEFA": {"category": "Defensive", "subcategory": "Hedged DM Equity", "issuer": "iShares",   "name": "iShares Currency Hedged MSCI EAFE"},
    "HEDJ": {"category": "Defensive", "subcategory": "Hedged Europe",    "issuer": "WisdomTree", "name": "WisdomTree Europe Hedged Equity"},
    "SHV":  {"category": "Defensive", "subcategory": "Short Treasury",   "issuer": "iShares",   "name": "iShares Short Treasury Bond"},
    "BIL":  {"category": "Defensive", "subcategory": "T-Bills",          "issuer": "SPDR",      "name": "SPDR Bloomberg 1-3 Month T-Bill"},
    "BSV":  {"category": "Defensive", "subcategory": "Short Bonds",      "issuer": "Vanguard",  "name": "Vanguard Short-Term Bond"},
}


# Desk "thermometer": the ETFs whose flows say most about institutional positioning.
WATCHLIST = ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "HYG", "LQD", "TLT", "BIL", "GLD", "EEM", "IBIT", "UVXY"]

# Risk-appetite buckets. Flows into "on" add to the risk-on side, "off" to risk-off;
# "neutral" (IG/MBS credit, commodities ex-gold, currency-hedged equity) is ignored.
_RISK_OFF_TICKERS = {"TLT", "IEF", "SHY", "SHV", "BIL", "BSV", "AGG", "BND", "TIP", "IGOV", "BNDX",
                     "GLD", "IAU", "UVXY", "VIXY", "VXX", "USMV"}
_RISK_ON_TICKERS = {"HYG", "JNK", "EMB", "EMLC", "SVXY", "SVOL"}
_RISK_ON_CATEGORIES = {"US Equity Broad", "US Sectors", "US Industries", "US Factor", "Thematic", "Intl DM",
                       "EM", "Crypto", "Real Estate"}


# GICS sector per ETF, for sector-level flow aggregation. The Select Sector SPDR is
# each sector's benchmark (its NAV return is the sector's performance).
SECTOR_BENCHMARK = {
    "Technology": "XLK", "Financials": "XLF", "Energy": "XLE", "Healthcare": "XLV",
    "Industrials": "XLI", "Cons. Discretionary": "XLY", "Cons. Staples": "XLP", "Utilities": "XLU",
    "Materials": "XLB", "Real Estate": "XLRE", "Communications": "XLC",
}
SECTOR_ES = {
    "Technology": "Tecnología", "Financials": "Financiero", "Energy": "Energía", "Healthcare": "Salud",
    "Industrials": "Industrial", "Cons. Discretionary": "Consumo discrecional", "Cons. Staples": "Consumo básico",
    "Utilities": "Utilities", "Materials": "Materiales", "Real Estate": "Bienes raíces",
    "Communications": "Comunicaciones",
}
_SECTOR_OF = {
    **{etf: sector for sector, etf in SECTOR_BENCHMARK.items()},
    "KRE": "Financials", "KBE": "Financials", "KIE": "Financials", "REM": "Financials",
    "XOP": "Energy", "XES": "Energy",
    "XME": "Materials",
    "XHB": "Cons. Discretionary", "XRT": "Cons. Discretionary",
    "XAR": "Industrials", "XTN": "Industrials",
    "XSD": "Technology", "XSW": "Technology", "SMH": "Technology", "SOXX": "Technology",
    "XPH": "Healthcare", "XHE": "Healthcare", "XBI": "Healthcare", "IBB": "Healthcare",
    "IYR": "Real Estate", "VNQ": "Real Estate",
}
# iShares and Vanguard sector ETFs share the subcategory naming of the SPDR sectors
_SECTOR_OF.update({t: m["subcategory"] for t, m in ETF_UNIVERSE.items()
                   if m["category"] == "US Sectors" and m["issuer"] in ("iShares", "Vanguard")})


def sector_of(ticker: str) -> str | None:
    """GICS sector for sector/industry ETFs; None for broad, factor, bond, intl, etc."""
    return _SECTOR_OF.get(ticker)


def risk_bucket(ticker: str) -> str:
    if ticker in _RISK_OFF_TICKERS:
        return "off"
    if ticker in _RISK_ON_TICKERS:
        return "on"
    return "on" if ETF_UNIVERSE.get(ticker, {}).get("category") in _RISK_ON_CATEGORIES else "neutral"


def get_universe() -> dict[str, dict[str, str]]:
    return ETF_UNIVERSE


def get_tickers() -> list[str]:
    return list(ETF_UNIVERSE.keys())


def get_by_category(category: str | None = None):
    if category is None:
        out: dict[str, list[str]] = {}
        for tk, meta in ETF_UNIVERSE.items():
            out.setdefault(meta["category"], []).append(tk)
        return out
    return {tk: meta for tk, meta in ETF_UNIVERSE.items() if meta["category"] == category}


def get_categories() -> list[str]:
    return sorted({meta["category"] for meta in ETF_UNIVERSE.values()})
