# Implementation Comparison Report

## Overview

This document compares the main implementation tracks currently present on the `Demo-g1` branch:

- `DollarSymbol-Others`
- `P_Z`
- `0-D`
- `Phong_newdata`

The goal is to support the final presentation by clearly showing what the teams did similarly, what they did differently, and what results each track produced.

---

## How to Read This Report

These tracks are not all direct replacements for one another.

- `DollarSymbol-Others` is a polished end-to-end pipeline with strong CLI workflow and testing.
- `P_Z` is a structured analysis-heavy track, especially strong in Phases 1 and 2.
- `0-D` is a strong technical branch with full Step 5-8 coverage and the most aggressive raw attack run.
- `Phong_newdata` is a newer end-to-end track built around the NCSC 100k password file, including Step 8 and Step 9.

Because the data scope and attack settings differ between tracks, some numeric results are **directionally useful** but not perfectly apples-to-apples.

---

## Implementation Coverage Summary

| Track | Step 2 | Step 3 | Step 4 | Step 5 | Step 6 | Step 7 | Step 8 | Step 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `DollarSymbol-Others` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| `P_Z` | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| `0-D` | No standalone Step 2 | No standalone Step 3 | Yes | Yes | Yes | Yes | Yes | No |
| `Phong_newdata` | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

### Key takeaway

- The most complete end-to-end tracks are `DollarSymbol-Others` and `Phong_newdata`.
- `P_Z` is complete through Step 7.
- `0-D` is strongest from Step 4 through Step 8, but does not finish with a dedicated Step 9 script.

---

## Similarities Across Implementations

Despite structural differences, the tracks converge on the same core ideas.

### Shared goals

All tracks follow the same high-level pipeline:

1. Analyze password structure and semantics
2. Build a character-level predictability model
3. Grade passwords using predictability plus pattern penalties
4. Generate stronger passwords by avoiding weak patterns
5. Simulate attacks using known weak structures
6. Use attack results to explain vulnerability

### Shared technical ideas

Across the repo, the following ideas appear repeatedly:

- **Mask-based analysis** using `C / L / D / S`
- **Dictionary lookup** using the `english-words` package
- **L33t normalization / detection**
- **Keyboard pattern detection** such as `qwerty`, `asdf`, and numeric runs
- **Character-level n-gram modeling** for predictability
- **Grading with penalties and bonuses** rather than pure length checking
- **Password generation informed by prior analysis**
- **Attack simulation focused on common words, mutations, and predictable patterns**

### Shared security conclusion

All tracks reinforce the same main finding:

> Password weakness is driven more by **predictable structure and common words** than by length alone.

---

## High-Level Differences by Track

| Track | Main style | Biggest strength | Main limitation |
|---|---|---|---|
| `DollarSymbol-Others` | Modular, script-oriented, CLI-friendly | Best polished pipeline and strongest testing story | Attack run is more conservative because of the 100k-attempt cap in the reported result |
| `P_Z` | Class-based, analysis-heavy | Strongest Phase 1 and Phase 2 explanatory structure | Main folder stops before Step 8 and Step 9 |
| `0-D` | Technical, class-based, aggressive attack focus | Strongest raw Step 8 cracking result | No dedicated Step 9 script |
| `Phong_newdata` | Class-based, end-to-end experiment on NCSC 100k | Best attack-to-grading validation story | Uses a smaller, focused common-password dataset rather than the larger partitioned corpora |

---

## Phase 1 Comparison: Structural Analysis

Phase 1 includes Step 2 (general analysis), Step 3 (mask patterns), and Step 4 (semantic decomposition).

### Similarities

- All Phase 1 implementations aim to identify common password structure before any grading or attacks are attempted.
- Every track that implements Step 4 uses dictionary-based semantic analysis and pattern categorization.
- The implementations consistently treat semantic information as downstream input for both grading and attacks.

### Differences

#### `DollarSymbol-Others`

- Uses a **functional, lightweight** approach.
- Step 2 and Step 3 operate with simple iterator-style scripts.
- Step 4 is intentionally simpler and more modular through `shared_constants.py`.

This track is easiest to explain as a pipeline of small scripts with clear responsibilities.

#### `P_Z`

- Uses **class-based analysis** (`PasswordGeneralAnalysis`, `PasswordMaskAnalyzer`, `SemanticDecompositionAnalyzer`).
- Step 2 and Step 3 go deeper into **distribution analysis**, **category breakdown**, and **complexity statistics**.
- Step 4 is a full NLP-oriented implementation using **spaCy + NLTK + WordNet**.

This track is strongest if the presentation wants to emphasize formal analysis and richer interpretation.

#### `0-D`

- In Phase 1, the visible implementation is mainly **Step 4**.
- That Step 4 follows the same deeper NLP-oriented style as the class-based semantic analyzers elsewhere.

This makes `0-D` less complete in early-phase reporting, but still aligned with the project’s semantic-analysis direction.

#### `Phong_newdata`

- Architecturally closest to `P_Z`, but applied to the **NCSC 100k password dataset**.
- In the NCSC 100k dataset specifically, Step 4 produces a very presentation-friendly pattern ranking:
  - `word_digit`: 41.99%
  - `word_only`: 33.48%
  - `leet_speak`: 20.32%
  - `keyboard_pattern`: 2.35%

This track is useful because the outputs are easy to connect to real common-password behavior.

### Best presentation point for Phase 1

Use this phase to show that all teams converged on the same insight:

> Common passwords are not random. They cluster into recurring structures: dictionary words, words plus digits, l33t variants, and keyboard walks.

---

## Phase 2 Comparison: Predictability and Grading

Phase 2 includes Step 5 (probabilistic prediction) and Step 6 (grading).

### Similarities

- All tracks use a **character-level n-gram idea**.
- All tracks translate model output into a password score.
- All tracks include **complexity bonuses** and **pattern penalties**.
- All tracks attempt to penalize specific weak substrings like `password`, `asdf`, `qwerty`, and numeric suffixes.

### Differences in Step 5

| Track | Step 5 approach |
|---|---|
| `DollarSymbol-Others` | Interpolated n-gram with **0.60 trigram + 0.30 bigram + 0.10 unigram**, Laplace `alpha=0.5`, plus surprisal statistics for later grading calibration |
| `P_Z` | Interpolated n-gram with **0.40 bigram + 0.60 trigram**, class-based implementation, large-scale corpus analysis |
| `0-D` | Similar bigram/trigram blended model, also class-based, with explicit start/end-token style reporting |
| `Phong_newdata` | Same overall interpolation family as `P_Z`, but trained on the **100k NCSC** set rather than a huge partitioned corpus |

#### Important interpretation

- These weight differences reflect design choices about context window versus smoothing, not a simple quality ranking.
- `P_Z` and `0-D` model larger, more structured corpora.
- `Phong_newdata` models a smaller, very common-password-heavy dataset, which is why it reports extremely low predictability scores for most entries.
- Because `Phong_newdata` is trained on a curated common-password set rather than the larger partitioned corpora, its Step 5 predictability scores should not be compared directly to the scores from the other tracks.
- `DollarSymbol-Others` is the only one that explicitly carries **surprisal statistics forward** for a calibrated Step 6 formula.

### Differences in Step 6

| Track | Step 6 scoring style |
|---|---|
| `DollarSymbol-Others` | Most calibrated formula: `base - 0.90*pattern - 0.85*specific + 0.70*bonus` |
| `P_Z` | Most straightforward formula: `base + bonus - penalties` |
| `0-D` | Gentle calibration after raw scoring: `final = clamp(0.9 * raw + 6.5, 0, 100)` |
| `Phong_newdata` | Similar additive style to `P_Z`, but tuned against a common-password dataset |

### Reported results

#### `DollarSymbol-Others`

- Average score: **54.10 / 100**
- Grade distribution in reported full pass:
  - A: 3.56%
  - B: 16.33%
  - C: 21.43%
  - D: 42.01%
  - F: 16.66%

#### `P_Z`

- Strong explanatory report, especially around pattern penalties and score breakdown.
- Example grading emphasizes a transparent decomposition of score components.

#### `0-D`

- Grade distribution is heavily centered in the middle:
  - A+: 0.00%
  - A: 0.02%
  - B: 9.06%
  - C: 50.97%
  - D: 39.84%
  - F: 0.12%

This suggests a smoother, more compressed grading curve than the more punitive or more polarized alternatives.

#### `Phong_newdata`

- Uses the same general grading logic as `P_Z`, but with a common-password-heavy dataset.
- Bottom-ranked passwords include short names and name+digit combinations such as `john`, `alex123`, and `mike123`.

### Best presentation point for Phase 2

Use this phase to compare **how each team turned analysis into a score**.

Suggested framing for presentation purposes:

- `DollarSymbol-Others` = most calibrated
- `P_Z` = most interpretable
- `0-D` = most gently normalized
- `Phong_newdata` = most tightly aligned with common-password behavior

---

## Phase 3 Comparison: Generation, Attack, and Final Analysis

Phase 3 includes Step 7 (generation), Step 8 (attack simulation), and Step 9 (final analysis).

### Step 7 – Password Generation

#### Similarities

- All three main generation tracks try to avoid patterns learned in earlier phases.
- All use Step 6 grading as a quality filter.
- All aim to generate passwords that are not just long, but structurally less predictable.

#### Differences

| Track | Step 7 style |
|---|---|
| `DollarSymbol-Others` | Most user-facing: **harden** an existing password or **combine** chosen elements |
| `P_Z` | Multiprocessing generator with pattern avoidance and complexity insertion |
| `0-D` | Hardening plus secure-random fallback if the seed stays weak |
| `Phong_newdata` | Defensive generator with pre-screening for names, weak affixes, repeated chars, and keyboard patterns |

#### Reported generation examples

- `P_Z`: generated `|sDS6t|'zMgTuphg` with score **80.25**
- `Phong_newdata`: generated `miEeh2PE=?_HOO{yac6%` with score **90.46**
- `DollarSymbol-Others`: verified hardening and combine workflows both reached grade **B** in QA

### Step 8 – Attack Simulation

This is where the tracks diverge the most.

> ⚠️ **Important caveat:** the Step 8 results below are **not directly comparable** across tracks. The reported runs use different datasets, different guess-generation strategies, and very different attempt budgets. These numbers are best used to explain each track’s attack style, not to declare a single winner.

#### `DollarSymbol-Others`

- Uses a **priority-seed + dictionary stream** model.
- Combines ranked pattern seeds with `english-words`.
- Reported run uses a **100,000-attempt cap**.
- Reported result: **12,212 / 99,839 cracked (12.2%)**.

This is the most conservative and controlled attack setup among the complete tracks.

#### `P_Z`

- No Step 8 in the main `P_Z` folder.
- For presentation purposes, this is the cleanest place to say that the main `P_Z` branch specializes in analysis and grading rather than a full final attack pipeline.

#### `0-D`

- Implements a broad attack engine with keyboard, numeric, symbol, and dictionary-driven guesses.
- Reported run had **no cap** and executed **303,872,160 attempts**.
- Result: **30,446 / 99,818 cracked (30.5%)**.

This is the highest reported crack rate under an effectively unlimited-attempt run in the repo, but it is also the least directly comparable to the capped `DollarSymbol-Others` run.

#### `Phong_newdata`

- Most sophisticated final attack setup in terms of attack variety.
- Includes:
  - pattern-based guesses
  - spear-phishing guesses
  - leet variants
  - digit-sequence mutations
  - Markov/learned guess generation
- Step 9 reports:
  - pattern attack cracked **27,393**
  - spear-phishing cracked **11,010**
  - combined cracked **29,897 / 99,839 (29.95%)**

This makes `Phong_newdata` the strongest track for demonstrating multiple attack styles instead of only one dictionary stream.

### Step 9 – Final Analysis

#### `DollarSymbol-Others`

- Full reporting pipeline exists.
- Reported findings:
  - overall crack rate: **12.2%**
  - `<8` chars: **16.3%** crack rate
  - `8-11` chars: **7.9%**
  - `12-15` chars: **0.5%**
  - `16+` chars: **0.0%**

This track gives the clearest “length matters” story under a conservative attack budget.

#### `0-D`

- No dedicated Step 9 script.
- Step 8 report still gives useful findings, but lacks the same final cross-analysis layer.

#### `Phong_newdata`

- Strongest end-to-end **directional validation** story.
- Final report explicitly ties cracking results back to Step 6 grades.
- Reported findings include:
  - combined success rate: **29.95%**
  - cracked mean score: **33.75**
  - uncracked mean score: **37.66**

This is especially useful in presentation because it shows the grading system was not just designed, but directionally checked against real attack outcomes. The score gap is modest, so it supports the grading logic without proving strong separation.

### Best presentation point for Phase 3

Use this phase to show that the project moves from analysis into offensive validation.

The cleanest contrast is:

- `DollarSymbol-Others` = polished and controlled
- `0-D` = strongest raw cracking pressure
- `Phong_newdata` = strongest end-to-end experimental validation

---

## Most Important Cross-Track Similarities

If the presentation needs a short “what we all learned” section, these are the strongest common findings:

1. **Dictionary words remain central**
   - Pure words and word+digit combinations appear repeatedly across semantic reports and attack results.

2. **Predictability matters more than complexity theater**
   - A password with uppercase, digits, and symbols can still be weak if it follows common structure.

3. **Keyboard and sequence patterns are consistently exploitable**
   - `qwerty`, `asdf`, `123456`, and related runs appear in both grading penalties and attack logic.

4. **Generation and attack are tightly linked**
   - The same Phase 1 and Phase 2 insights used to generate strong passwords can also be used to crack weak ones.

5. **Grading improves when informed by real patterns**
   - The best graders are not purely entropy-based; they combine predictability with semantic and structural penalties.

---

## Most Important Cross-Track Differences

These are the strongest “what we did differently” points.

1. **Dataset choice**
   - Large partitioned corpora (`DollarSymbol-Others`, `P_Z`, `0-D`) produce different distributions than the focused NCSC 100k approach (`Phong_newdata`).

2. **Engineering style**
   - `DollarSymbol-Others` favors modular scripts.
   - `P_Z` and `Phong_newdata` favor class-based analyzers.
   - `0-D` mixes analysis classes with a more attack-heavy technical style.

3. **Scoring philosophy**
   - Some tracks emphasize **calibration** (`DollarSymbol-Others`, `0-D`).
   - Others emphasize **transparent additive scoring** (`P_Z`, `Phong_newdata`).

4. **Attack philosophy**
   - `DollarSymbol-Others` reports a capped, controlled dictionary stream.
   - `0-D` reports an uncapped, high-volume attack.
   - `Phong_newdata` combines pattern-based and spear-phishing strategies.

5. **End-of-pipeline completeness**
   - `DollarSymbol-Others` and `Phong_newdata` close the loop with Step 9.
   - `P_Z` and `0-D` are stronger in selected parts of the pipeline than in final integrated reporting.

---

## Recommended Presentation Framing

The cleanest presentation structure is not “which one is best,” but rather “what each track contributed.”

### Suggested framing

- **`DollarSymbol-Others`** contributed the most polished full workflow and strongest test/CLI story.
- **`P_Z`** contributed the clearest formal analysis for Phases 1 and 2.
- **`0-D`** contributed the strongest raw attack pressure and an aggressive cracking benchmark.
- **`Phong_newdata`** contributed the strongest attack-to-grading validation on a common-password dataset.

### Suggested one-line summary per track

- `DollarSymbol-Others`: **practical security pipeline**
- `P_Z`: **structured analytical model**
- `0-D`: **high-pressure attack branch**
- `Phong_newdata`: **validated end-to-end experiment**

---

## Final Conclusion

The repo does not show four completely unrelated implementations. Instead, it shows four variations on the same core idea.

All tracks agree that weak passwords are usually weak for predictable reasons:

- common words
- common suffixes
- keyboard walks
- digit runs
- reusable structural templates

The main differences are in **how deeply each track analyzes**, **how it calibrates scores**, and **how aggressive the attack simulation is**.

For the final presentation, the strongest unified conclusion is:

> Password security is not just about adding more character types. Real strength comes from avoiding common semantic content, common structural templates, and highly predictable character transitions.
