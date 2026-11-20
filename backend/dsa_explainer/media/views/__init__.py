"""Views: how each family of simulator snapshots is drawn. An algorithm names its VIEW."""

from __future__ import annotations

from .array import ArrayView
from .common import View
from .graph import GraphView
from .linear import LinkedListView, QueueView, StackView
from .table import BucketsView, TableView
from .tree import HeapView, TreeView

VIEWS: dict[str, View] = {v.name: v for v in (
    StackView(), QueueView(), LinkedListView(), TreeView(), HeapView(), GraphView(), ArrayView(), BucketsView(),
    TableView(),
)}


def get(name: str) -> View:
    if name not in VIEWS:
        raise KeyError(f"no view '{name}'; known views: {', '.join(VIEWS)}")
    return VIEWS[name]
