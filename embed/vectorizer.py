# embed/vectorizer.py
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_path: str = "vector_index.faiss",
        meta_path: str = "metadata.npy"
    ):
        # SentenceTransformer device safe init
        try:
            self.model = SentenceTransformer(model_name, device="cuda")
        except Exception:
            self.model = SentenceTransformer(model_name, device="cpu")

        self.index_path = index_path
        self.meta_path = meta_path

        self.emb_dim = self.model.get_sentence_embedding_dimension()

        # Try GPU resources; fall back to CPU index if unavailable
        try:
            self.gpu_res = faiss.StandardGpuResources()
            if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
                cpu_index = faiss.read_index(self.index_path)
                self.index = faiss.index_cpu_to_gpu(self.gpu_res, 0, cpu_index)
                self.metadata = np.load(self.meta_path, allow_pickle=True).tolist()
            else:
                cpu_index = faiss.IndexFlatL2(self.emb_dim)
                self.index = faiss.index_cpu_to_gpu(self.gpu_res, 0, cpu_index)
                self.metadata = []
        except Exception:
            # fallback to CPU-only index
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                self.metadata = np.load(self.meta_path, allow_pickle=True).tolist() if os.path.exists(self.meta_path) else []
            else:
                self.index = faiss.IndexFlatL2(self.emb_dim)
                self.metadata = []

    def embed(self, texts):
        return self.model.encode(texts, batch_size=32, show_progress_bar=False)

    def add_with_return(self, chunks, doc_id, filename, pages):
        embeddings = self.embed(chunks)
        stored = []
        for emb, text in zip(embeddings, chunks):
            self.index.add(emb.reshape(1, -1))
            self.metadata.append({
                "doc_id": doc_id,
                "text": text,
                "filename": filename,
                "pages": pages
            })
            stored.append(text)
        return stored

    def search(self, query, top_k=5):
        q_emb = self.embed([query])
        try:
            distances, indices = self.index.search(q_emb, top_k)
        except Exception:
            # empty index or cpu/gpu mismatch -> return empty
            return []
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.metadata):
                results.append((self.metadata[idx]["text"], float(dist)))
        return results

    def save(self):
        try:
            # if GPU index, convert to CPU for write
            cpu_index = faiss.index_gpu_to_cpu(self.index)
            faiss.write_index(cpu_index, self.index_path)
        except Exception:
            try:
                faiss.write_index(self.index, self.index_path)
            except Exception:
                pass
        np.save(self.meta_path, np.array(self.metadata, dtype=object))
