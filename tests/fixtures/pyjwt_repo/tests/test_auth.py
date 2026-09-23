import jwt

from app.auth import SECRET, decode_ignoring_expiry, decode_skipping_audience, is_expired
from app.errors import classify

EXPIRED = jwt.encode({"sub": "u1", "exp": 0}, SECRET, algorithm="HS256")
EXPIRED_WITH_AUDIENCE = jwt.encode({"sub": "u1", "exp": 0, "aud": "other"}, SECRET, algorithm="HS256")


def test_expired_token_still_decodes_when_expiry_disabled():
    assert decode_ignoring_expiry(EXPIRED)["sub"] == "u1"


def test_existing_options_are_kept_and_expiry_disabled():
    assert decode_skipping_audience(EXPIRED_WITH_AUDIENCE)["sub"] == "u1"


def test_is_expired():
    assert is_expired(EXPIRED) is True


def test_classify_uses_current_exception_names():
    assert classify(jwt.ExpiredSignatureError("x")) == "expired"
    assert classify(jwt.InvalidAudienceError("x")) == "audience"
    assert classify(ValueError("x")) == "other"
