"""
Step 8: Dictionary + keyboard-pattern attack on the NCSC password list

1. Common keyboard walks (QWERTY rows, qazwsx-style columns, 1qaz2wsx, etc.), numeric runs
   (12345, …), symbol-only strings (!, !@#, …), and optional symbol *prefixes* (!foo, @foo, …)
   on each candidate, × the same tail list as the dictionary stream (runs first).
2. `english-words` (web2 + gcide) × rule/capped leet × tails.

Usage:

  cd 0-D/Phase3
  python Step8.py
  python Step8.py --no-keyboard-patterns
  python Step8.py --no-keyboard-headers   # drop ! / @ prefixes on keyboard guesses only
  python Step8.py --max-attempts 1000000

Requires: pip install english-words
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

try:
    from english_words import get_english_words_set

    ENGLISH_WORDS_AVAILABLE = True
except ImportError:
    get_english_words_set = None  # type: ignore
    ENGLISH_WORDS_AVAILABLE = False

_DEFAULT_TARGETS = Path(__file__).resolve().parent.parent.parent / "100k-most-used-passwords-NCSC.txt"
_OUTPUT_DIR = Path(__file__).resolve().parent

YEARS = [str(y) for y in range(1980, 2031)]
SHORT_YEARS = [str(y)[-2:] for y in range(1990, 2031)]

_NUM_SEEN: Set[str] = set()
COMMON_NUM_SUFFIXES: List[str] = []
for x in [str(i) for i in range(100)] + [f"{i:02d}" for i in range(100)]:
    if x not in _NUM_SEEN:
        _NUM_SEEN.add(x)
        COMMON_NUM_SUFFIXES.append(x)
for x in [
    "123", "1234", "12345", "321", "007", "69", "88", "99", "111", "000",
    "4321", "024", "420", "8000", "1111", "0000", "1212",
]:
    if x not in _NUM_SEEN:
        _NUM_SEEN.add(x)
        COMMON_NUM_SUFFIXES.append(x)

SPECIAL_TAILS = [
    "!", "!!", "!@", "!@#", "@", "#", "$", "*", ".", "?", "!!1", "123!", "!123",
    "@123", "#1", "$1", "##", "%", "&",
]

_DICT_TAIL_PRIORITY = [
    "", "1234", "12345", "123", "123456", "1", "2", "12", "21", "3", "11", "22",
    "!", "!!", "@", "#", "$", "!!1", "!123", "123!",
    "2024", "2023", "2022", "2021", "2020", "2019", "2000", "99", "00", "01",
    "69", "88", "007", "420", "1337", "24", "23",
]

LEET_LIGHT = str.maketrans("aeio", "4310")
LEET_HEAVY = str.maketrans("aeioustl", "43105711")

LEET_CHAR_ALTS: Dict[str, Tuple[str, ...]] = {
    "a": ("a", "@", "4", "&"),
    "e": ("e", "3"),
    "i": ("i", "1", "!"),
    "o": ("o", "0"),
    "s": ("s", "$", "5"),
    "l": ("l", "1", "|"),
    "t": ("t", "7", "+"),
    "b": ("b", "8"),
    "g": ("g", "9"),
}

DEFAULT_ENGLISH_DICT_SOURCES: Tuple[str, ...] = ("web2", "gcide")

# US QWERTY layout — top rows (digits + letter rows)
KEYBOARD_ROWS: Tuple[str, ...] = (
    "1234567890",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
)

# Prefixes prepended to each keyboard base+tail when headers are enabled (common “starts with !” habits)
KEYBOARD_HEADER_PREFIXES: Tuple[str, ...] = (
    "!",
    "!!",
    "!!!",
    "@",
    "#",
    "$",
    "%",
    "^",
    "&",
    "*",
    "(",
    ")",
    "!@",
    "!@#",
    "!@#$",
    "@#",
    "#!",
    "$!",
    "~",
    ".",
    "?",
    "+",
    "=",
    "|",
    "/",
    "`",
)

# Hand-picked spatial / weak keyboard-style bases (overlaps with slides below are deduped)
KEYBOARD_EXPLICIT: Tuple[str, ...] = (
    # Symbol-only / shift-row runs (standalone passwords)
    "!",
    "!!",
    "!!!",
    "!!!!",
    "!!!!!",
    "!@",
    "!@#",
    "!@#$",
    "!@#$%",
    "!@#$%^",
    "!@#$%^&",
    "!@#$%^&*",
    "!@#$%^&*(",
    "!@#$%^&*()",
    "@",
    "#",
    "$",
    "%",
    "&",
    "*",
    ".",
    "..",
    "...",
    "....",
    "?",
    "??",
    "@@",
    "##",
    "qwerty",
    "qwertyuiop",
    "qwert",
    "asdf",
    "asdfg",
    "asdfgh",
    "asdfghjkl",
    "zxcv",
    "zxcvb",
    "zxcvbn",
    "zxcvbnm",
    "qaz",
    "qazw",
    "qazws",
    "qazwsx",
    "qazwsxe",
    "qazwsxedc",
    "wsx",
    "edc",
    "rfv",
    "tgb",
    "yhn",
    "ujm",
    "ikm",
    "poiuy",
    "lkjhg",
    "fdsa",
    "1qaz",
    "2wsx",
    "3edc",
    "1qaz2wsx",
    "1qaz2wsx3edc",
    "1q2w3e4r",
    "1q2w3e4r5t",
    "zaq1",
    "xsw2",
    "cde3",
    "!qaz2wsx",
    "wasd",
    "awds",
    "wdsa",
    "1234",
    "12345",
    "123456",
    "1234567",
    "12345678",
    "123456789",
    "1234567890",
    "0987654321",
    "9876543210",
    "87654321",
    "7654321",
    "654321",
    "54321",
    "4321",
    "321",
    "12341",
    "121212",
    "112233",
    "789456123",
    "7894561230",
    "147258369",
    "741852963",
    "159753",
    "951753",
    "000000",
    "111111",
    "0123456789",
    "abcdef",
    "abcde",
    "abcd",
    "abc",
    "qwe",
    "asd",
    "zxc",
    "letmein",
    "trustno1",
    "qazwsx",
    "plmokn"
)


def _sliding_row_fragments(row: str, min_len: int = 3, max_len: int = 10) -> List[str]:
    """Forward and reverse substrings along one keyboard row."""
    out: List[str] = []
    n = len(row)
    if n < min_len:
        return out
    hi = min(max_len, n)
    for size in range(min_len, hi + 1):
        for i in range(n - size + 1):
            frag = row[i : i + size]
            out.append(frag)
            rev = frag[::-1]
            if rev != frag:
                out.append(rev)
    return out


def _collect_keyboard_seeds() -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []

    def add(s: str) -> None:
        t = s.strip()
        if not t or len(t) > 48 or t in seen:
            return
        seen.add(t)
        ordered.append(t)

    for p in KEYBOARD_EXPLICIT:
        add(p)
    for row in KEYBOARD_ROWS:
        for frag in _sliding_row_fragments(row, 3, 10):
            add(frag)
    # Numpad-style line on many phones: 1-2-3 row, etc.
    for row in ("147258369", "369258147", "7894561230"):
        for frag in _sliding_row_fragments(row, 3, min(10, len(row))):
            add(frag)
    return ordered


def _keyboard_seed_variants(seed: str) -> List[str]:
    """Case / reverse variants; punctuation-heavy seeds kept mostly as-is."""
    s = seed.strip()
    if not s or len(s) > 64:
        return []
    has_letter = any(c.isalpha() for c in s)
    seen: Set[str] = set()
    out: List[str] = []

    def push(x: str) -> None:
        if x and x not in seen:
            seen.add(x)
            out.append(x)

    push(s)
    if has_letter:
        low = "".join(c.lower() if c.isalpha() else c for c in s)
        push(low)
        push(low.upper())
        # Title-case letters only version
        push(low.capitalize())
        rev = low[::-1]
        push(rev)
        if rev != low:
            push(rev.capitalize())
    else:
        rev = s[::-1]
        if rev != s:
            push(rev)
    return out


def keyboard_pattern_attack(english_dict: Dict[str, Any]) -> Iterator[str]:
    """
    Yield keyboard / numeric-walk bases × same tail ordering as dictionary_attack.
    Optionally prepend common symbol headers (!, !@#, …) to each candidate.
    """
    tails = prioritized_dictionary_tails(
        full_password_tail_list(
            int(english_dict["numeric_tail_count"]),
            bool(english_dict["tails_include_years"]),
        ),
        int(english_dict["max_tails"]),
    )
    headers_on = bool(english_dict.get("keyboard_headers_enabled", True))
    raw_prefixes = english_dict.get("keyboard_header_prefixes")
    if isinstance(raw_prefixes, (list, tuple)) and raw_prefixes:
        header_prefixes = tuple(str(p) for p in raw_prefixes if str(p).strip())
    else:
        header_prefixes = KEYBOARD_HEADER_PREFIXES

    for seed in _collect_keyboard_seeds():
        for base in _keyboard_seed_variants(seed):
            for t in tails:
                full = base + t
                yield full
                if not headers_on:
                    continue
                for h in header_prefixes:
                    if not h:
                        continue
                    yield h + full


def _ordered_numeric_suffixes(max_count: int = 220) -> List[str]:
    priority = [
        "1234", "12345", "123", "123456", "4321", "321", "1111", "0000",
        "1212", "6969", "1337",
    ]
    seen: Set[str] = set()
    out: List[str] = []
    for x in priority + COMMON_NUM_SUFFIXES:
        if x not in seen:
            seen.add(x)
            out.append(x)
        if len(out) >= max_count:
            break
    return out


def full_password_tail_list(
    numeric_count: int = 400,
    include_years: bool = True,
) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = [""]
    seen.add("")
    for t in _ordered_numeric_suffixes(numeric_count):
        if t not in seen:
            seen.add(t)
            out.append(t)
    for t in SPECIAL_TAILS:
        if t not in seen:
            seen.add(t)
            out.append(t)
    if include_years:
        for y in YEARS:
            if y not in seen:
                seen.add(y)
                out.append(y)
        for y in SHORT_YEARS:
            if y not in seen:
                seen.add(y)
                out.append(y)
    return out


def prioritized_dictionary_tails(full: List[str], max_tails: int) -> List[str]:
    if max_tails <= 0:
        return full
    pos = {t: i for i, t in enumerate(_DICT_TAIL_PRIORITY) if t in full}
    rest = [t for t in full if t not in pos]
    preferred = sorted(pos.keys(), key=lambda t: pos[t])
    merged = preferred + rest
    if len(merged) <= max_tails:
        return merged
    return merged[:max_tails]


def _iter_rule_substitution_bases(w: str) -> Iterator[str]:
    low = w.lower()
    if not low.isalpha():
        return
    seen: Set[str] = set()

    def push(s: str) -> None:
        if s not in seen:
            seen.add(s)

    for b in (low, low.capitalize(), low.upper()):
        push(b)

    for tr in (LEET_LIGHT, LEET_HEAVY):
        push(low.translate(tr))
        push(low.capitalize().translate(tr))

    push(low.replace("a", "@"))
    push(low.replace("a", "4"))
    push(low.replace("a", "&"))
    push(low.replace("e", "3"))
    push(low.replace("i", "1"))
    push(low.replace("o", "0"))
    push(low.replace("s", "$"))
    push(low.replace("l", "1"))

    stacked = low
    repl = [("e", "3"), ("a", "@"), ("o", "0"), ("i", "1"), ("s", "$")]
    for old, new in repl:
        stacked = stacked.replace(old, new)
    push(stacked)
    push(stacked.capitalize())

    stacked2 = low.replace("a", "4").replace("e", "3").replace("i", "1").replace("o", "0")
    push(stacked2)
    push(stacked2.capitalize())

    yield from seen


def _iter_exhaustive_leet_product(
    w: str,
    max_word_len: int,
    max_total_strings: int,
) -> Iterator[str]:
    low = w.lower()
    if not low.isalpha() or len(low) > max_word_len:
        return
    options: List[Tuple[str, ...]] = []
    for c in low:
        options.append(LEET_CHAR_ALTS.get(c, (c,)))
    est = 1
    for opt in options:
        est *= len(opt)
        if est > max_total_strings * 4:
            est = max_total_strings * 4
            break
    n = 0
    for combo in itertools.product(*options):
        yield "".join(combo)
        n += 1
        if n >= max_total_strings:
            break


def load_dictionary_word_list(
    min_len: int,
    max_len: int,
    max_words: int,
    sources: Tuple[str, ...] = DEFAULT_ENGLISH_DICT_SOURCES,
) -> List[str]:
    if not ENGLISH_WORDS_AVAILABLE:
        raise RuntimeError("english-words is required")
    src = tuple(s.strip().lower() for s in sources if (s or "").strip())
    if not src:
        src = DEFAULT_ENGLISH_DICT_SOURCES
    try:
        words = get_english_words_set(list(src), lower=True, alpha=True)
    except ValueError:
        words = get_english_words_set(["web2"], lower=True, alpha=True)
    filt = [w for w in words if w.isalpha() and min_len <= len(w) <= max_len]
    out = sorted(set(filt), key=lambda x: (len(x), x))
    if max_words > 0:
        out = out[:max_words]
    return out


def dictionary_attack(
    min_len: int,
    max_len: int,
    max_words: int,
    exhaust_product_max_word_len: int,
    exhaust_max_combos_per_word: int,
    numeric_tail_count: int,
    tails_include_years: bool,
    max_bases_per_word: int,
    max_tails: int,
    rule_only_leet: bool,
    sources: Tuple[str, ...],
) -> Iterator[str]:
    words = load_dictionary_word_list(min_len, max_len, max_words, sources)
    tails = prioritized_dictionary_tails(
        full_password_tail_list(numeric_tail_count, tails_include_years),
        max_tails,
    )
    for w in words:
        bases: Set[str] = set()
        for b in _iter_rule_substitution_bases(w):
            bases.add(b)
        if (
            not rule_only_leet
            and len(w) <= exhaust_product_max_word_len
            and len(bases) < max_bases_per_word
        ):
            for b in _iter_exhaustive_leet_product(
                w,
                exhaust_product_max_word_len,
                exhaust_max_combos_per_word,
            ):
                if len(bases) >= max_bases_per_word:
                    break
                bases.add(b)
                if b.capitalize() != b:
                    bases.add(b.capitalize())

        for b in bases:
            if not b:
                continue
            for t in tails:
                yield b + t


def _targets_casefold_maps(target_set: Set[str]) -> Tuple[Set[str], Dict[str, str]]:
    pending_cf: Set[str] = set()
    canon_by_cf: Dict[str, str] = {}
    for t in target_set:
        cf = t.casefold()
        pending_cf.add(cf)
        canon_by_cf.setdefault(cf, t)
    return pending_cf, canon_by_cf


def simulate_attack(
    targets: List[str],
    english_dict: Dict[str, Any],
    *,
    max_attempts: Optional[int],
    progress_every: int,
    dedup_guesses: bool,
) -> dict:
    target_set = {t.strip() for t in targets if t.strip()}
    found: Dict[str, Optional[int]] = {t: None for t in target_set}
    pending_cf, canon_by_cf = _targets_casefold_maps(target_set)
    attempt = 0

    dict_stream = dictionary_attack(
        int(english_dict["min_len"]),
        int(english_dict["max_len"]),
        int(english_dict["max_words"]),
        int(english_dict["exhaust_max_word_len"]),
        int(english_dict["exhaust_max_combos_per_word"]),
        int(english_dict["numeric_tail_count"]),
        bool(english_dict["tails_include_years"]),
        int(english_dict["max_bases_per_word"]),
        int(english_dict["max_tails"]),
        bool(english_dict["rule_only_leet"]),
        tuple(english_dict["sources"]),
    )
    if english_dict.get("keyboard_patterns_enabled", True):
        stream = itertools.chain(keyboard_pattern_attack(english_dict), dict_stream)
    else:
        stream = dict_stream

    src = tuple(english_dict.get("sources") or ())
    src_s = ",".join(src) if src else "web2,gcide"
    dedup_note = (
        " Guess deduplication is off (same candidate may be tried twice) to limit RAM; "
        "use --dedup-guesses to track uniques."
        if not dedup_guesses
        else ""
    )
    kb = english_dict.get("keyboard_patterns_enabled", True)
    hdr = kb and english_dict.get("keyboard_headers_enabled", True)
    if kb and hdr:
        kb_note = (
            "Keyboard / numeric / symbol patterns (with optional ! @ !@# … prefixes on each) × same tails, then "
        )
    elif kb:
        kb_note = "Keyboard / numeric / symbol patterns (no extra symbol prefixes), then "
    else:
        kb_note = ""
    note = (
        f"{kb_note}`english_words` [{src_s}] × rule/capped leet × password tails. "
        f"No Step 4, spear, or n-gram streams.{dedup_note}"
    )

    t0 = time.monotonic()
    for guess in stream:
        attempt += 1
        cf = guess.casefold()
        if cf in pending_cf:
            hit = canon_by_cf[cf]
            pending_cf.remove(cf)
            found[hit] = attempt
            if not pending_cf:
                break
        if max_attempts is not None and attempt >= max_attempts:
            break
        if progress_every > 0 and attempt % progress_every == 0:
            elapsed = time.monotonic() - t0
            print(
                f"[progress] {attempt:,} guesses  {elapsed:,.1f}s  "
                f"{len(pending_cf)} target(s) left (casefold slots)",
                flush=True,
            )

    return {
        "attempts_made": attempt,
        "max_attempts": max_attempts,
        "targets": list(target_set),
        "cracked_at_attempt": {k: v for k, v in found.items() if v is not None},
        "not_cracked": sorted([k for k, v in found.items() if v is None]),
        "pattern_priority_note": note,
        "ngram_enabled": False,
        "english_dictionary_enabled": True,
        "names_dataset_enabled": False,
        "keyboard_patterns_enabled": bool(english_dict.get("keyboard_patterns_enabled", True)),
        "keyboard_headers_enabled": (
            bool(english_dict.get("keyboard_patterns_enabled", True))
            and bool(english_dict.get("keyboard_headers_enabled", True))
        ),
        "case_insensitive_target_match": True,
        "dictionary_only": True,
        "guess_deduplication": dedup_guesses,
    }


def _attempts_summary_line(res: dict) -> str:
    cap = res.get("max_attempts")
    n = int(res["attempts_made"])
    if cap is None:
        return f"**Attempts executed:** {n:,} (no cap; ran until stream ended)"
    return f"**Attempts executed:** {n:,} (stopped at cap {int(cap):,})"


def write_markdown_report(out: Path, res: dict, config_summary: dict) -> None:
    out_dir = out.parent
    cracked = res["cracked_at_attempt"]
    not_ok = res["not_cracked"]
    n_targets = len(res["targets"])
    use_sidecars = n_targets > 400
    cracked_csv = out_dir / "step8_cracked_at_attempt.csv"
    not_txt = out_dir / "step8_not_cracked.txt"

    lines = [
        "# Step 8: Attack simulation report\n",
        "\n",
        "## Configuration\n\n",
        f"```json\n{json.dumps(config_summary, indent=2)}\n```\n\n",
        "## Results\n\n",
        f"- **N-gram model used:** False\n",
        f"- **Keyboard / numeric patterns:** {res.get('keyboard_patterns_enabled', False)}\n",
        f"- **Keyboard symbol headers (!, @, …):** {res.get('keyboard_headers_enabled', False)}\n",
        f"- **English dictionary (`english-words`):** True\n",
        f"- {_attempts_summary_line(res)}\n",
        f"- **Targets:** {n_targets} (NCSC list)\n",
        f"- **Cracked:** {len(cracked):,}\n",
        f"- **Not cracked:** {len(not_ok):,}\n\n",
        "### Cracked (password → attempt index)\n\n",
    ]
    if cracked:
        rows = sorted(cracked.items(), key=lambda x: x[1])
        if use_sidecars:
            with open(cracked_csv, "w", encoding="utf-8", newline="") as cf:
                cf.write("password,attempt_index\n")
                for pw, att in rows:
                    pesc = '"' + pw.replace('"', '""') + '"' if "," in pw or '"' in pw or "\n" in pw else pw
                    cf.write(f"{pesc},{att}\n")
            preview_n = 25
            lines.append(
                f"_Full table: `{cracked_csv.name}` ({len(rows):,} rows). "
                f"First {preview_n} by attempt:_\n\n"
            )
            lines.append("| Password | Attempt |\n|---|---|\n")
            for pw, att in rows[:preview_n]:
                safe = pw.replace("|", "\\|")
                lines.append(f"| `{safe}` | {att:,} |\n")
        else:
            lines.append("| Password | Attempt |\n|---|---|\n")
            for pw, att in rows:
                safe = pw.replace("|", "\\|")
                lines.append(f"| `{safe}` | {att:,} |\n")
    else:
        lines.append("_None._\n")

    lines.append("\n### Not cracked (stream exhausted or cap reached)\n\n")
    if not_ok:
        if use_sidecars:
            with open(not_txt, "w", encoding="utf-8") as nf:
                for pw in not_ok:
                    nf.write(pw + "\n")
            prev = not_ok[:15]
            lines.append(
                f"_Full list: `{not_txt.name}` ({len(not_ok):,} lines). Sample:_\n\n"
            )
            for pw in prev:
                lines.append(f"- `{pw}`\n")
            if len(not_ok) > len(prev):
                lines.append(f"- _… and {len(not_ok) - len(prev):,} more in file_\n")
        else:
            for pw in not_ok:
                lines.append(f"- `{pw}`\n")
    else:
        lines.append("_All targeted passwords were cracked._\n")

    lines.append(f"\n---\n\n{res.get('pattern_priority_note', '')}\n")
    with open(out, "w", encoding="utf-8") as f:
        f.writelines(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Step 8: keyboard patterns + english-words dictionary attack on NCSC passwords."
    )
    p.add_argument(
        "--target-file",
        type=str,
        default=str(_DEFAULT_TARGETS),
        help="Password list (default: repo 100k-most-used-passwords-NCSC.txt)",
    )
    p.add_argument(
        "--output-dir",
        type=str,
        default=str(_OUTPUT_DIR),
        help="Directory for JSON, markdown, and CSV outputs",
    )
    p.add_argument(
        "--no-keyboard-patterns",
        action="store_true",
        help="Skip keyboard and numeric-walk guesses (english_words only)",
    )
    p.add_argument(
        "--no-keyboard-headers",
        action="store_true",
        help="Do not prepend symbol headers (!, @, !@#, …) to keyboard-pattern guesses",
    )
    p.add_argument(
        "--max-attempts",
        type=int,
        default=None,
        help="Stop after N guesses (default: run until full keyspace ends)",
    )
    p.add_argument(
        "--progress-every",
        type=int,
        default=500_000,
        help="Print progress every N guesses (0 disables)",
    )
    p.add_argument("--dict-min-len", type=int, default=3)
    p.add_argument("--dict-max-len", type=int, default=10)
    p.add_argument(
        "--dict-max-words",
        type=int,
        default=0,
        help="Cap merged bases after sort (0 = no cap)",
    )
    p.add_argument("--exhaust-leet-max-len", type=int, default=6)
    p.add_argument("--exhaust-max-combos-per-word", type=int, default=4000)
    p.add_argument("--dict-max-bases", type=int, default=72)
    p.add_argument("--dict-max-tails", type=int, default=96)
    p.add_argument("--dict-numeric-tails", type=int, default=400)
    p.add_argument("--dict-rule-only", action="store_true")
    p.add_argument("--dict-no-years", action="store_true")
    p.add_argument(
        "--dict-sources",
        type=str,
        default="web2,gcide",
        help="Comma-separated english_words list ids",
    )
    p.add_argument("--no-dedup", action="store_true")
    p.add_argument("--dedup-guesses", action="store_true")
    p.add_argument(
        "--print-json",
        action="store_true",
        help="Echo full result JSON to stdout (large for 100k targets)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if not ENGLISH_WORDS_AVAILABLE:
        print("Install english-words: pip install english-words", file=sys.stderr)
        sys.exit(1)

    target_path = Path(args.target_file).expanduser().resolve()
    if not target_path.is_file():
        print(f"Target file not found: {target_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    dict_src_tuple = tuple(
        x.strip().lower() for x in str(args.dict_sources or "").split(",") if x.strip()
    )
    if not dict_src_tuple:
        dict_src_tuple = DEFAULT_ENGLISH_DICT_SOURCES

    if args.dedup_guesses and args.no_dedup:
        print("Use only one of --dedup-guesses or --no-dedup.", file=sys.stderr)
        sys.exit(1)
    dedup_opt = True if args.dedup_guesses else (False if args.no_dedup else False)

    min_len = max(1, args.dict_min_len)
    max_len = max(min_len, args.dict_max_len)

    english_dict: Dict[str, Any] = {
        "enabled": True,
        "min_len": min_len,
        "max_len": max_len,
        "max_words": max(0, args.dict_max_words),
        "exhaust_max_word_len": max(0, args.exhaust_leet_max_len),
        "exhaust_max_combos_per_word": max(1, args.exhaust_max_combos_per_word),
        "numeric_tail_count": max(1, args.dict_numeric_tails),
        "tails_include_years": not args.dict_no_years,
        "max_bases_per_word": max(8, args.dict_max_bases),
        "max_tails": max(0, args.dict_max_tails),
        "rule_only_leet": bool(args.dict_rule_only),
        "sources": dict_src_tuple,
        "keyboard_patterns_enabled": not args.no_keyboard_patterns,
        "keyboard_headers_enabled": not args.no_keyboard_headers,
    }

    preview = load_dictionary_word_list(
        min_len,
        max_len,
        english_dict["max_words"],
        dict_src_tuple,
    )
    print(
        f"Dictionary bases: {len(preview):,} (len {min_len}-{max_len}; "
        f"sources {','.join(dict_src_tuple)}).\n",
        flush=True,
    )

    targets: List[str] = []
    with open(target_path, "r", encoding="utf-8", errors="replace") as f:
        targets.extend(
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        )

    if not targets:
        print("No targets in file.", file=sys.stderr)
        sys.exit(1)

    attempt_cap: Optional[int] = args.max_attempts
    if attempt_cap is not None and attempt_cap <= 0:
        attempt_cap = None

    res = simulate_attack(
        targets,
        english_dict,
        max_attempts=attempt_cap,
        progress_every=max(0, args.progress_every),
        dedup_guesses=dedup_opt,
    )

    if args.print_json:
        print(json.dumps(res, indent=2))
    else:
        print(
            json.dumps(
                {
                    "attempts_made": res["attempts_made"],
                    "cracked": len(res["cracked_at_attempt"]),
                    "not_cracked": len(res["not_cracked"]),
                    "targets": len(res["targets"]),
                },
                indent=2,
            ),
            flush=True,
        )

    config_summary = {
        "target_file": str(target_path),
        "english_words_sources": list(dict_src_tuple),
        "base_word_count": len(preview),
        "keyboard_patterns_enabled": not args.no_keyboard_patterns,
        "keyboard_headers_enabled": (not args.no_keyboard_patterns) and (not args.no_keyboard_headers),
        "dict_min_len": min_len,
        "dict_max_len": max_len,
        "guess_deduplication": dedup_opt,
    }

    out_payload: Dict[str, Any] = {
        "config": config_summary,
        **res,
    }
    out_payload["dictionary_config"] = dict(english_dict)

    js = out_dir / "step8_attack_results.json"
    with open(js, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2, default=str)
    print(f"\nWrote {js}")

    md = out_dir / "STEP8_ATTACK_REPORT.md"
    write_markdown_report(md, res, config_summary)
    print(f"Wrote {md}")


if __name__ == "__main__":
    main()
