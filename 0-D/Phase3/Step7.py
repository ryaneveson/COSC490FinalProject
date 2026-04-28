"""
Step 7: Password creation / hardening

Uses Phase 1 pattern statistics (Step 4) for awareness and Phase 2 grading (Step 6)
to steer generation away from high-frequency structural templates and to score
hardened passwords.

Usage:
  python Step7.py --generate 5 --length 16
  python Step7.py --harden "winter2024"
  python Step7.py --harden "baseball!" --min-score 65 --iterations 30
"""

from __future__ import annotations

import argparse
import json
import secrets
import string
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

_PHASE2 = Path(__file__).resolve().parent.parent / "Phase2"
if str(_PHASE2) not in sys.path:
    sys.path.insert(0, str(_PHASE2))

from Step6 import (  # noqa: E402
    COMMON_KEYBOARD_PATTERNS,
    COMMON_WEAK_WORDS,
    KEYBOARD_SEQS,
    PasswordGrader,
)

SAFE_SPECIAL = "!@#$%^&*-_=+?"
LOWER = string.ascii_lowercase
UPPER = string.ascii_uppercase
DIGITS = string.digits


def _has_keyboard_substr(p: str) -> bool:
    low = p.lower()
    if any(pat in low for pat in COMMON_KEYBOARD_PATTERNS):
        return True
    return any(s in low for s in KEYBOARD_SEQS)


def _char_classes(p: str) -> Set[str]:
    s = set()
    for c in p:
        if c.islower():
            s.add("lower")
        elif c.isupper():
            s.add("upper")
        elif c.isdigit():
            s.add("digit")
        else:
            s.add("special")
    return s


def generate_secure_password(length: int = 16, max_trials: int = 80) -> str:
    """Random password with four character classes; avoids common keyboard runs."""
    length = max(12, min(128, length))
    rng = secrets.SystemRandom()
    allch = LOWER + UPPER + DIGITS + SAFE_SPECIAL
    for _ in range(max_trials):
        body = [secrets.choice(allch) for _ in range(length)]
        # ensure each class at least once
        body[0] = secrets.choice(LOWER)
        body[1] = secrets.choice(UPPER)
        body[2] = secrets.choice(DIGITS)
        body[3] = secrets.choice(SAFE_SPECIAL)
        rng.shuffle(body)
        cand = "".join(body)
        cls = _char_classes(cand)
        if len(cls) < 4:
            continue
        if _has_keyboard_substr(cand):
            continue
        if any(w in cand.lower() for w in COMMON_WEAK_WORDS if len(w) > 3):
            continue
        return cand
    return "".join(
        secrets.choice(LOWER + UPPER + DIGITS + SAFE_SPECIAL) for _ in range(length)
    )


def _strip_run_breaks(s: str) -> str:
    """Insert disruptors into long alphanumeric runs to break keyboard-like streaks."""
    out: List[str] = []
    run = 0
    for i, c in enumerate(s):
        out.append(c)
        run = run + 1 if i and c.isalnum() and s[i - 1].isalnum() else 1
        if run == 4:
            out.insert(-2, secrets.choice(SAFE_SPECIAL))
            run = 0
    return "".join(out)


def harden_password(
    seed: str,
    grader: PasswordGrader,
    min_score: float = 62.0,
    max_iterations: int = 25,
    target_length: int = 16,
) -> Tuple[str, dict, List[dict]]:
    """
    Transform a weak or memorable seed into a stronger password while keeping
    some user-chosen entropy, then append high-entropy material until grade passes.
    """
    history: List[dict] = []
    seed = (seed or "").strip()
    if not seed:
        pw = generate_secure_password(target_length)
        g0 = grader.grade(pw)
        history.append(g0)
        return pw, g0, history

    base = list(seed)
    # break obvious whole-dictionary weak words by inserting separators
    low = seed.lower()
    for w in sorted(COMMON_WEAK_WORDS, key=len, reverse=True):
        if w in low and len(w) >= 4:
            idx = low.find(w)
            insert = secrets.choice(SAFE_SPECIAL + "_")
            base.insert(idx + len(w) // 2, insert)
            seed = "".join(base)
            low = seed.lower()
    seed = _strip_run_breaks(seed)

    disrupt = "".join(
        secrets.choice(SAFE_SPECIAL + DIGITS + UPPER) for _ in range(4)
    )
    core = seed[: max(1, len(seed) // 2)] + disrupt + seed[len(seed) // 2 :]
    pad_needed = max(0, target_length - len(core))
    pad = "".join(
        secrets.choice(LOWER + UPPER + DIGITS + SAFE_SPECIAL) for _ in range(pad_needed)
    )
    pw = core + pad

    for _ in range(max_iterations):
        g = grader.grade(pw)
        history.append(g)
        if g["final_score"] >= min_score and len(pw) >= 12 and len(_char_classes(pw)) >= 3:
            return pw, g, history
        addon = "".join(
            secrets.choice(LOWER + UPPER + DIGITS + SAFE_SPECIAL) for _ in range(4)
        )
        pw = pw + addon
        if len(pw) > 64:
            pw = pw[-64:]

    g = grader.grade(pw)
    history.append(g)
    if g["final_score"] < min_score:
        fallback = generate_secure_password(max(target_length, 16))
        gf = grader.grade(fallback)
        history.append(gf)
        return fallback, gf, history
    return pw, g, history


def load_step4_pattern_summary(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    pt = data.get("pattern_types", {})
    ranked = sorted(pt.items(), key=lambda x: x[1], reverse=True)
    return {
        "pattern_types_by_frequency": [{"type": k, "count": v} for k, v in ranked],
        "note": "Generator avoids keyboard templates and weak dictionary stems; "
        "grading uses Step 6 (pattern-type penalties from these frequencies).",
    }


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    phase1 = here.parent / "Phase1"
    phase2 = here.parent / "Phase2"
    p = argparse.ArgumentParser(description="Step 7: password generation / hardening")
    p.add_argument("--generate", type=int, default=0, help="Number of secure passwords to emit")
    p.add_argument("--harden", type=str, default=None, help="Seed string to harden")
    p.add_argument("--length", type=int, default=16, help="Target length for generated/hardened passwords")
    p.add_argument("--min-score", type=float, default=62.0, help="Minimum Step 6 final_score when hardening")
    p.add_argument("--iterations", type=int, default=30, help="Max hardening iterations")
    p.add_argument("--ngram-model", type=str, default=str(phase2 / "step5_ngram_model.json"))
    p.add_argument("--step4-results", type=str, default=str(phase1 / "step4_semantic_results.json"))
    p.add_argument("--output-dir", type=str, default=str(here))
    p.add_argument("--json-summary", action="store_true", help="Write step7_creation_results.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.generate <= 0 and not args.harden:
        print("Specify --generate N and/or --harden \"seed\"")
        return

    out_dir = Path(args.output_dir)
    ngram = Path(args.ngram_model)
    s4 = Path(args.step4_results)

    grader = PasswordGrader(
        ngram_model_path=ngram if ngram.exists() else None,
        step4_results_path=s4 if s4.exists() else None,
        quiet=True,
    )

    pattern_meta = load_step4_pattern_summary(s4) if s4.exists() else {}

    results: Dict = {
        "pattern_awareness": pattern_meta,
        "generated": [],
        "hardened": None,
    }

    if args.generate > 0:
        print(f"\nGenerated {args.generate} password(s) (length ~{args.length}):\n")
        for _ in range(args.generate):
            pw = generate_secure_password(args.length)
            g = grader.grade(pw)
            results["generated"].append(
                {"password": pw, "grade": g["grade"], "final_score": g["final_score"]}
            )
            print(f"  {pw}")
            print(
                f"     Grade {g['grade']}  score={g['final_score']:.2f}  "
                f"raw={g.get('raw_score', g['final_score']):.2f}\n"
            )

    if args.harden is not None:
        print(f"\nHardening seed (min score {args.min_score}):\n")
        pw, final_g, hist = harden_password(
            args.harden,
            grader,
            min_score=args.min_score,
            max_iterations=args.iterations,
            target_length=args.length,
        )
        results["hardened"] = {
            "original": args.harden,
            "password": pw,
            "final_grade": final_g,
            "final_score": final_g["final_score"],
            "iterations_tried": len(hist),
        }
        print(f"  Result: {pw}")
        print(
            f"  Grade {final_g['grade']}  score={final_g['final_score']:.2f}  "
            f"raw={final_g.get('raw_score', final_g['final_score']):.2f}\n"
        )

    if args.json_summary:
        jp = out_dir / "step7_creation_results.json"
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Wrote {jp}")


if __name__ == "__main__":
    main()
