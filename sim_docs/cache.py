"""LRU cache for parsed document facts with modification time tracking."""

from __future__ import annotations

import os
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CacheStats:
    """Cache statistics for debugging."""
    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: int = 0


@dataclass
class CacheEntry:
    """Cached document facts with metadata."""
    facts: Any
    mtime: float  # File modification time when cached
    path: str


class DocumentCache:
    """In-memory LRU cache for parsed document facts.

    Invalidates entries when source files are modified.
    """

    def __init__(self, max_size: int = 32):
        """Initialize cache with maximum size.

        Args:
            max_size: Maximum number of documents to cache.
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats(max_size=max_size)

    def get(self, path: str) -> Any | None:
        """Get cached facts for a document path.

        Checks modification time and invalidates if file changed.

        Args:
            path: Absolute path to the document.

        Returns:
            Cached facts if valid, None if not cached or stale.
        """
        resolved = str(Path(path).resolve())
        if resolved not in self._cache:
            self._stats.misses += 1
            return None

        entry = self._cache[resolved]
        current_mtime = self._get_mtime(resolved)

        if current_mtime is None or current_mtime != entry.mtime:
            # File modified or deleted, invalidate
            del self._cache[resolved]
            self._stats.size = len(self._cache)
            self._stats.misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(resolved)
        self._stats.hits += 1
        return entry.facts

    def set(self, path: str, facts: Any) -> None:
        """Cache facts for a document path.

        Evicts least recently used entry if cache is full.

        Args:
            path: Absolute path to the document.
            facts: Parsed document facts to cache.
        """
        resolved = str(Path(path).resolve())
        mtime = self._get_mtime(resolved)

        if mtime is None:
            return  # Cannot cache non-existent file

        if resolved in self._cache:
            # Update existing entry
            self._cache[resolved] = CacheEntry(facts=facts, mtime=mtime, path=resolved)
            self._cache.move_to_end(resolved)
        else:
            # Add new entry, evict LRU if full
            if len(self._cache) >= self._stats.max_size:
                self._cache.popitem(last=False)
            self._cache[resolved] = CacheEntry(facts=facts, mtime=mtime, path=resolved)

        self._stats.size = len(self._cache)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._stats.size = 0

    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            size=self._stats.size,
            max_size=self._stats.max_size,
        )

    def _get_mtime(self, path: str) -> float | None:
        """Get file modification time."""
        try:
            return os.path.getmtime(path)
        except OSError:
            return None