from __future__ import annotations
import json, os, time

# Try embedded Lua (fast path). If unavailable, degrade gracefully.
try:
    from lupa import LuaRuntime  # pip install lupa
except Exception:
    LuaRuntime = None  # type: ignore

SAFE_GLOBALS = (
    "math","table","string","pairs","ipairs","next","type","tonumber","tostring","assert","error",
)

def _lua_init():
    if LuaRuntime is None:
        raise RuntimeError("Lua runtime unavailable. Install `lupa` or skip Lua strategies.")
    lua = LuaRuntime(unpack_returned_tuples=True)
    # Remove dangerous libs
    lua_globals = lua.globals()
    for k in list(lua_globals.keys()):
        if k not in SAFE_GLOBALS:
            lua_globals[k] = None
    return lua

def run_lua_strategy(lua_source: str, ctx: dict, timeout_s: float=0.050) -> dict:
    """
    Executes a Lua strategy source with sandboxed globals.
    Contract: returns {orders=[...], notes=[...], telemetry={...}, warnings=[...]}
    """
    if LuaRuntime is None:
        # graceful fallback (mock)
        return {"orders": [], "notes": ["lua_unavailable"], "telemetry": {"mock": True}, "warnings": ["lua_unavailable"]}

    lua = _lua_init()
    start = time.time()
    fn = lua.execute(lua_source)
    # Provide ctx via JSON to minimize surface
    lua_ctx = json.dumps(ctx)
    result = fn(lua_ctx)  # strategy returns JSON string
    if time.time() - start > timeout_s:
        return {"orders": [], "notes": ["timeout"], "telemetry": {}, "warnings": ["timeout"]}
    try:
        return json.loads(result or "{}")
    except Exception:
        return {"orders": [], "notes": ["bad_json"], "telemetry": {}, "warnings": ["bad_json"]}