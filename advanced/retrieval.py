"""Full-document hybrid retrieval, separate from all benchmark files."""
import gzip
import json
import math
import os
import re

from starter.baseline import TfidfIndex
from starter.day6_backend.models import Chunk
from starter.day6_backend.store import PgVectorStore
from .budget import save
from .source import DATA, ROOT, PDF, PDF_HASH, digest

STRATEGY='ADV-WDR2021-v1'
MODEL='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'


def connection():
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    return os.getenv('ADV_DATABASE_URL','postgresql://day7:day7_local_only@127.0.0.1:55434/day7_lab')


def build_index():
    from starter.day6_backend.embeddings import MyEmbedder
    chunks=json.loads((DATA/'chunks.json').read_text(encoding='utf-8'))
    model=MyEmbedder(MODEL);store=PgVectorStore(connection(),model.dimensions)
    store.create_schema()
    vectors=[]
    for start in range(0,len(chunks),128):
        batch=chunks[start:start+128]
        encoded=model.embed_documents([c['text'] for c in batch])
        store.upsert(STRATEGY,[Chunk(c['id'],c['source_id'],c['source'],c['page'],c['text'],c['metadata']) for c in batch],encoded)
        vectors.extend(encoded)
        print(f'Indexed {min(start+128,len(chunks))}/{len(chunks)} chunks',flush=True)
    snapshot={'strategy':STRATEGY,'model':MODEL,'dimensions':model.dimensions,
              'chunks_sha256':digest(DATA/'chunks.json'),'chunks':chunks,'vectors':vectors}
    with gzip.GzipFile(DATA/'index.json.gz','wb',mtime=0) as f:
        f.write(json.dumps(snapshot,ensure_ascii=False,separators=(',',':')).encode())
    save(DATA/'index-manifest.json',{'strategy':STRATEGY,'model':MODEL,'dimensions':model.dimensions,
                                   'chunks':len(chunks),'physical_pages':350,'chunks_sha256':snapshot['chunks_sha256'],
                                   'snapshot_sha256':digest(DATA/'index.json.gz'),
                                   'base_A_B_modified':False,'dense_search':'exact cosine distance',
                                   'chunking':'350 characters with 50-character overlap; visual label repeated',
                                   'limitation':'Embedding model has 128-token input; long technical strings may truncate. Lexical branch and original images remain available.'})


class Retriever:
    def __init__(self):
        from starter.day6_backend.embeddings import MyEmbedder
        self.pages={p['page']:p for p in json.loads((DATA/'pages.json').read_text(encoding='utf-8'))}
        self.chunks=json.loads((DATA/'chunks.json').read_text(encoding='utf-8'))
        self.regions=json.loads((DATA/'regions.json').read_text(encoding='utf-8'))
        self.by_page={p:[] for p in self.pages}
        for c in self.chunks:self.by_page[c['page']].append(c)
        self.lexical=TfidfIndex([{'id':str(p),'text':'\n'.join(c['text'] for c in self.by_page[p]),'page':p}
                                  for p in self.pages if self.by_page[p]])
        self.model=MyEmbedder(MODEL)
        self.store=PgVectorStore(connection(),self.model.dimensions)
        self.verify_index()

    def verify_index(self):
        import psycopg
        if digest(PDF)!=PDF_HASH:raise ValueError('Original PDF differs from indexed source')
        manifest=json.loads((DATA/'index-manifest.json').read_text(encoding='utf-8'))
        if digest(DATA/'index.json.gz')!=manifest['snapshot_sha256'] or digest(DATA/'chunks.json')!=manifest['chunks_sha256']:
            raise ValueError('Index snapshot/manifest mismatch')
        with gzip.open(DATA/'index.json.gz','rt',encoding='utf-8') as f:snapshot=json.load(f)
        with psycopg.connect(connection()) as conn:
            rows=conn.execute('SELECT chunk_id,content,metadata,embedding::text,page,document_id,source FROM lab_chunks WHERE strategy=%s',(STRATEGY,)).fetchall()
        by_id={row[0]:row for row in rows}
        if set(by_id)!={c['id'] for c in self.chunks}:raise ValueError('Live advanced index IDs changed')
        for c,vector in zip(snapshot['chunks'],snapshot['vectors']):
            row=by_id[c['id']];actual=json.loads(row[3])
            if (row[1]!=c['text'] or row[2]!=c['metadata'] or row[4]!=c['page'] or
                    row[5]!=c['source_id'] or row[6]!=c['source'] or len(actual)!=len(vector) or any(
                    not math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-7) for a,b in zip(actual,vector))):
                raise ValueError('Live advanced index content/vector changed')

    def search(self,query,top_k=12):
        if not isinstance(query,str) or not query.strip():raise ValueError('Empty search query')
        lexical=self.lexical.search(query,top_k=40)
        dense=self.store.search(STRATEGY,self.model.embed_query(query),top_k=60,filters=None)
        scores={};ranks={};seen=set()
        for rank,row in enumerate(lexical,1):
            p=row['page'];scores[p]=scores.get(p,0)+1/(60+rank)
            ranks.setdefault(p,{})['lexical']=rank
        for rank,row in enumerate(dense,1):
            p=row['page']
            if p in seen: continue
            seen.add(p);scores[p]=scores.get(p,0)+1/(60+rank)
            ranks.setdefault(p,{})['dense_chunk_rank']=rank
        # Explicit source identifiers are parsed only from the user's/model's query.
        labels=re.findall(r'\b(?:figure|table|map)\s+(?:[a-z]\d?\.)?\d+(?:\.\d+)*',query.casefold())
        for p,page in self.pages.items():
            if p>20 and any(label in [x.casefold() for x in page['labels']] for label in labels):
                scores[p]=scores.get(p,0)+.05;ranks.setdefault(p,{})['query_locator_match']=True
        rows=[]
        for p in sorted(scores,key=lambda p:(-scores[p],p))[:top_k]:
            page=self.pages[p]
            regions=[r for r in self.regions if r['page']==p]
            rows.append({'page':p,'printed_page':page['printed_page'],'score':scores[p],'ranks':ranks[p],
                         'text':page['text'],'regions':regions,'labels':page['labels']})
        return rows


if __name__=='__main__':build_index()
