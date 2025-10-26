
import os, datetime as dt, pytz
from data.collectors.bars import mock_ohlcv
from data.collectors.options import mock_surface_metrics
from data.collectors.internals import mock_internals
from data.collectors.news_social import mock_news_window
from ops.narrate import information_shock_score, render_markdown
from ops.features import basic_intraday_features, text_window_stats, classify_regime
from ops.journal_ext import append_describer_log
from ops.db import connect, ensure_schema, insert_run, insert_symbol_row

def run_once(symbols=("SPY","QQQ")):
    bars = [mock_ohlcv(s) for s in symbols]
    opts = [mock_surface_metrics(s) for s in symbols]
    internals = mock_internals()

    sentiments, perps = [], []
    agg = {"avg_sentiment":0.0,"avg_perplexity":0.0,"novelty":0.0}
    for s in symbols:
        rows, a = mock_news_window(s, n=6)
        sentiments.extend([r["sentiment"] for r in rows])
        perps.extend([r["perplexity"] for r in rows])
        for k in agg: agg[k] += a[k]
    for k in agg: agg[k] /= len(symbols)

    sent_var, perp_z, topic_entropy = text_window_stats(sentiments, perps, agg["novelty"])

    ret_5m_0, atrp_0, vol_z_0 = basic_intraday_features(bars[0])
    score, z_perp, z_vix, z_sent = information_shock_score(
        agg["avg_perplexity"], agg["avg_sentiment"], internals["vix"], volume_z=vol_z_0
    )
    regime = classify_regime(score)

    tz = pytz.timezone("America/Chicago")
    ts_local = dt.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    md_path = os.path.join("ops", f"market_tape_{dt.datetime.now(tz).strftime('%Y%m%d')}.md")
    os.makedirs("ops", exist_ok=True)
    render_markdown(ts_local, bars, internals, agg, md_path, regime, score, z_perp, z_vix, z_sent)

    ts_utc = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
    vix_change = round(internals["vix"] - 18.0, 3)

    conn = connect("ops/describer.db")
    ensure_schema(conn)
    run_id = insert_run(conn, ts_utc, regime, score, z_perp, z_vix, z_sent)

    for i, s in enumerate(symbols):
        ret_5m, atrp, vol_z = basic_intraday_features(bars[i])
        row = {
            "ts": ts_utc,
            "symbol": s,
            "close": round(bars[i]["close"],2),
            "ret_5m": ret_5m,
            "atrp": atrp,
            "vol_z": vol_z,
            "ivr": opts[i]["ivr"],
            "skew_25d": opts[i]["skew_25d"],
            "term_slope": opts[i]["term_slope"],
            "vix": internals["vix"],
            "vix_change": vix_change,
            "avg_sentiment": round(agg["avg_sentiment"],3),
            "sent_var": sent_var,
            "avg_perplexity": round(agg["avg_perplexity"],1),
            "perp_z": perp_z,
            "topic_entropy": topic_entropy,
            "information_shock": score,
            "regime": regime
        }
        append_describer_log(os.path.join("ops","describer_log.csv"), row)
        insert_symbol_row(conn, run_id, row)

    conn.close()

if __name__ == "__main__":
    run_once()
