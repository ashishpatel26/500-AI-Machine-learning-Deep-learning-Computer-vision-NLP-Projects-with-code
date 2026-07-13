#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_PerceptionGuardrail_Classifier_v1.py — 母體感知守門統計分類器
origin_signature: MrliouAI
layer: L4 PERCEPTION / GUARDRAIL

吸收定位:把一份外部「垃圾訊息 / 毒性訊息偵測」ML 能力(TF-IDF + Multinomial
Naive Bayes / Logistic Regression 思路)回收為母體**原生**能力模組,純 stdlib、
零外部依賴、沙盒可跑。**這是統計感知分類器(perception),不是生成式 LLM**——
誠實標註,沿用先前約定(檢索/統計排序,非生成)。

對齊:
  rl_11 origin_signature 主權(產物簽 MrliouAI)
  rl_12 命名回收(對外能力名 → 母體 MRL_ 名)
  rl_00 deny-by-default(分數過閾值即 flag,不靜默放行)

能力:
  - tokenize:純 stdlib 斷詞 + 英文停用詞剔除
  - TF-IDF 向量化(自建詞典,max_features 截斷)
  - Multinomial Naive Bayes(Laplace 平滑,log 機率)訓練 / 推論
  - predict_proba → 0..1 機率;score+閾值 → flag(垃圾/毒性)

CLI:python3 09_workflow/MRL_PerceptionGuardrail_Classifier_v1.py
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Tuple

ORIGIN_SIGNATURE = "MrliouAI"

# 純 stdlib 英文停用詞(對齊外部 stop_words='english' 之意圖,母體自有清單)
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "to", "of", "in", "on", "for",
    "is", "are", "was", "were", "be", "been", "being", "it", "its", "this",
    "that", "these", "those", "i", "you", "he", "she", "we", "they", "me",
    "my", "your", "at", "by", "with", "as", "from", "so", "do", "does", "did",
}

_TOKEN_RE = re.compile(r"[a-z0-9']+", re.IGNORECASE)


def tokenize(text: str) -> List[str]:
    """純 stdlib 斷詞 + 停用詞剔除(小寫正規化)。"""
    toks = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    return [t for t in toks if t not in _STOPWORDS and len(t) > 1]


class MRL_PerceptionGuardrailClassifier:
    """TF-IDF + Multinomial Naive Bayes 統計感知分類器(母體原生,零外部)。"""

    def __init__(self, max_features: int = 5000) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.max_features = max_features
        self.vocab: Dict[str, int] = {}
        self.idf: List[float] = []
        self.class_log_prior: Dict[int, float] = {}
        self.feature_log_prob: Dict[int, List[float]] = {}
        self.classes: List[int] = []
        self._fitted = False

    # ── 建詞典 + IDF(由訓練語料) ──
    def _build_vocab(self, docs: List[List[str]]) -> None:
        df: Dict[str, int] = {}
        for toks in docs:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        # 依文件頻率排序,截斷 max_features = 母體詞典主權
        ranked = sorted(df.items(), key=lambda kv: (-kv[1], kv[0]))[: self.max_features]
        self.vocab = {t: i for i, (t, _) in enumerate(ranked)}
        n = len(docs)
        self.idf = [0.0] * len(self.vocab)
        for t, i in self.vocab.items():
            self.idf[i] = math.log((1 + n) / (1 + df[t])) + 1.0  # 平滑 IDF

    def _tfidf(self, toks: List[str]) -> List[float]:
        vec = [0.0] * len(self.vocab)
        for t in toks:
            j = self.vocab.get(t)
            if j is not None:
                vec[j] += 1.0
        for j in range(len(vec)):
            if vec[j]:
                vec[j] *= self.idf[j]
        return vec

    # ── 訓練:Multinomial NB(Laplace 平滑,log 空間) ──
    def fit(self, texts: List[str], labels: List[int]) -> "MRL_PerceptionGuardrailClassifier":
        docs = [tokenize(t) for t in texts]
        self._build_vocab(docs)
        X = [self._tfidf(d) for d in docs]
        self.classes = sorted(set(labels))
        nfeat = len(self.vocab)
        total = len(labels)
        for c in self.classes:
            idxs = [i for i, y in enumerate(labels) if y == c]
            self.class_log_prior[c] = math.log(len(idxs) / total)
            feat_sum = [0.0] * nfeat
            for i in idxs:
                row = X[i]
                for j in range(nfeat):
                    feat_sum[j] += row[j]
            denom = sum(feat_sum) + nfeat  # Laplace alpha=1
            self.feature_log_prob[c] = [
                math.log((feat_sum[j] + 1.0) / denom) for j in range(nfeat)
            ]
        self._fitted = True
        return self

    def _log_likelihood(self, vec: List[float]) -> Dict[int, float]:
        out: Dict[int, float] = {}
        for c in self.classes:
            flp = self.feature_log_prob[c]
            s = self.class_log_prior[c]
            for j in range(len(vec)):
                if vec[j]:
                    s += vec[j] * flp[j]
            out[c] = s
        return out

    # ── 推論:回正類(1)機率 0..1 ──
    def predict_proba(self, text: str) -> float:
        if not self._fitted:
            raise RuntimeError("classifier not fitted")
        vec = self._tfidf(tokenize(text))
        ll = self._log_likelihood(vec)
        m = max(ll.values())
        exp = {c: math.exp(v - m) for c, v in ll.items()}
        z = sum(exp.values())
        return exp.get(1, 0.0) / z if z else 0.0

    def predict(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        p = self.predict_proba(text)
        return {
            "prob": round(p, 6),
            "flag": p >= threshold,                # rl_00 deny-by-default:過閾值即攔
            "threshold": threshold,
            "origin_signature": ORIGIN_SIGNATURE,
        }


# 母體內建種子語料(由吸收文件之範例擴充;母體自有,無外部來源痕)
_SEED_SPAM = [
    ("Free money click now win prize claim reward", 1),
    ("Congratulations you won a free gift click link", 1),
    ("URGENT claim your cash prize now limited offer", 1),
    ("Win free iphone click here to claim today", 1),
    ("Cheap loans guaranteed approval click apply now", 1),
    ("Let's meet tomorrow for lunch", 0),
    ("Can you send me the report by Friday", 0),
    ("The meeting is rescheduled to next week", 0),
    ("Thanks for your help on the project", 0),
    ("I will review the document and reply", 0),
]


def main() -> int:
    clf = MRL_PerceptionGuardrailClassifier(max_features=5000)
    texts = [t for t, _ in _SEED_SPAM]
    labels = [y for _, y in _SEED_SPAM]
    clf.fit(texts, labels)
    samples = ["Free money click now!!!", "Let's meet tomorrow"]
    for s in samples:
        r = clf.predict(s)
        print(f"  {s!r:38} prob={r['prob']:.3f} flag={r['flag']}")
    a = clf.predict_proba("Free money click now!!!")
    b = clf.predict_proba("Let's meet tomorrow")
    assert a > b, "spam 範例機率應高於正常訊息"
    print(f"origin_signature={clf.origin_signature}")
    print("MRL_PERCEPTION_GUARDRAIL_CLASSIFIER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
