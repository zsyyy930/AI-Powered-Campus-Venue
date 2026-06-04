"""文本向量化：语义模型（需联网下载）或 TF-IDF（离线备选）"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

try:
    import config
except ImportError:

    class config:  # type: ignore
        EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
        HF_ENDPOINT = "https://hf-mirror.com"
        EMBEDDING_BACKEND = "tfidf"
        DATA_DIR = "data"


_st_model = None
_tfidf_vectorizer = None


def get_backend() -> str:
    return getattr(config, "EMBEDDING_BACKEND", "sentence_transformers").lower()


def _tfidf_path() -> Path:
    return Path(getattr(config, "DATA_DIR", "data")) / "tfidf_vectorizer.joblib"


def _setup_hf_mirror() -> None:
    endpoint = getattr(config, "HF_ENDPOINT", None) or os.environ.get("HF_ENDPOINT")
    if endpoint and str(endpoint).strip():
        endpoint = endpoint.rstrip("/")
        os.environ["HF_ENDPOINT"] = endpoint
        os.environ["HUGGINGFACE_HUB_BASE_URL"] = endpoint
        print(f"[embedder] HuggingFace 镜像: {endpoint}")


def _use_local_only() -> bool:
    return bool(getattr(config, "EMBEDDING_LOCAL_ONLY", True))


def _resolve_st_repo_id(model_name: str) -> str:
    """与 HuggingFace 缓存目录一致：sentence-transformers/模型名。"""
    if "/" in model_name:
        return model_name
    return f"sentence-transformers/{model_name}"


def _get_st_model():
    global _st_model
    if _st_model is None:
        _setup_hf_mirror()
        from sentence_transformers import SentenceTransformer

        model_name = getattr(config, "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        repo_id = _resolve_st_repo_id(model_name)
        local_only = _use_local_only()
        if local_only:
            print(f"[embedder] 加载语义模型 {repo_id}（仅本地缓存，不访问 huggingface.co）...")
        else:
            print(f"[embedder] 加载语义模型 {repo_id}（可能需要联网）...")

        from huggingface_hub import snapshot_download

        try:
            local_dir = snapshot_download(
                repo_id=repo_id,
                repo_type="model",
                local_files_only=local_only,
            )
            _st_model = SentenceTransformer(local_dir, local_files_only=local_only)
            print(f"[embedder] 模型就绪（本地目录）")
        except Exception as e:
            if local_only:
                raise RuntimeError(
                    "本地模型缓存不完整。请任选其一："
                    "① 开 VPN/镜像后设 EMBEDDING_LOCAL_ONLY=False 运行一次 indexer --rebuild；"
                    "② config 设 HF_ENDPOINT='https://hf-mirror.com' 且 EMBEDDING_LOCAL_ONLY=False 补全下载；"
                    "③ 改用 EMBEDDING_BACKEND='tfidf'。"
                ) from e
            _st_model = SentenceTransformer(repo_id)
    return _st_model


def warmup() -> None:
    """启动预热：进程启动时先加载模型，避免用户第一句等待过久。"""
    if get_backend() != "sentence_transformers":
        return
    print("[embedder] 启动预热：预加载向量模型…")
    embed_query("预热")
    print("[embedder] 预热完成")


def _get_tfidf_vectorizer():
    global _tfidf_vectorizer
    if _tfidf_vectorizer is None:
        path = _tfidf_path()
        if path.exists():
            import joblib

            _tfidf_vectorizer = joblib.load(path)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer

            # 中文无空格分词，用字级 n-gram
            _tfidf_vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
    return _tfidf_vectorizer


def _embed_st(texts: list[str]) -> np.ndarray:
    model = _get_st_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vectors, dtype=np.float32)


def _embed_tfidf(texts: list[str], fit: bool = False) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer

    global _tfidf_vectorizer
    if fit or not _tfidf_path().exists():
        print("[embedder] 使用 TF-IDF 构建向量（离线，无需下载模型）")
        _tfidf_vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
        matrix = _tfidf_vectorizer.fit_transform(texts)
        _data_dir().mkdir(parents=True, exist_ok=True)
        import joblib

        joblib.dump(_tfidf_vectorizer, _tfidf_path())
    else:
        _tfidf_vectorizer = _get_tfidf_vectorizer()
        matrix = _tfidf_vectorizer.transform(texts)

    dense = matrix.toarray().astype(np.float32)
    norms = np.linalg.norm(dense, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return dense / norms


def _data_dir() -> Path:
    return Path(getattr(config, "DATA_DIR", "data"))


def embed_texts(texts: list[str], *, fit_tfidf: bool = False) -> np.ndarray:
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)

    backend = get_backend()
    if backend == "tfidf":
        return _embed_tfidf(texts, fit=fit_tfidf or len(texts) > 1)
    return _embed_st(texts)


def embed_query(query: str) -> np.ndarray:
    if get_backend() == "tfidf":
        return _embed_tfidf([query], fit=False)[0]
    return _embed_st([query])[0]
