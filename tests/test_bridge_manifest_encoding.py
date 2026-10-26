import ast,json,tempfile,unittest
from pathlib import Path
class ManifestEncodingTests(unittest.TestCase):
 def test_windows_bom_manifest_is_recognized_without_republishing(self):
  source=(Path(__file__).resolve().parents[1]/'bin/runtime_supervisor_v074.py').read_text(encoding='utf-8')
  tree=ast.parse(source);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bridge_manifest_matches')
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);namespace={'ROOT':root,'json':json};exec(compile(ast.Module(body=[function],type_ignores=[]),'supervisor','exec'),namespace)
   for encoding in ['utf-8','utf-8-sig']:
    (root/'bridge.json').write_text(json.dumps({'url':'https://tower.example','read_token':'test-only'}),encoding=encoding)
    self.assertTrue(namespace['bridge_manifest_matches']('https://tower.example','test-only'))
    self.assertFalse(namespace['bridge_manifest_matches']('https://different.example','test-only'))
