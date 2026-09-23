"""Token helpers written against PyJWT 1.x."""
import jwt

SECRET = "fixture-secret"


def decode_ignoring_expiry(token):
    # Legacy callers rely on expired tokens still decoding here.
    return jwt.decode(token, SECRET, algorithms=["HS256"], verify_expiration=False)


def decode_skipping_audience(token):
    return jwt.decode(
        token,
        SECRET,
        algorithms=["HS256"],
        options={"verify_aud": False},  # audience is checked upstream
        verify_expiration=False,
    )


def is_expired(token):
    try:
        jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignature:
        return True
    return False
