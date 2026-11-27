# Dasha: judging periods

Contents: 1. Vimshottari mechanics · 2. What a dasha lord delivers · 3. MD-AD relationship ·
4. Rahu/Ketu dashas · 5. Special cases · 6. Other dasha systems · 7. Worked mini-example

## 1. Vimshottari mechanics

- 120-year cycle. Order and years: Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16,
  Saturn 19, Mercury 17. The first Mahadasha (MD) is the Moon's nakshatra lord; the balance equals
  the unelapsed part of that nakshatra.
- Each MD splits into 9 Antardashas (AD) starting with the MD lord itself, proportional to years
  (AD length = MD years x AD years / 120). Each AD splits the same way into Pratyantardashas (PD),
  then Sookshma (SD), Prana (PrD), Deha. Typical lengths: MD 6-20 years, AD 4 months-3 years, PD
  ~1 week-6 months, SD ~1-30 days, Prana hours-days.
- The script prints MD/AD/PD/SD/Prana around the as-of date and an AD table for the next N years.
- Precision: each minute of birth-time error shifts dates by ~3-9 days, so SD/Prana timing is
  meaningful only for a well-recorded birth time. Software also differs by a few days because of
  the year length (365.2425 here; some use 365.25 or 360).

## 2. What a dasha lord delivers (checklist)

For the MD lord, then the AD lord, then the PD lord, note:
1. **Houses it owns** (from Lagna, and secondarily from Moon) - the life areas activated.
2. **House it occupies** - where the results show up.
3. **Its nakshatra lord's houses** - often the deciding factor (KP's core rule: a planet gives
   results of its star lord; the sub lord says whether those results are favourable).
4. **Dignity and strength** in D1 and D9; combustion, retrogression, war, avastha.
5. **Conjunctions and aspects** it gives and receives.
6. **Natural significations** (Venus -> relationships/comforts, Saturn -> work/discipline...).
7. **Yogas it participates in** - they fructify now.
8. **Varga position** relevant to the question (D10 for career periods, D9 for marriage).
9. **Transits of the dasha lord itself** and over it (e.g. Saturn transiting over the natal MD lord).

Summarise each period as: theme, likely positives, likely challenges, advice.

## 3. MD-AD relationship

- Count the AD lord's house from the MD lord (in D1). 1, 3, 4, 5, 7, 9, 10, 11 from each other =
  cooperative; **6/8 (shadashtaka) or 2/12 relationship** = friction, the AD tends to give mixed or
  delayed results.
- Natural friendship between MD and AD lords helps; enemies create tension (e.g. Saturn MD - Sun AD).
- An AD lord placed in a dusthana from the MD lord brings the MD's difficult side forward.
- **Dasha sandhi**: the last ~6 months of an MD and the first months of the next are transitional
  (life changes, relocation, job switch, health vigilance). Mention it when a new MD is near.
- The AD of the MD lord itself (e.g. Jupiter-Jupiter) gives the MD's flavour most purely.

## 4. Rahu and Ketu dashas

Nodes have no signs of their own. They give results of (in this order of importance): the house
they occupy, their sign lord (dispositor), planets conjunct them, planets aspecting them, their
nakshatra lord. Rahu amplifies and brings unconventional/foreign/technology-related rises and
anxieties; Ketu detaches, sharpens research/spiritual depth, and can cut things off suddenly.
Rahu MD (18 years) often feels like two phases: first half restless striving, second half
consolidation if the dispositor is strong.

## 5. Special cases

- **Maraka periods** (dashas of 2nd/7th lords, or planets in 2/7): advise health check-ups and
  care; never interpret as death.
- **Functional malefic in a good house** (e.g. 11th lord in 11th): material gains with some strain.
- **Debilitated MD lord with neecha bhanga**: slow start, strong second half of the period.
- **Planets in 6/8/12** often bring the house's themes: competition and service (6), research,
  sudden changes, inheritance, insurance (8), foreign links, expenses, spiritual retreat (12).
- **Yogakaraka dasha**: usually the best period of life if the planet is strong.
- **Dasha of a planet in its own nakshatra / vargottama**: consistent, predictable results.

## 6. Other dasha systems (cross-checks)

- **Yogini dasha** (36-year cycle: Mangala 1, Pingala 2, Dhanya 3, Bhramari 4, Bhadrika 5, Ulka 6,
  Siddha 7, Sankata 8 years). Use when a report prints it; agreement with Vimshottari raises
  confidence.
- **Jaimini Chara dasha**: sign-based; strong for career and status timing (check the dasha sign's
  relation to AL, the 10th, and the karakas). Use if the report prints it; do not hand-compute.
- **Ashtottari**: traditionally used when Rahu is in a kendra/trikona from the Lagna lord and the
  birth is during day in Krishna paksha or at night in Shukla paksha (rules vary). Mention only if
  asked.
- **KP**: the dasha lord's significations come from its star lord and sub lord (houses
  signified). A period gives an event of house X when MD/AD/PD lords all signify the relevant group
  (marriage 2-7-11, job 2-6-10-11, property 4-11-12, foreign 3-9-12). Use the script's KP
  significator table.
- **Varshphal Mudda dasha** is an annual compressed Vimshottari; optional.

## 7. Worked mini-example (format to imitate)

> **Saturn MD, Venus AD** for a Leo Lagna (illustrative chart): Saturn owns the 6th and 7th and
> sits in the 10th in Taurus (Venus's sign), so it is a hard-working career influence. Venus owns
> the 3rd and 10th and sits in the 11th in Gemini. Venus is 2nd from Saturn (2/12 relationship),
> which means career gains come with money juggling. The 10th lord in the 11th, activated in its
> own AD, gives recognition and income from work. Jupiter transiting the 10th from Lagna in this
> AD, with Saturn aspecting it, is a double transit on the career house.
> **Confidence for "promotion or better job in this AD": likely** (promise + dasha + double transit).
> Advice: ask for the role change in Venus-Venus or Venus-Mercury PD; avoid conflict with
> colleagues in Venus-Mars PD (Mars is 4th/9th lord here, but placed 8th from Venus).
