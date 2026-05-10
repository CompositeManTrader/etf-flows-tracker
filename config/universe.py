"""ETF universe definition: ~95 ETFs categorized by asset class and theme."""
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

    # Volatility (5)
    "VXX":  {"category": "Volatility", "subcategory": "Long Vol Short-term", "issuer": "Barclays",  "name": "iPath Series B S&P 500 VIX Short-Term"},
    "UVXY": {"category": "Volatility", "subcategory": "Long Vol 1.5x",      "issuer": "ProShares", "name": "ProShares Ultra VIX Short-Term"},
    "SVXY": {"category": "Volatility", "subcategory": "Short Vol -0.5x",    "issuer": "ProShares", "name": "ProShares Short VIX Short-Term"},
    "VIXY": {"category": "Volatility", "subcategory": "Long Vol Short-term", "issuer": "ProShares", "name": "ProShares VIX Short-Term"},
    "SVOL": {"category": "Volatility", "subcategory": "Short Vol Income",   "issuer": "Simplify",  "name": "Simplify Volatility Premium"},

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
