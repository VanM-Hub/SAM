import sqlite3
conn = sqlite3.connect('sam.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print(tables)
conn.close()