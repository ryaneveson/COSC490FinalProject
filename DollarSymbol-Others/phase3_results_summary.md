# Phase 3

## What it adds

- `step7_password_creation.py`: harden weak passwords or combine elements into stronger ones
- `step8_attack_simulation.py`: dictionary and pattern-priority attacks
- `step9_final_analysis.py`: JSON/Markdown reporting for attack results
- `shared_constants.py`: shared constants used by Steps 4, 6, 7, and 8

## Verified results

| Check | Result |
|---|---|
| Step 7/8/9 CLI | `--help` works |
| Unit tests | `83` passed |
| QA harden scenario | `password123` reached grade `B` |
| QA combine scenario | `dragon,fire,2024` reached grade `B` |
| QA dictionary scenario | `dragon` cracked in `1,537` attempts |

## Common-password test

- **targets** = `100k-most-used-passwords-NCSC.txt`
- **dictionary** = Step 8 streamed dictionary attack using priority seeds + `english-words`
- file location = repo root
- under the `100000`-guess cap, the verified run stays within the priority-seed phase and the early raw `english-words` pass; later mutation-heavy passes remain available for larger caps

Result with dictionary mode and `--max-attempts 100000`:

- tested: `99,839`
- cracked: `12,212`
- failed: `87,627`
- priority seed words: `148`
- english-words entries: `234,450`
- dictionary stream mode: `True` (guesses generated on demand instead of prebuilding one list)

## Step 9 summary

- overall crack rate: `12.2%` (`12,212 / 99,839`)
- crack rate by length:
  - `<8`: `8,551 / 52,515` (`16.3%`)
  - `8-11`: `3,656 / 46,112` (`7.9%`)
  - `12-15`: `5 / 979` (`0.5%`)
  - `16+`: `0 / 233` (`0.0%`)
- pattern breakdown: `12,212` cracked passwords were reported as `unknown` in dictionary mode
- attempt stats across all tested targets: min `1`, max `100000`, mean `92212.6`, median `100000`
- grade analysis was not included in this run because no Step 6 grades file was provided

## Run tests

```bash
python3 -m pytest DollarSymbol-Others/tests/ -v
```

## Run Phase 3

### Harden one password

```bash
python3 DollarSymbol-Others/step7_password_creation.py \
  --mode harden \
  --password "password123" \
  --model DollarSymbol-Others/models/character_ngram_model.json \
  --target-grade B
```

### Combine user-chosen elements

```bash
python3 DollarSymbol-Others/step7_password_creation.py \
  --mode combine \
  --elements "dragon,fire,2024" \
  --model DollarSymbol-Others/models/character_ngram_model.json \
  --target-grade B
```

### Attack a target file

```bash
python3 DollarSymbol-Others/step8_attack_simulation.py \
  --mode dictionary \
  --target-file 100k-most-used-passwords-NCSC.txt \
  --max-attempts 100000 \
  --json-output /tmp/ncsc_targets_attack.json
```

### Generate the final report

```bash
python3 DollarSymbol-Others/step9_final_analysis.py \
  --attack-results /tmp/ncsc_targets_attack.json \
  --markdown-output /tmp/phase3_report.md
```
