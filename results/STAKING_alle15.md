# Inzetstrategie: Monte-Carlo (4000 gesimuleerde verlopen) — alle15

Basis: 4587 out-of-sample portfolio-bets 2018–2026 (soft-mandje), gem. odds 2.64, gem. CLV +2.80%, backtest-rendement +3.51%. Kelly gebruikt de edge die het model VOORAF schat (gem. +3.71%), gekrompen met factor 0.75 naar het CLV-niveau. 573 bets per seizoen, 15 tegelijk per speelronde, inzet = % van de **actuele** pot (progressief), minimaal €0,50, max 30% van de pot tegelijk in het spel.

| scenario    |   seizoenen | inzet/bet   |   mediaan € |   slechtste 10% € |   beste 10% € |   kans op winst |   kans pot ooit <€50 |   kans pot <€20 (bijna op) |
|:------------|------------:|:------------|------------:|------------------:|--------------:|----------------:|---------------------:|---------------------------:|
| realistisch |           1 | 1%          |         111 |                76 |           167 |           0.632 |                0.007 |                      0     |
| realistisch |           1 | 2%          |         114 |                53 |           249 |           0.583 |                0.162 |                      0     |
| realistisch |           1 | 3%          |         114 |                50 |           254 |           0.579 |                0.183 |                      0     |
| realistisch |           1 | 5%          |         114 |                52 |           253 |           0.583 |                0.17  |                      0     |
| realistisch |           1 | 8%          |         115 |                50 |           266 |           0.583 |                0.179 |                      0.004 |
| realistisch |           1 | 12%         |         113 |                50 |           264 |           0.577 |                0.178 |                      0.003 |
| realistisch |           1 | Kelly ½     |         116 |                74 |           183 |           0.652 |                0.016 |                      0     |
| realistisch |           1 | Kelly 1×    |         123 |                62 |           235 |           0.655 |                0.088 |                      0     |
| realistisch |           3 | 1%          |         139 |                68 |           282 |           0.732 |                0.062 |                      0     |
| realistisch |           3 | 2%          |         147 |                25 |           582 |           0.636 |                0.364 |                      0.001 |
| realistisch |           3 | 3%          |         143 |                29 |           563 |           0.632 |                0.365 |                      0.01  |
| realistisch |           3 | 5%          |         146 |                29 |           572 |           0.638 |                0.35  |                      0.014 |
| realistisch |           3 | 8%          |         141 |                30 |           547 |           0.632 |                0.377 |                      0.009 |
| realistisch |           3 | 12%         |         151 |                28 |           594 |           0.654 |                0.357 |                      0.014 |
| realistisch |           3 | Kelly ½     |         157 |                69 |           362 |           0.755 |                0.089 |                      0     |
| realistisch |           3 | Kelly 1×    |         188 |                58 |           602 |           0.758 |                0.212 |                      0.014 |
| backtest    |           1 | 1%          |         118 |                78 |           172 |           0.698 |                0.004 |                      0     |
| backtest    |           1 | 2%          |         125 |                56 |           270 |           0.64  |                0.142 |                      0     |
| backtest    |           1 | 3%          |         126 |                57 |           281 |           0.642 |                0.137 |                      0     |
| backtest    |           1 | 5%          |         126 |                54 |           277 |           0.637 |                0.149 |                      0     |
| backtest    |           1 | 8%          |         120 |                54 |           272 |           0.628 |                0.153 |                      0.002 |
| backtest    |           1 | 12%         |         122 |                54 |           274 |           0.618 |                0.156 |                      0.002 |
| backtest    |           1 | Kelly ½     |         121 |                78 |           193 |           0.701 |                0.009 |                      0     |
| backtest    |           1 | Kelly 1×    |         134 |                69 |           269 |           0.717 |                0.068 |                      0     |
| backtest    |           3 | 1%          |         155 |                77 |           313 |           0.791 |                0.042 |                      0     |
| backtest    |           3 | 2%          |         193 |                47 |           733 |           0.735 |                0.29  |                      0     |
| backtest    |           3 | 3%          |         185 |                44 |           717 |           0.723 |                0.292 |                      0.006 |
| backtest    |           3 | 5%          |         187 |                42 |           756 |           0.719 |                0.289 |                      0.01  |
| backtest    |           3 | 8%          |         195 |                43 |           738 |           0.729 |                0.288 |                      0.009 |
| backtest    |           3 | 12%         |         190 |                43 |           761 |           0.713 |                0.29  |                      0.006 |
| backtest    |           3 | Kelly ½     |         184 |                82 |           403 |           0.83  |                0.05  |                      0     |
| backtest    |           3 | Kelly 1×    |         246 |                76 |           816 |           0.842 |                0.139 |                      0.007 |