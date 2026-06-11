#!/usr/bin/env python3
"""Minimal CLI for kickga experiments. GAlib-style KickLang GA driver."""

import argparse
import json
import sys
from pathlib import Path

# allow running as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kickga import create_ga_from_kick, emit_kick_dna_block, load_kick_ga_spec


def main():
    p = argparse.ArgumentParser(description="kickga — evolve KickLang structures with GAlib-inspired GA")
    p.add_argument("spec", nargs="?", help="Path to .kick ga:experiment spec (or '-' for stdin)")
    p.add_argument("--seed", help="Path to JSON seed (e.g. current humor_dna dict)")
    p.add_argument("--gens", type=int, default=None, help="Override generations")
    p.add_argument("--emit", choices=["block", "json", "both"], default="both")
    p.add_argument("--out", default="-", help="Output file (or - for stdout)")
    args = p.parse_args()

    if args.spec and args.spec != "-":
        src = Path(args.spec).read_text(encoding="utf-8")
    else:
        src = sys.stdin.read()

    seed = None
    if args.seed:
        seed = json.loads(Path(args.seed).read_text(encoding="utf-8"))

    ga = create_ga_from_kick(src, seed=seed)
    if args.gens:
        ga.nGenerations = args.gens
    ga.evolve()

    best = ga.best()
    if best is None:
        print("No best genome produced", file=sys.stderr)
        sys.exit(1)

    out = []
    if args.emit in ("block", "both"):
        out.append(emit_kick_dna_block(best, version="ga-cli"))
    if args.emit in ("json", "both"):
        if hasattr(best, "to_dict"):
            out.append(json.dumps(best.to_dict(), indent=2))
        else:
            out.append(json.dumps({"score": best.score}, indent=2))

    result = "\n\n".join(out)
    if args.out == "-" or not args.out:
        print(result)
    else:
        Path(args.out).write_text(result, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
