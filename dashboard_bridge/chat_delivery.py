"""Durable, bounded chat acknowledgments independent of model execution."""
from __future__ import annotations
import json, os, re, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def fast_owner_command(message):
    from myles_runtime_v9 import desktop_action_request
    from myles_media import media_request
    media = media_request(message)
    if media and media.get('kind') in {'control','preferences'}: return True
    command = desktop_action_request(message) or {}
    return command.get('kind') in {'windows', 'windows_detail', 'windows_attention', 'app_status', 'minimize', 'focus', 'close'}

class DeliveryExecutors:
    """Reserve a worker for short owner controls even while inference is blocked."""
    def __init__(self):
        self.regular = ThreadPoolExecutor(max_workers=4, thread_name_prefix='myles-chat')
        self.fast = ThreadPoolExecutor(max_workers=1, thread_name_prefix='myles-owner-control')
    def submit(self, fn, scope, row, *args):
        return (self.fast if row.get('lane') == 'owner_fast' else self.regular).submit(fn, scope, row, *args)
    def shutdown(self, wait=True):
        self.regular.shutdown(wait=wait)
        self.fast.shutdown(wait=wait)

class DeliveryQueue:
    def __init__(self, directory):
        self.directory=Path(directory); self.lock=threading.RLock()
        self.executor=DeliveryExecutors()
        self.order=threading.Condition();self.pending={scope:[] for scope in ("public","owner","owner_fast")}
        self.records={}
        for scope in ("public","owner"):
            try: rows=json.loads(self.path(scope).read_text(encoding="utf-8")).get("deliveries",[])
            except (OSError,ValueError): rows=[]
            self.records[scope]=[r for r in rows if isinstance(r,dict)][-100:]
            for r in self.records[scope]:
                if r.get("status") in {"Sent","Running"} and not r.get("job_id"):
                    r.update(status="Failed",error="Tower restarted before completion could be verified. Check the result before retrying.",finished_at=time.time())
    def path(self,scope): return self.directory/("chat_delivery_"+scope+".json")
    def save(self,scope):
        self.directory.mkdir(parents=True,exist_ok=True)
        p=self.path(scope);tmp=p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"deliveries":self.records[scope][-100:]}),encoding="utf-8");os.replace(tmp,p)
    def submit(self,scope,request_id,message,handler,streaming=False,admit=None):
        if scope not in {"owner","public"} or not re.fullmatch(r"[A-Za-z0-9_-]{16,80}",str(request_id)):
            return 400,{"ok":False,"error":"Invalid chat request identifier"}
        with self.lock:
            lane = 'owner_fast' if scope == 'owner' and fast_owner_command(message) else scope
            rows=self.records[scope]
            existing=next((r for r in rows if r["client_id"]==request_id),None)
            if existing:
                if existing["message"]!=message:return 409,{"ok":False,"error":"Request identifier already belongs to another message"}
                return 202,{"ok":True,"delivery":dict(existing)}
            if admit is not None and not admit():
                return 429,{"ok":False,"error":"Public chat rate limit; wait before sending a new message."}
            if scope=='public' and sum(r['status'] in {'Sent','Running'} for r in rows)>=2:
                return 429,{"ok":False,"error":"Public chat is busy. Please wait."}
            active_rows = [r for values in self.records.values() for r in values if r['status'] in {'Sent','Running'}]
            if (lane == 'owner_fast' and sum(r.get('lane') == lane for r in active_rows)>=2) or (lane != 'owner_fast' and sum(r.get('lane') != 'owner_fast' for r in active_rows)>=4):
                return 429,{"ok":False,"error":"Myles is processing the current messages. Please wait."}
            row={"client_id":request_id,"message":message,"status":"Sent","accepted_at":time.time(),"lane":lane}
            rows.append(row);active=[r for r in rows if r["status"] in {"Sent","Running"}];terminal=[r for r in rows if r["status"] not in {"Sent","Running"}];self.records[scope]=sorted(active+terminal[-(100-len(active)):],key=lambda r:r["accepted_at"]);self.save(scope)
            with self.order:self.pending[lane].append(request_id)
            self.executor.submit(self.execute,scope,row,handler,streaming)
            return 202,{"ok":True,"delivery":dict(row)}
    def execute(self,scope,row,handler,streaming=False):
        lane = row.get('lane', scope)
        with self.order:
            while self.pending[lane][0]!=row['client_id']:self.order.wait()
        try:
            return self._execute(scope,row,handler,streaming)
        finally:
            with self.order:
                self.pending[lane].pop(0);self.order.notify_all()
    def _execute(self,scope,row,handler,streaming=False):
        with self.lock:
            row.update(status="Running",started_at=time.time());self.save(scope)
        try:
            code,data=handler(row["message"],lambda text:self.partial(scope,row,text)) if streaming else handler(row["message"])
            data=data if isinstance(data,dict) else {}
            reply=str(data.get("reply") or "")
            failed=not 200<=code<300 or data.get("ok") is False or reply.lower().startswith(("i couldn't", "i couldn’t", "i could not", "unable to", "failed to")) or any(x in reply.lower() for x in ["couldn't verify","couldn't launch","haven't verified","could not verify"])
            with self.lock:
                row.update(status="Failed" if failed else "Running" if data.get("job_id") or data.get("request_pending") else "Completed",reply=reply[:6000],reply_message_id=data.get("message_id"),user_message_id=data.get("user_message_id"),job_id=data.get("job_id"),finished_at=None if (data.get("job_id") or data.get("request_pending")) and not failed else time.time())
                if failed:row["error"]=str(data.get("error") or reply or "Command failed")[:1000]
                self.save(scope)
        except Exception as exc:
            with self.lock:
                row.update(status="Failed",error="Request failed: "+type(exc).__name__,finished_at=time.time());self.save(scope)
    def partial(self,scope,row,text):
        with self.lock:
            now=time.time();row.setdefault("first_token_at",now);row["partial_reply"]=str(text)[:6000];row["phase"]="Responding"
            if now-row.get("last_partial_write",0)>=1.0:
                row["last_partial_write"]=now;self.save(scope)
    def snapshot(self,scope,job_reader=None,result_reader=None):
        with self.lock:
            changed=False
            for row in self.records[scope]:
                limit = 20 if row.get('lane') == 'owner_fast' else 900 if row.get('job_id') else 180
                if row.get('status') in {'Sent','Running'} and time.time()-row.get('started_at',row['accepted_at']) > limit:
                    row.update(status='Failed',error='Execution deadline exceeded; completion is unconfirmed. This request will not be executed again on retry.',finished_at=time.time(),deadline_exceeded=True)
                    changed=True
                receipt=result_reader(row['client_id']) if result_reader and not row.get('core_result_adopted') else None
                if receipt and receipt.get('message')==row['message'] and isinstance(receipt.get('result'),dict):
                    result=receipt['result'];reply=str(result.get('reply') or '')
                    failed=result.get('ok') is False or reply.lower().startswith(("i couldn't", "i couldn’t", "i could not", "unable to", "failed to")) or any(x in reply.lower() for x in ["couldn't verify","couldn't launch","haven't verified","could not verify"])
                    row.update(core_result_adopted=True,reply=reply[:6000],reply_message_id=result.get('message_id'),user_message_id=result.get('user_message_id'),job_id=result.get('job_id'),status='Failed' if failed else 'Running' if result.get('job_id') else 'Completed',finished_at=receipt.get('finished_at'))
                    if failed:row['error']=reply[:1000]
                    else:row.pop('error',None)
                    changed=True
                if row.get("status")=="Running" and row.get("job_id") and job_reader:
                    job=job_reader(row["job_id"]) or {};state=job.get("state")
                    if not job:
                        row.update(status="Failed",error="Task record is unavailable; completion cannot be verified.",finished_at=time.time());changed=True;continue
                    row["phase"]=job.get("phase") or state
                    if state in {"done","completed","succeeded","failed","cancelled","blocked_auth"}:
                        row.update(status="Completed" if state in {"done","completed","succeeded"} else "Failed",finished_at=time.time())
                        if row["status"]=="Failed":row["error"]=str(job.get("error") or job.get("last_error") or state)[:1000]
                        if job.get('result'):
                            row['reply']=str(job['result'])[:6000]
                        changed=True
            if changed:self.save(scope)
            return [dict(r) for r in self.records[scope][-100:]]
