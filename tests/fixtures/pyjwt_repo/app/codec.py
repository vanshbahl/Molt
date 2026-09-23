"""Unrelated .decode()/.encode() calls: the rule must not touch this file."""
import json


class Codec:
    def decode(self, data, verify_expiration=False):
        return data


def parse(payload: bytes):
    return json.loads(payload.decode("utf-8"))


def roundtrip(codec, raw):
    return codec.decode(raw.encode(), verify_expiration=True)
