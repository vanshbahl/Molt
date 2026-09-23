"""Probe: the two sites in the registered PyJWT bounded task.

(a) `except jwt.ExpiredSignature` (removed compatibility alias)
(b) flat `jwt.decode(..., verify_expiration=False)` (silently ignored in 2.x)
"""
import json
import warnings

import jwt

out = {"library": "PyJWT", "version": jwt.__version__}
expired = jwt.encode({"exp": 0}, "secret", algorithm="HS256")

try:
    try:
        jwt.decode(expired, "secret", algorithms=["HS256"])
        out["old_exception_name"] = {"ok": False, "error": "no exception raised"}
    except jwt.ExpiredSignature as exc:
        out["old_exception_name"] = {"ok": True, "caught": type(exc).__name__}
except Exception as exc:  # noqa: BLE001
    out["old_exception_name"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    try:
        value = jwt.decode(expired, "secret", algorithms=["HS256"], verify_expiration=False)
        out["flat_verify_expiration"] = {"ok": True, "decoded": value}
    except Exception as exc:  # noqa: BLE001
        out["flat_verify_expiration"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
out["flat_verify_expiration"]["warnings"] = sorted({str(w.message)[:120] for w in caught if "verify" in str(w.message)})

try:
    value = jwt.decode(expired, "secret", algorithms=["HS256"], options={"verify_exp": False})
    out["options_form"] = {"ok": True, "decoded": value}
except Exception as exc:  # noqa: BLE001
    out["options_form"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
print("RESULT " + json.dumps(out, sort_keys=True))
