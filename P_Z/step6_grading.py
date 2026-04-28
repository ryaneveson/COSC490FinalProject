try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
# Top-level function for multiprocessing compatibility
def _defaultdict_counter():
    return defaultdict(Counter)
"""
Step 6: Password Grading System
Combines probabilistic prediction with pattern analysis to grade password strength.
"""

# Multiprocessing for speed
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Any, Tuple
import multiprocessing
# Utility to load step4 results if missing
def load_step4_results(json_path: Path) -> Dict:
    if not json_path.exists():
        raise FileNotFoundError(f"Step 4 results not found: {json_path}")
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)
import re

# Import from step5
from step5_probabilistic_model import password_score, build_ngram_counts

# Pattern type penalties (higher = more deduction)
# Based on Step 4 rankings - more common patterns get higher penalties
PATTERN_TYPE_PENALTIES = {
    "word_special_digit_mixed": 25,  # Most common, highest penalty
    "word_special_digit_upper": 20,
    "word_special_digit_lower": 18,
    "word_digit": 15,
    "word_special": 12,
    "word_only": 10,
    "leet_speak": 8,
    "keyboard_pattern": 6,
    "special_digit": 4,
    "digit_only": 2,
    "other": 0,  # Least penalty
}

# Specific pattern penalties
SPECIFIC_PATTERN_PENALTIES = {
    # Common keyboard patterns
    "asdf": 10,
    "qwerty": 10,
    "123456": 10,
    "password": 15,
    "admin": 12,
    "login": 8,
    "user": 6,
    # Adding ! at end
    r"!$": 5,  # Ends with !
    r"!!$": 8,  # Ends with !!
    # Common suffixes
    r"123$": 7,
    r"1234$": 9,
    # Common prefixes
    r"^admin": 8,
    r"^user": 6,
    r"^pass": 10,
}

# Complexity bonuses
COMPLEXITY_BONUSES = {
    "length": {
        8: 5,
        10: 10,
        12: 15,
        14: 20,
        16: 25,
    },
    "charsets": {
        1: 0,   # Only one type
        2: 5,   # Two types
        3: 15,  # Three types
        4: 25,  # All four types (upper, lower, digit, special)
    }
}

class PasswordGrader:
    def __init__(self, step5_counts: Dict, step4_results: Dict):
        self.step5_counts = step5_counts
        self.step4_results = step4_results

        # Compile regex patterns for specific penalties
        self.specific_patterns = {}
        for pattern, penalty in SPECIFIC_PATTERN_PENALTIES.items():
            try:
                self.specific_patterns[re.compile(pattern, re.IGNORECASE)] = penalty
            except:
                # If regex fails, treat as literal string
                self.specific_patterns[pattern.lower()] = penalty

    def get_pattern_type_penalty(self, password: str) -> int:
        """Calculate pattern type penalty based on Step 4 classification"""
        # Simplified pattern classification (similar to Step 4)
        has_dict_word = self._has_dictionary_word(password)
        has_leet = any(c in password for c in "01345789@$!+")
        has_keyboard = self._has_keyboard_pattern(password)
        has_special = any(not c.isalnum() for c in password)
        has_digits = any(c.isdigit() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)

        # Classify pattern type
        if has_dict_word and has_special and has_digits:
            if has_upper and has_lower:
                pattern_type = "word_special_digit_mixed"
            elif has_upper:
                pattern_type = "word_special_digit_upper"
            else:
                pattern_type = "word_special_digit_lower"
        elif has_dict_word and has_digits:
            pattern_type = "word_digit"
        elif has_dict_word and has_special:
            pattern_type = "word_special"
        elif has_dict_word:
            pattern_type = "word_only"
        elif has_keyboard:
            pattern_type = "keyboard_pattern"
        elif has_leet:
            pattern_type = "leet_speak"
        elif has_special and has_digits:
            pattern_type = "special_digit"
        elif has_digits:
            pattern_type = "digit_only"
        else:
            pattern_type = "other"

        return PATTERN_TYPE_PENALTIES.get(pattern_type, 0)

    def get_specific_pattern_penalty(self, password: str) -> int:
        """Calculate specific pattern penalties"""
        penalty = 0
        pwd_lower = password.lower()

        # Check regex patterns
        for pattern, pen in self.specific_patterns.items():
            if isinstance(pattern, str):
                if pattern in pwd_lower:
                    penalty += pen
            else:  # regex
                if pattern.search(password):
                    penalty += pen

        return penalty

    def get_complexity_bonus(self, password: str) -> int:
        """Calculate complexity bonus based on length and character variety"""
        bonus = 0

        # Length bonus
        length = len(password)
        for min_len, bonus_val in COMPLEXITY_BONUSES["length"].items():
            if length >= min_len:
                bonus = max(bonus, bonus_val)

        # Character set bonus
        charsets = 0
        if any(c.isupper() for c in password):
            charsets += 1
        if any(c.islower() for c in password):
            charsets += 1
        if any(c.isdigit() for c in password):
            charsets += 1
        if any(not c.isalnum() for c in password):
            charsets += 1

        bonus += COMPLEXITY_BONUSES["charsets"].get(charsets, 0)

        return bonus

    def grade_password(self, password: str) -> Dict[str, Any]:
        """Grade a single password and return detailed breakdown (new scale)"""
        if not password:
            return {
                "password": password,
                "final_score": 0,
                "base_predictability": 0,
                "pattern_type_penalty": 0,
                "specific_pattern_penalty": 0,
                "complexity_bonus": 0,
                "breakdown": "Empty password"
            }

        # Base predictability: scale to 0-50 (less predictable = higher score)
        pred_score = password_score(password, self.step5_counts)
        base_predictability = max(0, min(50, 50 - pred_score["predictability"]))

        # Complexity bonus: up to 50 (length + char diversity)
        length = len(password)
        charsets = 0
        if any(c.isupper() for c in password):
            charsets += 1
        if any(c.islower() for c in password):
            charsets += 1
        if any(c.isdigit() for c in password):
            charsets += 1
        if any(not c.isalnum() for c in password):
            charsets += 1
        # Length bonus: up to 25
        length_bonus = 0
        for min_len, bonus_val in sorted(COMPLEXITY_BONUSES["length"].items()):
            if length >= min_len:
                length_bonus = max(length_bonus, bonus_val)
        # Charset bonus: up to 25
        charset_bonus = COMPLEXITY_BONUSES["charsets"].get(charsets, 0)
        complexity_bonus = min(50, length_bonus + charset_bonus)

        # Pattern type penalty: up to 20
        pattern_penalty = min(20, self.get_pattern_type_penalty(password))

        # Specific pattern penalty: up to 25
        specific_penalty = min(25, self.get_specific_pattern_penalty(password))

        # Final score calculation
        final_score = base_predictability + complexity_bonus - pattern_penalty - specific_penalty
        final_score = max(0, min(100, final_score))

        return {
            "password": password,
            "final_score": round(final_score, 2),
            "base_predictability": round(base_predictability, 2),
            "pattern_type_penalty": pattern_penalty,
            "specific_pattern_penalty": specific_penalty,
            "complexity_bonus": complexity_bonus,
            "length": length,
            "breakdown": f"Base: {base_predictability:.1f} + Complexity: {complexity_bonus} - Pattern: {pattern_penalty} - Specific: {specific_penalty} = {final_score:.1f}"
        }

    def _has_dictionary_word(self, password: str) -> bool:
        """Check if password contains dictionary words (simplified)"""
        # Use common words from step4 results
        common_words = set(self.step4_results.get("matched_words", {}).keys())
        tokens = set(re.findall(r'[a-zA-Z]{3,}', password.lower()))
        return bool(tokens.intersection(common_words))

    def _has_keyboard_pattern(self, password: str) -> bool:
        """Check for keyboard patterns (simplified)"""
        keyboard_patterns = ["qwerty", "asdf", "zxcv", "1234", "qaz", "wsx", "edc"]
        pwd_lower = password.lower()
        return any(pattern in pwd_lower for pattern in keyboard_patterns)

def load_step5_counts(json_path: Path) -> Dict:
    """Load or rebuild n-gram counts from step5 JSON or data files"""
    if json_path.exists():
        print(f"[DEBUG] Found JSON file at: {json_path}")
        try:
            with json_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[DEBUG] JSON loaded. Top-level keys: {list(data.keys())}")
            if "unigram" in data:
                print(f"[DEBUG] 'unigram' key type: {type(data['unigram'])}")
            if "bigram" in data:
                print(f"[DEBUG] 'bigram' key type: {type(data['bigram'])}")
            if "trigram" in data:
                print(f"[DEBUG] 'trigram' key type: {type(data['trigram'])}")
            # Robustly handle both dict and int for bigram/trigram
            if "unigram" in data and isinstance(data["unigram"], dict):
                print("[DEBUG] Full n-gram model found in JSON. Using loaded data.")

                def safe_counter(val):
                    if isinstance(val, dict):
                        return Counter(val)
                    elif isinstance(val, int):
                        return Counter({"": val})
                    else:
                        return Counter()

                bigram = defaultdict(Counter)
                for k, v in data.get("bigram", {}).items():
                    bigram[k] = safe_counter(v)

                trigr = defaultdict(_defaultdict_counter)
                for k, v in data.get("trigram", {}).items():
                    if isinstance(v, dict):
                        for k2, v2 in v.items():
                            trigr[k][k2] = safe_counter(v2)
                    else:
                        # If v is int, treat as a Counter with a dummy key
                        trigr[k][""] = safe_counter(v)

                return {
                    "total_passwords": data.get("total_passwords", 0),
                    "unigram": Counter(data["unigram"]),
                    "bigram": bigram,
                    "trigram": trigr,
                }
            else:
                print("[DEBUG] 'unigram' key missing or not a dict.")
        except Exception as e:
            print(f"[DEBUG] Error loading or parsing JSON: {e}")

    # If no full counts available, rebuild from data
    print("Full counts not found in JSON, rebuilding n-gram model from data files...")
    script_dir = json_path.parent
    data_dir = script_dir.parent / "data" / "archive"

    TARGET_FOLDERS = ["P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "Symbols"]
    counts = build_ngram_counts(data_dir, TARGET_FOLDERS, verbose=True)
    return counts

def sample_passwords_from_data(data_dir: Path, folders, sample_size: int = 20) -> List[str]:
    """Load ALL passwords from the actual data files (no sampling)"""
    all_passwords = []
    for folder in folders:
        file_name = f"{folder}.txt" if folder != "Symbols" else "Symbols.txt"
        path = data_dir / folder / file_name
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    password = line.strip()
                    if password and len(password) >= 4:
                        all_passwords.append(password)
        except Exception as e:
            print(f"Error reading {path}: {e}")
    return all_passwords
def load_step4_results(json_path: Path) -> Dict:
    """Load step4 semantic results"""
    if not json_path.exists():
        raise FileNotFoundError(f"Step 4 results not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _init_grader(step5_counts, step4_results):
    global _GRADER
    _GRADER = PasswordGrader(step5_counts, step4_results)

def _grade_password_mp(args):
    # args: (folder, password)
    folder, pwd = args
    # Use the global grader
    result = _GRADER.grade_password(pwd)
    return (folder, result)

def main():
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="Grade passwords using probabilistic and pattern analysis")
    parser.add_argument("--step5_json", default=str(script_dir / "step5_probabilistic_summary.json"),
                        help="Step 5 probabilistic model JSON")
    parser.add_argument("--step4_json", default=str(script_dir / "step4_semantic_results.json"),
                        help="Step 4 semantic analysis JSON")
    parser.add_argument("--output", default=str(script_dir / "STEP6_GRADING_REPORT.md"),
                        help="Markdown report output")
    parser.add_argument("--json_output", default=str(script_dir / "step6_grading_results.json"),
                        help="JSON results output")
    parser.add_argument("--test_passwords", nargs="*", default=["Password123!", "asdf", "Admin123!", "MySecurePass2024!"],
                        help="Test passwords to grade")
    parser.add_argument("--verbose", action="store_true", help="Show progress while grading passwords")

    args = parser.parse_args()

    # Load required data
    print("Loading Step 5 probabilistic model...")
    step5_counts = load_step5_counts(Path(args.step5_json))

    print("Loading Step 4 semantic results...")
    step4_results = load_step4_results(Path(args.step4_json))

    # Initialize grader
    grader = PasswordGrader(step5_counts, step4_results)

    # Load ALL real passwords from data
    print("Loading ALL real passwords from data files...")
    data_dir = script_dir.parent / "data" / "archive"
    TARGET_FOLDERS = ["P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "Symbols"]
    # For progress reporting, load by folder
    real_passwords = []
    folder_password_counts = {}
    for folder in TARGET_FOLDERS:
        file_name = f"{folder}.txt" if folder != "Symbols" else "Symbols.txt"
        path = data_dir / folder / file_name
        count = 0
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    password = line.strip()
                    if password and len(password) >= 4:
                        real_passwords.append((folder, password))
                        count += 1
        except Exception as e:
            print(f"Error reading {path}: {e}")
        folder_password_counts[folder] = count
    print(f"Loaded {sum(folder_password_counts.values())} real passwords")

    # Grade test passwords
    print("\nGrading test passwords:")
    print("-" * 80)
    test_results = []
    for pwd in args.test_passwords:
        result = grader.grade_password(pwd)
        test_results.append(result)
        print(f"Password: {result['password']!r}")
        print(f"Score: {result['final_score']}/100")
        print()


    # Grade real passwords with multiprocessing
    print("Grading real passwords from data:")
    print("-" * 80)
    real_results = []
    total_graded = 0
    last_reported = 0
    progress_interval = 100000
    current_folder = None
    folder_graded = 0

    # Use multiprocessing Pool with tqdm progress bar
    cpu_count = max(1, multiprocessing.cpu_count() - 1)
    total_pwds = len(real_passwords)
    if tqdm:
        pbar = tqdm(total=total_pwds, desc="Grading real passwords", unit="pwds")
    else:
        pbar = None
    with multiprocessing.Pool(cpu_count, initializer=_init_grader, initargs=(step5_counts, step4_results)) as pool:
        for folder, result in pool.imap(_grade_password_mp, real_passwords, chunksize=100000):
            real_results.append(result)
            total_graded += 1
            if pbar:
                pbar.update(1)
            elif args.verbose and total_graded % 100000 == 0:
                print(f"Graded {total_graded:,} passwords...")
            if current_folder != folder:
                if current_folder is not None and args.verbose and not pbar:
                    print(f"Folder {current_folder}: {folder_graded:,} passwords evaluated (total {total_graded:,})")
                current_folder = folder
                folder_graded = 0
            folder_graded += 1
        if pbar:
            pbar.close()
        elif args.verbose and current_folder is not None:
            print(f"Folder {current_folder}: {folder_graded:,} passwords evaluated (total {total_graded:,})")

    # Sort real results by score for top/bottom analysis
    real_results_sorted = sorted(real_results, key=lambda x: x['final_score'], reverse=True)

    # Save results
    output_path = Path(args.output)
    json_output_path = Path(args.json_output)

    # Generate markdown report
    md = f"""# Step 6: Password Grading Report

## Methodology

Password strength grading combines multiple factors:

1. **Base Predictability Score** (0-100): From Step 5 probabilistic model
   - Higher score = more predictable (worse)
   - Based on n-gram character transition probabilities

2. **Pattern Type Penalties**: Based on Step 4 semantic analysis
   - More common pattern types get higher deductions
   - Examples: dictionary words, keyboard patterns, leet speak

3. **Specific Pattern Penalties**: Common weak patterns
   - Keyboard sequences (asdf, qwerty)
   - Common words (password, admin)
   - Simple suffixes (!, 123)

4. **Complexity Bonuses**: Length and character variety
   - Length: 8+ chars = +5, 12+ = +15, 16+ = +25
   - Character sets: 4 types (upper/lower/digit/special) = +25

## Scoring Components

| Component                | Range  | Description                                         |
|--------------------------|--------|-----------------------------------------------------|
| Base predictability      | 0–50   | Inverse of n-gram predictability (less predictable = higher, up to +50 pts) |
| Complexity bonus         | 0–50   | Length (+ up to 25 pts) + char-class diversity (+ up to 25 pts) |
| Pattern type penalty     | 0–20   | Deduction for common pattern types from Step 4 (up to -20 pts) |
| Specific pattern penalty | 0–25   | Keyboard runs, weak words, repeated chars, etc. (up to -25 pts) |

## Formula

```
final_score = base_predictability (max 50) + complexity_bonus (max 50)
              - pattern_type_penalty (max 20) - specific_pattern_penalty (max 25)
final_score = clamp(final_score, 0, 100)
```

## Points Allocation

- **Base predictability**: +0 to +50 points (less predictable = higher score)
- **Complexity bonus**: +0 to +50 points (length and character set diversity)
- **Pattern type penalty**: -0 to -20 points (common patterns)
- **Specific pattern penalty**: -0 to -25 points (weak substrings, keyboard walks, etc.)

## Pattern Type Penalties

| Pattern Type | Penalty | Description |
|-------------|---------|-------------|
"""

    for pattern, penalty in sorted(PATTERN_TYPE_PENALTIES.items(), key=lambda x: x[1], reverse=True):
        desc = {
            "word_special_digit_mixed": "Dictionary word + special + digit + mixed case",
            "word_special_digit_upper": "Dictionary word + special + digit + uppercase",
            "word_special_digit_lower": "Dictionary word + special + digit + lowercase",
            "word_digit": "Dictionary word + digits",
            "word_special": "Dictionary word + special characters",
            "word_only": "Dictionary word only",
            "leet_speak": "Leet speak substitutions",
            "keyboard_pattern": "Keyboard sequences",
            "special_digit": "Special characters + digits",
            "digit_only": "Digits only",
            "other": "Other patterns",
        }.get(pattern, pattern)
        md += f"| {pattern} | -{penalty} | {desc} |\n"

    md += "\n## Specific Pattern Penalties\n\n"
    for pattern, penalty in SPECIFIC_PATTERN_PENALTIES.items():
        md += f"- `{pattern}`: -{penalty} points\n"

    md += "\n## Complexity Bonuses\n\n"
    md += "### Length Bonuses\n"
    for length, bonus in COMPLEXITY_BONUSES["length"].items():
        md += f"- {length}+ characters: +{bonus} points\n"

    md += "\n### Character Set Bonuses\n"
    for sets, bonus in COMPLEXITY_BONUSES["charsets"].items():
        types = ["uppercase", "lowercase", "digits", "special"][:sets]
        md += f"- {sets} types ({', '.join(types)}): +{bonus} points\n"


    # Grading scale
    md += "\n## Grading Scale\n\n"
    md += "| Grade Range | Description         |\n"
    md += "|-------------|--------------------|\n"
    md += "| 90-100      | Excellent (Very Strong) |\n"
    md += "| 75-89       | Good (Strong)      |\n"
    md += "| 60-74       | Fair (Moderate)    |\n"
    md += "| 40-59       | Weak               |\n"
    md += "| 0-39        | Very Weak          |\n"

    # Test password grades
    md += "\n## Test Password Grades\n\n"
    md += "| Password | Final Score | Base Pred | Pattern Pen | Specific Pen | Complexity Bonus | Breakdown |\n"
    md += "|----------|-------------|-----------|-------------|--------------|------------------|-----------|\n"
    for result in test_results:
        md += f"| `{result['password']}` | {result['final_score']} | {result['base_predictability']} | -{result['pattern_type_penalty']} | -{result['specific_pattern_penalty']} | +{result['complexity_bonus']} | {result['breakdown']} |\n"

    # Top specific penalty reasons
    # Count top penalty triggers in real data
    penalty_reason_counter = Counter()
    for r in real_results:
        pwd = r['password'].lower()
        for pattern, pen in SPECIFIC_PATTERN_PENALTIES.items():
            try:
                if re.search(pattern, pwd):
                    penalty_reason_counter[pattern] += 1
            except:
                if pattern in pwd:
                    penalty_reason_counter[pattern] += 1

    md += "\n## Top Specific Penalty Reasons\n\n"
    md += "| Pattern | Penalty | Occurrences |\n"
    md += "|---------|---------|-------------|\n"
    for pattern, count in penalty_reason_counter.most_common(10):
        md += f"| `{pattern}` | -{SPECIFIC_PATTERN_PENALTIES[pattern]} | {count} |\n"

    # Top 10 and bottom 10 real data grades
    md += "\n## Top 10 Password Grades from Real Data\n\n"
    md += "| Rank | Password | Final Score | Base Pred | Pattern Pen | Specific Pen | Complexity Bonus |\n"
    md += "|------|----------|-------------|-----------|-------------|--------------|------------------|\n"
    for i, result in enumerate(real_results_sorted[:10], 1):
        md += f"| {i} | `{result['password']}` | {result['final_score']} | {result['base_predictability']} | -{result['pattern_type_penalty']} | -{result['specific_pattern_penalty']} | +{result['complexity_bonus']} |\n"

    md += "\n## Bottom 10 Password Grades from Real Data\n\n"
    md += "| Rank | Password | Final Score | Base Pred | Pattern Pen | Specific Pen | Complexity Bonus |\n"
    md += "|------|----------|-------------|-----------|-------------|--------------|------------------|\n"
    for i, result in enumerate(real_results_sorted[-10:], 1):
        md += f"| {len(real_results_sorted) - 10 + i} | `{result['password']}` | {result['final_score']} | {result['base_predictability']} | -{result['pattern_type_penalty']} | -{result['specific_pattern_penalty']} | +{result['complexity_bonus']} |\n"

    # Example passwords by grade
    md += "\n## Example Passwords by Grade\n\n"
    grade_buckets = {
        'Excellent (90-100)': [],
        'Good (75-89)': [],
        'Fair (60-74)': [],
        'Weak (40-59)': [],
        'Very Weak (0-39)': []
    }
    for r in real_results_sorted:
        score = r['final_score']
        if score >= 90:
            grade_buckets['Excellent (90-100)'].append(r['password'])
        elif score >= 75:
            grade_buckets['Good (75-89)'].append(r['password'])
        elif score >= 60:
            grade_buckets['Fair (60-74)'].append(r['password'])
        elif score >= 40:
            grade_buckets['Weak (40-59)'].append(r['password'])
        else:
            grade_buckets['Very Weak (0-39)'].append(r['password'])
    for label, pwds in grade_buckets.items():
        md += f"**{label}:**\n"
        for p in pwds[:3]:
            md += f"- `{p}`\n"
        md += "\n"

    # Save markdown
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(md)

    # Save JSON results
    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    with json_output_path.open("w", encoding="utf-8") as f:
        json.dump({
            "pattern_type_penalties": PATTERN_TYPE_PENALTIES,
            "specific_pattern_penalties": SPECIFIC_PATTERN_PENALTIES,
            "complexity_bonuses": COMPLEXITY_BONUSES,
            "test_results": test_results,
            "real_results": real_results,
            "top_10_real": real_results_sorted[:10],
            "bottom_10_real": real_results_sorted[-10:]
        }, f, indent=2)

    print(f"Saved grading report to {output_path}")
    print(f"Saved JSON results to {json_output_path}")

if __name__ == "__main__":
    main()