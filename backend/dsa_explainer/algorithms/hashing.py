"""Hashing: a hash table with separate chaining."""

from __future__ import annotations

from .base import MAX_ITEMS, OpError, Structure, as_int, normalize


class HashTable(Structure):
    NAME, TITLE = "hash_table", "Hash table (chaining)"
    CATEGORY = "hashing"
    DIFFICULTY = "intermediate"
    VIEW = "buckets"
    NOUN = "keys"
    SUMMARY = "A hash function picks the bucket; keys that collide share a chain."
    DESCRIPTION = ("A hash table turns a key into a bucket number with a hash function, here the key modulo the "
                   "number of buckets. Finding a key only means looking in one bucket, so lookups take constant "
                   "time on average. Keys that land in the same bucket collide and are kept in a chain.")
    COMPLEXITY = {"best": "O(1)", "average": "O(1)", "worst": "O(n)", "space": "O(n)"}
    PSEUDOCODE = ("bucket(k) = k mod m", "insert(k): append k to the chain of bucket(k)",
                  "search(k): walk the chain of bucket(k)", "delete(k): remove k from the chain of bucket(k)")
    KEYWORDS = ("hash", "hash table", "hashtable", "hashing", "hash map", "collision", "chaining", "bucket", "modulo")
    PRESETS = {"five buckets": {"buckets": 5, "keys": [12, 7, 3]},
               "collisions": {"buckets": 4, "keys": [5, 9, 13]},
               "empty": {"buckets": 7, "keys": []}}
    OPS = {"insert": ("key",), "search": ("key",), "delete": ("key",)}
    FACTS = ("size", "buckets", "bucket", "chain", "found", "items")
    HELP = (
        'hash_table (separate chaining, bucket = key mod number of buckets): initial = {"buckets": 5, '
        '"keys": [12, 7, 3]}, keys are whole numbers inserted in that order, 2 to 7 buckets. ops: insert(key) '
        "appends the key to the end of its bucket's chain (no duplicates); search(key) walks that chain; "
        "delete(key) removes it. state = list of chains, one per bucket, e.g. [[], [], [12, 7], [3], []]. "
        "facts: size (number of keys), buckets (number of buckets), bucket (the bucket of the last operation's "
        "key), chain (that bucket's keys), found (yes or no, for search and delete), items (every key, bucket "
        "by bucket)."
    )

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, dict) or not isinstance(initial.get("keys"), list):
            raise OpError('initial data must be {"buckets": 5, "keys": [12, 7, 3]}')
        self.m = as_int(initial.get("buckets", 5), "the number of buckets", 2, 7)
        self.chains: list[list[tuple[int, int]]] = [[] for _ in range(self.m)]
        self.last_bucket: int | None = None
        self.found: bool | None = None
        for k in initial["keys"]:
            self.op_insert(k)
        self.last_bucket, self.found = None, None

    def _key(self, k) -> int:
        return as_int(k, "a key", 0, 999)

    def _where(self, k: int) -> tuple[int, int | None]:
        b = k % self.m
        pos = next((i for i, (_, v) in enumerate(self.chains[b]) if v == k), None)
        return b, pos

    def op_insert(self, key):
        k = self._key(key)
        b, pos = self._where(k)
        if pos is not None:
            raise OpError(f"{k} is already in the table")
        if sum(len(c) for c in self.chains) >= MAX_ITEMS:
            raise OpError(f"keep at most {MAX_ITEMS} keys so the picture stays readable")
        walked = [iid for iid, _ in self.chains[b]]
        self.chains[b].append((self.new_id(), k))
        self.last_bucket, self.found = b, None
        return [("bucket", b)] + walked + [self.chains[b][-1][0]]

    def op_search(self, key):
        k = self._key(key)
        b, pos = self._where(k)
        self.last_bucket, self.found = b, pos is not None
        walked = [iid for iid, _ in self.chains[b][: (pos + 1 if pos is not None else len(self.chains[b]))]]
        return [("bucket", b)] + walked

    def op_delete(self, key):
        k = self._key(key)
        b, pos = self._where(k)
        if pos is None:
            raise OpError(f"{k} is not in the table, so it cannot be deleted")
        walked = [iid for iid, _ in self.chains[b][: pos + 1]]
        del self.chains[b][pos]
        self.last_bucket, self.found = b, True
        return [("bucket", b)] + walked

    def state(self):
        return [[v for _, v in chain] for chain in self.chains]

    def values(self) -> set[str]:
        return {normalize(v) for chain in self.state() for v in chain} | {normalize(self.m)}

    def facts(self) -> dict:
        b = self.last_bucket
        return {"size": sum(len(c) for c in self.chains), "buckets": self.m, "bucket": b,
                "chain": [v for _, v in self.chains[b]] if b is not None else None,
                "found": self.found, "items": [v for chain in self.state() for v in chain]}

    def snapshot(self) -> dict:
        return {"buckets": [[list(item) for item in chain] for chain in self.chains], "active": self.last_bucket}
