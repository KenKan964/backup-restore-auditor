"""Acceptance + repeated fixtures + comparison in one process, warning-visible GC gate."""
import gc,json,platform,sys,tempfile,unittest,warnings
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import bra,compare

def main():
 with warnings.catch_warnings(record=True) as caught:
  warnings.simplefilter('always',ResourceWarning)
  result=unittest.TextTestRunner(verbosity=2,warnings='always').run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
  with tempfile.TemporaryDirectory() as td:
   for i in range(3):bra.fixture(Path(td)/(str(i)+'.sqlite'))
  comparison=compare.main()
  for _ in range(3):gc.collect()
 for w in caught:sys.stderr.write(warnings.formatwarning(w.message,w.category,w.filename,w.lineno))
 n=sum(issubclass(w.category,ResourceWarning) for w in caught)
 r={'python':platform.python_version(),'platform':platform.platform(),'tests_run':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'skipped':len(result.skipped),'fixture_generations_after_suite':3,'comparison_executions':len(comparison['records']),'resource_warning_count':n,'gc_collections':3,'warning_filter':'always','passed':result.wasSuccessful() and not result.skipped and n==0}
 print(json.dumps(r,indent=2));return 0 if r['passed'] else 1
if __name__=='__main__':sys.exit(main())
