"""Concrete embedding implementation copied from Day 6."""
class MyEmbedder:
    """Tạo embedding bằng model Sentence Transformers chạy local."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        revision = ('e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
                    if model_name == 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' else None)
        self.model = SentenceTransformer(model_name, revision=revision)
        self.dimensions = self.model.get_embedding_dimension()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Tạo một vector cho mỗi đoạn văn bản."""
        if not texts:
            return []

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return vectors.tolist()

    def embed_query(self, question: str) -> list[float]:
        """Tạo vector câu hỏi bằng cùng model với tài liệu."""
        return self.embed_documents([question])[0]
