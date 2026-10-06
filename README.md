# 📊 ETF Flows Tracker

Dashboard de Streamlit que trackea **flows (creations / redemptions)** de 95 ETFs principales (US broad, sectores, factor, internacionales, EM, bonds, commodities, REITs, crypto, volatilidad, defensivos).

## Fórmula

```
Flow_t = (Shares_Outstanding_t − Shares_Outstanding_{t-1}) × NAV_t
Flow % AUM = Flow_t / (Shares_{t-1} × NAV_{t-1})
```

- **Shares y NAV vienen del issuer**, fechados por la sesión de trading a la que pertenecen (as-of), no por la hora en que corre el job.
- Si el issuer no publica NAV se usa el close de yfinance (columna `price_basis`).
- yfinance **no** se usa para shares: sus valores de ETFs quedaban congelados por meses (ver *Historia* abajo).

## Fuentes (una sola por ticker, sin fallbacks)

| Fuente | ETFs | Historial |
|---|---|---|
| SPDR `navhist-us-en-{ticker}.xlsx` | 17 (SPY, DIA, XL*, GLD, XBI, JNK, BIL) | Diario, ~1 año de backfill |
| iShares página de producto (`Shares Outstanding … as of …` + NAV JSON-LD) | 45 | Sólo valor actual; se acumula diario |
| ProShares `{ticker}-historical_nav.csv` | 3 (UVXY, SVXY, VIXY) | Diario, ~1 año de backfill |
| Invesco API de precios (`dng-api`, por CUSIP) | 5 (QQQ, QQQM, DBA, DBC, PDBC) | Sólo valor actual |
| Páginas de issuer (KraneShares, Simplify, Bitwise) | 3 (KWEB, SVOL, BITB) | Sólo valor actual |
| **Sin fuente oficial verificada** | 22 (Vanguard, ARK, VanEck, USCF, WisdomTree, Fidelity, iPath, ROBO) | — |

Si una fuente falla, ese ticker queda vacío esa sesión; **nunca** se rellena con otra fuente (mezclar fuentes generaba flows fantasma).

Notas de fuentes:
- **Invesco**: `effectiveDate` es la fecha de publicación; NAV y shares son de la sesión anterior (verificado contra el cierre), así que se guardan bajo esa sesión. Requiere `curl_cffi` (huella TLS de Chrome) para pasar su filtro anti-bots.
- **Vanguard** sólo publica shares a cierre de mes; VOO/VTI no pueden tener flow diario con fuentes públicas.
- **Nasdaq** (`api.nasdaq.com`, campo AUM) se evaluó y se descartó: va 1–3 días atrasado y difiere hasta 7% del dato del issuer.

## Controles de calidad

Cada fila de flow lleva `quality`; sólo `ok` y `multi_day` cuentan:

| quality | Regla |
|---|---|
| `first` | Primera observación del ticker |
| `split` | Salto >15% en shares compensado por el precio (split / reverse split) |
| `pending` | Salto >15% en el último dato; espera a la siguiente publicación |
| `suspect` | Salto >15% que la siguiente publicación revierte |
| `no_price` | Sin NAV ni close para la sesión |
| `price_mismatch` | NAV del issuer a >5% del cierre (fondo mal mapeado); tolera razones de split |
| `multi_day` | El dato previo está a >1 sesión; el flow cubre todo el hueco |

Además: rechazo de valores <100k shares y eliminación de picos aislados. Como cada issuer publica con distinto rezago, rankings, agregados y rotación usan la **última sesión completa** (≥60% de cobertura), no la fecha más nueva.

## Arquitectura

```
├── app.py                        # Streamlit entry point
├── config/universe.py            # 95 ETFs categorizados (issuer, categoría)
├── core/
│   ├── flows_calc.py             # ΔShares × NAV, quality gates, agregados, z-score, rotación
│   └── trading_calendar.py       # Calendario NYSE (feriados hardcodeados 2024-2027)
├── data/
│   ├── sources/                  # Una fuente oficial por issuer
│   ├── shares_loader.py          # Fetch + validación por ticker
│   ├── cache.py                  # Parquet keyed por (ticker, as_of_date)
│   ├── price_loader.py           # yfinance: sólo precios y volumen
│   ├── shares/                   # history.parquet + last_run_status.parquet (committed)
│   └── legacy/snapshots_v1/      # Histórico v1 descartado (sólo referencia)
├── tabs/                         # Daily Flows, Intraday, Rotation, Signals, Brief, Calidad de datos
└── jobs/daily_snapshot.py        # Job del cron
```

## Cron (GitHub Actions)

`daily_snapshot.yml` corre dos veces por sesión: 23:30 UTC (tarde) y 12:00 UTC (mañana siguiente, para issuers que publican tarde). Es idempotente: cada dato se guarda bajo su sesión as-of, así que corridas retrasadas o repetidas no pueden mal-fechar ni sobreescribir otros días. Usa `concurrency` y reintenta el push con rebase.

Al agregar un año nuevo, extender `NYSE_HOLIDAYS` en `core/trading_calendar.py`.

## Setup local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python jobs/daily_snapshot.py
streamlit run app.py
```

Morning brief: exportar `GROQ_API_KEY` o ponerlo en los secrets de Streamlit Cloud.

## Historia

- **v1 (may–oct 2026):** shares de yfinance + scrapers como fallback. Una auditoría en oct-2026 mostró que las shares de yfinance para ETFs no cambiaban (39 tickers sin un solo cambio en 103 días), que casi todos los flows venían de cambios de fuente (p. ej. ±$73B diarios en IWD) y que el cron retrasado fechaba los viernes como sábado. Ese histórico se archivó en `data/legacy/`.
- **v2 (oct 2026):** fuentes oficiales por issuer, fechas as-of, controles de calidad, NAV y % AUM.
