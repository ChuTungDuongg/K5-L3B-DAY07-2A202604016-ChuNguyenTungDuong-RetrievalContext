"""Responses API with counted inputs, reserved cost and durable usage events."""
import base64
import json
import time
from decimal import Decimal
from uuid import uuid4

from .budget import Budget, save
from .source import ROOT, digest

MODEL='gpt-6-luna'
RESULTS=ROOT/'advanced/results'


def object_schema(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


def text_schema(schema,name):
    return {'format':{'type':'json_schema','name':name,'strict':True,'schema':schema}}


class API:
    def __init__(self):
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv(ROOT/'.env')
        self.client=OpenAI(timeout=75,max_retries=0)
        self.budget=Budget(RESULTS/'budget.json','5')

    def call(self,label,instructions,text,schema,images=(),max_output=4000):
        content=[{'type':'input_text','text':text}];image_meta=[]
        for page,path in images:
            content.append({'type':'input_text','text':f'Original PDF physical page {page}. Coordinates normalized top-left.'})
            content.append({'type':'input_image','detail':'high',
                            'image_url':'data:image/jpeg;base64,'+base64.b64encode(path.read_bytes()).decode()})
            image_meta.append({'page':page,'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path)})
        args={'model':MODEL,'instructions':instructions,'input':[{'role':'user','content':content}],
              'text':text_schema(schema,'evidence_action'),'reasoning':{'effort':'low'}}
        started=time.perf_counter()
        count=self.client.responses.input_tokens.count(**args)
        tokens=count.input_tokens
        if type(tokens) is not int or not 0<tokens<260000: raise ValueError('Input outside audited short-context range')
        # Reserve above the most expensive short-context input category (12h writes)
        # plus full output allowance, with padding for counting/schema differences.
        maximum=(Decimal(tokens+2048)*Decimal('.25')+Decimal(max_output)*Decimal('.50'))/1_000_000*Decimal('1.1')
        ticket=self.budget.reserve(label,maximum)
        event={'id':ticket,'label':label,'model':MODEL,'counted_input_tokens':tokens,
               'maximum_output_tokens':max_output,'images':image_meta,'instructions_sha256':__import__('hashlib').sha256(instructions.encode()).hexdigest()}
        try:
            response=self.client.responses.create(**args,max_output_tokens=max_output,store=False)
            usage=response.usage.model_dump() if response.usage else None
            event.update(usage=usage,response_id=response.id,response_status=response.status,
                         output_text=response.output_text)
            self.budget.finish(ticket,usage,response_id=response.id,response_status=response.status)
            if response.status!='completed': raise RuntimeError(f'Response status {response.status}')
            result=json.loads(response.output_text)
            return result,event
        except Exception as exc:
            if 'response_id' not in event:
                self.budget.finish(ticket,None,error=type(exc).__name__)
            event.update(error_type=type(exc).__name__,error=str(exc))
            raise
        finally:
            event['elapsed_seconds']=time.perf_counter()-started
            save(RESULTS/'api-events'/f'{ticket}.json',event)
