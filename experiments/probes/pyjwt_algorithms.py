"""Probe: jwt.decode without algorithms= and jwt.encode return type (PyJWT 1.x vs 2.x)."""
import json

import jwt

out = {"library": "PyJWT", "version": jwt.__version__}
token = jwt.encode({"a": 1}, "secret")
out["encode_return_type"] = type(token).__name__
try:
    out["decode_without_algorithms"] = {"ok": True, "value": jwt.decode(token, "secret")}
except Exception as exc:  # noqa: BLE001 - the exception is the observation
    out["decode_without_algorithms"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
print("RESULT " + json.dumps(out, sort_keys=True))
