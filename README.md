# 📊 ETF Flows Tracker

Dashboard de Streamlit que trackea **flows (creations / redemptions)** de 145 ETFs (US broad, 11 sectores (SPDR, iShares, Vanguard) + 30 industrias (SPDR, iShares), factor, internacionales, EM, bonds, commodities, REITs, crypto, volatilidad, defensivos).

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
| SPDR `navhist-us-en-{ticker}.xlsx` | 31 (SPY, DIA, XL*, 14 industrias KRE…XHE, GLD, XBI, JNK, BIL) | Diario, ~1 año de backfill |
| iShares página de producto (`Shares Outstanding … as of …` + NAV JSON-LD) | 71 (incl. 10 sectoriales IYW…IYZ y 16 de industria IGV…REZ) | Sólo valor actual; se acumula diario |
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
│   ├── shares/                   # history.parquet, vanguard_monthly.parquet, last_run_status.parquet
│   └── legacy/snapshots_v1/      # Histórico v1 descartado (sólo referencia)
├── ui/theme.py                   # Tokens de color, template Plotly, CSS, formato de números
├── views/                        # Páginas: resumen, rotación, señales, ETF, Vanguard mensual,
│                                 # volumen relativo, calidad, metodología
├── .streamlit/config.toml        # Tema oscuro
└── jobs/daily_snapshot.py        # Job del cron (diario + cierre de mes Vanguard)
```

## Páginas

| Página | Para qué |
|---|---|
| **Sectores** | 11 sectores GICS (Select Sector SPDR + ETFs de industria): lectura de la sesión, tablero con 1D/5D/20D/60D, z y rachas, persistencia 20 sesiones, flow vs. rendimiento (cuadrantes) e industrias dentro de cada sector |
| **Resumen** | KPIs de la sesión, sesgo risk-on/off, flow por categoría, termómetro de la mesa (watchlist con 1D/5D/20D, z y últimas 20 sesiones), top entradas/salidas, mapa de flows |
| **Rotación** | Heatmap categoría × 1D/5D/20D/60D, flows acumulados por categoría, aceleración 5 vs. 15 sesiones previas |
| **Señales** | Flows anómalos para cada ETF (z-score de % AUM) |
| **ETF** | Detalle de un ETF: flow diario y acumulado, shares oficiales, NAV, datos por sesión |
| **Vanguard mensual** | 19 ETFs de Vanguard (incl. 10 sectoriales VGT…VOX): flow de cierre de mes a cierre de mes |
| **Volumen relativo** | Volumen ÷ ADV20 para los 95 ETFs (proxy de presión, no es flow) |
| **Calidad** | Fuente, rezago y flags de cada ETF |

Los controles del sidebar (sesión, unidad $ / % AUM, categorías) aplican a todas las páginas.

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

## Historia

- **v1 (may–oct 2026):** shares de yfinance + scrapers como fallback. Una auditoría en oct-2026 mostró que las shares de yfinance para ETFs no cambiaban (39 tickers sin un solo cambio en 103 días), que casi todos los flows venían de cambios de fuente (p. ej. ±$73B diarios en IWD) y que el cron retrasado fechaba los viernes como sábado. Ese histórico se archivó en `data/legacy/`.
- **v2 (oct 2026):** fuentes oficiales por issuer, fechas as-of, controles de calidad, NAV y % AUM.
- **v2.1 (oct 2026):** Invesco (QQQ), vista mensual de Vanguard, rediseño completo (navegación por páginas, tema oscuro, controles globales); se retiró el Morning Brief.
