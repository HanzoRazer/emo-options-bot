# Phase 3 to Phase 4 Checklist

## Production Patch Set Applied ✅

### Core Components Completed:
- ✅ **Database Router** - Environment-based routing (SQLite/PostgreSQL/TimescaleDB)
- ✅ **Core Schemas** - Production Pydantic models with hard boundaries  
- ✅ **Risk Gates** - Fail-closed evaluation system
- ✅ **Lua Bridge** - Sandboxed strategy runner with graceful fallback
- ✅ **Orchestrator & Synthesizer** - Modular LLM and plan-to-orders
- ✅ **Phase 3 Integration** - Stage-only end-to-end system
- ✅ **Dashboard Builder** - Minimal staged orders dashboard
- ✅ **Test Suite** - Contract tests for gates and Lua fallback
- ✅ **CI Workflow** - GitHub Actions with Lua support
- ✅ **Policy Configuration** - Safety policy YAML

### File Locations:
- **Checklist**: `PHASE3_TO_PHASE4_CHECKLIST.md`
- **Policy**: `config/policy.yaml`
- **Promotion logs**: `data/promotions/` (auto-created)
- **Gate outcomes**: `data/gates/` (auto-created)
- **Staged orders**: `data/staged/` (auto-created)

### Safety Defaults Encoded:
- Stage-only in Phase 3 (no broker writes)
- All strategy outputs must pass Pydantic schemas and risk gates
- Router fails closed to SQLite unless EMO_DB_URL configured
- Lua sandboxed and gracefully disabled when unavailable
- Default position caps and risk percentages enforced

### Dev Quick Checks:
```bash
# Status & smoke
pwsh ./tools/repo_readiness_check.ps1
python tools/release_check.py --fast

# Stage a plan end-to-end (no live orders)
python phase3_integration_patched.py

# Build minimal dashboard
python tools/build_dashboard.py
```

### Phase 4 Priorities:
1. **Real Market Data** - Replace mock data with live feeds
2. **Greeks Calculation** - Replace notional with proper risk metrics
3. **Live LLM Integration** - OpenAI/Anthropic API connections
4. **Broker Integration** - Stage → Execute pipeline
5. **Advanced Strategies** - Beyond iron condors
6. **Portfolio Management** - Real position tracking
7. **Risk Monitoring** - Live P&L and Greeks monitoring

### 🚀 Next Steps:
**Ready for Phase 4 Sprint!** See detailed roadmap: [PHASE4_INITIALIZATION_SPRINT_PLAN.md](PHASE4_INITIALIZATION_SPRINT_PLAN.md)