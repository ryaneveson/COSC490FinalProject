"""
Step 6: Password Grading
Multi-factor password scoring system combining:
  - Predictability scoring  (character n-gram model from Step 5)
  - Pattern type penalties   (weighted deduction from Step 4 rankings)
  - Specific pattern penalties (keyboard runs, trailing !, repeated chars …)
  - Complexity / length bonuses

Formula (conceptually):
    raw = base_predictability + complexity_bonus
          - pattern_type_penalty - specific_pattern_penalty
    final = gentle calibration(raw)  # spreads typical cases toward a fairer, bell-shaped spread
    clamped to [0, 100]

Depends on:
  - Step 5 n-gram model  (step5_ngram_model.json)
  - Step 4 results        (step4_semantic_results.json)  [optional]
  - english-words library  [optional, for dictionary lookup]

Usage:
    # Grade the full dataset
    python Step6.py --base-dir data/archive

    # Faster on multi-core machines (one process loads the model, then shards by folder)
    python Step6.py --base-dir data/archive --workers 4

    # Grade a single password interactively
    python Step6.py --grade "P@ssw0rd123"

    # Interactive prompt
    python Step6.py --interactive
"""

import json
import math
import os
import re
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from english_words import get_english_words_set
    DICT_AVAILABLE = True
except ImportError:
    DICT_AVAILABLE = False

TARGET_FOLDERS = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "A", "B", "C", "D",
]

START_TOKEN = "<S>"
END_TOKEN = "<E>"

# ====================================================================== #
#  L33t / keyboard pattern tables (mirrors Step 4)                         #
# ====================================================================== #
LEET_REPLACEMENTS = {
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "8": "b", "9": "g", "@": "a", "$": "s",
    "!": "i", "+": "t",
}

KEYBOARD_ROWS = ["1234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"]

COMMON_KEYBOARD_PATTERNS = {
    "qwerty", "asdf", "zxcv", "1234", "12345", "123456", "1234567",
    "qaz", "wsx", "edc", "rfv", "tgy", "uhy", "ijm", "poiuy",
    "asdfgh", "qwert", "12341", "qazwsx",
}

KEYBOARD_SEQS: Set[str] = set()
for _row in KEYBOARD_ROWS:
    for _i in range(len(_row) - 2):
        _seq = _row[_i:_i + 3]
        KEYBOARD_SEQS.add(_seq)
        KEYBOARD_SEQS.add(_seq[::-1])

COMMON_WEAK_WORDS = {
    "password", "admin", "welcome", "login", "master",
    "monkey", "dragon", "shadow", "sunshine", "princess",
    "football", "baseball", "soccer", "hockey", "batman",
    "trustno1", "letmein", "access", "hello", "charlie",
    "donald", "iloveyou", "abc123", "qwerty", "passw0rd",
}

SEQUENTIAL_ALPHA = "abcdefghijklmnopqrstuvwxyz"
SEQUENTIAL_DIGITS = "0123456789"


# ====================================================================== #
#  Lightweight n-gram model (loaded from Step 5)                           #
# ====================================================================== #
class NgramScorer:
    """Loads a pre-trained character n-gram model and computes scores."""

    def __init__(self, model_path: Optional[Path] = None, quiet: bool = False):
        self.bigram_counts: Dict[str, Dict[str, int]] = {}
        self.bigram_totals: Dict[str, int] = {}
        self.trigram_counts: Dict[str, Dict[str, int]] = {}
        self.trigram_totals: Dict[str, int] = {}
        self.vocab_size: int = 97
        self.loaded = False
        self._quiet = quiet

        if model_path and model_path.exists():
            self._load(model_path)

    def _load(self, path: Path):
        with open(path, "r") as f:
            data = json.load(f)
        self.bigram_counts = data.get("bigram_counts", {})
        self.bigram_totals = {
            k: int(v) for k, v in data.get("bigram_context_totals", {}).items()
        }
        self.trigram_counts = data.get("trigram_counts", {})
        self.trigram_totals = {
            k: int(v) for k, v in data.get("trigram_context_totals", {}).items()
        }
        self.vocab_size = int(data.get("vocab_size", 97))
        self.loaded = True
        if not self._quiet:
            print(f" Loaded n-gram model from {path}")

    def predictability(self, password: str) -> float:
        """0-100 score; higher = more predictable."""
        if not self.loaded:
            return 50.0

        LAMBDA_BI, LAMBDA_TRI = 0.4, 0.6
        vs = float(self.vocab_size)
        bc = self.bigram_counts
        btc = self.bigram_totals
        tc = self.trigram_counts
        tct = self.trigram_totals
        log_sum = 0.0
        n = 0
        p2, p1 = START_TOKEN, START_TOKEN
        for cur in (*password, END_TOKEN):
            row_b = bc.get(p1)
            cnt_b = row_b.get(cur, 0) if row_b else 0
            tot_b = btc.get(p1, 0)
            bi = (cnt_b + 1.0) / (tot_b + vs)
            tri_key = p2 + "|" + p1
            row_t = tc.get(tri_key)
            cnt_t = row_t.get(cur, 0) if row_t else 0
            tot_t = tct.get(tri_key, 0)
            tri = (cnt_t + 1.0) / (tot_t + vs)
            interp = LAMBDA_BI * bi + LAMBDA_TRI * tri
            log_sum += math.log2(interp) if interp > 0 else -30.0
            n += 1
            p2, p1 = p1, cur

        if n == 0:
            return 50.0
        avg_log = log_sum / n
        return max(0.0, min(100.0, (avg_log + 10.0) / 9.0 * 100.0))


# ====================================================================== #
#  Pattern detection helpers                                               #
# ====================================================================== #
def _normalize_leet(text: str) -> str:
    return "".join(LEET_REPLACEMENTS.get(c, c) for c in text.lower())


def _extract_alpha_tokens(text: str) -> List[str]:
    tokens, cur = [], []
    for c in text.lower():
        if c.isalpha():
            cur.append(c)
        elif cur:
            tok = "".join(cur)
            if len(tok) > 1:
                tokens.append(tok)
            cur = []
    if cur:
        tok = "".join(cur)
        if len(tok) > 1:
            tokens.append(tok)
    return tokens


def _has_keyboard_pattern(password: str) -> bool:
    p = password.lower()
    return (any(pat in p for pat in COMMON_KEYBOARD_PATTERNS) or
            any(seq in p for seq in KEYBOARD_SEQS))


def _find_keyboard_patterns(
    password: str, max_hits: Optional[int] = None
) -> List[str]:
    """If max_hits is set, stop once that many matches are found (penalty caps early)."""
    p = password.lower()
    found = []
    for pat in COMMON_KEYBOARD_PATTERNS:
        if pat in p:
            found.append(pat)
            if max_hits is not None and len(found) >= max_hits:
                return found
    for seq in KEYBOARD_SEQS:
        if seq in p and seq not in found:
            found.append(seq)
            if max_hits is not None and len(found) >= max_hits:
                break
    return found


def _count_repeated_chars(password: str) -> int:
    """Count groups of 3+ identical consecutive characters."""
    count = 0
    i = 0
    while i < len(password):
        run = 1
        while i + run < len(password) and password[i + run] == password[i]:
            run += 1
        if run >= 3:
            count += 1
        i += run
    return count


def _count_sequential_runs(password: str) -> int:
    """Count runs of 3+ sequential characters (abc, 123, cba, 321)."""
    p = password.lower()
    count = 0
    for seq_source in (SEQUENTIAL_ALPHA, SEQUENTIAL_DIGITS):
        fwd = seq_source
        rev = seq_source[::-1]
        for src in (fwd, rev):
            for start in range(len(src) - 2):
                sub = src[start:start + 3]
                if sub in p:
                    count += 1
    return count


def _has_trailing_special_only(password: str) -> bool:
    """True if password ends with a single special char preceded by alnum."""
    if len(password) < 2:
        return False
    return (not password[-1].isalnum() and password[-2].isalnum() and
            all(c.isalnum() for c in password[:-1]))


def _has_date_pattern(password: str) -> bool:
    return bool(re.search(r'(19|20)\d{2}', password))


def _classify_pattern_type(password: str, dict_tokens: Set[str]) -> str:
    """Mirror of Step 4's pattern classifier."""
    has_dict = bool(dict_tokens)
    has_leet = any(c in password for c in LEET_REPLACEMENTS)
    has_keyboard = _has_keyboard_pattern(password)
    has_special = any(not c.isalnum() for c in password)
    has_digits = any(c.isdigit() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)

    if has_dict and has_special and has_digits:
        if has_upper and has_lower:
            return "word_special_digit_mixed"
        elif has_upper:
            return "word_special_digit_upper"
        else:
            return "word_special_digit_lower"
    elif has_dict and has_digits:
        return "word_digit"
    elif has_dict and has_special:
        return "word_special"
    elif has_dict:
        return "word_only"
    elif has_keyboard:
        return "keyboard_pattern"
    elif has_leet:
        return "leet_speak"
    elif has_special and has_digits:
        return "special_digit"
    elif has_digits:
        return "digit_only"
    else:
        return "other"


# ====================================================================== #
#  Default penalty weights for pattern types (used when Step 4 unavailable)#
# ====================================================================== #
DEFAULT_PATTERN_PENALTIES = {
    "word_only":                  12,
    "word_digit":                 10,
    "word_special_digit_lower":    7,
    "word_special_digit_upper":    7,
    "word_special_digit_mixed":    6,
    "word_special":                8,
    "keyboard_pattern":           11,
    "leet_speak":                  4,
    "digit_only":                  9,
    "special_digit":               3,
    "other":                       0,
}


# ====================================================================== #
#  Grader                                                                  #
# ====================================================================== #
class PasswordGrader:
    """Multi-factor password grading system."""

    # Typical passwords should not all land in D/F because the top bucket types
    # (leet / word+digit+special) are common, not automatically catastrophic.
    PATTERN_TYPE_PENALTY_CAP = 12.0
    PATTERN_TYPE_PENALTY_SCALE = 0.72
    SPECIFIC_PATTERN_PENALTY_CAP = 18.0

    # Mild lift + compression: moves the mass from report (~30-50) toward ~45-65
    # (more bell-like letter grades) without flattening very strong passwords.
    SCORE_CALIBRATE_SLOPE = 0.90
    SCORE_CALIBRATE_OFFSET = 6.5

    GRADE_LABELS = [
        (90, "A+", "Excellent"),
        (80, "A",  "Very Strong"),
        (66, "B",  "Strong"),
        (52, "C",  "Fair"),
        (38, "D",  "Weak"),
        (0,  "F",  "Very Weak"),
    ]

    def __init__(
        self,
        ngram_model_path: Optional[Path] = None,
        step4_results_path: Optional[Path] = None,
        quiet: bool = False,
    ):
        self._quiet = quiet
        self._ngram_path_s = str(ngram_model_path) if ngram_model_path else ""
        self._step4_path_s = (
            str(step4_results_path)
            if step4_results_path and step4_results_path.exists()
            else ""
        )
        self.scorer = NgramScorer(ngram_model_path, quiet=quiet)
        self.dictionary: Optional[Set[str]] = None
        self.pattern_penalties = dict(DEFAULT_PATTERN_PENALTIES)

        self._load_dictionary()
        if step4_results_path and step4_results_path.exists():
            self._load_step4_penalties(step4_results_path)

    def _load_dictionary(self):
        if DICT_AVAILABLE:
            try:
                self.dictionary = get_english_words_set(["web2"], lower=True)
                if not self._quiet:
                    print(f" Dictionary loaded ({len(self.dictionary):,} words)")
            except Exception as e:
                if not self._quiet:
                    print(f"  Dictionary load failed: {e}")
        else:
            if not self._quiet:
                print("  english-words not installed; dictionary penalties disabled.")

    def _load_step4_penalties(self, path: Path):
        """Derive penalty weights from Step 4 pattern type frequencies."""
        with open(path, "r") as f:
            data = json.load(f)
        pt = data.get("pattern_types", {})
        total = sum(pt.values()) or 1

        for ptype, count in pt.items():
            pct = count / total * 100
            # Softer ladder: very common structure ≠ max deduction (was 18 for >30%).
            if pct > 30:
                penalty = 11
            elif pct > 15:
                penalty = 9
            elif pct > 5:
                penalty = 7
            elif pct > 1:
                penalty = 5
            else:
                penalty = 2
            self.pattern_penalties[ptype] = penalty
        if not self._quiet:
            print(f" Loaded pattern penalties from Step 4 ({len(pt)} types)")

    # ------------------------------------------------------------------ #
    #  Scoring components                                                  #
    # ------------------------------------------------------------------ #
    def _base_predictability_score(self, password: str) -> float:
        """0–50; higher = less predictable (better)."""
        pred = self.scorer.predictability(password)
        return 50.0 * (1.0 - pred / 100.0)

    def _complexity_bonus(self, password: str) -> Tuple[float, dict]:
        """0–50 bonus for length + character-class diversity + uniqueness."""
        length = len(password)
        if length >= 16:
            len_bonus = 20
        elif length >= 12:
            len_bonus = 16
        elif length >= 10:
            len_bonus = 12
        elif length >= 8:
            len_bonus = 8
        elif length >= 6:
            len_bonus = 5
        else:
            len_bonus = 0

        classes = set()
        for c in password:
            if c.islower():
                classes.add("lower")
            elif c.isupper():
                classes.add("upper")
            elif c.isdigit():
                classes.add("digit")
            else:
                classes.add("special")

        class_map = {1: 0, 2: 5, 3: 12, 4: 20}
        class_bonus = class_map.get(len(classes), 0)

        unique_ratio = len(set(password)) / length if length else 0
        if unique_ratio > 0.8:
            uniq_bonus = 10
        elif unique_ratio > 0.5:
            uniq_bonus = 5
        else:
            uniq_bonus = 0

        total = len_bonus + class_bonus + uniq_bonus
        detail = {
            "length_bonus": len_bonus,
            "class_bonus": class_bonus,
            "unique_ratio_bonus": uniq_bonus,
            "char_classes": sorted(classes),
            "unique_ratio": round(unique_ratio, 3),
        }
        return min(total, 50), detail

    def _pattern_type_penalty(self, password: str) -> Tuple[float, dict]:
        """Penalty from Step 4 pattern type (scaled/capped for reasonable spread)."""
        dict_tokens: Set[str] = set()
        if self.dictionary and any(c.isalpha() for c in password):
            plain = set(_extract_alpha_tokens(password.lower()))
            leet = set(_extract_alpha_tokens(_normalize_leet(password)))
            dict_tokens = plain.intersection(self.dictionary) | leet.intersection(self.dictionary)

        ptype = _classify_pattern_type(password, dict_tokens)
        raw = float(self.pattern_penalties.get(ptype, 0))
        penalty = min(
            self.PATTERN_TYPE_PENALTY_CAP,
            raw * self.PATTERN_TYPE_PENALTY_SCALE,
        )
        return penalty, {"pattern_type": ptype, "dict_words_found": sorted(dict_tokens)[:10]}

    def _specific_pattern_penalty(self, password: str) -> Tuple[float, dict]:
        """Penalty for known weak constructs (capped lower to avoid stacking with pattern type)."""
        penalty = 0.0
        reasons = []
        low = password.lower()

        # Keyboard patterns (max 3 hits: min(3*3,7) == max keyboard slice of cap 18)
        kb = _find_keyboard_patterns(password, max_hits=3)
        if kb:
            penalty += min(len(kb) * 3, 7)
            reasons.append(f"keyboard patterns: {', '.join(kb[:5])}")

        # Common weak words
        for word in COMMON_WEAK_WORDS:
            if word in low:
                penalty += 5
                reasons.append(f"common weak word: {word}")
                break

        # Trailing single special char
        if _has_trailing_special_only(password):
            penalty += 3
            reasons.append("trailing special char only")

        # Repeated characters
        reps = _count_repeated_chars(password)
        if reps:
            penalty += min(reps * 2, 7)
            reasons.append(f"repeated char groups: {reps}")

        # Sequential runs
        seqs = _count_sequential_runs(password)
        if seqs:
            penalty += min(int(seqs * 1.5 + 0.5), 5)
            reasons.append(f"sequential runs: {seqs}")

        # Date patterns
        if _has_date_pattern(password):
            penalty += 2
            reasons.append("date pattern detected")

        penalty = min(penalty, self.SPECIFIC_PATTERN_PENALTY_CAP)
        return penalty, {"reasons": reasons}

    # ------------------------------------------------------------------ #
    #  Main grading                                                        #
    # ------------------------------------------------------------------ #
    def grade(self, password: str) -> dict:
        """Grade a single password. Returns full breakdown."""
        base = self._base_predictability_score(password)
        comp, comp_detail = self._complexity_bonus(password)
        pt_pen, pt_detail = self._pattern_type_penalty(password)
        sp_pen, sp_detail = self._specific_pattern_penalty(password)

        raw = base + comp - pt_pen - sp_pen
        calibrated = raw * self.SCORE_CALIBRATE_SLOPE + self.SCORE_CALIBRATE_OFFSET
        final = max(0.0, min(100.0, calibrated))

        letter = "F"
        label = "Very Weak"
        for threshold, ltr, lbl in self.GRADE_LABELS:
            if final >= threshold:
                letter, label = ltr, lbl
                break

        return {
            "password": password,
            "raw_score": round(max(0.0, min(100.0, raw)), 2),
            "final_score": round(final, 2),
            "grade": letter,
            "grade_label": label,
            "breakdown": {
                "base_predictability": round(base, 2),
                "complexity_bonus": round(comp, 2),
                "pattern_type_penalty": round(pt_pen, 2),
                "specific_pattern_penalty": round(sp_pen, 2),
            },
            "details": {
                "complexity": comp_detail,
                "pattern_type": pt_detail,
                "specific_patterns": sp_detail,
            },
        }

    def _collect_folder_stats(
        self,
        base_dir: Path,
        folder: str,
        max_passwords: Optional[int],
        progress_log: bool = False,
    ) -> dict:
        """Accumulate stats for one folder shard (optionally cap lines for --sample)."""
        grade_counter: Counter = Counter()
        score_buckets: Counter = Counter()
        component_sums: Dict[str, float] = defaultdict(float)
        pattern_type_counts: Counter = Counter()
        specific_reason_counts: Counter = Counter()
        examples_by_grade: Dict[str, list] = defaultdict(list)
        total = 0

        fp = base_dir / folder / f"{folder}.txt"
        if not fp.exists():
            return {
                "folder": folder,
                "total": 0,
                "grade_counter": {},
                "score_buckets": {},
                "component_sums": {},
                "pattern_type_counts": {},
                "specific_reason_counts": {},
                "examples_by_grade": {},
            }

        try:
            with fp.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if max_passwords is not None and total >= max_passwords:
                        break
                    pw = line.strip()
                    if not pw:
                        continue

                    result = self.grade(pw)
                    total += 1

                    grade_counter[result["grade"]] += 1
                    bkt = int(result["final_score"] // 10) * 10
                    score_buckets[bkt] += 1

                    for k, v in result["breakdown"].items():
                        component_sums[k] += v

                    pt = result["details"]["pattern_type"]["pattern_type"]
                    pattern_type_counts[pt] += 1

                    for reason in result["details"]["specific_patterns"]["reasons"]:
                        specific_reason_counts[reason.split(":")[0].strip()] += 1

                    if len(examples_by_grade[result["grade"]]) < 10:
                        examples_by_grade[result["grade"]].append({
                            "password": pw[:20],
                            "score": result["final_score"],
                            "grade": result["grade"],
                        })

                    if progress_log and total % 200_000 == 0:
                        print(f"  [{folder}] graded {total:,} in shard ...")
        except Exception as e:
            print(f"  Error reading {fp}: {e}")

        return {
            "folder": folder,
            "total": total,
            "grade_counter": dict(grade_counter),
            "score_buckets": dict(score_buckets),
            "component_sums": dict(component_sums),
            "pattern_type_counts": dict(pattern_type_counts),
            "specific_reason_counts": dict(specific_reason_counts),
            "examples_by_grade": {
                g: list(exs) for g, exs in examples_by_grade.items()
            },
        }

    def _merge_folder_partials(self, partials: List[dict]) -> None:
        """Combine shard results into batch_results."""
        grade_counter: Counter = Counter()
        score_buckets: Counter = Counter()
        component_sums: Dict[str, float] = defaultdict(float)
        pattern_type_counts: Counter = Counter()
        specific_reason_counts: Counter = Counter()
        examples_by_grade: Dict[str, list] = defaultdict(list)
        total = 0

        for p in partials:
            total += p["total"]
            grade_counter.update(p["grade_counter"])
            for b, c in p["score_buckets"].items():
                score_buckets[int(b)] += c
            for k, v in p["component_sums"].items():
                component_sums[k] += v
            pattern_type_counts.update(p["pattern_type_counts"])
            specific_reason_counts.update(p["specific_reason_counts"])
            for g, exs in p["examples_by_grade"].items():
                for ex in exs:
                    if len(examples_by_grade[g]) < 10:
                        examples_by_grade[g].append(ex)

        component_avgs = (
            {k: round(v / total, 4) for k, v in component_sums.items()}
            if total
            else {}
        )

        self.batch_results = {
            "total_graded": total,
            "grade_distribution": dict(grade_counter),
            "score_distribution": dict(sorted(score_buckets.items())),
            "component_averages": component_avgs,
            "pattern_type_distribution": dict(
                pattern_type_counts.most_common()
            ),
            "specific_penalty_distribution": dict(
                specific_reason_counts.most_common()
            ),
            "examples_by_grade": {
                g: exs for g, exs in sorted(examples_by_grade.items())
            },
        }

    def grade_dataset(
        self,
        base_dir: Path,
        sample_size: Optional[int] = None,
        workers: int = 1,
    ):
        """Grade all passwords in the 0–D dataset; collect statistics."""
        print("\n" + "=" * 80)
        print("STEP 6: PASSWORD GRADING")
        print("=" * 80 + "\n")

        partials: List[dict] = []
        cpu = os.cpu_count() or 1
        use_pool = workers > 1 and sample_size is None

        if use_pool:
            n_workers = max(1, min(workers, len(TARGET_FOLDERS), cpu))
            print(
                f" Using {n_workers} parallel worker(s) "
                f"(model + dictionary loaded once per process).\n"
            )
            tasks = [(folder, str(base_dir.resolve())) for folder in TARGET_FOLDERS]
            with ProcessPoolExecutor(
                max_workers=n_workers,
                initializer=_pool_init_grader,
                initargs=(
                    getattr(self, "_ngram_path_s", ""),
                    getattr(self, "_step4_path_s", ""),
                ),
            ) as pool:
                partials = list(pool.map(_pool_grade_folder_task, tasks))
            for p in partials:
                if p["total"] == 0 and not (base_dir / p["folder"] / f"{p['folder']}.txt").exists():
                    print(f"  {base_dir / p['folder'] / (p['folder'] + '.txt')} not found")
        else:
            grand_total = 0
            for folder in TARGET_FOLDERS:
                if sample_size is not None and grand_total >= sample_size:
                    break
                remain = None
                if sample_size is not None:
                    remain = sample_size - grand_total
                print(f"Grading {folder}...")
                part = self._collect_folder_stats(
                    base_dir,
                    folder,
                    max_passwords=remain,
                    progress_log=True,
                )
                partials.append(part)
                grand_total += part["total"]
                if sample_size is not None and grand_total >= sample_size:
                    break

        self._merge_folder_partials(partials)
        self._print_batch_results()
        return self.batch_results

    # ------------------------------------------------------------------ #
    #  Console output                                                      #
    # ------------------------------------------------------------------ #
    def _print_batch_results(self):
        r = self.batch_results
        print("\n" + "=" * 80)
        print("PASSWORD GRADING RESULTS")
        print("=" * 80 + "\n")

        total = r["total_graded"]
        print(f"Total passwords graded: {total:,}\n")

        print(" GRADE DISTRIBUTION")
        print("-" * 80)
        for _, ltr, lbl in self.GRADE_LABELS:
            cnt = r["grade_distribution"].get(ltr, 0)
            pct = cnt / total * 100 if total else 0
            bar = "\u2588" * int(pct / 2)
            print(f"  {ltr:3s} ({lbl:12s}): {cnt:10,} ({pct:6.2f}%) {bar}")
        print()

        print(" SCORE DISTRIBUTION (0-100)")
        print("-" * 80)
        for bkt, cnt in sorted(r["score_distribution"].items()):
            pct = cnt / total * 100 if total else 0
            bar = "\u2588" * int(pct / 2)
            print(f"  {bkt:3d}-{bkt + 10:3d}: {cnt:10,} ({pct:6.2f}%) {bar}")
        print()

        print(" AVERAGE SCORING COMPONENTS")
        print("-" * 80)
        for k, v in r["component_averages"].items():
            label = k.replace("_", " ").title()
            sign = "+" if "bonus" in k or "base" in k else "-"
            print(f"  {label:<35s}: {sign}{v:.4f}")
        print()

        print(" PATTERN TYPE DISTRIBUTION")
        print("-" * 80)
        for pt, cnt in sorted(r["pattern_type_distribution"].items(),
                              key=lambda x: x[1], reverse=True):
            pct = cnt / total * 100 if total else 0
            print(f"  {pt:<35s}: {cnt:10,} ({pct:6.2f}%)")
        print()

        print(" TOP SPECIFIC PENALTY REASONS")
        print("-" * 80)
        for reason, cnt in sorted(r["specific_penalty_distribution"].items(),
                                  key=lambda x: x[1], reverse=True)[:15]:
            pct = cnt / total * 100 if total else 0
            print(f"  {reason:<35s}: {cnt:10,} ({pct:6.2f}%)")
        print()

        print(" EXAMPLE PASSWORDS BY GRADE")
        print("-" * 80)
        for grade, exs in sorted(r["examples_by_grade"].items()):
            print(f"\n  Grade {grade}:")
            for ex in exs[:5]:
                print(f"    {ex['password']:<22s}  score={ex['score']:.2f}")

    @staticmethod
    def print_single_grade(result: dict):
        """Pretty-print a single password grade."""
        print("\n" + "=" * 60)
        print(f"  Password:  {result['password']}")
        print(f"  Grade:     {result['grade']} — {result['grade_label']}")
        print(f"  Score:     {result['final_score']:.2f} / 100")
        print("=" * 60)

        bd = result["breakdown"]
        print(f"\n  Base predictability:       +{bd['base_predictability']:.2f}")
        print(f"  Complexity bonus:          +{bd['complexity_bonus']:.2f}")
        print(f"  Pattern type penalty:      -{bd['pattern_type_penalty']:.2f}")
        print(f"  Specific pattern penalty:  -{bd['specific_pattern_penalty']:.2f}")
        print(f"                              {'—' * 10}")
        print(f"  Raw score (sum):           {result.get('raw_score', result['final_score']):.2f}")
        print(f"  Final score:               {result['final_score']:.2f}\n")

        det = result["details"]
        cx = det["complexity"]
        print(f"  Length bonus:        {cx['length_bonus']}")
        print(f"  Class bonus:         {cx['class_bonus']}  "
              f"(classes: {', '.join(cx['char_classes'])})")
        print(f"  Unique-ratio bonus:  {cx['unique_ratio_bonus']}  "
              f"(ratio: {cx['unique_ratio']:.3f})")

        pt = det["pattern_type"]
        print(f"\n  Pattern type: {pt['pattern_type']}")
        if pt["dict_words_found"]:
            print(f"  Dictionary words: {', '.join(pt['dict_words_found'])}")

        sp = det["specific_patterns"]
        if sp["reasons"]:
            print(f"\n  Specific penalties:")
            for r in sp["reasons"]:
                print(f"    - {r}")
        print()

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #
    def save_results(self, output_dir: str = "."):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        if hasattr(self, "batch_results"):
            res_file = out / "step6_grading_results.json"
            with open(res_file, "w") as f:
                json.dump(self.batch_results, f, indent=2, default=str)
            print(f"\n Results saved to {res_file}")
            self._save_markdown_report(out)

    def _save_markdown_report(self, output_dir: Path):
        r = self.batch_results
        total = r["total_graded"]
        report = output_dir / "STEP6_GRADING_REPORT.md"

        with open(report, "w", encoding="utf-8") as f:
            f.write("# Step 6: Password Grading Report (0\u2013D)\n\n")
            f.write(f"**Data source:** folders `{', '.join(TARGET_FOLDERS)}` "
                    f"under base archive.\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Passwords Graded**: {total:,}\n")
            for _, ltr, lbl in self.GRADE_LABELS:
                cnt = r["grade_distribution"].get(ltr, 0)
                pct = cnt / total * 100 if total else 0
                f.write(f"- **Grade {ltr} ({lbl})**: {cnt:,} ({pct:.2f}%)\n")
            f.write("\n")

            f.write("## Scoring Formula\n\n")
            f.write("```\n")
            f.write("raw = base_predictability + complexity_bonus\n")
            f.write("      - pattern_type_penalty - specific_pattern_penalty\n")
            f.write(
                f"final = clamp({self.SCORE_CALIBRATE_SLOPE} * raw + "
                f"{self.SCORE_CALIBRATE_OFFSET}, 0, 100)\n"
            )
            f.write("```\n\n")
            f.write("| Component | Range | Description |\n")
            f.write("|-----------|-------|-------------|\n")
            f.write("| Base predictability | 0\u201350 | "
                    "Inverse of n-gram predictability (less predictable = higher) |\n")
            f.write("| Complexity bonus | 0\u201350 | "
                    "Length + char-class diversity + uniqueness ratio |\n")
            f.write("| Pattern type penalty | 0\u201312 | "
                    "Scaled deduction: common types are not treated as near-max failure |\n")
            f.write("| Specific pattern penalty | 0\u201318 | "
                    "Keyboard runs, weak words, repeated chars, etc. |\n\n")

            f.write("## Grade Scale\n\n")
            f.write("| Grade | Score Range | Label |\n")
            f.write("|-------|------------|-------|\n")
            prev = 100
            for threshold, ltr, lbl in self.GRADE_LABELS:
                f.write(f"| {ltr} | {threshold}\u2013{prev} | {lbl} |\n")
                prev = threshold - 1
            f.write("\n")

            f.write("## Grade Distribution\n\n")
            f.write("| Grade | Count | % |\n")
            f.write("|-------|-------|---|\n")
            for _, ltr, lbl in self.GRADE_LABELS:
                cnt = r["grade_distribution"].get(ltr, 0)
                pct = cnt / total * 100 if total else 0
                f.write(f"| {ltr} ({lbl}) | {cnt:,} | {pct:.2f}% |\n")
            f.write("\n")

            f.write("## Score Distribution\n\n")
            f.write("| Score Range | Count | % |\n")
            f.write("|-------------|-------|---|\n")
            for bkt, cnt in sorted(r["score_distribution"].items()):
                pct = cnt / total * 100 if total else 0
                f.write(f"| {bkt}\u2013{bkt + 10} | {cnt:,} | {pct:.2f}% |\n")
            f.write("\n")

            f.write("## Average Scoring Components\n\n")
            f.write("| Component | Average |\n")
            f.write("|-----------|--------|\n")
            for k, v in r["component_averages"].items():
                label = k.replace("_", " ").title()
                sign = "+" if "bonus" in k or "base" in k else "\u2212"
                f.write(f"| {label} | {sign}{v:.4f} |\n")
            f.write("\n")

            f.write("## Pattern Type Distribution\n\n")
            f.write("| Pattern Type | Count | % |\n")
            f.write("|-------------|-------|---|\n")
            for pt, cnt in sorted(r["pattern_type_distribution"].items(),
                                  key=lambda x: x[1], reverse=True):
                pct = cnt / total * 100 if total else 0
                f.write(f"| {pt} | {cnt:,} | {pct:.2f}% |\n")
            f.write("\n")

            f.write("## Top Specific Penalty Reasons\n\n")
            f.write("| Reason | Count | % |\n")
            f.write("|--------|-------|---|\n")
            for reason, cnt in sorted(
                r["specific_penalty_distribution"].items(),
                key=lambda x: x[1], reverse=True
            )[:15]:
                pct = cnt / total * 100 if total else 0
                f.write(f"| {reason} | {cnt:,} | {pct:.2f}% |\n")
            f.write("\n")

            f.write("## Example Passwords by Grade\n\n")
            for grade, exs in sorted(r["examples_by_grade"].items()):
                f.write(f"### Grade {grade}\n\n")
                f.write("| Password | Score |\n")
                f.write("|----------|-------|\n")
                for ex in exs[:5]:
                    f.write(f"| `{ex['password']}` | {ex['score']:.2f} |\n")
                f.write("\n")

        print(f" Report saved to {report}")


# Pool workers load the grader once per process (Windows: run as script, not nested).
_worker_grader: Optional[PasswordGrader] = None


def _pool_init_grader(ngram_s: str, step4_s: str) -> None:
    global _worker_grader
    np: Optional[Path] = Path(ngram_s) if ngram_s else None
    if np is not None and not np.exists():
        np = None
    sp: Optional[Path] = Path(step4_s) if step4_s else None
    if sp is not None and not sp.exists():
        sp = None
    _worker_grader = PasswordGrader(
        ngram_model_path=np,
        step4_results_path=sp,
        quiet=True,
    )


def _pool_grade_folder_task(pair: Tuple[str, str]) -> dict:
    assert _worker_grader is not None
    folder, base_dir_s = pair
    return _worker_grader._collect_folder_stats(
        Path(base_dir_s),
        folder,
        max_passwords=None,
        progress_log=False,
    )


# ====================================================================== #
#  Interactive mode                                                        #
# ====================================================================== #
def interactive_mode(grader: PasswordGrader):
    print("\n" + "=" * 60)
    print("  PASSWORD GRADER — Interactive Mode")
    print("  Type a password to grade it, or 'quit' to exit.")
    print("=" * 60 + "\n")

    while True:
        try:
            pw = input("Enter password: ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if pw.lower() in ("quit", "exit", "q"):
            break
        result = grader.grade(pw)
        PasswordGrader.print_single_grade(result)


# ====================================================================== #
#  CLI                                                                     #
# ====================================================================== #
def parse_args():
    script_dir = Path(__file__).resolve().parent
    phase1_dir = script_dir.parent / "Phase1"

    parser = argparse.ArgumentParser(
        description="Step 6: Password Grading — Multi-factor scoring system"
    )
    parser.add_argument(
        "--base-dir",
        default=str(script_dir.parent.parent / "Data"),
        help="Base directory containing password files (default: Data/)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Limit grading to N passwords",
    )
    parser.add_argument(
        "--output-dir",
        default=str(script_dir),
        help="Output directory for results (default: 0-D/Phase2 folder)",
    )
    parser.add_argument(
        "--ngram-model",
        default=str(script_dir / "step5_ngram_model.json"),
        help="Path to Step 5 n-gram model JSON",
    )
    parser.add_argument(
        "--step4-results",
        default=str(phase1_dir / "step4_semantic_results.json"),
        help="Path to Step 4 results JSON (for pattern penalties)",
    )
    parser.add_argument(
        "--grade",
        type=str,
        default=None,
        help="Grade a single password and exit",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enter interactive grading mode",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Parallel processes for full dataset grading (ignored with --sample). Default 1.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    ngram_path = Path(args.ngram_model)
    step4_path = Path(args.step4_results)

    grader = PasswordGrader(
        ngram_model_path=ngram_path if ngram_path.exists() else None,
        step4_results_path=step4_path if step4_path.exists() else None,
    )

    if args.grade:
        result = grader.grade(args.grade)
        PasswordGrader.print_single_grade(result)
        return

    if args.interactive:
        interactive_mode(grader)
        return

    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f" Error: Base directory not found: {base_dir}")
        return

    grader.grade_dataset(
        base_dir,
        sample_size=args.sample,
        workers=max(1, args.workers),
    )
    grader.save_results(args.output_dir)


if __name__ == "__main__":
    main()
