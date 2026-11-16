"""Conservative shared request budget. Unknown usage retains the reservation."""
import json
import os
import time
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from scripts.summarize_results import estimate_usage


class BudgetExceeded(RuntimeError):
    pass


def save(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid4().hex+'.tmp')
    temporary.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temporary,path)


class Budget:
    def __init__(self,path,cap='5'):
        self.path=Path(path);self.cap=Decimal(cap)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.lock():
            if not self.path.exists(): save(self.path,{'cap_usd':str(self.cap),'requests':[]})
            if Decimal(self.load()['cap_usd']) != self.cap:
                raise ValueError('Existing budget cap differs; do not reset recorded spend')

    @contextmanager
    def lock(self):
        lock=self.path.with_suffix('.lock');deadline=time.monotonic()+10
        while True:
            try:
                fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
                break
            except FileExistsError:
                if time.monotonic()>deadline: raise RuntimeError('Budget lock busy; inspect stale lock before retry')
                time.sleep(.05)
        try: yield
        finally:
            os.close(fd);lock.unlink()

    def load(self): return json.loads(self.path.read_text(encoding='utf-8'))

    def reserve(self,label,maximum):
        maximum=Decimal(maximum)
        if maximum<=0: raise ValueError('Reservation must be positive')
        with self.lock():
            obj=self.load()
            if any(r.get('reservation_breach') for r in obj['requests']):
                raise BudgetExceeded('Prior reservation breach requires an explicit budget audit')
            exposure=sum((Decimal(r.get('estimated_usd',r['reserved_usd'])) for r in obj['requests']),Decimal(0))
            if exposure+maximum>self.cap: raise BudgetExceeded(f'USD {self.cap} budget would be exceeded')
            ticket=uuid4().hex
            obj['requests'].append({'id':ticket,'label':label,'status':'reserved','reserved_usd':str(maximum)})
            save(self.path,obj)
            return ticket

    def finish(self,ticket,usage,error=None,**metadata):
        with self.lock():
            obj=self.load();row=next(r for r in obj['requests'] if r['id']==ticket)
            if row['status']!='reserved': raise ValueError('Reservation already settled')
            row.update(metadata,status='usage_recorded' if usage is not None else 'unknown_usage',error=error)
            if usage is not None:
                row['usage']=usage
                cost=Decimal(estimate_usage(usage)['estimated_usd'])
                row['estimated_usd']=str(cost.normalize())
                if cost>Decimal(row['reserved_usd']):
                    row['reservation_breach']=True
                    save(self.path,obj)
                    raise BudgetExceeded('Recorded charge exceeds reservation; stop and audit')
            save(self.path,obj)

    def snapshot(self):
        with self.lock(): obj=self.load()
        known=sum((Decimal(r['estimated_usd']) for r in obj['requests'] if 'estimated_usd' in r),Decimal(0))
        unknown=sum((Decimal(r['reserved_usd']) for r in obj['requests'] if 'estimated_usd' not in r),Decimal(0))
        return {**obj,'recorded_estimated_usd':str(known.normalize()),
                'unknown_reserved_usd':str(unknown.normalize()),'exposure_usd':str((known+unknown).normalize())}
