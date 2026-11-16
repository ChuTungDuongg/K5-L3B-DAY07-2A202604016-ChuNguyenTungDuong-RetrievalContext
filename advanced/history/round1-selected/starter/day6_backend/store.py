"""Day 6 PostgreSQL/pgvector storage, reused locally for Day 7."""
from typing import Any
import psycopg
from psycopg import sql
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        """Lưu cấu hình kết nối và số chiều của embedding."""
        if not database_url:
            raise ValueError("Thiếu đường dẫn kết nối database")
        if not isinstance(dimensions, int) or isinstance(dimensions, bool) or dimensions <= 0:
            raise ValueError("Số chiều embedding phải là số nguyên dương")
        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        """Tạo bảng lưu chunk và vector nếu bảng chưa tồn tại."""
        statement = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS lab_chunks (
                strategy TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                source TEXT NOT NULL,
                page INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB NOT NULL,
                embedding vector({dimensions}) NOT NULL,
                PRIMARY KEY (strategy, chunk_id)
            )
            """
        ).format(dimensions=sql.Literal(self.dimensions))

        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement)

    def upsert(
        self,
        strategy: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> None:
        """Thêm hoặc cập nhật các chunk cùng vector tương ứng."""
        import json
        import math

        from psycopg.types.json import Jsonb

        if not strategy:
            raise ValueError("Thiếu tên cấu hình")

        if len(chunks) != len(vectors):
            raise ValueError("Số chunk và số vector phải bằng nhau")

        rows = []

        for chunk, vector in zip(chunks, vectors):
            if len(vector) != self.dimensions:
                raise ValueError(
                    f"Vector của {chunk.chunk_id} không đúng số chiều"
                )

            if not all(math.isfinite(value) for value in vector):
                raise ValueError(
                    f"Vector của {chunk.chunk_id} có giá trị không hợp lệ"
                )

            rows.append(
                (
                    strategy,
                    chunk.chunk_id,
                    chunk.document_id,
                    chunk.source,
                    chunk.page,
                    chunk.text,
                    Jsonb(chunk.metadata),
                    json.dumps(vector),
                )
            )

        statement = """
            INSERT INTO lab_chunks (
                strategy, chunk_id, document_id, source,
                page, content, metadata, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
            ON CONFLICT (strategy, chunk_id)
            DO UPDATE SET
                document_id = EXCLUDED.document_id,
                source = EXCLUDED.source,
                page = EXCLUDED.page,
                content = EXCLUDED.content,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding
        """

        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(statement, rows)

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Tìm các chunk gần câu hỏi nhất bằng cosine similarity."""
        import json
        import math

        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        if not strategy:
            raise ValueError("Thiếu tên cấu hình")

        if len(query_vector) != self.dimensions:
            raise ValueError("Vector câu hỏi không đúng số chiều")

        if not all(math.isfinite(value) for value in query_vector):
            raise ValueError("Vector câu hỏi có giá trị không hợp lệ")

        if not any(value != 0 for value in query_vector):
            raise ValueError("Không thể tìm cosine với vector toàn số 0")

        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise ValueError("top_k phải là số nguyên dương")

        if filters and (
            set(filters) != {"section"}
            or not isinstance(filters["section"], str)
        ):
            raise ValueError("Hiện chỉ hỗ trợ lọc theo section")

        query = """
            SELECT
                chunk_id,
                document_id,
                source,
                page,
                content AS text,
                metadata,
                1 - (embedding <=> %s::vector) AS score
            FROM lab_chunks
            WHERE strategy = %s
        """

        params = [json.dumps(query_vector), strategy]

        if filters:
            query += " AND metadata @> %s"
            params.append(Jsonb(filters))

        query += " ORDER BY score DESC NULLS LAST LIMIT %s"
        params.append(top_k)

        with psycopg.connect(self.database_url) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
