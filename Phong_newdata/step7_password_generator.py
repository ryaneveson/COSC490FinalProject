import argparse
import secrets
import string
import re
from pathlib import Path
from step6_grading import PasswordGrader, load_step5_counts, load_step4_results, COMMON_FIRST_NAMES
import multiprocessing
from tqdm import tqdm

# Patterns and words to reject before even grading
KEYBOARD_PATTERNS = {"qwerty", "asdf", "zxcv", "1234", "qaz", "wsx", "edc"}
WEAK_PREFIXES = ("admin", "user", "pass")
WEAK_SUFFIXES = ("123", "1234", "!", "!!")

# Module-level grader for pool workers (initialized once per worker via _init_worker)
_WORKER_GRADER = None
_WORKER_COMMON_WORDS = None


def _init_worker(step5_counts, step4_results_obj, common_words_list):
    """Pool initializer: create the grader once per worker process."""
    global _WORKER_GRADER, _WORKER_COMMON_WORDS
    _WORKER_GRADER = PasswordGrader(step5_counts, step4_results_obj)
    _WORKER_COMMON_WORDS = set(common_words_list)


def _secure_choice(population):
    """Pick one element using secrets (CSPRNG)."""
    return secrets.choice(population)


def _secure_sample(population, k):
    """Pick k elements using secrets (CSPRNG), with replacement."""
    return [secrets.choice(population) for _ in range(k)]


def _harden_base(base):
    """Strip weak patterns from a user-supplied base password."""
    pwd = base
    # Remove keyboard patterns
    for pat in KEYBOARD_PATTERNS:
        while pat in pwd.lower():
            idx = pwd.lower().index(pat)
            replacement = ''.join(_secure_sample(string.ascii_letters + string.digits, len(pat)))
            pwd = pwd[:idx] + replacement + pwd[idx + len(pat):]
    # Remove weak prefixes
    low = pwd.lower()
    for pre in WEAK_PREFIXES:
        if low.startswith(pre):
            pwd = ''.join(_secure_sample(string.ascii_letters, len(pre))) + pwd[len(pre):]
            break
    # Remove weak suffixes
    low = pwd.lower()
    for suf in WEAK_SUFFIXES:
        if low.endswith(suf):
            pwd = pwd[:-len(suf)] + ''.join(_secure_sample(string.ascii_letters + "!@#$%^&*", len(suf)))
            break
    return pwd


def _build_candidate(base=None, min_length=20):
    """Build a structured candidate that guarantees all 4 char classes."""
    chars = []

    if base:
        chars.extend(_harden_base(base))

    # Guarantee at least 2 of each character class
    chars.extend(_secure_sample(string.ascii_uppercase, 2))
    chars.extend(_secure_sample(string.ascii_lowercase, 2))
    chars.extend(_secure_sample(string.digits, 2))
    chars.extend(_secure_sample("!@#$%^&*()-_=+[]{}|;:,.<>?", 2))

    # Fill remaining length with mixed characters
    fill_pool = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    while len(chars) < min_length:
        chars.append(_secure_choice(fill_pool))

    # Trim to min_length if base made it too long
    if len(chars) > min_length:
        chars = chars[:min_length]

    # Secure shuffle (Fisher-Yates with secrets)
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]

    return "".join(chars)


def _contains_name(pwd):
    """Check if the alphabetic content of the password is a common first name."""
    alpha_only = re.sub(r'[^a-zA-Z]', '', pwd).lower()
    return alpha_only in COMMON_FIRST_NAMES


def _contains_keyboard_pattern(pwd):
    """Check for common keyboard patterns."""
    low = pwd.lower()
    return any(pat in low for pat in KEYBOARD_PATTERNS)


def _contains_weak_affix(pwd):
    """Check for weak prefixes/suffixes."""
    low = pwd.lower()
    return any(low.startswith(p) for p in WEAK_PREFIXES) or any(low.endswith(s) for s in WEAK_SUFFIXES)


def _contains_dictionary_word(pwd, common_words):
    """Check if password contains common dictionary words from step4 (4+ chars to avoid false positives)."""
    tokens = set(re.findall(r'[a-zA-Z]{4,}', pwd.lower()))
    return bool(tokens.intersection(common_words))


def _has_repeated_chars(pwd, run_length=3):
    """Check for 3+ identical consecutive characters (e.g. 'aaa', '!!!', '111')."""
    for i in range(len(pwd) - run_length + 1):
        if len(set(pwd[i:i + run_length])) == 1:
            return True
    return False


def _pre_screen(pwd, common_words):
    """Reject obviously weak candidates before grading (cheap checks)."""
    if len(pwd) < 8:
        return False
    if _contains_name(pwd):
        return False
    if _contains_keyboard_pattern(pwd):
        return False
    if _contains_weak_affix(pwd):
        return False
    if _contains_dictionary_word(pwd, common_words):
        return False
    if _has_repeated_chars(pwd):
        return False
    return True


def single_attempt(args):
    """Worker function: build a candidate, pre-screen it, grade if it passes."""
    base, min_length = args
    candidate = _build_candidate(base=base, min_length=min_length)

    # Pre-screen: skip grading if candidate has obvious weaknesses
    if not _pre_screen(candidate, _WORKER_COMMON_WORDS):
        return candidate, {"final_score": 0, "rejected": "pre-screen"}

    grade = _WORKER_GRADER.grade_password(candidate)

    # Feedback-guided retry: if short_password_penalty or name_penalty triggered,
    # mark as rejected so we don't count it as a real attempt
    if grade.get("short_password_penalty", 0) > 0 or grade.get("name_penalty", 0) > 0:
        return candidate, {"final_score": 0, "rejected": "penalty-triggered"}

    return candidate, grade


def generate_password(base=None, elements=None, grader=None, step4_results=None, min_score=100, max_attempts=10000):
    # Determine the seed for structured generation
    seed_base = None
    if base:
        seed_base = base
    elif elements:
        seed_base = ''.join(elements)

    # Extract common dictionary words for pre-screening
    common_words = set(step4_results.get("matched_words", {}).keys()) if step4_results else set()
    common_words_list = list(common_words)  # for pickling to subprocesses

    step5_counts = grader.step5_counts if hasattr(grader, 'step5_counts') else None
    step4_results_obj = grader.step4_results if hasattr(grader, 'step4_results') else None

    print("[INFO] Starting parallel password generation process...")
    cpu_count = max(2, multiprocessing.cpu_count() - 1)
    batch_size = cpu_count * 4
    graded_attempts = 0  # Only count non-rejected attempts
    total_candidates = 0
    best = (None, {'final_score': 0})

    with multiprocessing.Pool(cpu_count, initializer=_init_worker,
                              initargs=(step5_counts, step4_results_obj, common_words_list)) as pool, \
         tqdm(desc="Graded Attempts", unit="attempt", dynamic_ncols=True, total=max_attempts) as pbar:
        while graded_attempts < max_attempts:
            # Build batch: first candidate uses user base (if any), rest are purely random
            batch_args = []
            for i in range(batch_size):
                b = seed_base if (i == 0 and seed_base) else None
                batch_args.append((b, 20))

            results = pool.map(single_attempt, batch_args)
            found = False
            for pwd2, grade in results:
                total_candidates += 1
                if grade.get("rejected"):
                    continue
                graded_attempts += 1
                pbar.update(1)
                if grade['final_score'] > best[1].get('final_score', 0):
                    best = (pwd2, grade)
                    tqdm.write(f"[BEST SO FAR] Attempt {graded_attempts}: Password='{pwd2}' | Score={grade['final_score']}")
                if grade['final_score'] >= min_score:
                    tqdm.write(f"[SUCCESS] Password meets minimum score ({min_score}) after {graded_attempts} graded attempts ({total_candidates} total candidates).")
                    found = True
                    break
            if found:
                return best[0], best[1]
            # After first batch, stop injecting the base so we explore freely
            seed_base = None

    # Max attempts reached — return best candidate found
    tqdm.write(f"[WARN] Max attempts ({max_attempts}) reached. Returning best password (score={best[1].get('final_score', 0)}).")
    return best[0], best[1]

def generate_step7_report(pwd, grade, args):
        report_md = "# Step 7: Password Generation Report\n\n"
        if args.base:
            report_md += f"**Input base:** `{args.base}`\n\n"
        if args.elements:
            report_md += f"**Input elements:** `{args.elements}`\n\n"
        report_md += f"**Minimum score required:** {args.min_score}\n\n"
        report_md += f"## Generated Password\n\n`{pwd}`\n\n"
        report_md += "## Grading Breakdown\n\n"
        report_md += "| Metric | Value |\n|--------|-------|\n"
        for k, v in grade.items():
            report_md += f"| {k} | {v} |\n"
        report_path = Path(__file__).parent / "STEP7_GENERATION_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"\nSaved generation report to {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Password Generator using Step 6 Grader")
    parser.add_argument('--base', type=str, help='Base password to harden')
    parser.add_argument('--elements', nargs='*', help='Elements to include in password')
    parser.add_argument('--min_score', type=int, default=100, help='Minimum grading score')
    parser.add_argument('--step5_json', default=str(Path(__file__).parent / "step5_probabilistic_summary.json"))
    parser.add_argument('--step4_json', default=str(Path(__file__).parent / "step4_semantic_results.json"))
    parser.add_argument('--data_file', default=str(Path(__file__).parent.parent / 'data' / 'archive' / '100k-most-used-passwords-NCSC.txt'), help='Path to the password dataset file')
    args = parser.parse_args()

    # The data_file argument is now available for future use if needed
    step5_counts = load_step5_counts(Path(args.step5_json))
    step4_results = load_step4_results(Path(args.step4_json))
    grader = PasswordGrader(step5_counts, step4_results)

    pwd, grade = generate_password(base=args.base, elements=args.elements, grader=grader, step4_results=step4_results, min_score=args.min_score)
    print("Generated password:", pwd)
    print("Grading breakdown:", grade)
    generate_step7_report(pwd, grade, args)

    # Write only the generated password to a text file
    pwd_file = Path(__file__).parent / "step7_generated_passwords.txt"
    with open(pwd_file, "w", encoding="utf-8") as f:
        f.write(pwd + "\n")
    print(f"Generated password saved to {pwd_file}")


if __name__ == "__main__":
    main()
