from app.security import sign, verify

SECRET = "secret_test"
BODY = b'{"type":"payment_succeeded"}'


def test_valid_signature_passes():
    assert verify(SECRET, BODY, sign(SECRET, BODY))


def test_tampered_body_fails():
    assert not verify(SECRET, BODY, sign(SECRET, BODY + b" "))


def test_wrong_secret_fails():
    assert not verify(SECRET, BODY, sign("other_secret", BODY))


def test_missing_signature_fails():
    assert not verify(SECRET, BODY, None)
    assert not verify(SECRET, BODY, "")
