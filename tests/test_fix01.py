from contextlib import closing
import hashlib,json,os,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
import bra
from test_acceptance import preserve
ROOT=Path(bra.__file__).parent
class Fix01(unittest.TestCase):
 def conflict(self,kind):
  with tempfile.TemporaryDirectory() as td:
   base=Path(td);d=base/'evidence';d.mkdir();marker=base/'marker';marker.write_bytes(b'BRA FIX01 synthetic marker');target=d/'basic.json'
   if kind=='existing':target.write_bytes(marker.read_bytes());protected=target
   elif kind=='file_symlink':
    try:target.symlink_to(marker)
    except OSError:self.skipTest('symlink unavailable')
    protected=marker
   else:
    d.rmdir();(base/'real').mkdir()
    try:d.symlink_to(base/'real',target_is_directory=True)
    except OSError:self.skipTest('symlink unavailable')
    protected=marker
   before=bra.sha(protected);r=subprocess.run([sys.executable,'-W','always::ResourceWarning','-m','unittest','discover','-s','tests','-p','test_acceptance.py','-v'],cwd=ROOT,env=dict(os.environ,BRA_EVIDENCE=str(d)),capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(bra.sha(protected),before);self.assertNotIn('ResourceWarning:',r.stderr)
   if kind=='directory_symlink':self.assertEqual(list((base/'real').iterdir()),[])
   preserve('FIX01_'+kind,{'exit_code':r.returncode,'before_sha256':before,'after_sha256':bra.sha(protected),'stdout':r.stdout,'stderr':r.stderr})
 def test_existing(self):self.conflict('existing')
 def test_file_symlink(self):self.conflict('file_symlink')
 def test_directory_symlink(self):self.conflict('directory_symlink')
 def test_repeated_fixture_handles(self):
  with tempfile.TemporaryDirectory() as td:
   for i in range(3):
    f=Path(td)/(str(i)+'.sqlite');bra.fixture(f);new=f.with_suffix('.renamed');f.rename(new);new.unlink()
   preserve('FIX01_handles',{'fixture_generations':3,'rename_delete_success':True,'platform':sys.platform,'windows_verified':sys.platform=='win32'})

def tztest(name,stamp,expected):
 def test(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);bra.fixture(p/'source');bra.capture(p/'source',p/'capture',{'people':'id','orders':'id'});mf=p/'capture/expected.json';m=json.loads(mf.read_text());m['snapshot_at']=stamp;mf.write_text(json.dumps(m));r=bra.audit(p/'capture/backup.sqlite',mf,p/'restore');self.assertEqual(r['exit_code'],expected,r);preserve('FIX01_time_'+name,{'snapshot_at':stamp,'expected_exit':expected,'report':r})
 return test
for n,s,e in [('positive','2026-11-14T12:00:00+09:00',0),('negative','2026-11-14T12:00:00-07:00',0),('z','2026-11-14T12:00:00Z',0),('naive','2026-11-14T12:00:00',2),('invalid','not-a-time',2)]:setattr(Fix01,'test_time_'+n,tztest(n,s,e))
