from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO


class Tee:
    def __init__(self, *streams: TextIO) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def open_log(log_dir: Path, prefix: str = "run") -> tuple[TextIO, Path]:
    from datetime import datetime, timezone

    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = log_dir / f"{prefix}-{stamp}.log"
    return path.open("w"), path


def print_step(title: str) -> None:
    print(f"\n== {title} ==", file=sys.stdout)

