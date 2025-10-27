-- Returns JSON string
return function(ctx_json)
  local json = require("json")  -- if present; otherwise emit raw JSON strings
  -- Minimal fallback without a JSON lib:
  -- parse not required; we only need to echo a fixed structure in example
  local out = {
    orders = {
      {symbol="SPY", side="sell", instrument="call", strike=470, expiry="2025-12-20", quantity=1},
      {symbol="SPY", side="buy",  instrument="call", strike=475, expiry="2025-12-20", quantity=1},
      {symbol="SPY", side="sell", instrument="put",  strike=430, expiry="2025-12-20", quantity=1},
      {symbol="SPY", side="buy",  instrument="put",  strike=425, expiry="2025-12-20", quantity=1},
    },
    notes = {"demo_iron_condor"},
    telemetry = {version="v1"},
    warnings = {}
  }
  -- naive JSON to avoid external deps:
  local function q(s) return '"'..s..'"' end
  local function leg(l)
    return string.format(
      '{%s:%s,%s:%s,%s:%s,%s:%d,%s:%s,%s:%d}',
      q('symbol'), q(l.symbol), q('side'), q(l.side), q('instrument'), q(l.instrument),
      q('strike'), l.strike, q('expiry'), q(l.expiry), q('quantity'), l.quantity
    )
  end
  local legs = {}
  for i,l in ipairs(out.orders) do table.insert(legs, leg(l)) end
  local json_out = string.format(
    '{"orders":[%s],"notes":["demo_iron_condor"],"telemetry":{"version":"v1"},"warnings":[]}', table.concat(legs, ",")
  )
  return json_out
end