from sig_verify.mrl_sig_verify import keypair, sign, verify_sig


def test_sign_and_verify_roundtrip():
    sk, pk = keypair()
    msg = b"hello MRL"
    sig = sign(sk, msg)
    assert verify_sig(pk, msg, sig)


def test_tampered_message_fails():
    sk, pk = keypair()
    sig = sign(sk, b"original")
    assert not verify_sig(pk, b"tampered", sig)


def test_wrong_key_fails():
    sk1, _ = keypair()
    _, pk2 = keypair()
    sig = sign(sk1, b"msg")
    assert not verify_sig(pk2, b"msg", sig)
