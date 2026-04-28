# Password Analysis Report

**Data folder:** `C:\Users\rbeve\OneDrive\Desktop\Sem 2 Year 4\COSC 490\Password-Analysis-Project\data\archive`
**Total passwords:** 48,189,550

## STEP 2: General analysis

- **Length — mean:** 13.89, **std dev:** 5.37
- **Length — min:** 8, **max:** 32

### Top 20 most common lengths (length → count)

| Count | Length |
|------:|-------:|
| 9,531,283 | 9 |
| 8,904,054 | 12 |
| 7,232,774 | 24 |
| 3,260,173 | 13 |
| 3,252,886 | 11 |
| 2,872,820 | 15 |
| 2,808,306 | 10 |
| 2,622,855 | 8 |
| 2,551,912 | 14 |
| 1,552,602 | 16 |
| 1,090,988 | 18 |
| 1,079,436 | 17 |
| 508,602 | 19 |
| 443,650 | 32 |
| 378,927 | 20 |
| 48,754 | 28 |
| 9,543 | 21 |
| 8,306 | 22 |
| 7,336 | 23 |
| 6,452 | 25 |

## STEP 3: Password mask patterns (C=Cap, S=Special, L=Lower, D=Digit)

### Top 20 most frequent mask patterns

| Count | Mask |
|------:|------|
| 291,141 | C L L L L S D D D D |
| 197,636 | C L L L L L S D D D D |
| 189,177 | C L L L L L L S D D D D |
| 164,994 | C L L S D D D D D D D |
| 158,235 | C L L L L S D D |
| 147,985 | C L L L S D D D D |
| 134,879 | C L L L L L S D D |
| 129,128 | C L L S C L L L D D D D |
| 115,031 | D D D C L L S S S |
| 114,913 | D D D S S S C L L |
| 110,045 | C L L L L L L L S D D D D |
| 108,143 | C L L L L S C L D D D D |
| 105,736 | C L L S L L L L D D D D |
| 92,518 | L L L S C L L L D D D D |
| 90,698 | C L L L S C L L D D D D |
| 89,501 | C L L S L L L L L D D D D |
| 87,380 | D D D S D D C L L |
| 87,360 | D D D C L L S D D |
| 84,593 | C L L L S C L L L L D D D D |
| 83,457 | C L L L S C L L L D D D D |

---

**Output files:**
- `password_analysis_summary.csv` — summary metrics
- `password_analysis_lengths.csv` — full length counts
- `password_analysis_masks.csv` — full mask pattern counts
