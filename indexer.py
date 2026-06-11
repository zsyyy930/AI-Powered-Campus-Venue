"""P1：将 knowledge/*.md 切块并保存；P2：一并构建向量索引"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

try:
    import config
except ImportError:
    raise ImportError("请先复制 config.example.py 为 config.py")

from embedder import embed_texts


def _data_dir() -> Path:
    return Path(getattr(config, "DATA_DIR", "data"))


def chunks_path() -> Path:
    name = getattr(config, "CHUNKS_FILE", "chunks.json")
    return _data_dir() / name


def embeddings_path() -> Path:
    name = getattr(config, "EMBEDDINGS_FILE", "embeddings.npz")
    return _data_dir() / name


def chunk_markdown(text: str, source: str) -> list[dict]:
    """
    按 Markdown 二级标题 ## 切块，无 ## 时整篇为一组。
    记录每个段落的起始行号和结束行号（用于引用标注）。
    """
    min_chars = getattr(config, "CHUNK_MIN_CHARS", 30)
    stem = Path(source).stem
    text = text.strip()
    if not text:
        return []

    # 把全文按行拆分，方便计算行号
    lines = text.splitlines()
    
    # 找到所有 ## 标题的行号
    header_indices = []
    for i, line in enumerate(lines):
        if re.match(r'^##\s+', line):
            header_indices.append(i)
    
    parts = []  # 每个元素: (start_line, end_line, content)
    
    if len(header_indices) == 0:
        # 没有 ## 标题，整篇作为一个段落
        content = '\n'.join(lines)
        if len(content) >= min_chars:
            parts.append((0, len(lines) - 1, content))
    else:
        # 有 ## 标题，按标题切分
        for idx, start_idx in enumerate(header_indices):
            # 确定结束行：下一个标题的前一行，或文件末尾
            if idx + 1 < len(header_indices):
                end_idx = header_indices[idx + 1] - 1
            else:
                end_idx = len(lines) - 1
            # 从标题行开始到结束行
            content = '\n'.join(lines[start_idx:end_idx + 1])
            if len(content) >= min_chars:
                parts.append((start_idx, end_idx, content))
    
    chunks: list[dict] = []
    for i, (start_line, end_line, part) in enumerate(parts):
        part = part.strip()
        # 降低最小字符数限制，确保"基本信息"等重要部分不会被过滤掉
        if len(part) < 10:
            continue
        part_lines = part.splitlines()
        title = part_lines[0].lstrip("#").strip() if part_lines else stem
        chunk_id = f"{stem}_{i}"
        chunks.append({
            "id": chunk_id,
            "source": source,
            "title": title,
            "text": part,
            "start_line": start_line + 1,  # 转为 1-based 行号（人类习惯）
            "end_line": end_line + 1,
        })
    return chunks

def build_chunks() -> list[dict]:
    root = Path(config.KNOWLEDGE_DIR)
    all_chunks: list[dict] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        all_chunks.extend(chunk_markdown(text, path.name))
    return all_chunks


def save_chunks(chunks: list[dict]) -> Path:
    out = chunks_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def save_embeddings(chunks: list[dict]) -> Path:
    from embedder import get_backend

    texts = [c["text"] for c in chunks]
    fit = get_backend() == "tfidf"
    vectors = embed_texts(texts, fit_tfidf=fit)
    out = embeddings_path()
    np.savez_compressed(
        out,
        embeddings=vectors,
        ids=[c["id"] for c in chunks],
        backend=get_backend(),
    )
    return out


def rebuild_index() -> None:
    chunks = build_chunks()
    if not chunks:
        print(f"[indexer] knowledge/ 下没有有效 .md，请先添加资料。")
        return

    md_count = len(list(Path(config.KNOWLEDGE_DIR).glob("*.md")))
    cp = save_chunks(chunks)
    print(f"[indexer] 知识库文档 {md_count} 个 .md，切块后 {len(chunks)} 段 → {cp}")
    if md_count < 15:
        print(f"[indexer] 提示：任务书要求 ≥15 个场馆文档，当前 {md_count} 个，请继续在 knowledge/ 添加 .md")

    if getattr(config, "BUILD_EMBEDDINGS_ON_INDEX", True):
        try:
            ep = save_embeddings(chunks)
            print(f"[indexer] 已保存向量索引 → {ep}")
        except Exception as e:
            print(f"[indexer] 向量构建失败（P1 段落索引已保存）: {e}")
            print("  → 可开 VPN/镜像后重试 --rebuild，见 docs/P1P2入门实战.md「模型下载失败」")
    else:
        print("[indexer] 已跳过向量（BUILD_EMBEDDINGS_ON_INDEX=False）")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="构建知识库段落与向量索引")
    parser.add_argument("--rebuild", action="store_true", help="重新扫描 knowledge 并生成 data/")
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="仅 P1 切块，不下载向量模型（网络不好时用）",
    )
    args = parser.parse_args()
    if args.rebuild:
        if args.no_embed:
            import config as cfg

            cfg.BUILD_EMBEDDINGS_ON_INDEX = False
        rebuild_index()
    else:
        print("用法: python indexer.py --rebuild")


if __name__ == "__main__":
    main()
