import os, json, sqlite3
root='.'
py_files=[]
for dirpath,dirnames,filenames in os.walk(root):
    for f in filenames:
        if f.endswith('.py'):
            py_files.append(os.path.join(dirpath,f))
line_count=0
for p in py_files:
    try:
        with open(p,'r',encoding='utf-8') as fh:
            line_count+=len(fh.readlines())
    except Exception:
        pass
modules=set()
for p in py_files:
    parts=p.split(os.sep)
    if len(parts)>1:
        modules.add(parts[1])
db_path=os.path.abspath(os.path.join('..','sam.db'))
if not os.path.exists(db_path):
    db_path=os.path.abspath(os.path.join('.','sam.db'))
counts={}
try:
    conn=sqlite3.connect(db_path)
    cur=conn.cursor()
    for t in ['evidence','knowledge','patterns','recommendations','approvals']:
        try:
            cur.execute(f'SELECT COUNT(*) FROM {t}')
            counts[t]=cur.fetchone()[0]
        except Exception:
            counts[t]=None
    conn.close()
except Exception:
    for t in ['evidence','knowledge','patterns','recommendations','approvals']:
        counts[t]=None

out={'py_files':len(py_files),'lines':line_count,'modules':sorted(list(modules)),'db_path':db_path,'db_counts':counts}
print(json.dumps(out))
