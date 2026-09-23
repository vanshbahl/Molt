"""Probe: select([cols]) list form (SQLAlchemy 1.3 vs 2.0). No database needed."""
import json

import sqlalchemy as sa

out = {"library": "SQLAlchemy", "version": sa.__version__}
t = sa.table("t", sa.column("x"), sa.column("y"))
try:
    out["select_list_form"] = {"ok": True, "sql": " ".join(str(sa.select([t.c.x, t.c.y])).split())}
except Exception as exc:  # noqa: BLE001
    out["select_list_form"] = {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
try:
    out["select_positional_form"] = {"ok": True, "sql": " ".join(str(sa.select(t.c.x, t.c.y)).split())}
except Exception as exc:  # noqa: BLE001
    out["select_positional_form"] = {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
print("RESULT " + json.dumps(out, sort_keys=True))
