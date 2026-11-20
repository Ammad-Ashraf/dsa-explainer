"""Dynamic programming: tables filled one cell at a time (Fibonacci, coin change)."""

from __future__ import annotations

from .base import OpError, Structure, as_int, normalize


class _Table(Structure):
    CATEGORY = "dp"
    VIEW = "table"
    NOUN = "cells"

    def __init__(self, size: int) -> None:
        super().__init__()
        self.cells: list[tuple[int, object]] = [(self.new_id(), None) for _ in range(size)]
        self.i = -1  # the cell filled last

    def _set(self, i: int, value) -> None:
        self.cells[i] = (self.cells[i][0], value)

    def table(self) -> list:
        return [v for _, v in self.cells]

    def state(self):
        return self.table()

    def values(self) -> set[str]:
        return {normalize(v) for v in self.table() if v is not None}

    def snapshot(self) -> dict:
        return {"cells": [[iid, v] for iid, v in self.cells], "current": self.i if self.i >= 0 else None}


class Fibonacci(_Table):
    NAME, TITLE = "fibonacci", "Fibonacci (dynamic programming)"
    SUMMARY = "Fill a table where each cell is the sum of the two before it: no repeated work."
    DESCRIPTION = ("The naive recursive Fibonacci recomputes the same values again and again. Dynamic programming "
                   "stores each answer in a table and builds up from F(0) = 0 and F(1) = 1, so every value is "
                   "computed once.")
    COMPLEXITY = {"best": "O(n)", "average": "O(n)", "worst": "O(n)", "space": "O(n)"}
    PSEUDOCODE = ("F[0] = 0; F[1] = 1", "for i from 2 to n: F[i] = F[i - 1] + F[i - 2]")
    KEYWORDS = ("fibonacci", "fib", "memo", "memoization", "dynamic programming", "dp table")
    PRESETS = {"up to F(7)": {"n": 7}, "up to F(5)": {"n": 5}, "up to F(9)": {"n": 9}}
    OPS = {"fill_next": ()}
    FACTS = ("current", "value", "table", "size")
    HELP = (
        'fibonacci (bottom-up table): initial = {"n": 7}, n from 2 to 10. The table has cells F[0] to F[n]; '
        "F[0] = 0 and F[1] = 1 are filled before the first step. ops: fill_next() fills the next empty cell "
        "with F[i] = F[i - 1] + F[i - 2]. state = the table, with null for empty cells, e.g. [0, 1, 1, null]. "
        "facts: current (the index just filled), value (its value), table, size (number of cells)."
    )

    def __init__(self, initial) -> None:
        if not isinstance(initial, dict) or "n" not in initial:
            raise OpError('initial data must be {"n": 7}')
        n = as_int(initial["n"], "n", 2, 10)
        super().__init__(n + 1)
        self._set(0, 0)
        self._set(1, 1)
        self.i = 1

    def op_fill_next(self):
        if self.i + 1 >= len(self.cells):
            raise OpError("the table is full")
        i = self.i + 1
        self._set(i, self.cells[i - 1][1] + self.cells[i - 2][1])
        self.i = i
        return [self.cells[i - 2][0], self.cells[i - 1][0], self.cells[i][0]]

    def facts(self) -> dict:
        return {"current": self.i, "value": self.cells[self.i][1], "table": self.table(), "size": len(self.cells)}

    def snapshot(self) -> dict:
        return {**super().snapshot(), "labels": [f"F({i})" for i in range(len(self.cells))]}


class CoinChange(_Table):
    NAME, TITLE = "coin_change", "Coin change (fewest coins)"
    DIFFICULTY = "advanced"
    SUMMARY = "For every amount up to the target, find the fewest coins that make it."
    DESCRIPTION = ("To pay an amount with the fewest coins, dynamic programming solves every smaller amount first. "
                   "The best way to pay amount a is one coin c plus the best way to pay a minus c, so each cell "
                   "looks back at a few earlier cells and keeps the smallest count.")
    COMPLEXITY = {"best": "O(n k)", "average": "O(n k)", "worst": "O(n k)", "space": "O(n)"}
    PSEUDOCODE = ("best[0] = 0", "for a from 1 to amount:",
                  "    best[a] = 1 + the smallest best[a - c] over coins c <= a (inf if none)")
    KEYWORDS = ("coin change", "coins", "fewest coins", "minimum coins", "change making", "making change")
    PRESETS = {"coins 1, 3, 4 for 6": {"coins": [1, 3, 4], "amount": 6},
               "coins 1, 2, 5 for 7": {"coins": [1, 2, 5], "amount": 7},
               "coins 2, 3 for 7": {"coins": [2, 3], "amount": 7}}
    OPS = {"fill_next": ()}
    FACTS = ("current", "value", "table", "coins", "size")
    HELP = (
        'coin_change (fewest coins, bottom-up): initial = {"coins": [1, 3, 4], "amount": 6}, 1 to 4 distinct '
        "coins from 1 to 20, amount from 2 to 10. Cell a holds the fewest coins that pay amount a; cell 0 is 0 "
        "before the first step. ops: fill_next() fills the next cell a with 1 + the smallest of cell a - c over "
        'the coins c no larger than a, or "inf" when no coin fits a payable amount. state = the table, null for '
        'empty cells and "inf" for amounts that cannot be paid, e.g. [0, 1, 2, null]. facts: current (the '
        "amount just filled), value (its fewest coins), table, coins, size (number of cells)."
    )

    def __init__(self, initial) -> None:
        if not isinstance(initial, dict) or "coins" not in initial or "amount" not in initial:
            raise OpError('initial data must be {"coins": [1, 3, 4], "amount": 6}')
        coins = initial["coins"]
        if not isinstance(coins, list) or not 1 <= len(coins) <= 4:
            raise OpError("give 1 to 4 coins")
        self.coins = sorted({as_int(c, "a coin", 1, 20) for c in coins})
        amount = as_int(initial["amount"], "the amount", 2, 10)
        super().__init__(amount + 1)
        self._set(0, 0)
        self.i = 0
        self.used: int | None = None

    def op_fill_next(self):
        if self.i + 1 >= len(self.cells):
            raise OpError("the table is full")
        a = self.i + 1
        options = [(self.cells[a - c][1] + 1, c) for c in self.coins
                   if c <= a and isinstance(self.cells[a - c][1], int)]
        best = min(options) if options else None
        self._set(a, best[0] if best else "inf")
        self.used = best[1] if best else None
        self.i = a
        looked = [self.cells[a - c][0] for c in self.coins if c <= a]
        return looked + [self.cells[a][0]]

    def values(self) -> set[str]:
        return super().values() | {normalize(c) for c in self.coins} | {normalize(len(self.cells) - 1)}

    def facts(self) -> dict:
        return {"current": self.i, "value": self.cells[self.i][1], "table": self.table(), "coins": self.coins,
                "size": len(self.cells)}

    def snapshot(self) -> dict:
        return {**super().snapshot(), "labels": [str(a) for a in range(len(self.cells))],
                "caption": "coins: " + ", ".join(map(str, self.coins))}
