# 📊 ETF Flows Tracker

Dashboard de Streamlit que trackea **flows (creations / redemptions)** de ~95 ETFs principales (US broad, sectores, factor, internacionales, EM, bonds, commodities, REITs, crypto, defensivos).

## Fórmula

```
Flow_t = (Shares_Outstanding_t − Shares_Outstanding_{t-1}) × Close_t
```

`yfinance` solo expone `sharesOutstanding` actual, no histórico. Por eso el approach es:

1. **Snapshot diario** de shares outstanding → persistido en `data/snapshots/*.parquet`
2. El histórico se construye **día por día** (un GitHub Action commitea el snapshot a las 5:30 PM ET, lun-vie)
3. Los flows se calculan **on-the-fly** cruzando el histórico de shares con el `Close` de yfinance

Los snapshots **se commitean al repo** — son la "base de datos" del proyecto.

## Arquitectura

```
etf-flows-tracker/
├── app.py                      # Streamlit entry point
├── config/universe.py          # 95 ETFs categorizados
├── data/
│   ├── price_loader.py         # yfinance: shares + precios
│   ├── cache.py                # Persistencia parquet
│   └── snapshots/              # Histórico (committed)
├── core/flows_calc.py          # Δshares × Close, agregaciones, z-scores, rotación
├── tabs/
│   ├── tab_daily_flows.py      # Top inflows/outflows + bar chart por categoría
│   ├── tab_intraday.py         # Proxy intraday (volumen relativo)
│   ├── tab_rotation.py         # Heatmap categoría × ventana + signal 5D vs 20D
│   ├── tab_signals.py          # Anomalías z-score
│   └── tab_morning_brief.py    # Brief narrativo con Groq (Llama 3.3-70b)
├── jobs/daily_snapshot.py      # Cron job standalone
└── .github/workflows/daily_snapshot.yml
```

## Setup local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
python jobs/daily_snapshot.py   # primer snapshot
streamlit run app.py
```

Para el morning brief con LLM, exportar `GROQ_API_KEY` (https://console.groq.com).

## Deploy: Streamlit Community Cloud

1. Conectar el repo en https://share.streamlit.io
2. Main module: `app.py`
3. Python: 3.11
4. (Opcional) Secrets:

```toml
GROQ_API_KEY = "gsk_..."
```

Cada commit (incluyendo snapshots automáticos del cron) **redeploya** la app.

## GitHub Actions cron

`.github/workflows/daily_snapshot.yml` corre `python jobs/daily_snapshot.py` cada lunes-viernes a las 22:30 UTC (5:30 PM ET en horario de verano). Idempotente: si se corre 2× el mismo día, deduplica por `snapshot_date`.

Permisos requeridos: `contents: write` (ya configurado en el yml). El workflow puede dispararse manualmente desde la pestaña **Actions** con "Run workflow".

## Roadmap

**v2 — Issuer-by-issuer scrapers (cobertura → ~99%)**

- ARK (csv diario en su web): ARKK, ARKG, ARKW, ARKB
- iShares (productpage JSON): MTUM, QUAL, USMV, IBIT, ETHA, …
- SPDR / State Street: GLD, XLK, XLF, …
- Invesco, Vanguard, VanEck, ProShares: scrapers dedicados
- Cross-validate contra ETF.com como ground-truth

**v3 — Avanzado**

- Schwab API → premium / discount intraday
- Alertas push (Telegram / Discord) cuando |z-score| ≥ 3
- Backtesting de la señal de rotación

## Notas de diseño

- **Idempotencia:** `save_daily_snapshot` deduplica por `snapshot_date`.
- **Defensive:** todas las funciones de cálculo manejan DataFrame vacío sin crashear.
- **Sin paths absolutos:** todo relativo con `Path(__file__)`.
- **El campo `issuer`** existe sólo como hook para los scrapers v2.
