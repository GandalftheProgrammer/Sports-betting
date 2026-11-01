# Onderzoek: waar zit geld te verdienen?

## 1. Literatuur (kern)

- **Kaunitz, Zhong & Kreiner (2017), "Beating the bookies with their own numbers"**:
  gebruikte de *gemiddelde* marktkoers als schatting van de echte kans en wedde
  bij bookmakers die daar flink boven zaten. Dat werkte in de backtest (+3,5%) en
  in de praktijk (+6,2% in 5 maanden), totdat de bookmakers hun accounts
  beperkten. Onze `value_vs_sharp` is een scherpere variant: Pinnacle als
  referentie in plaats van het marktgemiddelde.
- **Efficiëntie van Pinnacle:** Pinnacle laat professionals toe en heeft lage
  marges. De slotkoers (closing line) is de beste publieke kansschatting. Dat is
  ook in onze data te zien: de logloss van de Pinnacle-slotkoers (0,952) is beter
  dan die van de openingskoers (0,956), en die is weer beter dan ons model (0,989).
- **Favourite-longshot bias** (o.a. Cain, Law & Peel 2000; Snowberg & Wolfers 2010):
  de marge zit vooral op underdogs. Bevestigd: longshots > 7 kosten 16–19%,
  favorieten < 1,5 ongeveer 0%. Je wint er niets aan, maar het helpt wel om de
  marge goed uit de koersen te halen (de *power*- en *Shin*-methode, Štrumbelj 2014).
- **Dixon & Coles (1997)**: Poisson-model voor voetbalscores. Dit is ons eigen
  model. Het is nuttig als extra signaal, maar het verslaat de markt niet in zijn eentje.
- **Kelly (1956) / fractionele Kelly:** optimale inzetgrootte bij een bekende edge.
  Omdat de edge onzeker is, gebruiken professionals 10–50% Kelly. Bij een bankroll
  van €100 zijn Kelly-inzetten vaak kleiner dan de minimale inzet. Dat speelt
  bij ons echt.
- **Closing Line Value (CLV):** wie structureel een betere koers krijgt dan de
  slotkoers, wint op lange termijn. CLV heeft veel minder ruis dan winst. Het is
  daarom onze belangrijkste maatstaf, zowel bij het selecteren van strategieën
  als straks live.

## 2. Bevindingen campagne #1

Zie [results/REPORT.md](../results/REPORT.md) voor alle cijfers. Samengevat:

1. **Value betting tegen Pinnacle met line shopping (`book=max`)** is de enige
   strategie met een robuuste edge: TRAIN +7,8% yield / +4,4% CLV (3.188 bets),
   VALID +7,9% / +3,9% CLV (445 bets). Beste instellingen: edge ≥ 3%, koers ≤ 6,
   1X2 én Over/Under.
2. Met een realistischer mandje (`soft` = Bet365, Bwin, William Hill, Interwetten,
   VC Bet, Ladbrokes, BetVictor, BetMGM) is de edge per bet hoger, maar zijn er
   veel minder bets. Op VALID zijn het er te weinig voor een harde conclusie.
3. **Met alleen Bet365 is er onvoldoende edge.** De conclusie: wie meer
   bookmakers kan vergelijken, heeft meer kansen. Dit bepaalt ook de keuze voor
   uitvoering (§5).
4. Eigen model: niet winstgevend, ook niet gemengd met Pinnacle. Mogelijk
   later bruikbaar als filter (bijv. alleen wedden als model én markt het eens zijn).
5. Arbitrage: elk jaar minder en dunner (~0,6% marge). Het is ook kwetsbaar:
   bookmakers sluiten "arbers" snel af. Daarom geen prioriteit.
6. Staking met €100: vlak 1–2% gaf op VALID €138–169. Bij Kelly 10% vallen
   veel inzetten onder het minimum van €0,50. Kelly 25–50% met een plafond lijkt
   het beste compromis.

## 3. Beperkingen van de backtest (waarom de echte resultaten lager uitvallen)

- `max` is de beste koers over tientallen bookmakers, waaronder exchanges en
  bookmakers die niet bereikbaar zijn. In werkelijkheid heb je een paar accounts.
- Het tijdstip van de koers is grof: football-data neemt de koersen
  vrijdagmiddag of dinsdagmiddag op. Een live systeem kan beter timen, maar de
  koers kan ook al weg zijn voordat je wedt.
- Limieten: na succes gaan de inzetlimieten omlaag. Dat is nog niet dynamisch
  gemodelleerd.
- 2025/26: Pinnacle-koersen ontbreken in ongeveer 50% van de data. Daardoor is
  de TEST-set klein (46 bets) en nog niet beslissend.

## 4. Technisch: koersdata

| Bron | Wat | Kosten |
|---|---|---|
| football-data.co.uk | Historisch, incl. Pinnacle open + slot, ~10 bookmakers + max/gem. | gratis |
| The Odds API | Live koersen van ~40 bookmakers (EU/UK), incl. Pinnacle (EU) en Betfair Exchange | gratis 500 req/mnd; ~$30/mnd voor meer |
| Betfair Exchange API | Live koersen + wedden via API | gratis, maar account nodig |

## 5. Uitvoering: waar en hoe wedden (te beslissen in fase 6)

**Mijn standpunt over VPN en buitenlandse bookmakers:** daar help ik niet bij.
Het is ook gewoon een slecht idee voor dit doel:

- Bookmakers zonder Nederlandse vergunning weigeren Nederlanders. Bij uitbetaling
  doen ze een identiteitscontrole (paspoort, adres). Wie met een VPN een ander
  land opgeeft, overtreedt de voorwaarden. De bookmaker mag dan de **winst en
  het saldo inhouden**. Bij een strategie die juist winst moet opleveren, is dat
  precies het moment waarop je het geld kwijtraakt.
- Je hebt bovendien geen bescherming (KSA, Cruks, klachtenregeling) als iets misgaat.

**Wat wel kan:**
1. **Halfautomatisch (aanbevolen start):** de agent vindt de value bets, bepaalt de
   inzet en stuurt je een melding (Telegram/e-mail) met een directe link. Jij plaatst
   de bet in ±30 seconden bij een Nederlandse bookmaker met vergunning (Bet365,
   Unibet, TOTO, BetCity, Holland Casino, Jack's, …). Line shopping over 3–5 van
   die accounts geeft de meeste kansen.
2. **Volautomatisch via API:** kan alleen bij een partij die je legaal vanuit
   Nederland mag gebruiken en die een API heeft. Betfair Exchange is daarvoor
   technisch ideaal: je wedt tegen andere spelers, je wordt niet beperkt omdat je
   wint, en er is een officiële API. Maar Betfair is momenteel niet beschikbaar
   voor Nederlanders. Dit check ik in fase 6 opnieuw, omdat dat kan veranderen.
3. **Browserautomatisering bij een Nederlandse bookmaker:** technisch mogelijk,
   maar meestal in strijd met de voorwaarden. Dan riskeer je dat je account wordt
   gesloten. Niet aan te raden.

De keuze tussen 1 en 2 hangt af van wat er in fase 6 legaal beschikbaar is. In
fase 4 (paper trading) maakt het nog niet uit.
