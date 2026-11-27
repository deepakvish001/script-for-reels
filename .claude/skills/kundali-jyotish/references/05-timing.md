# Timing: transits and the five resolutions

Contents: 1. Gochar basics · 2. Slow planets · 3. Double transit · 4. Ashtakavarga in transit ·
5. Years (incl. Varshphal) · 6. Months · 7. Weeks · 8. Days · 9. Hours · 10. Confidence wording

## 1. Gochar basics

- Read transits **from the natal Moon** (classical gochar, mind and lived experience) **and from
  the Lagna** (events and body). When both agree, the effect is clearer.
- Classical favourable houses from the Moon (Phaladeepika): Sun 3, 6, 10, 11 · Moon 1, 3, 6, 7, 10,
  11 · Mars 3, 6, 11 · Mercury 2, 4, 6, 8, 10, 11 · Jupiter 2, 5, 7, 9, 11 · Venus 1, 2, 3, 4, 5, 8,
  9, 11, 12 · Saturn, Rahu, Ketu 3, 6, 11.
- **Vedha** (obstruction): a favourable transit is blocked if another planet transits its vedha
  house (the script flags it; no vedha between Sun-Saturn and Moon-Mercury).
- Transits over natal planets matter: Saturn over natal Moon (Sade Sati peak), Jupiter over the
  natal Sun/Moon/Lagna lord (support), Rahu/Ketu over natal Moon/Sun (confusion/eclipse-like
  months), Mars over natal Saturn (friction).
- Retrograde transits repeat the theme ("the matter comes back"); stations (turning R or D) are
  sensitive dates for that planet's significations.
- Eclipses on natal Lagna/Moon/Sun degrees (within ~3-5°) mark turning points for 6 months.

## 2. Slow planets (the year-level backdrop)

| Transit | Typical theme from Moon / Lagna | Duration |
|---|---|---|
| Jupiter in 2, 5, 7, 9, 11 from Moon | growth, support, marriage/children/fortune openings | ~1 year per sign |
| Jupiter in 1, 3, 4, 6, 8, 10, 12 from Moon | slower, effort needed, travel/expense (12), health care (8) | |
| Saturn in 3, 6, 11 from Moon | achievements through effort, wins over rivals | ~2.5 years |
| Saturn in 12, 1, 2 from Moon | Sade Sati (see 03-yogas-doshas.md) | ~7.5 years |
| Saturn in 4 / 8 from Moon | Kantaka / Ashtama dhaiya | ~2.5 years |
| Saturn in 5, 7, 9, 10 from Moon | responsibility in that house's area | |
| Rahu-Ketu axis | obsession (Rahu house) vs detachment (Ketu house); 3/6/11 from Moon good | ~1.5 years |

## 3. Double transit (K. N. Rao's rule of thumb)

An event of house X is most likely when, in a supportive dasha, **both Jupiter and Saturn
influence house X or its lord** (by transit or by their aspect: Jupiter 5/7/9, Saturn 3/7/10),
from Lagna and ideally also from Moon. Examples: marriage - 7th house/7th lord (also from Venus);
job - 10th/10th lord; child - 5th/5th lord; property - 4th. Use the monthly transit table to find
the months where both influence the house, then intersect with the dasha.

## 4. Ashtakavarga in transit

- SAV of the sign being transited: ≥30 the transit gives better results; ≤25 weaker results.
- A planet's own BAV bindus in the transited sign: 0-2 difficult, 3-4 average, 5-8 good.
- **Kakshya**: each sign has 8 parts of 3°45' ruled (in order) by Saturn, Jupiter, Mars, Sun, Venus,
  Mercury, Moon, Lagna. When a slow planet transits a kakshya whose lord gave it a bindu (script
  shows "yes"), that stretch of weeks is good for its significations; "no" = flat.
- Saturn's BAV in the Sade Sati signs is the best single gauge of how heavy Sade Sati will feel.

## 5. Years

Primary: MD/AD (what life is "about"). Overlay: Jupiter, Saturn, Rahu-Ketu sign changes; Sade Sati
phase; dasha sandhi. Present a table: period, dasha, main transits, theme, confidence.

**Varshphal (Tajik annual chart)** - optional but strong for "is this year good":
- `jyotish.py varshphal --year YYYY` gives the solar-return moment, Varsha lagna, Muntha, planets.
  Use the current residence (`--at-lat/--at-lon/--at-tz`) - common practice, mention which.
- **Muntha** advances one sign per year from the natal Lagna. In houses 9, 10, 11 (best) and 1, 2, 3
  of the annual chart: favourable year; 4, 6, 7, 8, 12: caution; 5: mixed. Muntha lord's strength
  matters too.
- **Year lord (Varsheshwar)**: among the five office-bearers - Muntha lord, natal Lagna lord, Varsha
  lagna lord, Tri-rashi pati, Dina-ratri pati (lord of the Sun's sign for a day return, Moon's sign
  for night) - the strongest one that aspects the Varsha lagna rules the year. If unsure of
  tri-rashi lords, say so and rely on Muntha + Varsha lagna lord.
- Varsha lagna = natal 8th sign or Muntha in 8th = health vigilance that year.

## 6. Months

Primary: Pratyantardasha. Overlay: Sun's sign each month (Sankranti ~14th-17th of each month;
the Sun lights up the house it transits), Mars (energy/conflict), Venus (relationships, comfort),
Mercury (communication, paperwork; retrogrades = review, not launch), eclipses, Jupiter/Saturn
retrograde stations. Use `transits --from <1st of next month> --to <+12 months> --monthly` for the
positions table and the events list. Present: month, PD lord(s), key transits, theme, do/avoid.

## 7. Weeks

Primary: Sookshma dasha. Overlay: the Moon crosses all 12 houses in ~27 days (2.25 days per sign),
so each week the Moon highlights 3 houses; Chandrashtama (Moon in 8th from natal Moon) ~2.25 days
every month = low-energy days, avoid big launches; Mercury/Venus ingresses. Present per week:
dates, SD lords, Moon houses, key day(s), advice.

## 8. Days

Primary (only with a reliable birth time): Prana dasha. Overlay for every day:
- **Tarabala** - count from birth nakshatra to the day's nakshatra, remainder by 9: 1 Janma
  (mixed), 2 Sampat (wealth, good), 3 Vipat (obstacles), 4 Kshema (well-being, good), 5 Pratyari
  (opposition), 6 Sadhaka (accomplishment, good), 7 Naidhana/Vadha (avoid important starts),
  8 Mitra (friendly), 9 Parama Mitra (very friendly).
- **Chandrabala** - Moon in 1, 3, 6, 7, 10, 11 from natal Moon good; 8th = Chandrashtama (most
  cautioned); 4, 12 weak.
- Tithi (Rikta tithis 4, 9, 14 avoided for beginnings; Amavasya for rest/introspection),
  weekday lord's natal role, the day's nakshatra nature (Pushya, Rohini, Hasta, Anuradha,
  Shravana, Revati etc. are popular for starts).
The script's `transits` daily table lists all of these with change times. Present: date, Moon
house, tarabala, chandrabala, verdict (good / average / careful), best use of the day.

## 9. Hours

Run `day --day YYYY-MM-DD` with the person's current location. Combine:
1. **Hora** (1/24 of day/night, starting at sunrise with the weekday lord; order Sun, Venus,
   Mercury, Moon, Saturn, Jupiter, Mars). Traditional uses: Sun - government, authority, father;
   Moon - public, travel, home, food; Mars - property, sports, courage tasks, disputes; Mercury -
   writing, exams, trade, calls, contracts; Jupiter - learning, finance, elders, spiritual work,
   important meetings; Venus - arts, romance, shopping, luxury; Saturn - routine, labour,
   repairs; avoid starting new ventures. Weight the hora by the lord's **natal** role (a
   yogakaraka's hora is better for that person than a 6th/8th lord's hora).
2. **Choghadiya**: Amrit (best), Shubh, Labh (good), Chal (neutral, travel), Udveg, Kaal, Rog (avoid).
3. **Avoid** Rahu kaal, Yamaganda and Gulika kaal for beginnings; Abhijit muhurta (midday) is good
   (traditionally not used on Wednesday).
4. **Rising sign** at that hour = which natal house is "lit up": natal 10th rising - career calls;
   7th - meetings, partners; 11th - gains, networking; 8th/12th - avoid risky decisions, good for
   rest/research.
5. Prana dasha lord running in that window (if birth time is reliable).
Present: a table of the day's 24 horas with a verdict and best use, plus the top 2-3 windows for
the person's stated purpose. Remind once that hourly guidance is about choosing better windows,
not guaranteeing outcomes.

## 10. Confidence wording

| Label | Meaning | Hinglish phrasing |
|---|---|---|
| Likely (strong) | promise + dasha + transit agree | "Is samay ... hone ke strong yog hain" |
| Possible (medium) | two of three agree | "... ki sambhavna hai, koshish se behtar" |
| Tendency (light) | one factor only | "... ki taraf jhukav rahega" |
| Unclear | factors conflict or birth time too uncertain | "Yahan chart saaf nahi bolta; ..." |
