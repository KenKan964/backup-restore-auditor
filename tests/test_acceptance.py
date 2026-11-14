from contextlib import closing
import hashlib,json,os,sqlite3,tempfile,unittest
from pathlib import Path
import bra
def preserve(name,data):
 if not os.environ.get('BRA_EVIDENCE'):return
 d=Path(os.path.abspath(os.environ['BRA_EVIDENCE']))
 if any(x.is_symlink() for x in [d,*d.parents]):raise ValueError('symlink evidence path')
 d.mkdir(parents=True,exist_ok=True)
 with (d/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2)

CASES=[('basic',0),('wal_live',0),('empty_db',0),('multiple',0),('unicode',0),('blob',0),('many',0),('hashmatch',0),('corrupt',2),('zero_file',2),('fake',2),('missing_table',2),('missing_row',1),('tamper',1),('orphan',1),('no_manifest_table',2),('unknown_time',2),('bad_version',2),('missing_manifest',2),('existing',2),('symlink',2),('missing_parent',2),('simple_wal_copy',2),('bad_count',2),('wrong_schema',1),('extra_row',1),('bad_key',2),('duplicate_json',2)]
class Acceptance(unittest.TestCase):pass
def make(name,expected):
 def test(self):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td);source=base/'source.sqlite';bra.fixture(source,empty=name=='empty_db',n=2000 if name=='many' else 2)
   keys={} if name=='empty_db' else {'people':'id','orders':'id'};live=None
   if name in ('wal_live','simple_wal_copy'):
    live=sqlite3.connect(source);live.execute('PRAGMA journal_mode=WAL');live.execute("INSERT INTO people VALUES('wal','pending committed',X'01')");live.commit()
   try:
    before=bra.sha(source);bra.capture(source,base/'cap',keys);db=base/'cap/backup.sqlite';mf=base/'cap/expected.json';out=base/'restore';m=json.loads(mf.read_text())
    if name in ('missing_table','missing_row','tamper','orphan','extra_row'):
     scripts={'missing_table':'DROP TABLE orders;','missing_row':"DELETE FROM people WHERE id='1';",'tamper':"UPDATE people SET name='changed' WHERE id='1';",'orphan':"UPDATE orders SET person='absent';",'extra_row':"INSERT INTO people VALUES('extra','x',NULL);"}
     with closing(sqlite3.connect(db)) as c, c:c.executescript(scripts[name])
    if name=='corrupt':db.write_bytes(b'x'*4096)
    if name=='zero_file':db.write_bytes(b'')
    if name=='fake':db.write_bytes(b'not sqlite'*100)
    if name=='no_manifest_table':del m['tables']['people']
    if name=='unknown_time':m['snapshot_at']='unknown'
    if name=='bad_version':m['manifest_version']=2
    if name=='bad_count':m['tables']['people']['count']=999
    if name=='wrong_schema':m['schema']['index:unexpected']='CREATE INDEX unexpected ON people(name)'
    if name=='bad_key':m['tables']['people']['key']='missing'
    mf.write_text(json.dumps(m))
    if name=='missing_manifest':mf.unlink()
    if name=='duplicate_json':mf.write_text('{"manifest_version":1,"manifest_version":2}')
    if name=='existing':out.mkdir();(out/'marker').write_bytes(b'keep')
    if name=='missing_parent':out=base/'absent/restore'
    if name=='symlink':
     try:(base/'link').symlink_to(db)
     except OSError:self.skipTest('symlink unavailable')
     db=base/'link'
    if name=='simple_wal_copy':
     db=base/'unsafe.sqlite';db.write_bytes(source.read_bytes());m['method']='simple_file_copy';mf.write_text(json.dumps(m))
    input_hash=bra.sha(db);r=bra.audit(db,mf,out);self.assertEqual(r['exit_code'],expected,r);self.assertEqual(bra.sha(db),input_hash);self.assertEqual(bra.sha(source),before)
    if name=='wal_live':
     with closing(sqlite3.connect(out/'restored.sqlite')) as c, c:self.assertEqual(c.execute("SELECT COUNT(*) FROM people WHERE id='wal'").fetchone()[0],1)
    if name=='orphan':self.assertIn('FOREIGN_KEY_VIOLATION',[x['code'] for x in r['findings']])
    if name=='existing':self.assertEqual((out/'marker').read_bytes(),b'keep')
    preserve(name,{'expected_exit':expected,'input_hash_unchanged':True,'report':r})
   finally:
    if live:live.close()
 return test
for n,e in CASES:setattr(Acceptance,'test_'+n,make(n,e))
