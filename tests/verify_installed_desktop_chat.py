"""Explicit installed-tower integration; targets only disposable QA windows."""
import json, os, pathlib, subprocess, sys, tempfile, time, urllib.request, uuid

def run():
    root=pathlib.Path('C:/Users/Joshu/AppData/Local/MylesAI')
    token=(root/'data/dashboard_bridge_token.txt').read_text().strip()
    endpoint='https://desktop-ckiivnp.taildc4191.ts.net'
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(route,body=None):
        payload=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(endpoint+route,data=payload,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with opener.open(req,timeout=15) as response:return response.status,json.load(response)
    with tempfile.TemporaryDirectory() as directory:
        folder=pathlib.Path(directory);ready=folder/'ready';stop=folder/'stop'
        child=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).with_name('windows_control_fixture.py')),str(ready),str(stop)],creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            deadline=time.monotonic()+10
            while not ready.exists() and time.monotonic()<deadline:time.sleep(.1)
            assert ready.exists()
            results=[]
            def command(text,expected,alias=False,replay=False):
                identifier='qa_'+uuid.uuid4().hex;body={'message':text,'client_request_id':identifier}
                route='/dashboard/public-chat/messages' if alias else '/dashboard/messages'
                started=time.perf_counter();code,data=request(route,body);ack=(time.perf_counter()-started)*1000
                assert code==202,(text,code)
                deadline=time.monotonic()+100
                while time.monotonic()<deadline:
                    _,snapshot=request(route)
                    row=next((r for r in snapshot['deliveries'] if r['client_id']==identifier),{})
                    if row.get('status') in {'Completed','Failed'}:break
                    time.sleep(.75)
                assert row.get('status')==expected,(text,row)
                if replay:
                    _,again=request(route,body)
                    assert again['delivery']['client_id']==identifier and again['delivery']['reply']==row['reply']
                results.append({'command':text,'client_id':identifier,'status':row['status'],'reply':row.get('reply','') if 'windows' not in text.lower() else 'Verified window list returned privately','ack_ms':round(ack,2),'owner_role':snapshot.get('role'),'authenticated_public_alias':alias,'replay_checked':replay})
            command('Show me my open windows','Completed')
            command('Switch to MYLES_CONTROL_QA Alpha','Completed')
            command('Minimize the current window','Completed')
            command('Switch to MYLES_CONTROL_QA Alpha','Completed')
            command('Close MYLES_CONTROL_QA','Failed')
            command('Close MYLES_CONTROL_QA Alpha','Completed',replay=True)
            command('Close MYLES_CONTROL_QA Beta','Completed',alias=True,replay=True)
            command('Close MYLES_CONTROL_QA Unsaved','Failed')
            command('Force close MYLES_CONTROL_QA Unsaved','Failed')
            command('Close MYLES_CONTROL_QA Missing','Failed')
            command('Hello?','Completed')
            print(json.dumps({'pass':True,'commands':results},indent=2))
        finally:
            stop.touch();child.wait(timeout=10)

if __name__=='__main__':run()
