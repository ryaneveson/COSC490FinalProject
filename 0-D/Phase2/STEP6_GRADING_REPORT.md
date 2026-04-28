# Step 6: Password Grading Report (0–D)

**Data source:** folders `0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D` under base archive.

## Executive Summary

- **Total Passwords Graded**: 48,189,550
- **Grade A+ (Excellent)**: 3 (0.00%)
- **Grade A (Very Strong)**: 7,638 (0.02%)
- **Grade B (Strong)**: 4,365,288 (9.06%)
- **Grade C (Fair)**: 24,563,188 (50.97%)
- **Grade D (Weak)**: 19,197,587 (39.84%)
- **Grade F (Very Weak)**: 55,846 (0.12%)

## Scoring Formula

```
raw = base_predictability + complexity_bonus
      - pattern_type_penalty - specific_pattern_penalty
final = clamp(0.9 * raw + 6.5, 0, 100)
```

| Component | Range | Description |
|-----------|-------|-------------|
| Base predictability | 0–50 | Inverse of n-gram predictability (less predictable = higher) |
| Complexity bonus | 0–50 | Length + char-class diversity + uniqueness ratio |
| Pattern type penalty | 0–12 | Scaled deduction: common types are not treated as near-max failure |
| Specific pattern penalty | 0–18 | Keyboard runs, weak words, repeated chars, etc. |

## Grade Scale

| Grade | Score Range | Label |
|-------|------------|-------|
| A+ | 90–100 | Excellent |
| A | 80–89 | Very Strong |
| B | 66–79 | Strong |
| C | 52–65 | Fair |
| D | 38–51 | Weak |
| F | 0–37 | Very Weak |

## Grade Distribution

| Grade | Count | % |
|-------|-------|---|
| A+ (Excellent) | 3 | 0.00% |
| A (Very Strong) | 7,638 | 0.02% |
| B (Strong) | 4,365,288 | 9.06% |
| C (Fair) | 24,563,188 | 50.97% |
| D (Weak) | 19,197,587 | 39.84% |
| F (Very Weak) | 55,846 | 0.12% |

## Score Distribution

| Score Range | Count | % |
|-------------|-------|---|
| 20–30 | 257 | 0.00% |
| 30–40 | 170,437 | 0.35% |
| 40–50 | 14,835,629 | 30.79% |
| 50–60 | 21,807,728 | 45.25% |
| 60–70 | 10,822,014 | 22.46% |
| 70–80 | 545,813 | 1.13% |
| 80–90 | 7,669 | 0.02% |
| 90–100 | 3 | 0.00% |

## Average Scoring Components

| Component | Average |
|-----------|--------|
| Base Predictability | +19.7725 |
| Complexity Bonus | +43.1917 |
| Pattern Type Penalty | −7.6231 |
| Specific Pattern Penalty | −1.7820 |

## Pattern Type Distribution

| Pattern Type | Count | % |
|-------------|-------|---|
| leet_speak | 20,942,050 | 43.46% |
| word_special_digit_mixed | 18,982,125 | 39.39% |
| keyboard_pattern | 7,430,028 | 15.42% |
| special_digit | 835,347 | 1.73% |

## Top Specific Penalty Reasons

| Reason | Count | % |
|--------|-------|---|
| keyboard patterns | 10,149,228 | 21.06% |
| sequential runs | 5,833,936 | 12.11% |
| trailing special char only | 3,834,740 | 7.96% |
| date pattern detected | 3,580,073 | 7.43% |
| repeated char groups | 1,334,111 | 2.77% |
| common weak word | 119,434 | 0.25% |

## Example Passwords by Grade

### Grade A

| Password | Score |
|----------|-------|
| `0!4^A+x($*P@i)8%` | 81.16 |
| `0!Fc*i/{sBVT(mO]uE#H` | 81.94 |
| `0!Go]D+>[,<m"` | 81.05 |
| `0!HWC{D~;u%{g` | 80.64 |
| `0!M@W}l$EZjy{iLh]e` | 80.74 |

### Grade A+

| Password | Score |
|----------|-------|
| `2ÔwH³Utµ§ÔÝ'OsÀß` | 93.26 |
| `aэtoУ}|{Еб6HЕвышрпyГ` | 93.26 |
| `cÁí6S¨‘á\\àŠ˜)Wq\\` | 93.26 |

### Grade B

| Password | Score |
|----------|-------|
| `0 Kn$tZZ%2p8` | 78.54 |
| `0!!11))^B$cD` | 66.40 |
| `0!!>t}On@b/-@` | 77.68 |
| `0!!eJ>!<'` | 66.65 |
| `0!!LffSAE%t|` | 72.91 |

### Grade C

| Password | Score |
|----------|-------|
| `0!!!VJvv` | 54.45 |
| `0!!$kK0z` | 57.78 |
| `0!!,Gx7q` | 65.50 |
| `0!!00VLg` | 55.39 |
| `0!!3qL`,` | 64.69 |

### Grade D

| Password | Score |
|----------|-------|
| `0!QAZ2wsx` | 44.65 |
| `0">Access` | 47.26 |
| `0"PLMNBVcx` | 51.85 |
| `0#4Me!!!` | 50.66 |
| `0#Mnbvcxz` | 43.33 |

### Grade F

| Password | Score |
|----------|-------|
| `0------Nb` | 37.70 |
| `0-=;lkJkl` | 37.92 |
| `0-=Aq1234` | 36.90 |
| `0-=Asdfds` | 36.63 |
| `0-=Asdfgh` | 37.83 |

