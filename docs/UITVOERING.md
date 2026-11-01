# Uitvoering: hoe de agent in Nederland gaat wedden

*Stand: november 2026. Bronnen onderaan.*

## 1. Waar mag het, en kan het via een API?

| Optie | Legaal vanuit NL? | API om te wedden? |
|---|---|---|
| Bookmakers met KSA-vergunning (Bet365, Unibet, TOTO, BetCity, Holland Casino, Jacks, BetMGM, …) | ✅ | ❌ Geen enkele heeft een publieke wed-API |
| Betfair Exchange | ❌ Vertrokken in 2021, geen vergunning aangevraagd | ✅ (niet voor NL) |
| Polymarket, Kalshi en andere prediction markets | ❌ KSA: dwangsom voor Polymarket. "Niet toegestaan, ook niet voor vergunninghouders" | ✅ (illegaal aanbod) |
| Bot die de website van je eigen bookmaker bedient | Niet strafbaar, maar in strijd met de voorwaarden. Risico: account gesloten | – |

**Conclusie:** volledig automatisch wedden kan in Nederland niet legaal. **Koersen
ophalen kan wel volledig automatisch.**

## 2. Werkwijze: de agent doet alles, jij tikt één keer per bet

1. **Vrijdagmiddag** (en dinsdag bij midweek-ronden) draait de agent via GitHub
   Actions. Dat is hetzelfde moment als waarop de historische data is
   verzameld, dus backtest en praktijk sluiten op elkaar aan.
2. De agent haalt koersen op van je NL-bookmakers en van de scherpe referentie
   (Pinnacle, met Betfair als reserve), berekent het slotkoersmodel en selecteert value bets.
3. **Telegram-bericht** per bet: wedstrijd, keuze, bookmaker, **minimale koers**,
   inzet in euro's, link. Jij plaatst de bet en tikt ✅. Is de koers onder het
   minimum, dan sla je de bet over.
4. De agent verwerkt de uitslagen, het saldo en de CLV automatisch, en past de
   inzetten en modellen aan.

Tijd: 5–15 minuten per week. Ongeveer 75% van de bets valt in het weekend.

## 3. Koersdata (live) — status Pinnacle

- Pinnacle heeft zijn publieke API op **23 juli 2025** gesloten. Toegang is er alleen nog voor partners.
- **The Odds API** (gratis, 500 credits per maand) heeft volgens de eigen documentatie in
  regio `eu` nog steeds `pinnacle`, plus `betfair_ex_eu` en `unibet_nl`.
  Kanttekening: de Pinnacle-koersen komen van de publieke website en kunnen vertraagd zijn.
  Bet365, TOTO en BetCity staan daar niet in.
- **OddsPapi** (gratis, 250 requests per maand) dekt TOTO NL, BetCity NL, Unibet NL en Jacks.
- Betaalde Pinnacle-feeds (pinnapi, pinnwire) vanaf ~$89 per maand.
- **Waarom Pinnacle telt** (gemeten op 2025/26): bets met een Pinnacle-referentie
  hadden een CLV van **+2,0 à 2,5%**. Met alleen Betfair als referentie was dat **+0,3 à 1,3%**.
- ⚠️ Nog niet live geverifieerd: the-odds-api.com, odds-api.io en dev.to zijn
  geblokkeerd in de cloudomgeving waarin dit is gebouwd. Eerste actie zodra er een
  API-sleutel is: één scan draaien en controleren of `pinnacle` koersen teruggeeft
  voor de 15 competities, en hoe groot de vertraging is.

## 4. Inzetstrategie: progressief, proportioneel aan de pot

Zie [results/STAKING_alle15.md](../results/STAKING_alle15.md) en
[STAKING_kern7.md](../results/STAKING_kern7.md) (Monte-Carlo, 4000 verlopen).

**Regel:** inzet = **½ Kelly**, altijd berekend over de **actuele** pot:
`inzet = ½ × (verwachte edge / (koers − 1)) × pot`, met de edge gekrompen naar het
CLV-niveau (×0,75), maximaal 5% per bet en maximaal 30% van de pot tegelijk in het spel.

- Groeit de pot van €100 naar €150, dan worden alle inzetten 1,5× zo groot.
  Daardoor groeit de pot exponentieel.
- Een typische inzet is 1–2% van de pot. Bets met een grotere edge krijgen meer.
- Waarom niet meer? Boven ~2–3% per bet daalt de verwachte groei en stijgt de
  kans op een halve pot snel. Met 15 bets tegelijk zakt het optimum verder.

Realistisch scenario (edge = gemeten CLV), alle 15 competities, ~570 bets per seizoen:

| | na 1 seizoen | na 3 seizoenen |
|---|---|---|
| ½ Kelly – mediaan | €116 | €157 |
| ½ Kelly – slechtste 10% | €74 | €69 |
| kans op winst | 65% | 76% |
| kans dat de pot ooit onder €50 komt | 2% | 9% |

## 5. Competities

De 8 extra competities (Championship, 2. Bundesliga, Segunda, Serie B, Ligue 2,
Jupiler Pro League, Süper Lig, Scottish Premiership) hebben een vergelijkbare CLV
(~+3%). Ze ongeveer **verdubbelen tot verdrievoudigen het aantal bets**. Meer bets met
dezelfde edge geeft meer groei. Dat is een grotere hefboom dan een hogere inzet per bet.

## Bronnen
- [Pinnacle API-documentatie (gesloten sinds 23-07-2025)](https://github.com/pinnacleapi/pinnacleapi-documentation)
- [The Odds API – bookmakers per regio](https://the-odds-api.com/sports-odds-data/bookmaker-apis.html)
- [OddsPapi – TOTO NL](https://oddspapi.io/sportsbooks/toto-nl), [BetCity NL](https://oddspapi.io/sportsbooks/betcity-nl), [Unibet NL](https://oddspapi.io/sportsbooks/unibet-nl)
- [Odds-API.io – Pinnacle shutdown alternatives](https://odds-api.io/blog/pinnacle-api-shutdown-alternatives)
- [Betfair verlaat Nederland – CasinoNieuws](https://www.casinonieuws.nl/online/betfair-nederland/)
- [Polymarket-dwangsom – NL Times](https://nltimes.nl/2026/02/17/dutch-regulator-threatens-polymarket-eu420k-weekly-fines-unlicensed-gambling)
- [KSA waarschuwt sportbonden voor prediction markets](https://www.cardplayer.com/nl/ksa-waarschuwt-sportbonden-prediction-markets)
- [BetCity, bet365 vergunning tot 2031](https://www.gamblinginsider.com/nl/?p=109312)
