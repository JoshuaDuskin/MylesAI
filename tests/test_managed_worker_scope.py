import ast,unittest,tempfile
from pathlib import Path
class WorkerScopeTests(unittest.TestCase):
 def test_mentions_and_other_checkouts_are_not_workers(self):
  source=(Path(__file__).resolve().parents[1]/'bin/runtime_supervisor_v074.py').read_text(encoding='utf-8');tree=ast.parse(source)
  function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='managed_process_args')
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)/'MylesAI';root.mkdir();namespace={'ROOT':root,'Path':Path};exec(compile(ast.Module(body=[function],type_ignores=[]),'supervisor','exec'),namespace);check=namespace['managed_process_args']
   canonical=str(root/'quant/quant_service.mjs')
   self.assertTrue(check(['C:/Program Files/nodejs/node.exe',canonical]))
   self.assertTrue(check(['C:/Python/pythonw.exe',str(root/'myles_core.py')]))
   self.assertFalse(check(['powershell.exe','-Command','Get-Content '+canonical]))
   self.assertFalse(check(['python.exe','-c','print("'+canonical+'")']))
   self.assertFalse(check(['node.exe',str(root.parent/'validation/quant_service.mjs')]))
   self.assertFalse(check(['node.exe',str(root/'../outside/quant_service.mjs')]))
