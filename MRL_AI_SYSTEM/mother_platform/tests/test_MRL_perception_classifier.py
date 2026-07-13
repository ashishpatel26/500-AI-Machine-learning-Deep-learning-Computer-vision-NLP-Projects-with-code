"""test_MRL_perception_classifier.py (origin: MrliouAI)

吸收外部「垃圾/毒性訊息偵測」ML 能力 → 母體原生統計感知分類器。
驗:訓練後 spam>ham、flag 行為、純 stdlib 可重現、origin_signature。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_PerceptionGuardrail_Classifier_v1 import (
    MRL_PerceptionGuardrailClassifier, tokenize, _SEED_SPAM,
)


def _fit():
    clf = MRL_PerceptionGuardrailClassifier()
    clf.fit([t for t, _ in _SEED_SPAM], [y for _, y in _SEED_SPAM])
    return clf


def test_tokenize_drops_stopwords():
    toks = tokenize("The cat is on the mat")
    assert "the" not in toks and "is" not in toks and "cat" in toks


def test_spam_scores_higher_than_ham():
    clf = _fit()
    assert clf.predict_proba("Free money click now win prize") > \
           clf.predict_proba("Let's meet tomorrow for lunch")


def test_predict_flag_threshold():
    clf = _fit()
    r = clf.predict("Free money click now win prize claim reward")
    assert r["flag"] is True and 0.0 <= r["prob"] <= 1.0


def test_deterministic_refit():
    # 純 stdlib 確定性:同語料兩次訓練 → 同機率
    a = _fit().predict_proba("Win free iphone click here")
    b = _fit().predict_proba("Win free iphone click here")
    assert a == b


def test_origin_signature():
    assert _fit().origin_signature == "MrliouAI"
