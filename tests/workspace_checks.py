"""Local-storage integrity tests, isolated in a temporary directory."""
import json,tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rotary_melter.Workspace import WorkspaceStore,SCHEMA

def run():
 from rotary_melter.Paths import OUTPUTS_DIR
 OUTPUTS_DIR.mkdir(exist_ok=True)
 checks=[]
 def check(name,passed):checks.append({'name':name,'passed':bool(passed)})
 with tempfile.TemporaryDirectory(dir=OUTPUTS_DIR) as tmp:
  path=Path(tmp)/'workspace.json';store=WorkspaceStore(path)
  base=store.read();check('Missing workspace opens empty',base['revision']==0 and base['cases']==[])
  sample={'schema':SCHEMA,'cases':[{'id':'a','name':'Türkçe · <case>','notes':'line1\nline2','inputs':{'diameter':600}}],'draft':{'inputs':{'flow':'10'}}}
  revision=store.save(sample,0);read=WorkspaceStore(path).read()
  check('UTF-8 and draft roundtrip',revision==1 and read['cases']==sample['cases'] and read['draft']==sample['draft'])
  before=path.read_bytes()
  try:store.save(sample,0);stale=False
  except ValueError:stale=True
  check('Stale revision cannot overwrite existing data',stale and path.read_bytes()==before)
  bad={**sample,'cases':sample['cases']*2}
  try:store.save(bad,1);rejected=False
  except ValueError:rejected=True
  check('Duplicate identifiers rejected without data loss',rejected and path.read_bytes()==before)
  try:store.save({**sample,'draft':{'bad':float('nan')}},1);rejected=False
  except ValueError:rejected=True
  check('NaN rejected without replacing the file',rejected and path.read_bytes()==before)
  def concurrent_write(i):
   try:return WorkspaceStore(path).save({**sample,'draft':{'writer':i}},1)
   except ValueError:return None
  with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(concurrent_write,[1,2]))
  check('Concurrent windows cannot both commit the same revision',sum(x is not None for x in results)==1 and store.read()['revision']==2)
  path.write_text('{broken',encoding='utf-8');corrupt=path.read_bytes()
  try:store.save(sample,2);rejected=False
  except (ValueError,json.JSONDecodeError):rejected=True
  check('Corrupt record preserved for recovery',rejected and path.read_bytes()==corrupt)
 return {'version':'2.0','passed':all(x['passed'] for x in checks),'checks':checks}

if __name__=='__main__':
 from rotary_melter.Paths import OUTPUTS_DIR
 result=run();OUTPUTS_DIR/'validation_workspace.json'.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['passed'] else 1)
