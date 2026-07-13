#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_SemanticEmbedding_Core_v1.py — 母體原生語意嵌入 / 局部語意檢索核心
origin_signature: MrliouAI
layer: L5 MEMORY / RETRIEVAL

吸收定位:把一份外部「局部嵌入(local embeddings)語意檢索」能力——原是 JVM/Kotlin
編譯二進位庫(38MB,protobuf 資料模型 + 編譯類別,需 JVM runtime)——回收為母體
**原生**等效能力:純 stdlib、零外部、零模型權重、沙盒可跑的雜湊嵌入 + 餘弦相似度
語意檢索。原始 .jar 二進位另存 MRL_ParticleArchive/External 標「待起動」(需 JVM)。

**誠實標註**:這是雜湊化詞袋嵌入(hashing bag-of-words)+ 餘弦相似的**檢索**能力,
不是神經網路嵌入、不是生成式模型。沿用先前約定(檢索/統計,非生成)。

對齊:rl_11 origin_signature、rl_12 命名回收、rl_01 no-delete(原檔另存不刪)。
CLI:python3 09_workflow/MRL_SemanticEmbedding_Core_v1.py
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Dict, List, Tuple

ORIGIN_SIGNATURE = "MrliouAI"
_TOKEN_RE = re.compile(r"[a-z0-9']+", re.IGNORECASE)


def _tokens(text: str) -> List[str]:
    toks = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    # 加 char 3-gram 提升短文 / 跨語(中文無空白)語意覆蓋
    s = re.sub(r"\s+", "", (text or "").lower())
    grams = [s[i:i + 3] for i in range(max(0, len(s) - 2))]
    return toks + grams


def _bucket(token: str, dim: int) -> int:
    h = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") % dim


class MRL_SemanticEmbeddingCore:
    """雜湊嵌入 + 餘弦相似語意檢索(母體原生,零外部依賴,確定性)。"""

    def __init__(self, dim: int = 256) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.dim = dim
        self.docs: List[Tuple[str, List[float]]] = []  # (text, vector)

    # ── 確定性嵌入:雜湊化詞袋 → L2 normalize ──
    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for tok in _tokens(text):
            vec[_bucket(tok, self.dim)] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm else vec

    @staticmethod
    def cosine(a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))  # 已 L2 normalize → 點積即餘弦

    # ── 建索引(append-only;rl_01 no-delete) ──
    def index(self, text: str) -> None:
        self.docs.append((text, self.embed(text)))

    def index_all(self, texts: List[str]) -> None:
        for t in texts:
            self.index(t)

    # ── 語意檢索:回 top-k(text, score) ──
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        q = self.embed(query)
        scored = [
            {"text": t, "score": round(self.cosine(q, v), 6)} for t, v in self.docs
        ]
        scored.sort(key=lambda d: (-d["score"], d["text"]))
        return scored[:k]


def main() -> int:
    core = MRL_SemanticEmbeddingCore(dim=256)
    corpus = [
        "母體根源法則 origin_signature MrliouAI 命名主權",
        "durable replay across reboot exact state hash",
        "spam detection naive bayes tfidf classifier",
        "multi world deterministic synchronization verdict",
        "the cat sat on the warm sunny windowsill",
    ]
    core.index_all(corpus)
    hits = core.search("reboot replay state hash exact", k=2)
    for h in hits:
        print(f"  score={h['score']:.3f}  {h['text']}")
    top = core.search("reboot replay state hash exact", k=1)[0]
    assert "durable replay" in top["text"], "語意檢索應命中 replay 文件"
    print(f"origin_signature={core.origin_signature}")
    print("MRL_SEMANTIC_EMBEDDING_CORE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
