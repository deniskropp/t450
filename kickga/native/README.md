# Native GAlib Bridge (Optional)

When the pure-Python kickga is not enough (very large populations, custom allele sets, real-time constraints), drop to the real GAlib.

## Minimal C++ Example (GAlib 2.4 / 3.x style)

```cpp
#include <ga/GASimpleGA.h>
#include <ga/GA1DArrayGenome.h>
#include <ga/GASelector.h>
#include <iostream>

float objective(GAGenome& g) {
    GA1DArrayGenome<float>& genome = (GA1DArrayGenome<float>&)g;
    // compute KickLang-style humor / coherence / TAS fitness here
    float score = 0;
    for(int i=0; i<genome.length(); i++) score += genome.gene(i);
    return score;
}

int main() {
    int length = 14;
    GA1DArrayGenome<float> genome(length);
    genome.initializer(GA1DArrayGenome<float>::UniformInitializer);
    genome.mutator(GA1DArrayGenome<float>::GaussianMutator);
    genome.crossover(GA1DArrayGenome<float>::UniformCrossover);
    genome.evaluator(objective);

    GASimpleGA ga(genome);
    ga.populationSize(50);
    ga.pCrossover(0.85);
    ga.pMutation(0.02);
    ga.nGenerations(80);
    ga.selectScores(GAStatistics::Maximum);
    ga.evolve();

    std::cout << "Best: " << ga.population().best().score() << std::endl;
    return 0;
}
```

Compile against a built GAlib (`-I/path/to/galib -L... -lga`).

## Bridge Strategy

- kickga writes a JSON population + fitness descriptor
- native binary reads it, runs the GA using real GAlib operators + your C++ fitness (which can call back into Python humor scorers or a full KickLang interpreter via pybind11 / subprocess)
- Results written back as JSON → `emit_kick_dna_block` or direct .kick emission

This keeps the symbolic KickLang layer 100% in control while the heavy search can use the canonical library.
