# Step 4: Semantic Decomposition Report (0–D)

**Data source:** folders `0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D` under base archive.

## Executive Summary

- **Total Passwords Analyzed**: 48,189,550
- **Dictionary Used**: english-words library (234,450 words)
- **Dictionary Matches**: 18,982,125 (39.39%)
- **L33t Speak Detected**: 3,414,735 (7.09%)
- **Keyboard Patterns**: 10,149,228 (21.06%)

## Top 20 Matched Dictionary Words

| Rank | Word | Count |
|------|------|-------|
| 1 | marie | 710,948 |
| 2 | anne | 649,350 |
| 3 | de | 642,862 |
| 4 | bo | 569,712 |
| 5 | ann | 366,800 |
| 6 | as | 346,975 |
| 7 | anna | 337,499 |
| 8 | go | 324,825 |
| 9 | ae | 283,167 |
| 10 | splat | 272,553 |
| 11 | po | 258,503 |
| 12 | chi | 251,323 |
| 13 | jean | 244,223 |
| 14 | lo | 233,471 |
| 15 | di | 223,917 |
| 16 | sa | 211,519 |
| 17 | al | 209,207 |
| 18 | ed | 186,779 |
| 19 | on | 181,794 |
| 20 | ben | 174,479 |

## L33t Speak Examples

- `0!!,Gx7q` → words: oii
- `0!!]jZ0%` → words: oii
- `0!%&j2X1` → words: xi
- `0!*EXIATtence*!0` → words: io
- `0!+/"S3y` → words: sey
- `0!,0R^nC` → words: or
- `0!/+0W%p` → words: tow
- `0!0Lq.J0` → words: jo
- `0!128c3U` → words: oii
- `0!1_8HNOjpSt` → words: oii
- `0!1l$?M!` → words: mi
- `0!61d6G2` → words: id
- `0!;+0%Jd` → words: to
- `0!=1O\4z` → words: io
- `0!=rS%p@>]` → words: pa

## Keyboard Pattern Examples

- `0!@!qAzXsw`
- `0!@!qAzxsw`
- `0!@!qAZxsw`
- `0!@!qaZxsw`
- `0!@!QaZxSW`
- `0!@!qazXsw`
- `0!@!QAZxSW`
- `0!@!QaZXSW`
- `0!AF*VCx`
- `0!BvcioV`
- `0!H2tGy0`
- `0!ic)rFv`
- `0!JEseRT7`
- `0!Q_Cvbo`
- `0!QAZ2wsx`

## Pattern Type Ranking (Most → Least Predictable)

| Rank | Pattern Type | Count | % |
|------|---------------|-------|-----|
| 1 | leet_speak | 20,942,050 | 43.46% |
| 2 | word_special_digit_mixed | 18,982,125 | 39.39% |
| 3 | keyboard_pattern | 7,430,028 | 15.42% |
| 4 | special_digit | 835,347 | 1.73% |

## Tools Used

- **Dictionary Lookup**: english-words library
- **POS Tagging**: spaCy (en_core_web_sm) + NLTK WordNet
- **Semantic Analysis**: WordNet definitions

## Part-of-Speech Classification

### PROPER NOUN
Occurrences: 11467209

- **marie**: 710,948
- **anne**: 649,350 — *Queen of England and Scotland and Ireland; daughter if James II and the last of the Stuart monarchs; in 1707 she was the last English ruler to exercise the royal veto over parliament (1665-1714)*
- **ann**: 366,800
- **anna**: 337,499
- **chi**: 251,323
- **jean**: 244,223
- **sa**: 211,519
- **al**: 209,207
- **ed**: 186,779
- **ben**: 174,479

### NOUN
Occurrences: 6164047

- **de**: 642,862 — *a Mid-Atlantic state; one of the original 13 colonies*
- **po**: 258,503 — *a radioactive metallic element that is similar to tellurium and bismuth; occurs in uranium ores but can be produced by bombarding bismuth with neutrons in a nuclear reactor*
- **ca**: 174,267 — *a white metallic element that burns with a brilliant light; the fifth most abundant element in the earth's crust; an important component of most plants and animals*
- **gol**: 153,744
- **diane**: 146,559
- **dee**: 134,281
- **bat**: 118,920
- **claude**: 111,110
- **fa**: 103,930
- **es**: 93,646

### VERB
Occurrences: 2808925

- **go**: 324,825 — *a time for working (after which you will be relieved by someone else)*
- **ae**: 283,167
- **lo**: 233,471
- **ai**: 126,912
- **ba**: 89,866
- **is**: 70,657
- **ga**: 68,853
- **cho**: 62,170
- **gi**: 55,546
- **en**: 51,782

### ADPOSITION
Occurrences: 1814018

- **bo**: 569,712
- **as**: 346,975 — *a very poisonous metallic element that has three allotropic forms; arsenic and arsenic compounds are used as herbicides and insecticides and various alloys; found in arsenopyrite and orpiment and realgar*
- **on**: 181,794 — *in operation or operational*
- **og**: 149,097
- **in**: 106,392
- **by**: 99,020
- **at**: 76,835
- **na**: 70,227
- **ta**: 55,078
- **te**: 49,988

### ADJECTIVE
Occurrences: 893003

- **splat**: 272,553 — *a single splash*
- **wert**: 27,564
- **pro**: 21,607 — *an athlete who plays for pay*
- **big**: 20,261
- **black**: 19,505
- **crazy**: 17,645
- **olivier**: 15,996
- **abe**: 14,941
- **dead**: 14,111
- **ant**: 11,648

### ADVERB
Occurrences: 630289

- **out**: 88,599 — *(baseball) a failure by a batter or runner to reach a base safely in baseball*
- **os**: 57,643 — *a mouth or mouthlike opening*
- **ar**: 50,460 — *a colorless and odorless inert gas; one of the six inert gases; comprises approximately 1% of the earth's atmosphere*
- **so**: 42,566
- **ow**: 27,019
- **long**: 21,110
- **om**: 17,481
- **pu**: 16,307
- **ug**: 15,489
- **cal**: 15,046

### INTERJECTION
Occurrences: 539315

- **er**: 69,815 — *a trivalent metallic element of the rare earth group; occurs with yttrium*
- **ti**: 59,863 — *a light strong grey lustrous corrosion-resistant metallic element used in strong lightweight alloys (as for airplane parts); the main sources are rutile and ilmenite*
- **da**: 58,487 — *an official prosecutor for a judicial district*
- **oe**: 54,413
- **bu**: 40,479
- **aw**: 37,319
- **ah**: 34,061
- **la**: 30,331
- **ha**: 19,245
- **ni**: 18,768

### PRONOUN
Occurrences: 428551

- **an**: 129,265 — *an associate degree in nursing*
- **it**: 57,770 — *the branch of engineering that deals with the use of computers and telecommunications to retrieve and store and transmit information*
- **me**: 38,449 — *a state in New England*
- **ya**: 32,961
- **id**: 26,037
- **us**: 17,561
- **he**: 16,304
- **em**: 15,717
- **my**: 13,982
- **all**: 12,207

### UNKNOWN
Occurrences: 365601

- **di**: 223,917
- **to**: 52,473
- **wo**: 28,397
- **nicolas**: 19,184
- **ye**: 9,434
- **vu**: 8,196
- **yn**: 7,829
- **bon**: 4,521
- **sai**: 4,085
- **augustin**: 1,885

### CONJUNCTION
Occurrences: 75557

- **or**: 58,422 — *a state in northwestern United States on the Pacific*
- **and**: 11,431
- **but**: 4,209 — *and nothing more*
- **nor**: 960
- **plus**: 535

### SUBORDINATING CONJUNCTION
Occurrences: 12829

- **if**: 10,623
- **how**: 711
- **because**: 498
- **why**: 343
- **that**: 228
- **till**: 189
- **since**: 107
- **when**: 44
- **where**: 40
- **upon**: 16

### NUMBER
Occurrences: 11943

- **one**: 3,756 — *the smallest whole number or a numeral representing this number*
- **ten**: 1,234 — *the cardinal number that is the sum of nine and one; the base of the decimal system*
- **six**: 850 — *the cardinal number that is the sum of five and one*
- **dispatcher**: 727
- **two**: 711
- **zero**: 613
- **million**: 554
- **billion**: 313
- **seven**: 300
- **aileen**: 300

### DETERMINER
Occurrences: 21

- **whose**: 21

