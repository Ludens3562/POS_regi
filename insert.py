import sqlite3

dbname = "items.sqlite"
conn = sqlite3.connect(dbname)
cur = conn.cursor()

cur.execute(
    "CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT, JAN INTEGER NOT NULL UNIQUE, name TEXT, tax INTEGER DEFAULT 10 CHECK (tax >= 0), price INTEGER, stock INTEGER)"
)
conn.commit()

cur.execute('INSERT INTO items(JAN, name, tax, price, stock) values(4953103254350, "EDT-TMEX10",10, 1562, 10)')

conn.commit()

cur.close()
conn.close()
