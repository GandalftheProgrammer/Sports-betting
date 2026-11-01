# Sports-betting agent ⚽

Een systeem dat zelf zoekt naar winstgevende voetbalweddenschappen. Het test
strategieën streng op historische data en leert wat wel en niet werkt. Pas
als een strategie dat aantoonbaar doorstaat, gaat er echt geld (€100) in.

> **Status:** fase 1–2 (onderzoek + backtesten) staat. Er wordt nog **niet**
> met echt geld gewed. Zie [Roadmap](#roadmap) en het laatste
> [onderzoeksrapport](results/REPORT.md).

## Snel starten

```bash
pip install -r requirements.txt
python -m pytest -q                 # tests
python -m research.models_eval     # modellen vs. markt (~3 min, eerste keer)
python -m research.hypotheses      # 48 biases -> results/HYPOTHESES.md
python -m research.campaign2       # strategieën + portfolio + €100-simulatie -> results/REPORT.md
```

## Hoe verdien je (misschien) geld met sportweddenschappen?

Twee onderzoekscampagnes: [campagne #1](results/REPORT_campagne1.md) en
**[campagne #2 (actueel)](results/REPORT.md)**. Daarnaast
[48 geteste biases](results/HYPOTHESES.md). De literatuur staat in [docs/RESEARCH.md](docs/RESEARCH.md).

Data: 2016–2026, 7 competities, ~24.000 wedstrijden. Rendement = winst per ingezette euro bij vlakke inzet.

| Aanpak | Oordeel | Bewijs (VALID 23/24–24/25 · TEST 25/26, nooit gezien bij het bouwen) |
|---|---|---|
| Blind wedden / favorieten / underdogs | ❌ | −5% tot −19% |
| 48 biases (publieksclubs, reeksen, geluk vs. schoten, promovendi, motivatie, rust, ghost games, …) | ❌ / 👀 | Na correctie voor meervoudig testen geen enkele structureel. Te volgen: gelijkspel tussen gelijkwaardige teams laat in het seizoen |
| Eigen modellen (Dixon-Coles op goals/schoten, pi-ratings, Elo, ML) **als uitslagvoorspeller** | ➖ | Sterk verbeterd (logloss 0,991 → 0,978), maar nog niet beter dan de markt (0,960) |
| **Eigen model als "slotkoers-voorspeller"** | ✅✅ | Voorspelt in 53–69% de richting van de Pinnacle-koersbeweging. Value betting op die voorspelde koers: positief in TRAIN, VALID én TEST |
| Value t.o.v. Pinnacle (v1) | ✅ | +4,9% · +17% (max), CLV +2–3% |
| Asian handicap value | ✅ | +6% · +30%, weinig bets |
| Wedden vlak voor aftrap t.o.v. de Pinnacle-slotkoers | ❌ | −12% in TEST, afgevallen |
| **Portfolio** (slotkoers-model 1X2 + AH + O/U) | ✅✅ | Beste marktkoers: +8,2% (t=1,95) · +5%, CLV +3,7–4,6%. Soft-mandje: +8,8% · +6,4% |

**Met €100 (vlakke inzet 2%, inzetplafonds):** VALID €100 → €136 (soft) / €275 (beste
marktkoers). TEST €100 → €120 (soft) / €116 (max).

**Eerlijke verwachting:** de CLV (1–4%) is een betrouwbaardere schatting van de
echte edge dan het rendement (6–9%), want rendement bevat veel geluk. Reken
dus op **+1 tot +4% per ingezette euro**. Dat is een echte edge, maar het potje
groeit geleidelijk. Bookmakerlimieten zijn nog steeds het grootste
praktische risico.

## Architectuur

```
sbagent/
  data.py         historische CSV's laden + normaliseren (teamnamen, koersbronnen)
  devig.py        marge uit koersen halen (multiplicatief, power, Shin)
  model.py        eenvoudig online Poisson-model (v1)
  ratings.py      Dixon-Coles MLE (goals en schoten-op-doel), pi-ratings, Elo
  teamfeat.py     pre-match teamfeatures: vorm, reeksen, schoten, 'geluk', stand, motivatie, rust, promovendi
  ml.py           walk-forward ML (logistische regressie, gradient boosting) op markt + modellen + team
  movement.py     'voorspel de slotkoers'-model (ridge + gradient boosting)
  features.py     eerlijke kansen per bron (Pinnacle / Betfair / consensus, open + slot) + alle modellen
  strategies.py   ValueVsSharp (elke kansbron × elke bookmaker × 1X2/OU/AH), Portfolio, OddsBand, Arbitrage
  backtest.py     bankroll-simulatie per speeldag: Kelly/flat, limieten, CLV, drawdown
  experiments.py  leer-lus: zoeken op TRAIN -> toetsen op VALID -> eindexamen TEST, alles gelogd
research/
  campaign.py     campagne #1
  models_eval.py  modelvergelijking (logloss/RPS) vs. markt
  movement_eval.py  evaluatie slotkoers-voorspeller
  hypotheses.py   48 bias-hypotheses met Benjamini-Hochberg correctie
  campaign2.py    campagne #2 -> results/REPORT.md
results/
  REPORT.md            laatste rapport
  experiments.jsonl    logboek van álle experimenten (wat werkte, wat niet)
data/raw/<seizoen>/<competitie>.csv   football-data.co.uk formaat
```

**Hoe het systeem leert zonder zichzelf voor de gek te houden:**
- **TRAIN** (2016/17–2022/23): hier mag het systeem honderden varianten proberen.
- **VALID** (2023/24–2024/25): alleen de beste kandidaten worden hier getoetst.
- **TEST** (2025/26): eindexamen. Wordt zelden gebruikt, anders wordt het ook trainingsdata.
- Selectie gebeurt op **t-statistiek en Closing Line Value**, niet op ruwe winst.
  Winst is erg toevallig: na 500 bets met koers ~2,5 is ±10% nog ruis. CLV is
  een veel sneller en betrouwbaarder signaal of je echt een edge hebt.

## Roadmap

| Fase | Wat | Status |
|---|---|---|
| 1 | Onderzoek + historische data (7 competities, 10 seizoenen) | ✅ |
| 2 | Backtester + strategieën + leer-lus met train/valid/test | ✅ (campagne #1) |
| 3 | Verbeteren: sterkere modellen, slotkoers-voorspeller, 2e referentie, AH, slotkoers-wedden, 48 biases, portfolio | ✅ (campagne #2) |
| 3b | Verder: slotkoers-voorspeller verfijnen (meer features: blessures/opstellingen, nieuws-timing), per-competitie-modellen, gelijkspelsignaal volgen | ⏳ |
| 4 | Live koersen ophalen (The Odds API) + **paper trading**: dezelfde beslissingen live, zonder geld, CLV meten | ⏳ |
| 5 | Dashboard (bankroll, CLV, bets, wat werkt) | ⏳ |
| 6 | Echt geld (€100), strikte risicoregels, automatische uitvoering waar dat mag | ⏳ alleen na bewezen CLV in fase 4 |

**Draaien in productie:** GitHub Actions (gratis, met een schema elke X
minuten/uren) is hiervoor het meest geschikt. n8n kan ook. Netlify is alleen
geschikt voor het dashboard, niet voor de agent zelf.

## Wat ik (later) nodig heb

- **Fase 4:** een API-sleutel van [The Odds API](https://the-odds-api.com). Het gratis
  plan (500 requests per maand) volstaat om te beginnen; ~$30 per maand voor serieus
  live gebruik. Dat is een vaste kostenpost die uit de €100 moet komen. Daarom
  eerst gratis paper traden.
- **Fase 6:** een keuze over welke bookmaker(s), zie docs/RESEARCH.md §5. Accounts
  en KYC moet je zelf regelen, op je eigen naam en adres.
