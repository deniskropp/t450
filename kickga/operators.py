"""
Reusable operators inspired by GAlib's GAAllele, GA1DArrayAlleleGenome mutators/crossover,
and classic EC operators. Kept simple and KickLang-friendly.
"""

from __future__ import annotations
import random
from typing import List, Sequence, Tuple


def gaussian_mutate(vec: List[float], pmut: float, sigma: float = 0.7, clamp: Tuple[float, float] = (0.0, 16.0)) -> int:
    """In-place gaussian mutation. Returns mutation count."""
    mutations = 0
    for i in range(len(vec)):
        if random.random() < pmut:
            vec[i] = round(max(clamp[0], min(clamp[1], vec[i] + random.gauss(0, sigma))), 4)
            mutations += 1
    return mutations


def uniform_crossover(a: List[float], b: List[float]) -> Tuple[List[float], List[float]]:
    """Uniform (bit-wise / locus-wise) crossover."""
    n = min(len(a), len(b))
    c1, c2 = list(a), list(b)
    for i in range(n):
        if random.random() < 0.5:
            c1[i], c2[i] = c2[i], c1[i]
    return c1, c2


def list_swap_mutate(items: List[str], pmut: float) -> int:
    mutations = 0
    n = len(items)
    if n < 2:
        return 0
    if random.random() < pmut:
        i, j = random.sample(range(n), 2)
        items[i], items[j] = items[j], items[i]
        mutations += 1
    if random.random() < pmut * 0.5:
        # light content mutation
        idx = random.randrange(n)
        s = items[idx]
        if len(s) > 3:
            k = random.randint(1, len(s) - 2)
            items[idx] = s[:k][::-1] + s[k:]
        else:
            items[idx] = s + "_m"
        mutations += 1
    return mutations


def list_order_crossover(a: List[str], b: List[str]) -> Tuple[List[str], List[str]]:
    """Order crossover for permutations / sequences."""
    n = min(len(a), len(b))
    if n < 2:
        return list(a), list(b)
    i = random.randint(0, n - 2)
    j = random.randint(i + 1, n - 1)

    def ox(p1, p2):
        child = [None] * n
        child[i:j] = p1[i:j]
        remaining = [x for x in p2 if x not in child[i:j]]
        ptr = 0
        for k in range(n):
            if child[k] is None:
                child[k] = remaining[ptr]
                ptr += 1
        return [x for x in child if x is not None]

    return ox(a, b), ox(b, a)
