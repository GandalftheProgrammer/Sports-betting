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
python -m research.campaign         # draait alle experimenten -> results/REPORT.md
python -m research.campaign --test  # idem, plus het 'eindexamen' op 2025/26
```

## Hoe verdien je (misschien) geld met sportweddenschappen?

Wat het onderzoek en onze eigen backtests laten zien (details in [docs/RESEARCH.md](docs/RESEARCH.md)):

| Aanpak | Werkt het? | Bewijs in onze data (2016–2026, 7 competities, ~24.000 wedstrijden) |
|---|---|---|
| Blind wedden / "gevoel" | ❌ | −4,6% (Pinnacle) tot −7,1% (Bet365) per ingezette euro |
| Favorieten wedden (bias) | ➖ | ±0% bij Pinnacle, −1,6% bij Bet365: geen winst |
| Longshots/underdogs | ❌❌ | −16% tot −19%: hier zit de grootste marge van de bookmaker |
| Eigen Poisson-model vs. markt | ❌ | Model (logloss 0,989) is slechter dan de markt (0,956); verliest op VALID |
| **Value betting t.o.v. Pinnacle** | ✅ | +5 tot +8% op TRAIN **én** VALID, positieve Closing Line Value (+3–4%) |
| Arbitrage (surebets) | ➖ | Bestaat, maar is zeldzaam (<1% marge) en neemt elk jaar sterk af |

**Kern-inzicht:** het is ongeveer kansloos om de *markt* te verslaan. Wel kun je
**trage bookmakers** verslaan. Pinnacle is de scherpste bookmaker: zijn koers,
zonder marge, is de beste schatting van de echte kans. Biedt een andere
bookmaker op hetzelfde moment een hogere koers, dan heb je een verwachte
winst. Hoe meer bookmakers je kunt vergelijken (line shopping), hoe meer
kansen.

**De grote valkuilen (eerlijk):**
1. Met **alleen Bet365** is er te weinig edge: ±30 bets per seizoen, niet significant.
   De edge zit in het vergelijken van veel bookmakers.
2. **Bookmakers beperken winnaars.** Een value-bettor krijgt na een paar
   weken tot maanden limieten. Daarom simuleert de backtester inzetlimieten.
3. De kansen worden kleiner: het aantal surebets en value-bets daalt per seizoen.
4. In 2025/26 ontbreken voor de helft van de wedstrijden Pinnacle-koersen in
   de data, omdat Pinnacle de toegang tot zijn data heeft beperkt. Een tweede
   scherpe referentie (Betfair Exchange) is daarom een prioriteit.

## Architectuur

```
sbagent/
  data.py         historische CSV's laden + normaliseren (teamnamen, koersbronnen)
  devig.py        marge uit koersen halen (multiplicatief, power, Shin)
  model.py        eigen online Poisson-model (aanval/verdediging), strikt zonder look-ahead
  features.py     eerlijke kansen + modelkansen per wedstrijd
  strategies.py   ValueVsSharp, ModelValue, OddsBand (bias-tests), Arbitrage
  backtest.py     bankroll-simulatie per speeldag: Kelly/flat, limieten, CLV, drawdown
  experiments.py  leer-lus: zoeken op TRAIN -> toetsen op VALID -> eindexamen TEST, alles gelogd
research/
  campaign.py     onderzoekscampagne die het rapport genereert
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
| 3 | Verbeteren: Betfair als 2e scherpe referentie, timing (koers vlak voor aftrap), extra markten (Asian handicap), limieten realistischer, combinaties | ⏳ volgende |
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
