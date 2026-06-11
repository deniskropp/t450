"""
GASimpleGA and supporting machinery — GAlib style.

Key GAlib concepts reproduced:
- Generational loop with select/crossover/mutate/replace
- pCrossover, pMutation, population size, scaling, selector, replacement
- Statistics collection
- terminate on generation count or convergence (score plateau)

Selectors and Scaling are simple but effective starting points.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence, Tuple

from .genome import GAGenome


# --- Selectors (inspired by GARouletteWheelSelector, GATournamentSelector) ---

class Selectors:
    @staticmethod
    def roulette(pop: Sequence[GAGenome], k: int = 1) -> List[GAGenome]:
        """Fitness-proportional (higher score better). Assumes all evaluated."""
        scores = [g.score if g.score is not None else 0.0 for g in pop]
        total = sum(scores)
        if total <= 0:
            # fallback to uniform
            return [random.choice(pop) for _ in range(k)]
        picks = []
        for _ in range(k):
            r = random.uniform(0, total)
            acc = 0.0
            for g, s in zip(pop, scores):
                acc += s
                if acc >= r:
                    picks.append(g)
                    break
            else:
                picks.append(pop[-1])
        return picks

    @staticmethod
    def tournament(pop: Sequence[GAGenome], k: int = 1, tourney_size: int = 3) -> List[GAGenome]:
        picks = []
        for _ in range(k):
            contestants = random.sample(list(pop), min(tourney_size, len(pop)))
            # best (highest score)
            best = max(contestants, key=lambda g: (g.score if g.score is not None else float("-inf")))
            picks.append(best)
        return picks

    @staticmethod
    def best(pop: Sequence[GAGenome], k: int = 1) -> List[GAGenome]:
        sorted_pop = sorted(pop, key=lambda g: (g.score if g.score is not None else float("-inf")), reverse=True)
        return sorted_pop[:k]


# --- Scaling (GASigmaTruncationScaling, GALinearScaling, etc. simplified) ---

class Scaling:
    @staticmethod
    def none(scores: List[float]) -> List[float]:
        return scores

    @staticmethod
    def sigma_truncation(scores: List[float], c: float = 2.0) -> List[float]:
        if not scores:
            return scores
        mean = sum(scores) / len(scores)
        var = sum((s - mean) ** 2 for s in scores) / max(1, len(scores) - 1)
        sigma = var ** 0.5 or 1.0
        return [max(0.0, s - mean + c * sigma) for s in scores]


@dataclass
class GAStatistics:
    generation: int = 0
    best_score: float = float("-inf")
    avg_score: float = 0.0
    worst_score: float = float("inf")
    best_genome: Optional[GAGenome] = None
    score_history: List[float] = field(default_factory=list)

    def update(self, pop: Sequence[GAGenome]) -> None:
        evaluated = [g for g in pop if g.score is not None]
        if not evaluated:
            return
        scores = [g.score for g in evaluated]  # type: ignore
        best = max(evaluated, key=lambda g: g.score)  # type: ignore
        self.best_score = best.score  # type: ignore
        self.avg_score = sum(scores) / len(scores)
        self.worst_score = min(scores)
        self.best_genome = best.clone()
        self.score_history.append(self.best_score)


class GASimpleGA:
    """
    Generational GA modeled on GAlib's GASimpleGA.

    Typical usage (GAlib-ish):
        ga = GASimpleGA(pop, fitness_fn=some_fitness)
        ga.pCrossover = 0.9
        ga.pMutation = 0.01
        ga.populationSize(80)
        ga.evolve(100)   # or while not ga.done(): ga.step()
    """

    def __init__(
        self,
        pop: Sequence[GAGenome],
        fitness_fn: Callable[[GAGenome], float],
        maximize: bool = True,
        pop_size: Optional[int] = None,
    ):
        if not pop:
            raise ValueError("Initial population must be non-empty")
        self.fitness_fn = fitness_fn
        self.maximize = maximize
        self._pop: List[GAGenome] = [g.clone() for g in pop]
        self.pop_size = pop_size or len(self._pop)

        # GAlib-like parameters
        self.pCrossover: float = 0.9
        self.pMutation: float = 0.02
        self.nGenerations: int = 100
        self.pReplacement: float = 1.0  # fraction replaced each gen (1.0 = full generational)

        # Termination control
        # - nGenerations is the hard maximum (respected by evolve()).
        # - terminate_on_convergence (default True) enables the plateau early-stop
        #   inside done(). Set it to False on a GA instance when you specifically
        #   want the full number of generations to run (common for TAS/playbook
        #   parameter evolution where you want to observe long-term dynamics).
        self.terminate_on_convergence: bool = True

        self.selector = Selectors.roulette
        self.scaling = Scaling.none

        self.stats = GAStatistics()
        self.generation: int = 0
        self._best_ever: Optional[GAGenome] = None

        # Ensure initial evaluation
        self._evaluate_pop()

    def populationSize(self, n: int) -> None:
        self.pop_size = n

    def _evaluate_pop(self) -> None:
        for g in self._pop:
            if not g.is_evaluated():
                s = g.evaluate(self.fitness_fn)
                if not self.maximize:
                    g.set_score(-s)  # store as "higher better" internally for selection

    def best(self) -> Optional[GAGenome]:
        if self._best_ever is not None:
            return self._best_ever
        evaluated = [g for g in self._pop if g.score is not None]
        if not evaluated:
            return None
        b = max(evaluated, key=lambda g: g.score or float("-inf"))
        return b.clone()

    def step(self) -> None:
        """One generation."""
        self._evaluate_pop()

        # Record stats before replacement
        self.stats.generation = self.generation
        self.stats.update(self._pop)

        if self._best_ever is None or (self.stats.best_genome and (self.stats.best_genome.score or float("-inf")) > (self._best_ever.score or float("-inf"))):
            self._best_ever = self.stats.best_genome.clone() if self.stats.best_genome else None

        # Selection pool (scaled conceptually; we use raw for simplicity here)
        parents: List[GAGenome] = []
        needed = int(self.pop_size * self.pReplacement) or self.pop_size
        while len(parents) < needed:
            picks = self.selector(self._pop, k=2)
            parents.extend(picks)

        # Crossover + mutation into new population
        new_pop: List[GAGenome] = []
        i = 0
        while len(new_pop) < needed:
            p1 = parents[i % len(parents)].clone()
            p2 = parents[(i + 1) % len(parents)].clone()
            i += 2

            if random.random() < self.pCrossover:
                c1, c2 = p1.crossover(p2)
            else:
                c1, c2 = p1, p2

            c1.mutate(self.pMutation)
            c2.mutate(self.pMutation)

            new_pop.append(c1)
            if len(new_pop) < needed:
                new_pop.append(c2)

        # Elitism: keep previous best if full replacement
        if self.pReplacement >= 0.999 and self.stats.best_genome:
            # replace the worst in new_pop
            worst_idx = min(range(len(new_pop)), key=lambda idx: (new_pop[idx].score or float("-inf")))
            new_pop[worst_idx] = self.stats.best_genome.clone()

        # If we scaled for internal use, we may need to re-evaluate with original sign
        self._pop = new_pop[: self.pop_size]
        self._evaluate_pop()

        self.generation += 1
        self.stats.update(self._pop)

    def evolve(self, ngen: Optional[int] = None) -> GAStatistics:
        """Run up to ngen (or self.nGenerations) generations.

        Early termination can occur if self.terminate_on_convergence is True
        and the best score has plateaued (see done()).
        """
        gens = ngen if ngen is not None else self.nGenerations
        for _ in range(gens):
            if self.done():
                break
            self.step()
        return self.stats

    def done(self) -> bool:
        """Return True if we should stop.

        Hard cap: generation count >= nGenerations.
        Optional early stop: best-score plateau over recent history
        (common once elitism protects a good individual).
        """
        if self.generation >= self.nGenerations:
            return True

        if not self.terminate_on_convergence:
            return False

        # Simple convergence / stagnation detector.
        # Because of elitism, best_score often becomes constant after a good
        # solution is found. This causes the GA to stop even if nGenerations
        # was set higher. Set terminate_on_convergence=False to ignore this.
        hist = self.stats.score_history
        if len(hist) >= 8:
            recent = hist[-8:]
            if max(recent) - min(recent) < 1e-4:
                return True
        return False

    def population(self) -> List[GAGenome]:
        return [g.clone() for g in self._pop]

    def statistics(self) -> GAStatistics:
        return self.stats
