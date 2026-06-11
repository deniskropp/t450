"""
GAGenome and concrete genome types inspired by GAlib.

GAlib core ideas mirrored here:
- GAGenome base with score, evaluate(), clone(), crossover(), mutate()
- Typed genomes (array/vector for numeric DNA, list for symbolic sequences)
- Support for KickLang-serializable representations (dicts, lists, blocks)
"""

from __future__ import annotations
import copy
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


class GAGenome(ABC):
    """
    Abstract base mirroring GAlib GAGenome.

    Subclasses must implement:
      - clone()
      - crossover(mate) -> (child1, child2) or single child policy handled by GA
      - mutate(pmut) -> int (number of mutations performed)
      - optionally: evaluate() can be attached or supplied externally
    """

    def __init__(self, score: Optional[float] = None):
        self._score: Optional[float] = score
        self._evaluated: bool = score is not None
        self.user_data: Dict[str, Any] = {}

    @property
    def score(self) -> Optional[float]:
        return self._score

    def set_score(self, s: float) -> None:
        self._score = s
        self._evaluated = True

    def is_evaluated(self) -> bool:
        return self._evaluated

    def invalidate(self) -> None:
        self._evaluated = False
        self._score = None

    @abstractmethod
    def clone(self) -> "GAGenome":
        ...

    @abstractmethod
    def crossover(self, mate: "GAGenome") -> Tuple["GAGenome", "GAGenome"]:
        """Return two children (classic GAlib style)."""
        ...

    @abstractmethod
    def mutate(self, pmut: float) -> int:
        """Apply mutation with probability pmut per locus. Return #mutations."""
        ...

    def evaluate(self, fitness_fn: Optional[Callable[["GAGenome"], float]] = None) -> float:
        """
        If a fitness_fn is provided, compute and cache.
        Otherwise assume subclass or external side-effect set the score.
        """
        if fitness_fn is not None:
            s = float(fitness_fn(self))
            self.set_score(s)
            return s
        if self._score is not None:
            return self._score
        raise RuntimeError("No score and no fitness_fn supplied to evaluate()")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} score={self.score}>"


@dataclass
class KickVectorGenome(GAGenome):
    """
    Numeric vector genome — direct analog to GA1DArrayGenome<float> or GABin2Dec.

    Primary use: evolving HumorDNA.core_preferences, role weights, TAS var values,
    dynamic command weights (⫻cmd/weight), etc.

    Values are list[float]. Bounds per locus optional (min/max pairs).
    """
    vector: List[float] = field(default_factory=list)
    bounds: Optional[List[Tuple[float, float]]] = None  # per-locus (low, high) or None
    name: str = "vector"

    def __post_init__(self):
        super().__init__()
        if self.bounds and len(self.bounds) != len(self.vector):
            # pad or truncate gracefully
            if len(self.bounds) < len(self.vector):
                self.bounds = list(self.bounds) + [(0.0, 1.0)] * (len(self.vector) - len(self.bounds))
            else:
                self.bounds = self.bounds[: len(self.vector)]

    def clone(self) -> "KickVectorGenome":
        g = KickVectorGenome(
            vector=list(self.vector),
            bounds=copy.deepcopy(self.bounds),
            name=self.name,
        )
        g.user_data = copy.deepcopy(self.user_data)
        if self.score is not None:
            g.set_score(self.score)
        return g

    def crossover(self, mate: "GAGenome") -> Tuple["KickVectorGenome", "KickVectorGenome"]:
        if not isinstance(mate, KickVectorGenome):
            raise TypeError("KickVectorGenome can only crossover with another KickVectorGenome")
        if len(self.vector) != len(mate.vector):
            raise ValueError("Vector length mismatch for crossover")

        n = len(self.vector)
        # Single-point (GAlib default often uses uniform or multi-point; we do both options via p)
        point = random.randint(1, n - 1) if n > 1 else 0

        c1 = self.clone()
        c2 = mate.clone()
        c1.vector = self.vector[:point] + mate.vector[point:]
        c2.vector = mate.vector[:point] + self.vector[point:]

        # inherit bounds from self (or could blend)
        c1.bounds = copy.deepcopy(self.bounds)
        c2.bounds = copy.deepcopy(self.bounds)
        c1.invalidate()
        c2.invalidate()
        return c1, c2

    def mutate(self, pmut: float) -> int:
        """Gaussian perturbation per locus with prob pmut. Respects bounds when present."""
        mutations = 0
        for i in range(len(self.vector)):
            if random.random() < pmut:
                sigma = 0.8  # reasonable default scale for [-1,15] style prefs
                delta = random.gauss(0.0, sigma)
                new_val = self.vector[i] + delta

                if self.bounds:
                    lo, hi = self.bounds[i]
                    new_val = max(lo, min(hi, new_val))
                else:
                    # soft clamp for typical DNA range
                    new_val = max(0.0, min(16.0, new_val))

                self.vector[i] = round(new_val, 4)
                mutations += 1
        if mutations > 0:
            self.invalidate()
        return mutations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "vector": list(self.vector),
            "bounds": self.bounds,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "KickVectorGenome":
        g = cls(vector=list(d.get("vector", [])), bounds=d.get("bounds"), name=d.get("name", "vector"))
        if d.get("score") is not None:
            g.set_score(float(d["score"]))
        return g


@dataclass
class KickListGenome(GAGenome):
    """
    Genome over lists of strings/symbols.

    Good for: signature_jokes, banned_structures, affirm lists, pipeline stage names,
    evolution_history, recurring anchors, etc.
    """
    items: List[str] = field(default_factory=list)
    name: str = "list"

    def clone(self) -> "KickListGenome":
        g = KickListGenome(items=list(self.items), name=self.name)
        g.user_data = copy.deepcopy(self.user_data)
        if self.score is not None:
            g.set_score(self.score)
        return g

    def crossover(self, mate: "GAGenome") -> Tuple["KickListGenome", "KickListGenome"]:
        if not isinstance(mate, KickListGenome):
            raise TypeError("KickListGenome only crosses with KickListGenome")
        # Order crossover (OX) style - good for sequences that have meaning in order
        a, b = self.items, mate.items
        if not a or not b:
            return self.clone(), mate.clone()

        n = min(len(a), len(b))
        if n < 2:
            return self.clone(), mate.clone()

        i = random.randint(0, n - 2)
        j = random.randint(i + 1, n - 1)

        # Build children preserving relative order from the other parent outside the slice
        def ox(p1: List[str], p2: List[str], start: int, end: int) -> List[str]:
            child = [None] * len(p1)
            child[start:end] = p1[start:end]
            p2_iter = [x for x in p2 if x not in child[start:end]]
            ptr = 0
            for k in range(len(child)):
                if child[k] is None:
                    child[k] = p2_iter[ptr]
                    ptr += 1
            return [x for x in child if x is not None]

        c1 = KickListGenome(items=ox(a, b, i, j), name=self.name)
        c2 = KickListGenome(items=ox(b, a, i, j), name=self.name)
        c1.invalidate()
        c2.invalidate()
        return c1, c2

    def mutate(self, pmut: float) -> int:
        mutations = 0
        # With pmut prob: swap two elements, or replace one with a "neighbor" variant (here: delete+insert random)
        n = len(self.items)
        if n < 2:
            return 0

        if random.random() < pmut:
            # swap
            i, j = random.sample(range(n), 2)
            self.items[i], self.items[j] = self.items[j], self.items[i]
            mutations += 1

        if random.random() < pmut * 0.6 and n > 1:
            # replace one item with a lightly edited version (simulates "point mutation" on string content)
            idx = random.randrange(n)
            original = self.items[idx]
            # very light transform: reverse a substring or append a marker (keeps it KickLang-ish)
            if len(original) > 4:
                k = random.randint(1, len(original) - 2)
                mutated = original[:k][::-1] + original[k:]
            else:
                mutated = original + "_var"
            self.items[idx] = mutated
            mutations += 1

        if mutations > 0:
            self.invalidate()
        return mutations

    def to_kick_lines(self, key: str = "items") -> List[str]:
        """Emit as KickLang list block style."""
        lines = [f"{key}:"]
        for it in self.items:
            lines.append(f"  - {it}")
        return lines


@dataclass
class KickBlockGenome(GAGenome):
    """
    Genome representing a KickLang declarative block (or fragment).

    The 'data' is a dict following the ⫻block style (see runtime.kick, humor.kick).
    This enables GA over higher-level symbolic structures (e.g. entire ⫻ga:result or ⫻humor:dna:block).
    Mutation/crossover are structural (add/remove keys, splice lists).
    """
    data: Dict[str, Any] = field(default_factory=dict)
    block_type: str = "generic"

    def clone(self) -> "KickBlockGenome":
        g = KickBlockGenome(data=copy.deepcopy(self.data), block_type=self.block_type)
        g.user_data = copy.deepcopy(self.user_data)
        if self.score is not None:
            g.set_score(self.score)
        return g

    def crossover(self, mate: "GAGenome") -> Tuple["KickBlockGenome", "KickBlockGenome"]:
        if not isinstance(mate, KickBlockGenome):
            raise TypeError("KickBlockGenome only crosses with same type")
        # Simple: split keys
        keys_self = list(self.data.keys())
        keys_mate = list(mate.data.keys())
        random.shuffle(keys_self)
        random.shuffle(keys_mate)
        mid = len(keys_self) // 2
        c1d = {k: self.data[k] for k in keys_self[:mid]}
        c1d.update({k: mate.data[k] for k in keys_mate[mid:] if k not in c1d})
        c2d = {k: mate.data[k] for k in keys_mate[:mid]}
        c2d.update({k: self.data[k] for k in keys_self[mid:] if k not in c2d})

        c1 = KickBlockGenome(data=c1d, block_type=self.block_type)
        c2 = KickBlockGenome(data=c2d, block_type=self.block_type)
        c1.invalidate()
        c2.invalidate()
        return c1, c2

    def mutate(self, pmut: float) -> int:
        mutations = 0
        if not self.data:
            return 0
        # Randomly tweak a list value inside, or flip a scalar, or add a generated key
        for k, v in list(self.data.items()):
            if isinstance(v, list) and random.random() < pmut:
                if v and random.random() < 0.5:
                    # drop or duplicate an element
                    if random.random() < 0.5 and len(v) > 1:
                        v.pop(random.randrange(len(v)))
                    else:
                        v.append(v[random.randrange(len(v))] + "_evolved")
                    mutations += 1
            elif isinstance(v, (int, float)) and random.random() < pmut:
                self.data[k] = round(v + random.gauss(0, 0.7), 4)
                mutations += 1
            elif isinstance(v, str) and random.random() < pmut * 0.4:
                self.data[k] = v + " [evolved]"
                mutations += 1

        # Occasionally inject a new key
        if random.random() < pmut * 0.3:
            new_key = f"evolved_trait_{random.randint(100,999)}"
            self.data[new_key] = round(random.uniform(5, 14), 2)
            mutations += 1

        if mutations > 0:
            self.invalidate()
        return mutations

    def to_kick_block(self, directive: str = "⫻ga:result") -> str:
        """Very small emitter for human + machine readable KickLang block."""
        lines = [directive]
        for k, v in self.data.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{k}: {v}")
        return "\n".join(lines)
