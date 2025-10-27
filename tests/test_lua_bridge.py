from src.strategies.lua_runner import run_lua_strategy

def test_lua_fallback_runs_without_lua():
    out = run_lua_strategy("return function(ctx) return '{}' end", {"x":1})
    assert "orders" in out and "notes" in out and "warnings" in out