# Phase 2

## Summary

- Gave each password a base score from how predictable the transitions were: common/easy patterns score lower, unusual patterns score higher.
- Then it subtracts points for weak habits (common words, keyboard patterns like `asdf`, weak endings like `!` or `123`) and adds points for strength (longer length and mixed character types).
- Final score formula: **base predictability score - penalties + bonuses**.

## Procedure

### Step 5 internals

- Model: interpolated character n-gram with Laplace smoothing (`alpha=0.5`)
  - `P_uni = (count_uni + alpha) / (total_uni + alpha * |V|)`
  - `P_bi = (count_bi + alpha) / (total_bi + alpha * |V|)`
  - `P_tri = (count_tri + alpha) / (total_tri + alpha * |V|)`
  - `P(next|context) = 0.60 * P_tri + 0.30 * P_bi + 0.10 * P_uni`

### Step 6 internals

- Base predictability score:
  - Compute average surprisal over transitions: `avg = mean(-log2(P_t))`
  - Primary mapping (with Step 5 stats): `base = clip(35 + 11 * ((avg - mean) / std), 0, 70)`
  - Fallback mapping (if stats missing): `base = clip(((avg - 2.0) / 5.0) * 70.0, 0, 70)`
- Pattern penalties:
  - Pattern-type penalties (dictionary/l33t/keyboard/category), capped at 45
  - Specific-sequence penalties (`qwerty`, `asdf`, suffixes like `!`, `123`, etc.), capped at 30
- Complexity bonus:
  - Length + character-class diversity + uniqueness ratio, capped at 30
- Final scoring:
  - `final = clip(round(base - 0.90*pattern_type_penalty - 0.85*specific_penalty + 0.70*complexity_bonus), 0, 100)`
  - Grade map: `A >= 78`, `B >= 63`, `C >= 48`, `D >= 33`, else `F`

## Step 5: Probabilistic Prediction Model

- Model: character-level interpolated n-gram (unigram + bigram + trigram)
- Total transitions observed: **848,896,571**
- Smoothing: Laplace (`alpha=0.5`)

### Example next-character prediction (`context='Pass'`)

| Rank | Predicted token | Probability |
|---|---:|---:|
| 1 | `e` | 0.091550 |
| 2 | `i` | 0.088022 |
| 3 | `a` | 0.070711 |
| 4 | `<END>` | 0.058367 |
| 5 | `1` | 0.049288 |

## Step 6: Grading Results (Full Pass)

- Average score: **54.10 / 100**


### Grade distribution

| Grade | Count | Percent |
|---|---:|---:|
| A | 2,044,822 | 3.56% |
| B | 9,374,708 | 16.33% |
| C | 12,304,101 | 21.43% |
| D | 24,119,166 | 42.01% |
| F | 9,564,265 | 16.66% |

## Reproducibility

### 1) Train Step 5 model

```bash
python3 DollarSymbol-Others/step5_probabilistic_prediction.py \
  --base-dir data/archive \
  --output /tmp/password_ngram_model_full.json \
  --context Pass \
  --top 5 \
  --alpha 0.5
```

### 2) Grade one password with Step 6

```bash
python3 DollarSymbol-Others/step6_password_grading.py \
  --model /tmp/password_ngram_model_full.json \
  --password "Password123!" \
  --alpha 0.5
```

### 3) Grade a batch file with Step 6

```bash
python3 DollarSymbol-Others/step6_password_grading.py \
  --model /tmp/password_ngram_model_full.json \
  --input-file /path/to/passwords.txt \
  --alpha 0.5 \
  --json-output /tmp/grading_output.json
```

## Step 6 simplification (single grading path)

Phase 2 now uses one clean grading path:

- Step 5 always computes and stores `metadata.surprisal_stats` from a fixed 200,000-password sample.
- Step 6 always grades with the same non-synthetic `natural_raw` formula.
- No profile switching and no distribution-shaping modes.

### Current Step 6 internals (simplified)

- Base predictability score:
  - Compute `avg = mean(-log2(P_t))`
  - If Step 5 metadata includes surprisal stats:
    - `z = (avg - mean_surprisal) / std_surprisal`
    - `base = clip(35 + 11*z, 0, 70)`
  - Fallback if stats missing:
    - `base = clip(((avg - 2.0) / 5.0) * 70.0, 0, 70)`
- Final score:
  - `final = clip(round(base - 0.90*pattern_penalty - 0.85*specific_penalty + 0.70*complexity_bonus), 0, 100)`
- Grade map:
  - `A >= 78`, `B >= 63`, `C >= 48`, `D >= 33`, else `F`

### Validation snapshots (raw only, no shaping)

| Input batch | Mean | Grade distribution |
|---|---:|---|
| mixed 125,354 sample | 73.82 | A 40.00% · B 49.17% · C 6.14% · D 4.47% · F 0.22% |
| 200,000 DollarSymbol sample | 51.95 | A 1.37% · B 22.72% · C 41.74% · D 32.38% · F 1.79% |

### Simplified commands

Train Step 5 model:

```bash
python3 DollarSymbol-Others/step5_probabilistic_prediction.py \
  --base-dir data/archive \
  --output /tmp/password_model_simplified.json \
  --alpha 0.5
```

Grade one password:

```bash
python3 DollarSymbol-Others/step6_password_grading.py \
  --model /tmp/password_model_simplified.json \
  --password "Password123!" \
  --alpha 0.5
```

Grade a batch file:

```bash
python3 DollarSymbol-Others/step6_password_grading.py \
  --model /tmp/password_model_simplified.json \
  --input-file /path/to/passwords.txt \
  --alpha 0.5 \
  --json-output /tmp/grading_output.json
```
