"""Practical SQLite backup + integrity/FK baseline; synthetic data only."""
import json,sqlite3,tempfile,time
from contextlib import closing
from pathlib import Path
import bra

def baseline(db):
 with closing(bra.connect(db)) as source,closing(sqlite3.connect(':memory:')) as restored:
  bra.backup(source,restored)
  checks={'integrity':list(restored.execute('PRAGMA integrity_check'))==[('ok',)],'foreign_keys':not list(restored.execute('PRAGMA foreign_key_check')),'people_count':restored.execute('SELECT COUNT(*) FROM people').fetchone()[0]==2,'important_key':restored.execute("SELECT COUNT(*) FROM people WHERE id='0'").fetchone()[0]==1}
  return {'accepted':all(checks.values()),'checks':checks}
def main():
 records=[]
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);bra.fixture(root/'source.sqlite');bra.capture(root/'source.sqlite',root/'cap',{'people':'id','orders':'id'})
  for i,(name,sql,expected) in enumerate([('normal','SELECT 1;',True),('missing',"DELETE FROM people WHERE id='1';",False),('value',"UPDATE people SET name='tampered' WHERE id='1';",False),('orphan',"UPDATE orders SET person='absent';",False)]):
   db=root/(name+'.sqlite')
   with closing(bra.connect(root/'cap/backup.sqlite')) as s,closing(sqlite3.connect(db)) as c:bra.backup(s,c);c.executescript(sql)
   for mode in ('baseline','bra'):
    start=time.perf_counter();r=baseline(db) if mode=='baseline' else bra.audit(db,root/'cap/expected.json',root/('run'+str(i)))
    accepted=r['accepted'] if mode=='baseline' else r['exit_code']==0
    records.append({'case':name,'mode':mode,'expected_accept':expected,'accepted':accepted,'contract_matched':accepted==expected,'seconds':time.perf_counter()-start,'evidence':r})
 return {'records':records,'human_work_seconds':None,'limits':'Baseline includes restoration, integrity, FK, count and important-key checks. BRA additionally compares all manifest record hashes. Shared Backup API permitted; memory versus disk/evidence overhead prohibits speed superiority claim.','source_lines':{x:len(Path(x).read_text().splitlines()) for x in ('bra.py','compare.py')}}
if __name__=='__main__':print(json.dumps(main(),indent=2))
