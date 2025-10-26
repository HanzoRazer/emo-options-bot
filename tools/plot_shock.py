
import os, sqlite3, datetime as dt
import matplotlib.pyplot as plt

DB_PATH = os.path.join("ops", "describer.db")
OUT_PATH = os.path.join("tools", "shock_trend.png")

def main():
    if not os.path.exists(DB_PATH):
        print("No ops/describer.db found. Run app_describer.py at least once first.")
        return
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT ts_utc, info_shock FROM runs ORDER BY ts_utc ASC")
    rows = cur.fetchall()
    con.close()
    if not rows:
        print("No rows in runs table yet.")
        return
    times = [dt.datetime.fromisoformat(t.replace('Z','')) for (t, _) in rows]
    shocks = [float(s) for (_, s) in rows]
    plt.figure()
    plt.plot(times, shocks, marker='o')
    plt.title("Information Shock Over Time")
    plt.xlabel("UTC Timestamp")
    plt.ylabel("Info Shock")
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    os.makedirs("tools", exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=120)
    print(f"Wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
