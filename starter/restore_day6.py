"""Restore the public Day 6 A index without overwriting a different existing index."""
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_snapshot(data):
    dimensions = data.get('dimensions')
    if type(dimensions) is not int or dimensions < 1 or data.get('strategy') != 'A':
        raise ValueError('Invalid strategy or dimensions')
    rows = data.get('chunks')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Snapshot must contain chunks')
    seen = set()
    for row in rows:
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in ('id','source_id','source','text')):
            raise ValueError('Missing chunk identity or text')
        if row['id'] in seen or type(row.get('page')) is not int or row['page'] < 1 or not isinstance(row.get('metadata'), dict):
            raise ValueError('Duplicate ID or invalid page/metadata')
        seen.add(row['id'])
        vector = row.get('embedding')
        if not isinstance(vector, list) or len(vector) != dimensions:
            raise ValueError('Invalid vector dimension')
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in vector) or not any(vector):
            raise ValueError('Invalid vector values')


def verify_existing(existing, expected):
    stored = {row['id']:row for row in existing}
    if len(stored) != len(existing) or set(stored) != {row['id'] for row in expected}:
        raise ValueError('Existing strategy A is different; refusing to overwrite')
    for row in expected:
        before = stored[row['id']]
        if any(before[k] != row[k] for k in ('source_id','source','page','text','metadata')):
            raise ValueError('Existing strategy A is different; refusing to overwrite')
        if len(before['embedding']) != len(row['embedding']) or any(
                not math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-7) for a,b in zip(before['embedding'],row['embedding'])):
            raise ValueError('Existing vectors are different; refusing to overwrite')


def main():
    parser = argparse.ArgumentParser(description='Khôi phục 273 vector A từ snapshot Day 6')
    parser.add_argument('--check-only', action='store_true', help='Chỉ đối chiếu database, không tạo hoặc ghi bảng')
    args = parser.parse_args()
    snapshot = ROOT / 'data/day6_index_A.json.gz'
    expected_hash = (ROOT / 'data/day6_index_A.sha256').read_text(encoding='utf-8').split()[0]
    if hashlib.sha256(snapshot.read_bytes()).hexdigest() != expected_hash:
        raise ValueError('Snapshot checksum mismatch')
    with gzip.open(snapshot, 'rt', encoding='utf-8') as source:
        data = json.load(source)
    validate_snapshot(data)
    from dotenv import load_dotenv
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
    load_dotenv(ROOT / '.env')
    if not os.getenv('DATABASE_URL'):
        raise SystemExit('DATABASE_URL missing from .env')
    with psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row) as conn:
        if args.check_only:
            conn.execute('SET TRANSACTION READ ONLY')
        else:
            conn.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('day7-restore-A',))
            conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            conn.execute(sql.SQL('''CREATE TABLE IF NOT EXISTS public.lab_chunks (
                strategy TEXT NOT NULL, chunk_id TEXT NOT NULL, document_id TEXT NOT NULL,
                source TEXT NOT NULL, page INTEGER NOT NULL, content TEXT NOT NULL,
                metadata JSONB NOT NULL, embedding vector({dimension}) NOT NULL,
                PRIMARY KEY (strategy, chunk_id))''').format(dimension=sql.Literal(data['dimensions'])))
            conn.execute('LOCK TABLE public.lab_chunks IN SHARE ROW EXCLUSIVE MODE')
        existing = conn.execute('''SELECT chunk_id AS id, document_id AS source_id, source,
                page, content AS text, metadata, embedding::text AS embedding
                FROM public.lab_chunks WHERE strategy=%s''', ('A',)).fetchall()
        for row in existing:
            row['embedding'] = json.loads(row['embedding'])
        if existing or args.check_only:
            verify_existing(existing, data['chunks'])
            print(f"Index A khớp snapshot: {len(existing)} chunk, {data['dimensions']} chiều. Không ghi dữ liệu.")
        else:
            with conn.cursor() as cur:
                cur.executemany('''INSERT INTO public.lab_chunks
                    (strategy,chunk_id,document_id,source,page,content,metadata,embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::vector)''',
                    [('A',row['id'],row['source_id'],row['source'],row['page'],row['text'],
                      Jsonb(row['metadata']),json.dumps(row['embedding'])) for row in data['chunks']])
            print(f"Đã khôi phục {len(data['chunks'])} vector A trong một transaction.")


if __name__ == '__main__':
    main()
