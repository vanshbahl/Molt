"""Test-wide isolation: no credentials, no external network, no model calls.

Every test runs with provider credentials removed from the environment and
``MOLT_NO_NETWORK=1`` set (the pilot runner refuses live calls when it sees
it). In-process socket connections to anything other than loopback raise, so
an accidental HTTP request fails loudly instead of reaching a provider.
Subprocesses must be started with ``isolated_env()``.
"""

import os
import socket

import pytest

# Fixture repositories contain their own test suites (some intentionally
# failing before migration); they are run only by the engine's verifier.
collect_ignore = ["fixtures"]

SECRET_ENV_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")
LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def isolated_env(extra=None):
    """Environment for subprocesses: current env minus secrets, network disabled."""
    env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV_VARS}
    env["MOLT_NO_NETWORK"] = "1"
    if extra:
        env.update(extra)
    return env


def pytest_configure(config):
    for key in SECRET_ENV_VARS:
        os.environ.pop(key, None)
    os.environ["MOLT_NO_NETWORK"] = "1"


@pytest.fixture(autouse=True)
def _block_external_network(monkeypatch):
    for key in SECRET_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MOLT_NO_NETWORK", "1")

    real_connect = socket.socket.connect
    real_getaddrinfo = socket.getaddrinfo

    def guarded_connect(self, address):
        if isinstance(address, tuple) and address[0] not in LOOPBACK:
            raise RuntimeError(f"external network access blocked in tests: {address!r}")
        return real_connect(self, address)

    def guarded_getaddrinfo(host, *args, **kwargs):
        if host not in LOOPBACK and host is not None:
            raise RuntimeError(f"external DNS lookup blocked in tests: {host!r}")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
