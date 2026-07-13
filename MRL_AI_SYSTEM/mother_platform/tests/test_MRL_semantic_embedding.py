"""test_MRL_semantic_embedding.py (origin: MrliouAI)

吸收外部「局部嵌入語意檢索」能力 → 母體原生雜湊嵌入 + 餘弦檢索。
驗:確定性嵌入、自相似=1、語意檢索命中、append-only 索引、origin_signature。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_SemanticEmbedding_Core_v1 import MRL_SemanticEmbeddingCore


def test_embed_deterministic():
    c = MRL_SemanticEmbeddingCore()
    assert c.embed("durable replay state hash") == c.embed("durable replay state hash")


def test_self_similarity_is_one():
    c = MRL_SemanticEmbeddingCore()
    v = c.embed("origin signature MrliouAI")
    assert abs(c.cosine(v, v) - 1.0) < 1e-9


def test_search_hits_relevant_doc():
    c = MRL_SemanticEmbeddingCore()
    c.index_all([
        "durable replay across reboot exact state hash",
        "the cat sat on the warm windowsill",
        "spam detection naive bayes tfidf",
    ])
    top = c.search("reboot replay exact hash", k=1)[0]
    assert "durable replay" in top["text"] and top["score"] > 0.0


def test_index_is_append_only():
    c = MRL_SemanticEmbeddingCore()
    c.index("doc one"); c.index("doc two")
    assert len(c.docs) == 2  # rl_01 no-delete:只增不減


def test_origin_signature():
    assert MRL_SemanticEmbeddingCore().origin_signature == "MrliouAI"
