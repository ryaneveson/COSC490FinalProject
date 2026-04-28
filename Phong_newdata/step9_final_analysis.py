"""
Step 9: Final Vulnerability Analysis
Cross-references Step 8 attack results with Step 6 grading data to determine
which password characteristics made them susceptible to cracking, and validates
the grading weightings against actual cracking success rates.
"""

import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def load_attack_results(json_path: Path):
    """Load Step 8 attack results from JSON."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_grading_results(json_path: Path):
    """Load step6 grading results and build a password -> grade lookup."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    lookup = {}
    for entry in data.get("real_results", []):
        lookup[entry["password"]] = entry
    return data, lookup


def classify_password_content(password: str):
    """Classify password into content categories."""
    pwd_lower = password.lower()
    has_alpha = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)

    charset_count = sum([has_upper, has_lower, has_digit, has_special])

    # Content type
    if has_alpha and not has_digit and not has_special:
        content_type = "alpha_only"
    elif has_alpha and has_digit and not has_special:
        content_type = "alpha_digit"
    elif has_digit and not has_alpha and not has_special:
        content_type = "digit_only"
    elif has_alpha and has_special and has_digit:
        content_type = "mixed"
    elif has_alpha and has_special:
        content_type = "alpha_special"
    else:
        content_type = "other"

    return {
        "content_type": content_type,
        "charset_count": charset_count,
        "has_upper": has_upper,
        "has_lower": has_lower,
        "has_digit": has_digit,
        "has_special": has_special,
    }


# Common English first names for categorization
COMMON_NAMES = {
    "michael", "jessica", "daniel", "ashley", "matthew", "andrew", "joshua",
    "david", "james", "robert", "john", "william", "thomas", "joseph",
    "charlie", "jordan", "justin", "anthony", "brandon", "taylor", "amanda",
    "nicole", "michelle", "jennifer", "stephanie", "melissa", "elizabeth",
    "lauren", "samantha", "rachel", "sarah", "rebecca", "heather", "hannah",
    "natasha", "vanessa", "olivia", "sophie", "victoria", "austin", "nathan",
    "samuel", "gabriel", "edward", "oliver", "george", "benjamin", "richard",
    "steven", "kevin", "jason", "brian", "eric", "patrick", "adam", "mark",
    "paul", "donald", "ryan", "tyler", "aaron", "jose", "timothy", "jacob",
    "henry", "peter", "dennis", "jerry", "alexander", "johnny", "sandra",
    "maria", "angela", "anna", "diana", "emma", "karen", "lisa", "nancy",
    "betty", "helen", "carol", "ruth", "sharon", "laura", "andrea", "debra",
    "maggie", "mickey", "hockey", "jesus", "batman", "mustang", "junior",
    "martin", "carlos", "antonio",
}


def categorize_word(password: str):
    """Categorize whether a password is a name, common word, or other."""
    pwd_lower = password.lower().strip()
    if pwd_lower in COMMON_NAMES:
        return "personal_name"
    # Check if it's a single alphabetic word
    if pwd_lower.isalpha() and len(pwd_lower) >= 3:
        return "common_word"
    return "other"


def compute_stats(values):
    """Compute basic statistics for a list of numbers."""
    if not values:
        return {"count": 0, "mean": 0, "median": 0, "min": 0, "max": 0, "stdev": 0}
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
    }


def point_biserial_correlation(binary_var, continuous_var):
    """
    Compute point-biserial correlation between a binary variable (0/1)
    and a continuous variable. Returns r value.
    """
    if len(binary_var) != len(continuous_var) or len(binary_var) < 2:
        return 0.0

    group0 = [c for b, c in zip(binary_var, continuous_var) if b == 0]
    group1 = [c for b, c in zip(binary_var, continuous_var) if b == 1]

    if not group0 or not group1:
        return 0.0

    n = len(binary_var)
    n0 = len(group0)
    n1 = len(group1)
    mean0 = statistics.mean(group0)
    mean1 = statistics.mean(group1)
    overall_std = statistics.stdev(continuous_var)

    if overall_std == 0:
        return 0.0

    r = ((mean1 - mean0) / overall_std) * ((n0 * n1) / (n * n)) ** 0.5
    return round(r, 4)


def main():
    parser = argparse.ArgumentParser(description="Step 9: Final Vulnerability Analysis")
    script_dir = Path(__file__).resolve().parent

    parser.add_argument("--step6_json", default=str(script_dir / "step6_grading_results.json"),
                        help="Step 6 grading results JSON")
    parser.add_argument("--step8_json", default=str(script_dir / "step8_attack_results.json"),
                        help="Step 8 attack results JSON")
    parser.add_argument("--output", default=str(script_dir / "STEP9_FINAL_ANALYSIS_REPORT.md"),
                        help="Output markdown report")
    parser.add_argument("--json_output", default=str(script_dir / "step9_final_analysis_results.json"),
                        help="Output JSON results")
    args = parser.parse_args()

    # ── Load data ──────────────────────────────────────────────────────────
    print("Loading Step 6 grading results...")
    grading_data, grade_lookup = load_grading_results(Path(args.step6_json))

    print("Loading Step 8 attack results...")
    attack_data = load_attack_results(Path(args.step8_json))

    all_passwords = attack_data["all_passwords"]
    pattern_cracked_dict = attack_data["pattern_attack"]["cracked_passwords"]
    spear_cracked_dict = attack_data["spear_attack"]["cracked_passwords"]
    pattern_total_guesses = attack_data["pattern_attack"]["total_guesses"]
    spear_total_guesses = attack_data["spear_attack"]["total_guesses"]

    # Build lists analogous to old format
    cracked_passwords_set = set(pattern_cracked_dict.keys())
    spear_cracked_set = set(spear_cracked_dict.keys())
    all_cracked_set = cracked_passwords_set | spear_cracked_set
    uncracked_passwords = [pwd for pwd in all_passwords if pwd not in cracked_passwords_set]

    print(f"\nPattern attack: {len(cracked_passwords_set):,} cracked / {len(all_passwords):,} tested "
          f"({attack_data['pattern_attack']['success_rate']}%)")
    print(f"Spear phishing: {len(spear_cracked_set):,} cracked / {len(all_passwords):,} tested "
          f"({attack_data['spear_attack']['success_rate']}%)")
    print(f"Combined unique: {len(all_cracked_set):,} cracked ({attack_data['combined_success_rate']}%)")

    # ── Enrich cracked passwords with grading data ────────────────────────
    cracked_enriched = []
    for pwd in cracked_passwords_set:
        attack_info = pattern_cracked_dict[pwd]
        grade = grade_lookup.get(pwd, {})
        classification = classify_password_content(pwd)
        word_category = categorize_word(pwd)
        also_spear = pwd in spear_cracked_set

        cracked_enriched.append({
            "password": pwd,
            "attack_pattern": attack_info.get("pattern_type"),
            "also_spear_cracked": also_spear,
            "final_score": grade.get("final_score", None),
            "base_predictability": grade.get("base_predictability", None),
            "pattern_type_penalty": grade.get("pattern_type_penalty", None),
            "specific_pattern_penalty": grade.get("specific_pattern_penalty", None),
            "complexity_bonus": grade.get("complexity_bonus", None),
            "length": len(pwd),
            "content_type": classification["content_type"],
            "charset_count": classification["charset_count"],
            "word_category": word_category,
        })

    # Also add spear-only cracked passwords
    for pwd in spear_cracked_set - cracked_passwords_set:
        attack_info = spear_cracked_dict[pwd]
        grade = grade_lookup.get(pwd, {})
        classification = classify_password_content(pwd)
        word_category = categorize_word(pwd)

        cracked_enriched.append({
            "password": pwd,
            "attack_pattern": attack_info.get("pattern_type"),
            "also_spear_cracked": True,
            "final_score": grade.get("final_score", None),
            "base_predictability": grade.get("base_predictability", None),
            "pattern_type_penalty": grade.get("pattern_type_penalty", None),
            "specific_pattern_penalty": grade.get("specific_pattern_penalty", None),
            "complexity_bonus": grade.get("complexity_bonus", None),
            "length": len(pwd),
            "content_type": classification["content_type"],
            "charset_count": classification["charset_count"],
            "word_category": word_category,
        })

    # Sort by score (weakest first)
    cracked_enriched.sort(key=lambda x: (x["final_score"] if x["final_score"] is not None else 0, x["length"]))

    # ── Vulnerability factor analysis ─────────────────────────────────────
    print("\n── Analyzing vulnerability factors ──")

    # 1. Length analysis
    cracked_lengths = [e["length"] for e in cracked_enriched]
    uncracked_lengths = [len(pwd) for pwd in uncracked_passwords]
    cracked_len_stats = compute_stats(cracked_lengths)
    uncracked_len_stats = compute_stats(uncracked_lengths)

    print(f"  Length — cracked avg: {cracked_len_stats['mean']}, uncracked avg: {uncracked_len_stats['mean']}")

    # 2. Score analysis
    cracked_scores = [e["final_score"] for e in cracked_enriched if e["final_score"] is not None]
    uncracked_scores = [grade_lookup.get(pwd, {}).get("final_score")
                        for pwd in uncracked_passwords]
    uncracked_scores = [s for s in uncracked_scores if s is not None]
    cracked_score_stats = compute_stats(cracked_scores)
    uncracked_score_stats = compute_stats(uncracked_scores)

    print(f"  Score — cracked avg: {cracked_score_stats['mean']}, uncracked avg: {uncracked_score_stats['mean']}")

    # 3. Pattern type distribution
    attack_pattern_counts = Counter(e["attack_pattern"] for e in cracked_enriched)
    print(f"  Attack patterns that succeeded: {dict(attack_pattern_counts)}")

    # 4. Content type distribution
    content_type_counts = Counter(e["content_type"] for e in cracked_enriched)
    print(f"  Content types of cracked: {dict(content_type_counts)}")

    # 5. Word category distribution
    word_cat_counts = Counter(e["word_category"] for e in cracked_enriched)
    print(f"  Word categories of cracked: {dict(word_cat_counts)}")

    # 6. Charset analysis
    cracked_charsets = [e["charset_count"] for e in cracked_enriched]
    uncracked_charsets = [classify_password_content(pwd)["charset_count"]
                         for pwd in uncracked_passwords]
    cracked_charset_stats = compute_stats(cracked_charsets)
    uncracked_charset_stats = compute_stats(uncracked_charsets)

    print(f"  Charsets — cracked avg: {cracked_charset_stats['mean']}, uncracked avg: {uncracked_charset_stats['mean']}")

    # ── Correlation: score vs cracking outcome ────────────────────────────
    # Binary: 1 = survived (not cracked), 0 = cracked
    all_binary = []
    all_scores = []
    for pwd in all_passwords:
        score = grade_lookup.get(pwd, {}).get("final_score")
        if score is not None:
            all_binary.append(0 if pwd in all_cracked_set else 1)
            all_scores.append(score)

    correlation = point_biserial_correlation(all_binary, all_scores)
    print(f"\n  Point-biserial correlation (score vs survival): r = {correlation}")

    # ── Score vs length correlation for cracked passwords ────────────────
    if len(cracked_enriched) > 2:
        score_vals = [e["final_score"] for e in cracked_enriched if e["final_score"] is not None]
        length_vals_for_scored = [e["length"] for e in cracked_enriched if e["final_score"] is not None]
        # Simple Pearson correlation between length and score among cracked
        if len(score_vals) == len(length_vals_for_scored) and len(score_vals) > 2:
            mean_s = statistics.mean(score_vals)
            mean_l = statistics.mean(length_vals_for_scored)
            num = sum((s - mean_s) * (l - mean_l) for s, l in zip(score_vals, length_vals_for_scored))
            den_s = sum((s - mean_s) ** 2 for s in score_vals) ** 0.5
            den_l = sum((l - mean_l) ** 2 for l in length_vals_for_scored) ** 0.5
            score_length_corr = round(num / (den_s * den_l), 4) if den_s * den_l > 0 else 0
        else:
            score_length_corr = None
    else:
        score_length_corr = None

    print(f"  Score vs Length correlation (cracked only): {score_length_corr}")

    # ── Grading weight validation ─────────────────────────────────────────
    # Check how many cracked passwords fell into each grade band
    grade_bands = {
        "Very Weak (0-19)": (0, 19),
        "Weak (20-39)": (20, 39),
        "Fair (40-59)": (40, 59),
        "Strong (60-79)": (60, 79),
        "Very Strong (80-100)": (80, 100),
    }

    cracked_by_band = defaultdict(int)
    uncracked_by_band = defaultdict(int)

    for entry in cracked_enriched:
        score = entry["final_score"]
        if score is None:
            continue
        for band, (lo, hi) in grade_bands.items():
            if lo <= score <= hi:
                cracked_by_band[band] += 1
                break

    for pwd in uncracked_passwords:
        score = grade_lookup.get(pwd, {}).get("final_score")
        if score is None:
            continue
        for band, (lo, hi) in grade_bands.items():
            if lo <= score <= hi:
                uncracked_by_band[band] += 1
                break

    # ── Analyze specific grading component gaps ───────────────────────────
    # Check if word_only penalty is adequate
    cracked_pattern_penalties = [e["pattern_type_penalty"] for e in cracked_enriched
                                 if e["pattern_type_penalty"] is not None]
    cracked_specific_penalties = [e["specific_pattern_penalty"] for e in cracked_enriched
                                  if e["specific_pattern_penalty"] is not None]
    cracked_complexity = [e["complexity_bonus"] for e in cracked_enriched
                          if e["complexity_bonus"] is not None]

    avg_cracked_pattern_pen = round(statistics.mean(cracked_pattern_penalties), 2) if cracked_pattern_penalties else 0
    avg_cracked_specific_pen = round(statistics.mean(cracked_specific_penalties), 2) if cracked_specific_penalties else 0
    avg_cracked_complexity = round(statistics.mean(cracked_complexity), 2) if cracked_complexity else 0

    # Overall dataset averages for comparison
    all_pattern_pen = [e.get("pattern_type_penalty", 0) for e in grading_data.get("real_results", [])]
    all_specific_pen = [e.get("specific_pattern_penalty", 0) for e in grading_data.get("real_results", [])]
    all_complexity = [e.get("complexity_bonus", 0) for e in grading_data.get("real_results", [])]

    avg_all_pattern_pen = round(statistics.mean(all_pattern_pen), 2) if all_pattern_pen else 0
    avg_all_specific_pen = round(statistics.mean(all_specific_pen), 2) if all_specific_pen else 0
    avg_all_complexity = round(statistics.mean(all_complexity), 2) if all_complexity else 0

    # ── Build recommendations ─────────────────────────────────────────────
    recommendations = []

    if avg_cracked_pattern_pen < avg_all_pattern_pen + 2:
        recommendations.append(
            "**Increase `word_only` penalty** from 10 → 18: All cracked passwords were single "
            "common words. The current penalty (10) underestimates the vulnerability of standalone "
            "dictionary words, especially personal names."
        )

    if cracked_len_stats["mean"] < 8:
        recommendations.append(
            f"**Add short-password penalty**: Cracked passwords averaged {cracked_len_stats['mean']} chars. "
            "Consider adding a penalty of -10 for passwords under 6 characters and -5 for under 8 characters "
            "rather than only rewarding length with bonuses."
        )

    if cracked_charset_stats["mean"] <= 1.1:
        recommendations.append(
            "**Penalize single-charset passwords**: All cracked passwords used only 1 character set "
            "(lowercase). Add a penalty of -10 for single-charset passwords instead of relying solely "
            "on bonuses for diversity."
        )

    name_count = word_cat_counts.get("personal_name", 0)
    if name_count > len(cracked_enriched) * 0.5:
        recommendations.append(
            f"**Add personal name penalty**: {name_count}/{len(cracked_enriched)} cracked passwords "
            "were common first names. Incorporate a name dictionary check with a -15 penalty."
        )

    if score_length_corr is not None and abs(score_length_corr) < 0.3:
        recommendations.append(
            f"**Refine score granularity**: Correlation between score and length among cracked passwords is weak "
            f"(r={score_length_corr}), suggesting the current scoring doesn't differentiate well among "
            "vulnerable passwords. Consider weighting word commonality more heavily."
        )

    # ── Save JSON results ─────────────────────────────────────────────────
    json_results = {
        "summary": {
            "total_passwords": len(all_passwords),
            "pattern_attack_cracked": len(cracked_passwords_set),
            "pattern_attack_success_rate": attack_data["pattern_attack"]["success_rate"],
            "pattern_attack_guesses": pattern_total_guesses,
            "spear_attack_cracked": len(spear_cracked_set),
            "spear_attack_success_rate": attack_data["spear_attack"]["success_rate"],
            "spear_attack_guesses": spear_total_guesses,
            "combined_cracked": len(all_cracked_set),
            "combined_success_rate": attack_data["combined_success_rate"],
        },
        "cracked_passwords_sample": cracked_enriched[:500],
        "vulnerability_factors": {
            "length": {
                "cracked": cracked_len_stats,
                "uncracked": uncracked_len_stats,
            },
            "score": {
                "cracked": cracked_score_stats,
                "uncracked": uncracked_score_stats,
            },
            "charset_count": {
                "cracked": cracked_charset_stats,
                "uncracked": uncracked_charset_stats,
            },
            "attack_patterns": dict(attack_pattern_counts),
            "content_types": dict(content_type_counts),
            "word_categories": dict(word_cat_counts),
        },
        "correlations": {
            "score_vs_survival": correlation,
            "score_vs_length_cracked": score_length_corr,
        },
        "grading_validation": {
            "cracked_by_grade_band": dict(cracked_by_band),
            "uncracked_by_grade_band": dict(uncracked_by_band),
            "avg_cracked_components": {
                "pattern_type_penalty": avg_cracked_pattern_pen,
                "specific_pattern_penalty": avg_cracked_specific_pen,
                "complexity_bonus": avg_cracked_complexity,
            },
            "avg_overall_components": {
                "pattern_type_penalty": avg_all_pattern_pen,
                "specific_pattern_penalty": avg_all_specific_pen,
                "complexity_bonus": avg_all_complexity,
            },
        },
        "recommendations": recommendations,
    }

    with open(args.json_output, "w", encoding="utf-8") as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    print(f"\nJSON results saved to {args.json_output}")

    # ── Generate markdown report ──────────────────────────────────────────
    md = []
    md.append("# Step 9: Final Vulnerability Analysis Report\n")

    # --- Overview ---
    md.append("## Overview\n")
    md.append("This analysis cross-references Step 8 attack simulation results with Step 6 grading data ")
    md.append("to identify which password characteristics made them susceptible to cracking, and validates ")
    md.append("the grading system's effectiveness at predicting password vulnerability.\n")

    md.append(f"\n| Metric | Pattern Attack | Spear Phishing | Combined |")
    md.append(f"\n|--------|---------------|----------------|----------|")
    md.append(f"\n| Passwords tested | {len(all_passwords):,} | {len(all_passwords):,} | {len(all_passwords):,} |")
    md.append(f"\n| Unique guesses | {pattern_total_guesses:,} | {spear_total_guesses:,} | — |")
    md.append(f"\n| Passwords cracked | {len(cracked_passwords_set):,} | {len(spear_cracked_set):,} | {len(all_cracked_set):,} |")
    md.append(f"\n| Success rate | {json_results['summary']['pattern_attack_success_rate']}% | {json_results['summary']['spear_attack_success_rate']}% | {json_results['summary']['combined_success_rate']}% |")
    md.append("\n")

    # --- Cracked Passwords Detail Table ---
    md.append("\n## Cracked Passwords — Detailed Breakdown (first 200)\n")
    md.append("\n| # | Password | Attack | Score | Base Pred. | Pattern Pen. | Specific Pen. | Complexity | Length | Charset | Category |")
    md.append("\n|---|----------|--------|-------|------------|-------------|---------------|------------|--------|---------|----------|")
    for i, e in enumerate(cracked_enriched[:200], 1):
        md.append(
            f"\n| {i} | {e['password']} | {e['attack_pattern']} | "
            f"{e['final_score'] if e['final_score'] is not None else 'N/A'} | "
            f"{e['base_predictability'] if e['base_predictability'] is not None else 'N/A'} | "
            f"{e['pattern_type_penalty'] if e['pattern_type_penalty'] is not None else 'N/A'} | "
            f"{e['specific_pattern_penalty'] if e['specific_pattern_penalty'] is not None else 'N/A'} | "
            f"{e['complexity_bonus'] if e['complexity_bonus'] is not None else 'N/A'} | "
            f"{e['length']} | {e['charset_count']} | {e['word_category']} |"
        )
    md.append("\n")

    # --- Factor Analysis ---
    md.append("\n## Vulnerability Factor Analysis\n")

    # Length
    md.append("\n### 1. Password Length\n")
    md.append(f"\n| Metric | Cracked | Uncracked |")
    md.append(f"\n|--------|---------|-----------|")
    md.append(f"\n| Count | {cracked_len_stats['count']} | {uncracked_len_stats['count']} |")
    md.append(f"\n| Mean | {cracked_len_stats['mean']} | {uncracked_len_stats['mean']} |")
    md.append(f"\n| Median | {cracked_len_stats['median']} | {uncracked_len_stats['median']} |")
    md.append(f"\n| Min | {cracked_len_stats['min']} | {uncracked_len_stats['min']} |")
    md.append(f"\n| Max | {cracked_len_stats['max']} | {uncracked_len_stats['max']} |")
    md.append(f"\n| Std Dev | {cracked_len_stats['stdev']} | {uncracked_len_stats['stdev']} |")
    md.append("\n")
    md.append(f"\n**Finding:** Cracked passwords are shorter on average ({cracked_len_stats['mean']} chars) ")
    md.append(f"compared to uncracked ({uncracked_len_stats['mean']} chars).\n")

    # Score
    md.append("\n### 2. Grading Score (Step 6)\n")
    md.append(f"\n| Metric | Cracked | Uncracked |")
    md.append(f"\n|--------|---------|-----------|")
    md.append(f"\n| Count | {cracked_score_stats['count']} | {uncracked_score_stats['count']} |")
    md.append(f"\n| Mean | {cracked_score_stats['mean']} | {uncracked_score_stats['mean']} |")
    md.append(f"\n| Median | {cracked_score_stats['median']} | {uncracked_score_stats['median']} |")
    md.append(f"\n| Min | {cracked_score_stats['min']} | {uncracked_score_stats['min']} |")
    md.append(f"\n| Max | {cracked_score_stats['max']} | {uncracked_score_stats['max']} |")
    md.append(f"\n| Std Dev | {cracked_score_stats['stdev']} | {uncracked_score_stats['stdev']} |")
    md.append("\n")
    md.append(f"\n**Finding:** Cracked passwords scored an average of {cracked_score_stats['mean']}/100 ")
    md.append(f"vs {uncracked_score_stats['mean']}/100 for uncracked — ")
    if cracked_score_stats['mean'] < uncracked_score_stats['mean']:
        md.append("confirming the grading system directionally identifies weaker passwords.\n")
    else:
        md.append("suggesting the grading system needs recalibration.\n")

    # Charset
    md.append("\n### 3. Character Set Diversity\n")
    md.append(f"\n| Metric | Cracked | Uncracked |")
    md.append(f"\n|--------|---------|-----------|")
    md.append(f"\n| Mean charsets | {cracked_charset_stats['mean']} | {uncracked_charset_stats['mean']} |")
    md.append("\n")
    charset_note = "all" if cracked_charset_stats["mean"] <= 1.05 else "most"
    md.append(f"\n**Finding:** {charset_note.title()} cracked passwords used only 1 character set (lowercase letters).\n")

    # Content type
    md.append("\n### 4. Content Type\n")
    md.append("\n| Content Type | Cracked Count |")
    md.append("\n|-------------|---------------|")
    for ct, count in content_type_counts.most_common():
        md.append(f"\n| {ct} | {count} |")
    md.append("\n")

    # Word category
    md.append("\n### 5. Word Category\n")
    md.append("\n| Category | Cracked Count | % of Cracked |")
    md.append("\n|----------|---------------|--------------|")
    for cat, count in word_cat_counts.most_common():
        pct = round(100 * count / max(1, len(cracked_enriched)), 1)
        md.append(f"\n| {cat} | {count} | {pct}% |")
    md.append("\n")

    name_pct = round(100 * word_cat_counts.get("personal_name", 0) / max(1, len(cracked_enriched)), 1)
    md.append(f"\n**Finding:** {name_pct}% of cracked passwords were personal first names — the dominant vulnerability class.\n")

    # Attack pattern
    md.append("\n### 6. Attack Pattern That Succeeded\n")
    md.append("\n| Pattern | Count |")
    md.append("\n|---------|-------|")
    for pat, count in attack_pattern_counts.most_common():
        md.append(f"\n| {pat} | {count} |")
    md.append("\n")

    # --- Correlations ---
    md.append("\n## Statistical Correlations\n")
    md.append(f"\n| Correlation | r value | Interpretation |")
    md.append(f"\n|-------------|---------|----------------|")
    # Score vs survival
    if correlation > 0.3:
        interp = "Higher scores moderately associated with surviving attack"
    elif correlation > 0.1:
        interp = "Higher scores weakly associated with surviving attack"
    elif correlation < -0.1:
        interp = "Higher scores unexpectedly associated with being cracked"
    else:
        interp = "Very weak or no relationship"
    md.append(f"\n| Score vs Survival | {correlation} | {interp} |")

    if score_length_corr is not None:
        if abs(score_length_corr) < 0.3:
            interp2 = "Weak — score and length are loosely related among cracked passwords"
        elif score_length_corr > 0:
            interp2 = "Longer cracked passwords tended to have higher scores"
        else:
            interp2 = "Longer cracked passwords tended to have lower scores"
        md.append(f"\n| Score vs Length (cracked) | {score_length_corr} | {interp2} |")
    md.append("\n")

    # --- Grade Band Distribution ---
    md.append("\n## Grading System Validation\n")
    md.append("\n### Cracked vs Uncracked by Grade Band\n")
    md.append("\n| Grade Band | Cracked | Uncracked | Crack Rate |")
    md.append("\n|-----------|---------|-----------|------------|")
    for band in grade_bands:
        c = cracked_by_band.get(band, 0)
        u = uncracked_by_band.get(band, 0)
        total = c + u
        rate = f"{100 * c / total:.1f}%" if total > 0 else "N/A"
        md.append(f"\n| {band} | {c} | {u} | {rate} |")
    md.append("\n")

    # Component comparison
    md.append("\n### Scoring Component Comparison\n")
    md.append("\n| Component | Cracked Avg | Overall Avg | Gap |")
    md.append("\n|-----------|-------------|-------------|-----|")
    md.append(f"\n| Pattern Type Penalty | {avg_cracked_pattern_pen} | {avg_all_pattern_pen} | "
              f"{round(avg_cracked_pattern_pen - avg_all_pattern_pen, 2)} |")
    md.append(f"\n| Specific Pattern Penalty | {avg_cracked_specific_pen} | {avg_all_specific_pen} | "
              f"{round(avg_cracked_specific_pen - avg_all_specific_pen, 2)} |")
    md.append(f"\n| Complexity Bonus | {avg_cracked_complexity} | {avg_all_complexity} | "
              f"{round(avg_cracked_complexity - avg_all_complexity, 2)} |")
    md.append("\n")

    # --- Score Distribution of Cracked ---
    md.append("\n## Score Distribution of Cracked Passwords\n")
    md.append("\nPasswords sorted by score (weakest first), showing first 200:\n")
    md.append("\n| Rank | Password | Score | Attack | Length | Category |")
    md.append("\n|------|----------|-------|--------|--------|----------|")
    for i, e in enumerate(cracked_enriched[:200], 1):
        md.append(f"\n| {i} | {e['password']} | {e['final_score'] if e['final_score'] is not None else 'N/A'} | {e['attack_pattern']} | {e['length']} | {e['word_category']} |")
    md.append("\n")

    if cracked_enriched:
        weakest = cracked_enriched[0]
        strongest = cracked_enriched[-1]
        md.append(f"\n**Weakest cracked:** `{weakest['password']}` (score: {weakest['final_score']})\n")
        md.append(f"**Strongest cracked:** `{strongest['password']}` (score: {strongest['final_score']})\n")

    # --- Recommendations ---
    md.append("\n## Recommendations for Grading Weight Adjustments\n")
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            md.append(f"\n{i}. {rec}\n")
    else:
        md.append("\nNo adjustments recommended — grading system performed well.\n")

    # --- Key Takeaways ---
    md.append("\n## Key Takeaways\n")

    # Compute spear success pct string
    spear_pct = json_results['summary']['spear_attack_success_rate']
    pattern_pct = json_results['summary']['pattern_attack_success_rate']
    combined_pct = json_results['summary']['combined_success_rate']

    md.append(f"""
1. **Attack effectiveness**: The improved multi-strategy pattern attack cracked {len(cracked_passwords_set):,} 
   passwords ({pattern_pct}%), while spear phishing cracked {len(spear_cracked_set):,} ({spear_pct}%). 
   Combined, {len(all_cracked_set):,} unique passwords ({combined_pct}%) were vulnerable.

2. **Primary vulnerability classes**: Common dictionary words, personal names, digit-only sequences, 
   and keyboard patterns. These categories dominate the cracked set because the attack uses word 
   mutation (suffixes, leet speak, case variants), digit sequence generation, and keyboard pattern 
   dictionaries.

3. **Length matters**: Cracked passwords averaged {cracked_len_stats['mean']} characters vs 
   {uncracked_len_stats['mean']} for uncracked. Max cracked length was {cracked_len_stats['max']} characters.

4. **Charset diversity is critical**: Cracked passwords averaged {cracked_charset_stats['mean']:.1f} 
   character set(s) vs {uncracked_charset_stats['mean']:.1f} for uncracked. Adding digits, uppercase, 
   or special characters provides meaningful resistance against pattern-based attacks.

5. **Grading system validation**: The scoring system {"correctly" if cracked_score_stats['mean'] < uncracked_score_stats['mean'] else "did not correctly"} 
   assigned lower scores to cracked passwords (avg {cracked_score_stats['mean']} vs {uncracked_score_stats['mean']}). 
   The point-biserial correlation between score and survival was r={correlation}.

6. **Spear phishing vs pattern attack**: Spear phishing cracked {spear_pct}% using name-based 
   mutations with personal context, while the broader pattern attack cracked {pattern_pct}% using 
   dictionary words, digit sequences, keyboard patterns, Markov chains, and fuzzy matching.
""")

    # Write report
    report_text = "".join(md)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
