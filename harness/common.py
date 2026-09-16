"""Shared file contracts. Standard library only."""

import hashlib
import json
import os
import tempfile
from pathlib import Path


class ContractError(ValueError):
    pass


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContractError(f"Cannot read JSON {path}: {exc}") from exc


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def confined(base, relative):
    path = (Path(base) / relative).resolve()
    if not path.is_relative_to(Path(base).resolve()) or not path.is_file():
        raise ContractError(f"Disallowed or missing file: {relative}")
    return path
