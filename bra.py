"""Read-only inputs, SQLite Backup API restoration and manifest contracts."""
from contextlib import closing
import argparse,datetime,hashlib,json,os,sqlite3,sys,time
from pathlib import Path
def path(p):
 p=Path(os.path.abspath(p))
 if any(x.is_symlink() for x in [p,*p.parents]):raise ValueError('symlink rejected')
 return p
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def q(s):return '"'+s.replace('"','""')+'"'
def connect(p):
 c=sqlite3.connect(path(p).as_uri()+'?mode=ro',uri=True,timeout=2);c.enable_load_extension(False);c.execute('PRAGMA trusted_schema=OFF');return c
def backup(source,dest):
 start=time.monotonic()
 def progress(*args):
  if time.monotonic()-start>10:raise TimeoutError('backup deadline')
 source.backup(dest,pages=128,progress=progress,sleep=.01)
def schema(c):return {r[0]+':'+r[1]:r[2] for r in c.execute("SELECT type,name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")}
def value(v):return ['blob',v.hex()] if isinstance(v,bytes) else [type(v).__name__,v]
def token(v):return json.dumps(value(v),ensure_ascii=True,separators=(',',':'))
def contents(c,keys):
 result={}
 for table,key in sorted(keys.items()):
  cur=c.execute('SELECT * FROM '+q(table));cols=[x[0] for x in cur.description]
  if key not in cols:raise ValueError('missing key')
  records={}
  for i,row in enumerate(cur):
   if i>=100000:raise ValueError('row limit')
   v=row[cols.index(key)]
   if v is None or type(v) not in (int,str):raise ValueError('invalid business key')
   k=token(v)
   if k in records:raise ValueError('duplicate business key')
   records[k]=hashlib.sha256(json.dumps([[n,value(x)] for n,x in zip(cols,row)],ensure_ascii=True,separators=(',',':')).encode()).hexdigest()
  result[table]={'key':key,'count':len(records),'records':records}
 return result
def manifest(c,keys,snapshot_at):return {'manifest_version':1,'method':'sqlite_backup_api','snapshot_at':snapshot_at,'schema':schema(c),'tables':contents(c,keys)}
def unique(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('duplicate JSON key')
  d[k]=v
 return d
def validate(m):
 if not isinstance(m,dict) or set(m)!={'manifest_version','method','snapshot_at','schema','tables'} or type(m['manifest_version']) is not int or m['manifest_version']!=1:raise ValueError('manifest fields/version')
 if m['method']!='sqlite_backup_api' or not isinstance(m['snapshot_at'],str):raise ValueError('unverified snapshot provenance')
 stamp=datetime.datetime.fromisoformat(m['snapshot_at'].replace('Z','+00:00'))
 if stamp.tzinfo is None or stamp.utcoffset() is None:raise ValueError('timezone required')
 if not isinstance(m['schema'],dict) or not all(isinstance(k,str) and (v is None or isinstance(v,str)) for k,v in m['schema'].items()) or not isinstance(m['tables'],dict):raise ValueError('manifest types')
 declared={k.split(':',1)[1] for k in m['schema'] if k.startswith('table:')}
 if set(m['tables'])!=declared:raise ValueError('manifest must cover every table')
 for t,r in m['tables'].items():
  if not isinstance(r,dict) or set(r)!={'key','count','records'} or not isinstance(r['key'],str) or type(r['count']) is not int or not isinstance(r['records'],dict) or r['count']!=len(r['records']):raise ValueError('table contract')
  if not all(isinstance(k,str) and isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v) for k,v in r['records'].items()):raise ValueError('record hashes')
 return m

def audit(db,mfile,out):
 r={'schema_version':'bra-report-v1','tool_version':'0.1.0','status':'UNVERIFIABLE','exit_code':2,'findings':[],'manifest_trust':'CALLER_SUPPLIED_NOT_EXTERNALLY_AUTHENTICATED','scope':'Snapshot only; no latest-state, disaster recovery, RPO/RTO or external-effects guarantee.'};created=False;c=None
 def add(code,**kw):r['findings'].append({'code':code,**kw})
 try:
  db=path(db);mfile=path(mfile);out=path(out)
  if not db.is_file() or db.stat().st_size<100:raise ValueError('empty or non-DB backup')
  if mfile.stat().st_size>20000000:raise ValueError('manifest limit')
  m=validate(json.loads(mfile.read_text(encoding='utf-8'),object_pairs_hook=unique));out.mkdir(mode=0o700);created=True
  r.update(backup_sha256_before=sha(db),manifest_sha256=sha(mfile),snapshot_at=m['snapshot_at'],restore_id=out.name)
  c=sqlite3.connect(out/'restored.sqlite')
  with closing(connect(db)) as source:backup(source,c)
  c.execute('PRAGMA trusted_schema=OFF');c.enable_load_extension(False)
  deadline=time.monotonic()+5
  c.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
  r['integrity_check']=[x[0] for x in c.execute('PRAGMA integrity_check')];r['foreign_key_check']=[list(x) for x in c.execute('PRAGMA foreign_key_check')]
  if r['integrity_check']!=['ok']:add('CORRUPT_BACKUP')
  if r['foreign_key_check']:add('FOREIGN_KEY_VIOLATION',rows=r['foreign_key_check'])
  observed=schema(c)
  if observed!=m['schema']:add('SCHEMA_MISMATCH',missing=sorted(set(m['schema'])-set(observed)),changed=sorted(k for k in observed if observed.get(k)!=m['schema'].get(k)))
  for table,expected in m['tables'].items():
   try:actual=contents(c,{table:expected['key']})[table]
   except (sqlite3.Error,ValueError):add('UNVERIFIABLE_TABLE',table=table);continue
   if actual!=expected:add('CONTENT_MISMATCH',table=table,expected_count=expected['count'],actual_count=actual['count'],missing_keys=sorted(set(expected['records'])-set(actual['records'])),changed_keys=sorted(k for k in expected['records'] if k in actual['records'] and expected['records'][k]!=actual['records'][k]),added_keys=sorted(set(actual['records'])-set(expected['records'])))
  r['backup_sha256_after']=sha(db)
  if r['backup_sha256_before']!=r['backup_sha256_after']:add('SOURCE_CHANGED')
  r['exit_code']=2 if any(x['code'] in ('SOURCE_CHANGED','UNVERIFIABLE_TABLE') for x in r['findings']) else int(bool(r['findings']));r['status']=['MATCH','VIOLATION','UNVERIFIABLE'][r['exit_code']]
 except (OSError,ValueError,TypeError,sqlite3.Error,TimeoutError,RecursionError) as e:add('UNVERIFIABLE',reason=type(e).__name__)
 finally:
  if c is not None:c.close()
 if created:
  try:(out/'report.json').write_text(json.dumps(r,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
  except OSError:r['status']='UNVERIFIABLE';r['exit_code']=2;add('OUTPUT_FAILED')
 return r

def fixture(p,empty=False,n=2):
 with closing(sqlite3.connect(p)) as c, c:
  if empty:return
  c.executescript('CREATE TABLE people(id TEXT PRIMARY KEY, name TEXT, data BLOB); CREATE TABLE orders(id TEXT PRIMARY KEY, person TEXT REFERENCES people(id));')
  c.executemany('INSERT INTO people VALUES(?,?,?)',[(str(i),'日本'+str(i),b'\x00\xff') for i in range(n)]);c.execute("INSERT INTO orders VALUES('o','0')")
def capture(db,out,keys):
 out=path(out);out.mkdir(mode=0o700)
 with closing(connect(db)) as s,closing(sqlite3.connect(out/'backup.sqlite')) as d:
  backup(s,d);m=validate(manifest(d,keys,datetime.datetime.now(datetime.timezone.utc).isoformat()))
 (out/'expected.json').write_text(json.dumps(m,indent=2,ensure_ascii=True),encoding='utf-8');return m
class Parser(argparse.ArgumentParser):
 def error(self,message):raise ValueError('arguments')
def main():
 try:
  p=Parser();s=p.add_subparsers(dest='cmd',required=True);a=s.add_parser('run')
  for x in ('backup','manifest','out'):a.add_argument('--'+x,required=True)
  a=s.add_parser('capture');a.add_argument('--db',required=True);a.add_argument('--keys',required=True);a.add_argument('--out',required=True)
  a=s.add_parser('demo');a.add_argument('--out',required=True);a=p.parse_args()
  if a.cmd=='run':r=audit(a.backup,a.manifest,a.out)
  elif a.cmd=='capture':
   keys=json.loads(a.keys,object_pairs_hook=unique)
   if not isinstance(keys,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in keys.items()):raise ValueError('keys')
   capture(a.db,a.out,keys);r={'exit_code':0,'status':'CAPTURED_NOT_AUDITED'}
  else:
   base=path(a.out);base.mkdir();fixture(base/'source.sqlite');capture(base/'source.sqlite',base/'capture',{'people':'id','orders':'id'});r=audit(base/'capture/backup.sqlite',base/'capture/expected.json',base/'restore')
 except (OSError,ValueError,TypeError,sqlite3.Error):r={'status':'UNVERIFIABLE','exit_code':2,'findings':[{'code':'UNVERIFIABLE'}]}
 print(json.dumps(r,ensure_ascii=True));return r['exit_code']
if __name__=='__main__':sys.exit(main())
