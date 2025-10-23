"""Content management for automation campaigns."""
from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class ContentItem:
    identifier: str
    title: str
    body: str
    target_group: str


class ContentManager:
    """Loads and rotates content variations from CSV files."""

    def __init__(self, csv_path: str) -> None:
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Content CSV not found: {self.csv_path}")
        self._items: List[ContentItem] = list(self._load_items(self.csv_path))
        if not self._items:
            raise ValueError("No content items available")
        self._unused = set(self._items)
        self._used: List[ContentItem] = []

    # ------------------------------------------------------------------
    @property
    def has_content(self) -> bool:
        return bool(self._unused)

    @property
    def remaining_items(self) -> int:
        return len(self._unused)

    def next_content(self) -> ContentItem:
        if not self._unused:
            raise StopIteration("No more content available")
        choice = random.choice(tuple(self._unused))
        return choice

    def mark_used(self, item: ContentItem) -> None:
        if item in self._unused:
            self._unused.remove(item)
            self._used.append(item)

    def reset(self) -> None:
        self._unused = set(self._items)
        self._used.clear()

    # ------------------------------------------------------------------
    def _load_items(self, path: Path) -> Iterable[ContentItem]:
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required_fields = {"identifier", "title", "body", "target_group"}
            if not required_fields.issubset(reader.fieldnames or []):
                missing = required_fields.difference(reader.fieldnames or [])
                raise ValueError(f"CSV missing required columns: {', '.join(missing)}")
            for row in reader:
                normalized = {key: value.strip() for key, value in row.items() if value is not None}
                item = ContentItem(
                    identifier=normalized.get("identifier", ""),
                    title=normalized.get("title", "Untitled"),
                    body=normalized.get("body", ""),
                    target_group=normalized.get("target_group", "General"),
                )
                yield item


__all__ = ["ContentManager", "ContentItem"]
