"""Owner request receipts: one execution, recoverable results after HTTP timeouts."""
import json, os, re, threading, time
from pathlib import Path

class OwnerReceipts:
    def __init__(self, path):
        self.path=Path(path);self.lock=threading.RLock()
        try:self.rows=json.loads(self.path.read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):self.rows={}
    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        # Active requests survive pruning. Retain the latest 1,000 terminal IDs.
        active={k:v for k,v in self.rows.items() if 'result' not in v}
        done={k:v for k,v in list(self.rows.items()) if 'result' in v}
        self.rows={**dict(list(done.items())[-1000:]),**active}
        temporary=self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.rows),encoding='utf-8');os.replace(temporary,self.path)
    def begin(self, identifier, message, source):
        if not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',str(identifier)):
            return 400,{'ok':False,'error':'Invalid request identifier'}
        with self.lock:
            old=self.rows.get(identifier)
            if old:
                if old['message']!=message or old['source']!=source:
                    return 409,{'ok':False,'error':'Request identifier belongs to another message'}
                if 'result' in old:return 200,old['result']
                return 202,{'ok':True,'request_pending':True,'reply':'This request was already accepted. Its result is not yet verified.'}
            self.rows[identifier]={'message':message,'source':source,'accepted_at':time.time()};self.save()
            return None
    def finish(self, identifier, result):
        with self.lock:
            self.rows[identifier].update(result=result,finished_at=time.time());self.save()
