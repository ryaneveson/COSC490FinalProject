import argparse
import random
import string
from pathlib import Path
from step6_grading import PasswordGrader, load_step5_counts, load_step4_results
import multiprocessing
from tqdm import tqdm

def avoid_patterns(pwd, step4_results):
    # Remove or modify common dictionary words
    common_words = set(step4_results.get("matched_words", {}).keys())
    tokens = [w for w in pwd.split() if w]
    for word in tokens:
        if word.lower() in common_words:
            # Replace with random chars, a symbol, and a digit
            replacement = ''.join(random.choices(string.ascii_letters, k=2)) + random.choice("!@#$%") + str(random.randint(10,99))
            pwd = pwd.replace(word, replacement)
    # Remove common keyboard patterns
    for pat in ["qwerty", "asdf", "zxcv", "1234", "qaz", "wsx", "edc"]:
        if pat in pwd.lower():
            replacement = ''.join(random.choices(string.ascii_letters + string.digits, k=3)) + random.choice(string.punctuation)
            pwd = pwd.replace(pat, replacement)
    # Remove common suffixes/prefixes
    for suf in ["123", "1234", "!", "!!"]:
        if pwd.endswith(suf):
            pwd = pwd[:-len(suf)] + random.choice(string.punctuation) + str(random.randint(10,99))
    for pre in ["admin", "user", "pass"]:
        if pwd.lower().startswith(pre):
            pwd = random.choice(string.ascii_letters) + pwd[len(pre):]
    # Add more randomization for extra security
    if len(pwd) < 16:
        pwd += ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=16-len(pwd)))
    return pwd

def add_complexity(pwd, min_length=12):
    # Ensure length
    if len(pwd) < min_length:
        pwd += ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=min_length-len(pwd)))
    # Ensure at least two of each type for extra strength
    for _ in range(2):
        if not any(c.isupper() for c in pwd):
            pwd += random.choice(string.ascii_uppercase)
        if not any(c.islower() for c in pwd):
            pwd += random.choice(string.ascii_lowercase)
        if not any(c.isdigit() for c in pwd):
            pwd += random.choice(string.digits)
        if not any(not c.isalnum() for c in pwd):
            pwd += random.choice(string.punctuation)
    # Shuffle
    pwd = list(pwd)
    random.shuffle(pwd)
    return ''.join(pwd)

def single_attempt(args):
    pwd, step4_results, min_length, step5_counts, step4_results_obj = args
    # Recreate grader in subprocess
    grader = PasswordGrader(step5_counts, step4_results_obj)
    pwd2 = avoid_patterns(pwd, step4_results)
    pwd2 = add_complexity(pwd2, min_length=min_length)
    grade = grader.grade_password(pwd2)
    return pwd2, grade
def generate_password(base=None, elements=None, grader=None, step4_results=None, min_score=80, max_attempts=20):
    # Prepare initial password
    if base:
        initial_pwd = base
    elif elements:
        initial_pwd = ''.join(elements)
    else:
        initial_pwd = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=16))

    print("[INFO] Starting parallel password generation process...")
    cpu_count = max(2, multiprocessing.cpu_count() - 1)
    batch_size = cpu_count * 4
    attempts = 0
    best = (None, {'final_score': 0})
    # Pass step5_counts and step4_results to subprocesses
    step5_counts = grader.step5_counts if hasattr(grader, 'step5_counts') else None
    step4_results_obj = grader.step4_results if hasattr(grader, 'step4_results') else None
    with multiprocessing.Pool(cpu_count) as pool, tqdm(desc="Password Attempts", unit="attempt", dynamic_ncols=True) as pbar:
        while True:
            # Prepare batch of random passwords
            pwds = [
                (initial_pwd if i == 0 else ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=16)),
                 step4_results, 16, step5_counts, step4_results_obj)
                for i in range(batch_size)
            ]
            results = pool.map(single_attempt, pwds)
            found = False
            for pwd2, grade in results:
                attempts += 1
                pbar.update(1)
                if grade['final_score'] > best[1]['final_score']:
                    best = (pwd2, grade)
                    tqdm.write(f"[BEST SO FAR] Attempt {attempts}: Password='{pwd2}' | Score={grade['final_score']}")
                if grade['final_score'] >= min_score:
                    tqdm.write(f"[SUCCESS] Password meets minimum score ({min_score}) after {attempts} attempts.")
                    found = True
                    break
            if found:
                return best[0], best[1]
            # After each batch, randomize initial_pwd for next batch
            initial_pwd = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=16))

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
    parser.add_argument('--min_score', type=int, default=80, help='Minimum grading score')
    parser.add_argument('--step5_json', default=str(Path(__file__).parent / "step5_probabilistic_summary.json"))
    parser.add_argument('--step4_json', default=str(Path(__file__).parent / "step4_semantic_results.json"))
    args = parser.parse_args()

    step5_counts = load_step5_counts(Path(args.step5_json))
    step4_results = load_step4_results(Path(args.step4_json))
    grader = PasswordGrader(step5_counts, step4_results)

    pwd, grade = generate_password(base=args.base, elements=args.elements, grader=grader, step4_results=step4_results, min_score=args.min_score)
    print("Generated password:", pwd)
    print("Grading breakdown:", grade)
    generate_step7_report(pwd, grade, args)
    


if __name__ == "__main__":
    main()
