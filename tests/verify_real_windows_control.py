"""Explicit integration runner, never automatic: operates only disposable QA windows."""
import json, os, pathlib, subprocess, sys, tempfile, time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from myles_windows import desktop_operation

def run():
    assert os.name=='nt'
    with tempfile.TemporaryDirectory() as directory:
        folder=pathlib.Path(directory);ready=folder/'ready.json';stop=folder/'stop'
        fixture=pathlib.Path(__file__).with_name('windows_control_fixture.py')
        child=subprocess.Popen([sys.executable,str(fixture),str(ready),str(stop)],creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            deadline=time.monotonic()+10
            while not ready.exists() and time.monotonic()<deadline:time.sleep(.1)
            assert ready.exists(),'Fixture did not start'
            output={}
            def action(label,kind,target,**kw):
                data=desktop_operation(kind,target,**kw);output[label]=data;return data
            output['window_discovery']={'windows':[r for r in desktop_operation('windows')['windows'] if 'MYLES_CONTROL_QA' in r['MainWindowTitle']]}
            assert len(output['window_discovery']['windows'])==3
            assert action('ambiguous','close','MYLES_CONTROL_QA')['state']=='choice_required'
            assert action('focus','focus','MYLES_CONTROL_QA Alpha')['ok']
            assert action('minimize','minimize','')['ok']
            assert action('restore','focus','MYLES_CONTROL_QA Alpha')['ok']
            assert action('close_alpha','close','MYLES_CONTROL_QA Alpha')['ok']
            assert action('close_beta','close','MYLES_CONTROL_QA Beta')['ok']
            assert action('unsaved','close','MYLES_CONTROL_QA Unsaved',timeout=.3)['state']=='waiting_on_application'
            assert action('force_guard','close','MYLES_CONTROL_QA Unsaved',force=True)['state']=='confirmation_required'
            assert action('missing','close','MYLES_CONTROL_QA DoesNotExist')['state']=='not_found'
            print(json.dumps({'pass':True,'results':output},indent=2))
        finally:
            stop.touch();child.wait(timeout=10)

if __name__=='__main__':run()
