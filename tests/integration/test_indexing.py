class FakeEmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        return [
            float(len(text)),
            float(len(text.split())),
        ]