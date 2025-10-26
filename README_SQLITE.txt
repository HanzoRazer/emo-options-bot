
SQLite + Plot upgrade

1) Unzip into your existing emo_options_bot folder (overwrite app_describer.py and add the new files).
2) Run once to create the DB:
   python app_describer.py
3) Plot the trend:
   python tools\plot_shock.py

Files:
- ops/describer.db (SQLite)
- ops/db.py (DB helper)
- tools/plot_shock.py (chart to tools/shock_trend.png)
