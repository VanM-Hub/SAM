import sqlite3
import json

DB='D:/Project AI/SAM/sam.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

tables = ['evidence', 'knowledge', 'patterns', 'recommendations', 'approvals']
print('Database:', DB)
for table in tables:
    print('\n=== {} ==='.format(table.upper()))
    # schema
    cols = cur.execute(f"PRAGMA table_info({table})").fetchall()
    print(' Schema:')
    for c in cols:
        pk = 'PK' if c[5] else ''
        print(f"  - {c[1]}: {c[2]} {pk}")
    rows = cur.execute(f"SELECT * FROM {table} ORDER BY timestamp LIMIT 5").fetchall()
    print(' Count:', len(cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()))
    if rows:
        print(' Sample rows:')
        for r in rows:
            d = dict(r)
            # shorten payload/metadata for readability
            if 'payload' in d and d['payload'] and len(d['payload'])>200:
                d['payload'] = d['payload'][:200] + '...'
            if 'metadata' in d and d['metadata'] and len(d['metadata'])>200:
                d['metadata'] = d['metadata'][:200] + '...'
            print('  -', json.dumps(d, ensure_ascii=False))
conn.close()
print('\nDone')
