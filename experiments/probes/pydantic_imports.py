"""Probe: Pydantic 1 -> 2 surface: warning-only shims vs genuinely removed imports."""
import json
import warnings

import pydantic

out = {"library": "pydantic", "version": pydantic.VERSION}


def attempt(label, fn):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            fn()
            out[label] = {"ok": True}
        except Exception as exc:  # noqa: BLE001
            out[label] = {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
    out[label]["warnings"] = len([w for w in caught if issubclass(w.category, (UserWarning, DeprecationWarning))])


def config_and_dict():
    class M(pydantic.BaseModel):
        x: int

        class Config:
            allow_population_by_field_name = True

    M(x=1).dict()


def generic_model():
    from pydantic.generics import GenericModel  # noqa: F401


def base_settings():
    from pydantic import BaseSettings  # noqa: F401


attempt("inner_config_and_dict", config_and_dict)
attempt("generics_GenericModel_import", generic_model)
attempt("BaseSettings_import", base_settings)
print("RESULT " + json.dumps(out, sort_keys=True))
