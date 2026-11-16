"""Restore the exact published index and page pixels without paid extraction."""
import argparse
import gzip
import json

from starter.day6_backend.models import Chunk
from starter.day6_backend.store import PgVectorStore
from .analyze import read
from .retrieval import STRATEGY, Retriever, connection
from .source import DATA, PDF, PDF_HASH, digest, render_page


def main():
    import psycopg
    parser=argparse.ArgumentParser()
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    if digest(PDF)!=PDF_HASH:raise ValueError('Download the exact source PDF first')
    manifest=read(DATA/'index-manifest.json')
    if digest(DATA/'index.json.gz')!=manifest['snapshot_sha256']:raise ValueError('Snapshot checksum mismatch')
    if digest(DATA/'chunks.json')!=manifest['chunks_sha256']:raise ValueError('Chunks checksum mismatch')
    images=read(DATA/'render-manifest.json')
    for page in range(1,351):
        if args.check_only and not (DATA/'pages'/f'p{page:03}.jpg').exists():raise ValueError('Render missing source pages with restore first')
        image=render_page(page)
        if digest(image)!=images['pages'][str(page)]:raise ValueError('Regenerated pixels differ; use the pinned PDFium/Pillow versions')
    with gzip.open(DATA/'index.json.gz','rt',encoding='utf-8') as f:snapshot=json.load(f)
    store=PgVectorStore(connection(),manifest['dimensions'])
    if not args.check_only:store.create_schema()
    with psycopg.connect(connection()) as conn:
        count=conn.execute('SELECT count(*) FROM lab_chunks WHERE strategy=%s',(STRATEGY,)).fetchone()[0]
    verifier=Retriever.__new__(Retriever);verifier.chunks=read(DATA/'chunks.json')
    if count:
        verifier.verify_index()  # Refuse to overwrite any conflicting live dataset.
    elif args.check_only:
        raise ValueError('Advanced index is empty')
    else:
        for start in range(0,len(snapshot['chunks']),128):
            rows=snapshot['chunks'][start:start+128]
            store.upsert(STRATEGY,[Chunk(c['id'],c['source_id'],c['source'],c['page'],c['text'],c['metadata']) for c in rows],
                         snapshot['vectors'][start:start+128])
        verifier.verify_index()
    print('Verified 350 exact page images and',len(snapshot['chunks']),'live chunks/vectors; other strategies unchanged.')


if __name__=='__main__':main()
