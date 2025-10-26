import sqlite3

# Create test database
conn = sqlite3.connect('data/emo_trading.sqlite')

# Create basic tables
conn.execute('''
    CREATE TABLE IF NOT EXISTS test_table (
        id INTEGER PRIMARY KEY,
        symbol TEXT
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        quantity REAL,
        avg_price REAL,
        market_value REAL,
        unrealized_pnl REAL,
        realized_pnl REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        side TEXT,
        quantity REAL,
        price REAL,
        pnl REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert test data
conn.execute('INSERT OR IGNORE INTO test_table (id, symbol) VALUES (1, "AAPL")')
conn.execute('''
    INSERT OR IGNORE INTO positions (id, symbol, quantity, avg_price, market_value, unrealized_pnl, realized_pnl)
    VALUES (1, "AAPL", 100, 150.0, 15500.0, 500.0, 0.0)
''')

conn.execute('''
    INSERT OR IGNORE INTO trades (id, symbol, side, quantity, price, pnl)
    VALUES (1, "AAPL", "BUY", 100, 150.0, 0.0)
''')

conn.commit()
conn.close()

print("✅ Test database created successfully")