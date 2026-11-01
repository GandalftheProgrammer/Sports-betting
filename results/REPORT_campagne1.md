# Onderzoeksrapport — campagne #1

Data: 23982 wedstrijden, 10 seizoenen, competities: E0 (Premier League), SP1 (La Liga), I1 (Serie A), D1 (Bundesliga), F1 (Ligue 1), P1 (Primeira Liga), N1 (Eredivisie)

Splitsing: TRAIN 2016/17–2022/23 (zoeken) · VALID 2023/24–2024/25 (toetsen) · TEST 2025/26 (eindexamen).

## 1. Bekende marktbiases (vlakke inzet op alles in de groep, TRAIN+VALID)

Een `yield` van −0,03 betekent 3% verlies per ingezette euro. `t` > 2 is pas statistisch interessant.

| test                             |     n |   yield_ |      t |
|:---------------------------------|------:|---------:|-------:|
| Alles (Pinnacle)                 | 64677 |  -0.0458 |  -6.97 |
| Alles (Bet365)                   | 64665 |  -0.0711 | -11.19 |
| Alles (gem. markt)               | 64677 |  -0.0706 | -11.19 |
| Grote favorieten <1.5 (Pinnacle) |  4946 |  -0.0009 |  -0.11 |
| Grote favorieten <1.5 (Bet365)   |  5478 |  -0.0159 |  -2.05 |
| Longshots >7 (Pinnacle)          |  5979 |  -0.1622 |  -4.24 |
| Longshots >7 (Bet365)            |  5987 |  -0.1941 |  -5.33 |
| Thuis (Pinnacle)                 | 21559 |  -0.0416 |  -4.5  |
| Gelijkspel (Pinnacle)            | 21559 |  -0.0325 |  -2.7  |
| Uit (Pinnacle)                   | 21559 |  -0.0632 |  -5.04 |
| Over 2.5 (Pinnacle)              | 14216 |  -0.032  |  -4.05 |
| Under 2.5 (Pinnacle)             | 14216 |  -0.0408 |  -4.58 |
| Alles E0 (Pinnacle)              | 10260 |  -0.0381 |  -2.23 |
| Alles SP1 (Pinnacle)             | 10251 |  -0.0406 |  -2.45 |
| Alles I1 (Pinnacle)              | 10239 |  -0.0573 |  -3.57 |
| Alles D1 (Pinnacle)              |  8259 |  -0.0185 |  -0.99 |
| Alles F1 (Pinnacle)              |  9489 |  -0.0399 |  -2.43 |
| Alles P1 (Pinnacle)              |  8208 |  -0.0782 |  -4.3  |
| Alles N1 (Pinnacle)              |  7971 |  -0.0494 |  -2.59 |

## 2. Value betting t.o.v. Pinnacle (zoeken op TRAIN, top-8 getoetst op VALID)

Aantal geteste combinaties: 181

| params                                                                                          |   tr_n_bets |   tr_flat_yield |   tr_clv |   tr_t_stat |   va_n_bets |   va_flat_yield |   va_clv |   va_t_stat |   va_p_pos |
|:------------------------------------------------------------------------------------------------|------------:|----------------:|---------:|------------:|------------:|----------------:|---------:|------------:|-----------:|
| {"book": "max", "min_edge": 0.03, "max_edge": null, "max_odds": 6.0, "markets": ["1x2", "ou"]}  |        3188 |          0.0779 |   0.044  |        3.07 |         445 |          0.0786 |   0.0386 |        1.08 |      0.86  |
| {"book": "max", "min_edge": 0.03, "max_edge": 0.15, "max_odds": 6.0, "markets": ["1x2", "ou"]}  |        3160 |          0.0761 |   0.0421 |        2.99 |         437 |          0.087  |   0.0352 |        1.18 |      0.885 |
| {"book": "max", "min_edge": 0.02, "max_edge": null, "max_odds": 3.0, "markets": ["1x2", "ou"]}  |        3628 |          0.0492 |   0.0342 |        2.97 |         380 |          0.0321 |   0.0232 |        0.66 |      0.752 |
| {"book": "max", "min_edge": 0.02, "max_edge": null, "max_odds": 6.0, "markets": ["1x2", "ou"]}  |        6156 |          0.0513 |   0.0324 |        2.95 |         929 |          0.0444 |   0.0293 |        0.94 |      0.84  |
| {"book": "soft", "min_edge": 0.03, "max_edge": 0.15, "max_odds": 6.0, "markets": ["1x2", "ou"]} |        1202 |          0.124  |   0.0469 |        2.93 |          41 |          0.1661 |   0.0139 |        0.61 |      0.722 |
| {"book": "max", "min_edge": 0.02, "max_edge": 0.15, "max_odds": 3.0, "markets": ["1x2", "ou"]}  |        3621 |          0.0478 |   0.0339 |        2.89 |         377 |          0.0354 |   0.0218 |        0.73 |      0.772 |
| {"book": "max", "min_edge": 0.02, "max_edge": 0.15, "max_odds": 6.0, "markets": ["1x2", "ou"]}  |        6128 |          0.0503 |   0.0314 |        2.89 |         921 |          0.048  |   0.0275 |        1.01 |      0.845 |
| {"book": "soft", "min_edge": 0.03, "max_edge": null, "max_odds": 6.0, "markets": ["1x2", "ou"]} |        1219 |          0.1184 |   0.0488 |        2.82 |          43 |          0.1119 |   0.0205 |        0.43 |      0.664 |

### Beste per boek (TRAIN-selectie)

- **b365** {"book": "b365", "min_edge": 0.03, "max_edge": 0.15, "max_odds": 6.0, "min_odds": 1.3, "markets": ["1x2", "ou"]} → VALID: 29 bets, yield -0.071, CLV +0.021, t=-0.23, P(winst)=0.412
- **soft** {"book": "soft", "min_edge": 0.03, "max_edge": 0.15, "max_odds": 6.0, "min_odds": 1.3, "markets": ["1x2", "ou"]} → VALID: 41 bets, yield +0.166, CLV +0.014, t=0.61, P(winst)=0.722
- **max** {"book": "max", "min_edge": 0.03, "max_edge": null, "max_odds": 6.0, "min_odds": 1.3, "markets": ["1x2", "ou"]} → VALID: 445 bets, yield +0.079, CLV +0.039, t=1.08, P(winst)=0.86

## 3. Eigen Poisson-model (gemengd met Pinnacle)

| params                                                                                  |   tr_n_bets |   tr_flat_yield |   tr_clv |   tr_t_stat |   va_n_bets |   va_flat_yield |   va_clv |   va_t_stat |   va_p_pos |
|:----------------------------------------------------------------------------------------|------------:|----------------:|---------:|------------:|------------:|----------------:|---------:|------------:|-----------:|
| {"book": "soft", "weight": 0.15, "min_edge": 0.08, "max_odds": 5.0, "markets": ["1x2"]} |         506 |          0.0586 |   0.0184 |        0.83 |          26 |         -0.1462 |  -0.0019 |       -0.45 |      0.332 |
| {"book": "soft", "weight": 0.15, "min_edge": 0.04, "max_odds": 5.0, "markets": ["1x2"]} |        2031 |         -0.0121 |  -0.0004 |       -0.37 |         210 |         -0.2269 |  -0.0218 |       -2.4  |      0.011 |
| {"book": "max", "weight": 0.15, "min_edge": 0.08, "max_odds": 5.0, "markets": ["1x2"]}  |         941 |         -0.0279 |   0.0182 |       -0.56 |         123 |         -0.0946 |   0.0073 |       -0.67 |      0.244 |
| {"book": "max", "weight": 0.15, "min_edge": 0.08, "max_odds": 5.0, "markets": ["ou"]}   |         171 |         -0.0771 |   0.0527 |       -0.81 |          30 |          0.0333 |   0.048  |        0.15 |      0.546 |

## 4. Arbitrage (beste marktkoersen, alle seizoenen)

Aantal 'surebets' per seizoen en gemiddelde gegarandeerde marge:

|      |   count |   mean |
|-----:|--------:|-------:|
| 1617 |    1363 | 0.0109 |
| 1718 |    1216 | 0.01   |
| 1819 |     854 | 0.0081 |
| 1920 |     921 | 0.0069 |
| 2021 |    1272 | 0.0062 |
| 2122 |    1457 | 0.0069 |
| 2223 |     681 | 0.0059 |
| 2324 |     562 | 0.0058 |
| 2425 |     249 | 0.0077 |
| 2526 |      30 | 0.0473 |

## 5. Staking-simulatie met €100 (VALID-periode, met limieten)

Strategie: `value_vs_sharp` {"book": "max", "min_edge": 0.03, "max_edge": 0.15, "max_odds": 6.0, "min_odds": 1.3, "markets": ["1x2", "ou"]}

| staking         | split   |   bets |   eind € |   max drawdown |   yield |    CLV |
|:----------------|:--------|-------:|---------:|---------------:|--------:|-------:|
| vlak 1% start   | valid   |    437 |   138    |         0.1505 |  0.087  | 0.0352 |
| vlak 1% start   | test    |     46 |    98.31 |         0.0779 | -0.0367 | 0.0436 |
| 2% van bankroll | valid   |    437 |   169.49 |         0.2888 |  0.0599 | 0.0352 |
| 2% van bankroll | test    |     46 |    95.56 |         0.1494 | -0.0514 | 0.0436 |
| Kelly 10%       | valid   |     51 |    94.41 |         0.0831 | -0.1357 | 0.0401 |
| Kelly 10%       | test    |      8 |   102.6  |         0.0032 |  0.441  | 0.0617 |
| Kelly 25%       | valid   |    219 |   112.48 |         0.1294 |  0.0523 | 0.0416 |
| Kelly 25%       | test    |     21 |   101.72 |         0.03   |  0.0721 | 0.0541 |
| Kelly 50%       | valid   |    422 |   138.46 |         0.2367 |  0.0553 | 0.0358 |
| Kelly 50%       | test    |     39 |   103.74 |         0.0716 |  0.0621 | 0.0489 |

Per seizoen (vlakke inzet, alle seizoenen — let op: TRAIN-seizoenen zijn in-sample):

|    s |   count |   mean |
|-----:|--------:|-------:|
| 1617 |     550 |  0.139 |
| 1718 |     529 |  0.11  |
| 1819 |     342 |  0.253 |
| 1920 |     422 | -0.009 |
| 2021 |     444 | -0.077 |
| 2122 |     578 |  0.007 |
| 2223 |     295 |  0.179 |
| 2324 |     230 |  0.119 |
| 2425 |     207 |  0.051 |
| 2526 |      46 | -0.037 |
