# Step 8: Attack simulation report

## Configuration

```json
{
  "target_file": "/Users/ryaneveson/Documents/GitHub/Password-Analysis-Project/100k-most-used-passwords-NCSC.txt",
  "english_words_sources": [
    "web2",
    "gcide"
  ],
  "base_word_count": 170739,
  "keyboard_patterns_enabled": true,
  "keyboard_headers_enabled": true,
  "dict_min_len": 3,
  "dict_max_len": 10,
  "guess_deduplication": false
}
```

## Results

- **N-gram model used:** False
- **Keyboard / numeric patterns:** True
- **Keyboard symbol headers (!, @, …):** True
- **English dictionary (`english-words`):** True
- **Attempts executed:** 303,872,160 (no cap; ran until stream ended)
- **Targets:** 99818 (NCSC list)
- **Cracked:** 30,446
- **Not cracked:** 69,372

### Cracked (password → attempt index)

_Full table: `step8_cracked_at_attempt.csv` (30,446 rows). First 25 by attempt:_

| Password | Attempt |
|---|---|
| `!` | 1 |
| `!!!!!!` | 355 |
| `@!@` | 383 |
| `!@#$%^` | 33,697 |
| `!@#$%^&*` | 44,065 |
| `!@#$%^&*(` | 49,249 |
| `!@#$%^&*()` | 54,433 |
| `@123456` | 59,725 |
| `&` | 69,985 |
| `&3` | 70,228 |
| `*123456` | 72,685 |
| `.` | 75,169 |
| `..` | 75,189 |
| `+.` | 75,191 |
| `...` | 77,781 |
| `....` | 80,373 |
| `.....` | 82,965 |
| `?` | 85,537 |
| `??` | 85,558 |
| `???` | 88,150 |
| `QWERTY` | 95,905 |
| `qwerty1234` | 95,932 |
| `qwerty12345` | 95,959 |
| `QWERTY123` | 95,986 |
| `QWERTY123456` | 96,013 |

### Not cracked (stream exhausted or cap reached)

_Full list: `step8_not_cracked.txt` (69,372 lines). Sample:_

- ``
- `!QAZ1qaz`
- `!QAZxsw2`
- `!ab#cd$`
- `!q`
- `!qaz1qaz`
- `!qaz2wsx`
- `!qazxsw2`
- `!qazzaq1`
- `!~!1`
- `$HEX`
- `$HEX[687474703a2f2f616473]`
- `$HEX[687474703a2f2f777777]`
- `$hex`
- `$money`
- _… and 69,357 more in file_

---

Keyboard / numeric / symbol patterns (with optional ! @ !@# … prefixes on each) × same tails, then `english_words` [web2,gcide] × rule/capped leet × password tails. No Step 4, spear, or n-gram streams. Guess deduplication is off (same candidate may be tried twice) to limit RAM; use --dedup-guesses to track uniques.
