import sqlite3

conn = sqlite3.connect('sam.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

tables = ['evidence', 'knowledge', 'patterns', 'recommendations', 'approvals']
for t in tables:
    cur.execute('SELECT correlation_id FROM {} ORDER BY created_at DESC LIMIT 1'.format(t))
    row = cur.fetchone()
    if row:
        print('{}: {}'.format(t, row['correlation_id']))
    else:
        print('{}: (empty)'.format(t))

conn.close()