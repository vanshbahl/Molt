from jwt import ExpiredSignature, InvalidAudience as BadAudience


def classify(exc):
    """Map a PyJWT exception to a short label."""
    if isinstance(exc, ExpiredSignature):
        return "expired"
    if isinstance(exc, BadAudience):
        return "audience"
    return "other"
