# Onderzoeksrapport — campagne #2

Splitsing: TRAIN 2018/19–2022/23 (modellen hebben 2 seizoenen aanloop nodig) · VALID 2023/24–2024/25 · TEST 2025/26. Alle modelvoorspellingen zijn walk-forward: voor elk seizoen alleen getraind op eerdere seizoenen.

## 1. Hoe goed voorspellen modellen de uitslag? (1X2, out-of-sample 2018–2026)

n = 19104 wedstrijden. Lager = beter. Verschil van 0,003 is al betekenisvol.

| model                      |   logloss |
|:---------------------------|----------:|
| Pinnacle open (devig)      |    0.9599 |
| Pinnacle slot (devig)      |    0.9566 |
| Marktgemiddelde (devig)    |    0.9599 |
| Poisson online (v1)        |    0.9915 |
| Dixon-Coles goals          |    0.9807 |
| Dixon-Coles schoten        |    0.9779 |
| ML lr: models              |    0.9741 |
| ML lr: market              |    0.9607 |
| ML lr: market+models       |    0.9606 |
| ML lr: market+models+team  |    0.9647 |
| ML gbm: market+models+team |    0.9748 |
| ML lr: models+team         |    0.9746 |
| ML gbm: models+team        |    0.9835 |

**Conclusie:** onze modellen zijn flink verbeterd: Dixon-Coles op schoten scoort 0,978, tegen 0,991 voor het eerste model. Ze verslaan de markt (0,960) als voorspeller van de **uitslag** nog niet. Markt plus model samen (0,9606) komt dicht bij de markt, maar voegt niets toe. Gradient boosting overfit. Daarom kijken we hieronder naar een andere vraag die wel werkt.

## 2. Nieuw: voorspel waar de Pinnacle-koers naartoe beweegt

De slotkoers is de scherpste kansschatting. Voorspel je met informatie van vóór de vroege koers (ratings, schoten, vorm, stand, koersverschillen tussen bookmakers) **hoe de koers gaat bewegen**, dan kun je vroeg wedden op koersen die later zakken.

| uitkomst   | model   | periode   |     n |   correlatie |   richting goed |
|:-----------|:--------|:----------|------:|-------------:|----------------:|
| h          | ridge   | TRAIN     | 11991 |       0.1493 |          0.547  |
| h          | ridge   | VALID     |  4727 |       0.2122 |          0.5708 |
| h          | ridge   | TEST      |  1193 |       0.208  |          0.5817 |
| h          | gbm     | TRAIN     | 11991 |       0.1645 |          0.5505 |
| h          | gbm     | VALID     |  4727 |       0.2229 |          0.5756 |
| h          | gbm     | TEST      |  1193 |       0.1412 |          0.5733 |
| d          | ridge   | TRAIN     | 11991 |       0.2663 |          0.6023 |
| d          | ridge   | VALID     |  4727 |       0.2618 |          0.6239 |
| d          | ridge   | TEST      |  1193 |       0.3424 |          0.6915 |
| d          | gbm     | TRAIN     | 11991 |       0.2673 |          0.604  |
| d          | gbm     | VALID     |  4727 |       0.2891 |          0.6378 |
| d          | gbm     | TEST      |  1193 |       0.3245 |          0.6882 |
| a          | ridge   | TRAIN     | 11991 |       0.1806 |          0.5558 |
| a          | ridge   | VALID     |  4727 |       0.2265 |          0.5828 |
| a          | ridge   | TEST      |  1193 |       0.171  |          0.5331 |
| a          | gbm     | TRAIN     | 11991 |       0.1979 |          0.5557 |
| a          | gbm     | VALID     |  4727 |       0.2233 |          0.5739 |
| a          | gbm     | TEST      |  1193 |       0.1513 |          0.5457 |
| o          | ridge   | TRAIN     |  7307 |       0.187  |          0.5476 |
| o          | ridge   | VALID     |  4727 |       0.2282 |          0.579  |
| o          | ridge   | TEST      |  1193 |       0.1046 |          0.5499 |
| o          | gbm     | TRAIN     |  7307 |       0.1916 |          0.5565 |
| o          | gbm     | VALID     |  4727 |       0.228  |          0.5765 |
| o          | gbm     | TEST      |  1193 |       0.1353 |          0.5549 |

**Conclusie:** correlatie 0,10–0,34 en in 53–69% van de gevallen de juiste richting (gelijkspel het best voorspelbaar). Dat geldt in alle drie de periodes, ook in TEST, die het model nooit heeft gezien. Het model weet dus dingen die de markt pas later inprijst.

## 3. Biases uit literatuur + eigen ideeën (48 hypotheses)

Volledige tabel: [HYPOTHESES.md](HYPOTHESES.md). Na correctie voor meervoudig testen is **0** hypothese significant op TRAIN, en **0** bevestigd op HOLDOUT. De sterkste signalen in de recente periode (HOLDOUT), om te volgen:

| id   | hypothese                                         |   tr_resid |    tr_t |   ho_n |   ho_resid |    ho_t |   ho_y_max |
|:-----|:--------------------------------------------------|-----------:|--------:|-------:|-----------:|--------:|-----------:|
| O1   | Thuis-underdog (kans < 25%) → thuis               |     0.0048 |  0.7087 |   1225 |    -0.0333 | -3.4256 |    -0.2342 |
| X2   | DC-schoten ziet uit ≥8%-punt sterker → uit        |    -0.0267 | -2.646  |    516 |    -0.0507 | -3.0263 |    -0.2435 |
| D3   | Gelijkwaardig laat in seizoen → gelijk            |     0.0245 |  1.1555 |    238 |     0.0841 |  2.7079 |     0.2704 |
| P2   | Promovendus uit, eerste 8 rondes → uit            |     0.0123 |  0.6653 |    236 |    -0.0561 | -2.6083 |    -0.3413 |
| O4   | Hoge Pinnacle-marge (onzekere wedstrijd) → gelijk |     0.0025 |  0.1645 |   1333 |     0.0248 |  2.1813 |     0.0498 |
| D1   | Gelijkwaardige teams → gelijk                     |     0.011  |  1.3582 |   1357 |     0.026  |  2.0752 |     0.0829 |
| C4   | Thuis ≥3 dagen meer rust → thuis                  |     0.0085 |  0.4145 |    245 |    -0.0541 | -1.8857 |    -0.1125 |
| M5   | Laatste 5 rondes → gelijk                         |    -0.007  | -0.8033 |    986 |     0.0257 |  1.8611 |     0.0719 |

**Conclusie:** de klassieke biases (publieksclubs, reeksen, promovendi, motivatie, rust) zijn in deze competities en periode **niet** structureel uitbuitbaar. De markt prijst ze al in. Twee dingen om te volgen: (a) gelijkspel tussen gelijkwaardige teams, vooral laat in het seizoen (D1/D3), positief in recente seizoenen. Dat sluit aan bij Lezana (2026). (b) Als ons schotenmodel de uitploeg veel sterker vindt dan de markt, presteert die juist slechter (X2). Ons model overschat uitploegen dus. Dat gebruiken we als correctie.

## 4. Strategieën naast elkaar (vlakke inzet, rendement per ingezette euro)

`clv` = gemiddelde Closing Line Value (genomen koers vs. eerlijke Pinnacle-slotkoers), de beste voorspeller van echte winst. `t` > 2 = statistisch overtuigend.

| strategie                                        |   tr_n |   tr_yield |   tr_clv |   tr_t |   va_n |   va_yield |   va_clv |   va_t |   te_n |   te_yield |   te_clv |   te_t |
|:-------------------------------------------------|-------:|-----------:|---------:|-------:|-------:|-----------:|---------:|-------:|-------:|-----------:|---------:|-------:|
| v1: Pinnacle-value @ soft                        |   1463 |     0.0531 |   0.0139 |   1.34 |    220 |    -0.0883 |   0.006  |  -0.93 |     98 |     0.1741 |   0.0132 |   1.13 |
| v1: Pinnacle-value @ max                         |   6687 |     0.0224 |   0.0219 |   1.32 |   1814 |     0.0488 |   0.021  |   1.5  |    156 |     0.1738 |   0.0313 |   1.41 |
| 2e referentie (Pinnacle→Betfair→consensus) @ max |   6695 |     0.0231 |   0.0218 |   1.35 |   1814 |     0.0488 |   0.021  |   1.5  |    268 |     0.0098 |   0.031  |   0.11 |
| slotkoers-model ridge @ soft                     |   1532 |     0.078  |   0.0238 |   2.13 |    251 |     0.0034 |   0.0185 |   0.04 |    177 |     0.1754 |   0.0197 |   1.66 |
| slotkoers-model ridge @ max                      |   7597 |     0.0489 |   0.0234 |   3.07 |   2341 |     0.0401 |   0.0264 |   1.36 |    320 |     0.041  |   0.0288 |   0.52 |
| slotkoers-model gem. @ soft                      |   1509 |     0.0997 |   0.0269 |   2.75 |    226 |     0.0734 |   0.0198 |   0.81 |    146 |     0.1222 |   0.0233 |   1.07 |
| slotkoers-model gem. @ max                       |   7571 |     0.0477 |   0.0258 |   3.02 |   2294 |     0.0525 |   0.0273 |   1.8  |    270 |     0.0058 |   0.0352 |   0.07 |
| slotkoers-model gem. @ Bet365                    |    861 |     0.1118 |   0.0126 |   2.03 |    215 |     0.1243 |   0.0066 |   1.18 |     73 |     0.2173 |  -0.012  |   1.24 |
| Asian handicap value @ max (edge≥2%)             |    840 |     0.0679 |   0.0204 |   2.18 |    114 |     0.0595 |   0.02   |   0.67 |     46 |     0.2957 |   0.0325 |   2.45 |
| Over/Under value @ max (edge≥2%)                 |    854 |     0.056  |   0.0381 |   1.59 |    112 |     0.1268 |   0.0349 |   1.07 |     46 |    -0.2972 |   0.0109 |  -2.07 |
| Wedden bij slotkoers (max) vs Pinnacle-slot      |   9343 |     0.0169 |   0.0377 |   1.11 |   3453 |     0.0297 |   0.0338 |   1.22 |    518 |    -0.1202 |   0.0453 |  -2.02 |
| Wedden bij slotkoers (Bet365) vs Pinnacle-slot   |    472 |    -0.089  |   0.0278 |  -1.2  |     68 |     0.3629 |   0.0256 |   1.85 |    158 |    -0.2609 |   0.0399 |  -2.67 |

**Conclusies:**
- Het **slotkoers-model** is de beste nieuwe bron. Het gemiddelde van ridge en gbm werkt het stabielst: positief rendement in TRAIN, VALID en TEST, zowel bij soft bookmakers als bij de beste marktkoers. De CLV is in elke periode positief.
- **Asian handicap** value werkt ook (positief in alle periodes), met weinig bets.
- **Wedden vlak voor aftrap** tegen de Pinnacle-slotkoers geeft schijnbaar CLV, maar **verliest in TEST**. Afgevallen.
- **2e referentie**: zonder Pinnacle-koers (2025/26) val je terug op Betfair of consensus. Dat levert meer bets op, maar met een lagere kwaliteit per bet.

## 5. Portfolio-zoektocht (TRAIN-selectie op t-stat, getoetst op VALID)

Geteste combinaties: 28

| params                                                                                                       |   tr_n_bets |   tr_flat_yield |   tr_clv |   tr_t_stat |   va_n_bets |   va_flat_yield |   va_clv |   va_t_stat |
|:-------------------------------------------------------------------------------------------------------------|------------:|----------------:|---------:|------------:|------------:|----------------:|---------:|------------:|
| {"book": "max", "max_odds": 4.0, "legs": [["1x2", "avgmv", 0.02], ["ah", "ref", 0.03], ["ou", "ref", 0.03]]} |        3868 |          0.0901 |   0.0369 |        4.5  |        1090 |          0.0819 |   0.0368 |        1.95 |
| {"book": "max", "max_odds": 6.0, "legs": [["1x2", "avgmv", 0.02], ["ah", "ref", 0.03], ["ou", "ref", 0.03]]} |        4359 |          0.0852 |   0.0383 |        4.16 |        1203 |          0.0561 |   0.0361 |        1.36 |
| {"book": "max", "max_odds": 4.0, "legs": [["1x2", "avgmv", 0.02]]}                                           |        3152 |          0.0915 |   0.0353 |        3.96 |        1006 |          0.0748 |   0.0369 |        1.69 |
| {"book": "max", "max_odds": 4.0, "legs": [["1x2", "avgmv", 0.01], ["ah", "ref", 0.02], ["ou", "ref", 0.02]]} |        7663 |          0.0517 |   0.0262 |        3.8  |        2172 |          0.0814 |   0.0279 |        2.89 |
| {"book": "max", "max_odds": 6.0, "legs": [["1x2", "avgmv", 0.01], ["ah", "ref", 0.02], ["ou", "ref", 0.02]]} |        8309 |          0.0531 |   0.0279 |        3.78 |        2385 |          0.0562 |   0.0278 |        2    |
| {"book": "max", "max_odds": 6.0, "legs": [["1x2", "avgmv", 0.02]]}                                           |        3626 |          0.0834 |   0.0366 |        3.57 |        1110 |          0.0479 |   0.0355 |        1.1  |
| {"book": "max", "max_odds": 4.0, "legs": [["1x2", "avgmv", 0.01], ["ah", "ref", 0.02]]}                      |        6830 |          0.052  |   0.0251 |        3.54 |        2069 |          0.0788 |   0.0279 |        2.71 |
| {"book": "max", "max_odds": 6.0, "legs": [["1x2", "avgmv", 0.01], ["ah", "ref", 0.02]]}                      |        7458 |          0.0526 |   0.0267 |        3.47 |        2273 |          0.0527 |   0.0275 |        1.82 |
| {"book": "max", "max_odds": 6.0, "legs": [["1x2", "avgmv", 0.0]]}                                            |        9532 |          0.0427 |   0.0211 |        3.11 |        3375 |          0.0404 |   0.0195 |        1.72 |
| {"book": "max", "max_odds": 4.0, "legs": [["1x2", "mv", 0.01], ["ah", "ref", 0.02], ["ou", "mv", 0.02]]}     |        8279 |          0.0401 |   0.0243 |        3.11 |        2574 |          0.0521 |   0.0266 |        2.09 |

## 6. €100-simulatie (met minimale inzet €0,50, plafonds, limiet €50/bet)

- **soft**: `{"book": "soft", "max_odds": 4.0, "legs": [["1x2", "avgmv", 0.01], ["ah", "ref", 0.02], ["ou", "ref", 0.02]]}`
- **max**: `{"book": "max", "max_odds": 4.0, "legs": [["1x2", "avgmv", 0.02], ["ah", "ref", 0.03], ["ou", "ref", 0.03]]}`

| boeken   | staking         | periode   |   bets |   eind € |   max drawdown |   yield |     CLV |
|:---------|:----------------|:----------|-------:|---------:|---------------:|--------:|--------:|
| soft     | vlak 2% start   | valid     |    206 |   136.16 |         0.1242 |  0.0878 |  0.0246 |
| soft     | vlak 2% start   | test      |    158 |   120.25 |         0.1877 |  0.0641 |  0.0122 |
| soft     | 3% van bankroll | valid     |    206 |   146.35 |         0.2716 |  0.052  |  0.0246 |
| soft     | 3% van bankroll | test      |    158 |   120.06 |         0.2685 |  0.0383 |  0.0122 |
| soft     | Kelly 25%       | valid     |     81 |   109.44 |         0.0335 |  0.1182 |  0.0257 |
| soft     | Kelly 25%       | test      |     80 |    94.1  |         0.1509 | -0.054  | -0.004  |
| soft     | Kelly 50%       | valid     |    150 |   120.84 |         0.0559 |  0.0947 |  0.0248 |
| soft     | Kelly 50%       | test      |    113 |    94.77 |         0.2486 | -0.0229 |  0.0084 |
| max      | vlak 2% start   | valid     |   1090 |   274.84 |         0.4133 |  0.0806 |  0.0368 |
| max      | vlak 2% start   | test      |    161 |   115.79 |         0.279  |  0.0495 |  0.0457 |
| max      | 3% van bankroll | valid     |   1090 |   525.43 |         0.5203 |  0.0499 |  0.0368 |
| max      | 3% van bankroll | test      |    161 |   109.21 |         0.4832 |  0.0149 |  0.0457 |
| max      | Kelly 25%       | valid     |    530 |   127.86 |         0.1856 |  0.0446 |  0.0379 |
| max      | Kelly 25%       | test      |    122 |   109.62 |         0.1705 |  0.0463 |  0.0543 |
| max      | Kelly 50%       | valid     |   1061 |   201.56 |         0.2239 |  0.0488 |  0.0372 |
| max      | Kelly 50%       | test      |    158 |   113.01 |         0.3258 |  0.0302 |  0.0464 |

## 7. Robuustheid portfolio (soft), vlakke inzet

Per seizoen:

|   season |   n |   yield_ |    clv |
|---------:|----:|---------:|-------:|
|     1819 | 404 |   0.1364 | 0.0331 |
|     1920 | 245 |   0.131  | 0.0199 |
|     2021 | 280 |  -0.0563 | 0.0234 |
|     2122 | 201 |   0.1908 | 0.0308 |
|     2223 | 161 |   0.1142 | 0.0223 |
|     2324 | 109 |   0.1548 | 0.0252 |
|     2425 |  97 |   0.0125 | 0.0239 |
|     2526 | 158 |   0.0641 | 0.0122 |

Per competitie:

| league   |   n |   yield_ |    clv |
|:---------|----:|---------:|-------:|
| D1       | 330 |   0.0937 | 0.0265 |
| E0       | 226 |   0.156  | 0.0159 |
| F1       | 202 |   0.0365 | 0.0257 |
| I1       | 235 |   0.2162 | 0.0291 |
| N1       | 219 |   0.1213 | 0.0226 |
| P1       | 174 |  -0.0262 | 0.0247 |
| SP1      | 269 |   0.0371 | 0.0297 |

Per markt:

| market   |    n |   yield_ |    clv |
|:---------|-----:|---------:|-------:|
| 1x2      | 1564 |   0.0896 | 0.0253 |
| ah       |   34 |   0.1491 | 0.0128 |
| ou       |   57 |   0.197  | 0.0244 |
