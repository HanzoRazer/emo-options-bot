# Phase 3 Overview (LLM + Voice + Intelligent Synthesis)

**Pipeline:** Voice → LLM → Synthesis → Risk Gates → (Stage/Submit elsewhere)

**Modules**
- `src/llm/` — Orchestrator (mock/OpenAI) + Pydantic schemas
- `src/trade/` — Deterministic synthesis from MarketView → options structure
- `src/risk/` — Non-bypassable hard gates (max risk per trade, cap on open positions)
- `src/voice/` — Graceful stub; enable real voice via EMO_VOICE=1 and audio libs later
- `src/phase3_integration.py` — Wires everything for CLI/automation
- `tools/release_check.py` — Import + E2E smoke test

**Run the smoke test**
```bash
python -m tools.release_check
```

This is dependency-light and safe to run without API keys.