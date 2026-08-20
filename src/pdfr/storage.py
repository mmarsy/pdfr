from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

APP_NAME = "pdfr"
VIEWER_STATE_FILE = "viewer_state.json"


@dataclass(frozen=True)
class DocumentIdentity:
    document_id: str
    path: str
    size: int
    modified_ns: int


@dataclass(frozen=True)
class ViewerState:
    zoom: float
    yview: float
    current_page: int


def app_data_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    return Path.home() / "AppData" / "Roaming" / APP_NAME


def document_identity(path: Path) -> DocumentIdentity:
    resolved_path = path.expanduser().resolve()
    stat = resolved_path.stat()
    normalized_path = str(resolved_path).casefold()
    document_id = sha256(normalized_path.encode("utf-8")).hexdigest()
    return DocumentIdentity(
        document_id=document_id,
        path=str(resolved_path),
        size=stat.st_size,
        modified_ns=stat.st_mtime_ns,
    )


class AppStorage:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root if root is not None else app_data_dir()
        self.annotations_dir = self.root / "annotations"
        self.viewer_state_path = self.root / VIEWER_STATE_FILE

    def ensure_ready(self) -> None:
        self.annotations_dir.mkdir(parents=True, exist_ok=True)

    def load_viewer_state(self, identity: DocumentIdentity) -> ViewerState | None:
        data = self._read_json(self.viewer_state_path)
        item = data.get(identity.document_id)
        if not isinstance(item, dict):
            return None

        try:
            if item.get("path") != identity.path:
                return None
            if item.get("size") != identity.size:
                return None
            if item.get("modified_ns") != identity.modified_ns:
                return None
            return ViewerState(
                zoom=float(item["zoom"]),
                yview=float(item["yview"]),
                current_page=int(item["current_page"]),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def save_viewer_state(self, identity: DocumentIdentity, state: ViewerState) -> None:
        self.ensure_ready()
        data = self._read_json(self.viewer_state_path)
        data[identity.document_id] = {
            **asdict(identity),
            **asdict(state),
        }
        self._write_json(self.viewer_state_path, data)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}

        return data if isinstance(data, dict) else {}

    @staticmethod
    def _write_json(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, sort_keys=True)
            file.write("\n")
        temp_path.replace(path)
