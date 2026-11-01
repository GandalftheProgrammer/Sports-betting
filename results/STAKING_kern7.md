# Inzetstrategie: Monte-Carlo (4000 gesimuleerde verlopen) — kern7

Basis: 1804 out-of-sample portfolio-bets 2018–2026 (soft-mandje), gem. odds 2.46, gem. CLV +2.41%, backtest-rendement +7.08%. Kelly gebruikt de edge die het model VOORAF schat (gem. +2.99%), gekrompen met factor 0.80 naar het CLV-niveau. 226 bets per seizoen, 5 tegelijk per speelronde, inzet = % van de **actuele** pot (progressief), minimaal €0,50, max 30% van de pot tegelijk in het spel.

| scenario    |   seizoenen | inzet/bet   |   mediaan € |   slechtste 10% € |   beste 10% € |   kans op winst |   kans pot ooit <€50 |   kans pot <€20 (bijna op) |
|:------------|------------:|:------------|------------:|------------------:|--------------:|----------------:|---------------------:|---------------------------:|
| realistisch |           1 | 1%          |         104 |                82 |           131 |           0.576 |                0     |                      0     |
| realistisch |           1 | 2%          |         105 |                66 |           165 |           0.549 |                0.038 |                      0     |
| realistisch |           1 | 3%          |          99 |                50 |           203 |           0.491 |                0.178 |                      0.003 |
| realistisch |           1 | 5%          |          86 |                27 |           270 |           0.43  |                0.449 |                      0.088 |
| realistisch |           1 | 8%          |          81 |                18 |           321 |           0.428 |                0.544 |                      0.171 |
| realistisch |           1 | 12%         |          75 |                18 |           309 |           0.4   |                0.562 |                      0.185 |
| realistisch |           1 | Kelly ½     |         106 |                83 |           137 |           0.61  |                0     |                      0     |
| realistisch |           1 | Kelly 1×    |         107 |                71 |           163 |           0.586 |                0.017 |                      0     |
| realistisch |           3 | 1%          |         112 |                75 |           167 |           0.638 |                0.008 |                      0     |
| realistisch |           3 | 2%          |         113 |                52 |           256 |           0.582 |                0.197 |                      0     |
| realistisch |           3 | 3%          |         103 |                29 |           333 |           0.512 |                0.422 |                      0.079 |
| realistisch |           3 | 5%          |          66 |                 9 |           492 |           0.391 |                0.704 |                      0.364 |
| realistisch |           3 | 8%          |          44 |                 7 |           482 |           0.336 |                0.782 |                      0.505 |
| realistisch |           3 | 12%         |          40 |                 7 |           464 |           0.32  |                0.8   |                      0.527 |
| realistisch |           3 | Kelly ½     |         117 |                75 |           181 |           0.67  |                0.011 |                      0     |
| realistisch |           3 | Kelly 1×    |         125 |                61 |           265 |           0.652 |                0.114 |                      0.001 |
| backtest    |           1 | 1%          |         115 |                91 |           147 |           0.779 |                0     |                      0     |
| backtest    |           1 | 2%          |         130 |                82 |           208 |           0.766 |                0.01  |                      0     |
| backtest    |           1 | 3%          |         141 |                68 |           282 |           0.728 |                0.066 |                      0     |
| backtest    |           1 | 5%          |         146 |                46 |           467 |           0.662 |                0.266 |                      0.032 |
| backtest    |           1 | 8%          |         145 |                34 |           635 |           0.631 |                0.372 |                      0.078 |
| backtest    |           1 | 12%         |         147 |                35 |           601 |           0.635 |                0.364 |                      0.071 |
| backtest    |           1 | Kelly ½     |         114 |                88 |           149 |           0.734 |                0     |                      0     |
| backtest    |           1 | Kelly 1×    |         134 |                88 |           202 |           0.817 |                0.004 |                      0     |
| backtest    |           3 | 1%          |         153 |               102 |           231 |           0.91  |                0.001 |                      0     |
| backtest    |           3 | 2%          |         216 |                99 |           482 |           0.898 |                0.035 |                      0     |
| backtest    |           3 | 3%          |         264 |                81 |           896 |           0.848 |                0.151 |                      0.008 |
| backtest    |           3 | 5%          |         309 |                41 |          2166 |           0.767 |                0.403 |                      0.113 |
| backtest    |           3 | 8%          |         320 |                22 |          3284 |           0.728 |                0.492 |                      0.2   |
| backtest    |           3 | 12%         |         300 |                21 |          3525 |           0.712 |                0.502 |                      0.202 |
| backtest    |           3 | Kelly ½     |         153 |                94 |           242 |           0.867 |                0.001 |                      0     |
| backtest    |           3 | Kelly 1×    |         237 |               115 |           497 |           0.936 |                0.013 |                      0     |