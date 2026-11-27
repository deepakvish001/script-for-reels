#!/usr/bin/env python3
"""
jyotish.py - calculation engine for the kundali-jyotish skill.

Sidereal (Vedic) astronomy on top of the Swiss Ephemeris (pyswisseph, built-in
Moshier ephemeris, so no data files are needed). Every number a reading relies
on should come from here, so the analysis never rests on mental arithmetic.

Subcommands
  chart      Full natal chart: panchang, planets (nakshatra, pada, KP sub lord,
             dignity, combustion, avastha), whole-sign houses, KP cusps and
             significators, 16 vargas (D1-D60), aspects, lordships, yoga/dosha
             candidates, ashtakavarga (BAV/SAV), chara karakas, arudhas,
             Vimshottari dasha (5 levels around --asof), transits at --asof,
             Sade Sati windows, birth-time sensitivity.
  transits   Ingresses, stations and eclipses in a date range, plus a
             day-by-day (or month-by-month) table with tarabala, chandrabala,
             chandrashtama and the running dasha.
  day        One day hour by hour: sunrise/sunset, 24 horas, 16 choghadiyas,
             Rahu kaal / Yamaganda / Gulika / Abhijit, rising-sign windows
             mapped to natal houses, tithi/nakshatra changes, Prana dashas.
  dasha      Vimshottari periods to any depth for a date range. Works WITHOUT
             pyswisseph if you pass --moon-lon (sidereal Moon from a report).
  varshphal  Tajik solar return for a year: exact moment, Varsha lagna,
             Muntha, planets.

Examples
  python3 jyotish.py chart --date 1996-03-14 --time 06:40 --tz Asia/Kolkata \
      --lat 22.7196 --lon 75.8577 --place Indore --asof 2026-11-27
  python3 jyotish.py day --date 1996-03-14 --time 06:40 --tz Asia/Kolkata \
      --lat 22.7196 --lon 75.8577 --day 2026-11-28
  python3 jyotish.py transits ... --from 2026-12-01 --to 2027-11-30 --monthly
  python3 jyotish.py dasha --date 1996-03-14 --time 06:40 --tz +5:30 \
      --moon-lon 301.25 --from 2026-01-01 --to 2028-01-01 --level 3

Conventions (print-out says the same): Lahiri ayanamsa, mean node, whole-sign
houses for Parashari work, Placidus cusps only for KP, Vimshottari year of
365.2425 days, sunrise = upper limb with refraction. All are switchable.
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime, timedelta, timezone

try:
    import swisseph as swe
    HAVE_SWE = True
except ImportError:  # dasha-only mode still works
    swe = None
    HAVE_SWE = False

try:
    import zoneinfo
except ImportError:  # pragma: no cover
    zoneinfo = None

# --------------------------------------------------------------------------
# Static tables
# --------------------------------------------------------------------------

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGNS_HI = ["Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya", "Tula",
            "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"]
SIGN_LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus",
             "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
           "Rahu", "Ketu"]
SEVEN = PLANETS[:7]
ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
        "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra",
        "Ketu": "Ke", "Lagna": "As"}

NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
              "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
              "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
              "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
              "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
              "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
NAK_SPAN = 360.0 / 27.0
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
               "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}

GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva",
        "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva",
        "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa",
        "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya",
        "Manushya", "Deva"]
YONI = ["Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat",
        "Sheep", "Cat", "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo",
        "Tiger", "Deer", "Deer", "Dog", "Monkey", "Mongoose", "Monkey", "Lion",
        "Horse", "Lion", "Cow", "Elephant"]
NADI = ["Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi"] * 5  # period 6
NADI = NADI[:27]

TITHIS = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
          "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi",
          "Dwadashi", "Trayodashi", "Chaturdashi"]
YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
         "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
         "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
         "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
         "Brahma", "Indra", "Vaidhriti"]
KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija",
                  "Vishti (Bhadra)"]

# (exaltation sign, deep-exaltation degree)
EXALT = {"Sun": (0, 10), "Moon": (1, 3), "Mars": (9, 28), "Mercury": (5, 15),
         "Jupiter": (3, 5), "Venus": (11, 27), "Saturn": (6, 20)}
# (sign, from-degree, to-degree)
MOOLATRIKONA = {"Sun": (4, 0, 20), "Moon": (1, 3, 30), "Mars": (0, 0, 12),
                "Mercury": (5, 15, 20), "Jupiter": (8, 0, 10),
                "Venus": (6, 0, 15), "Saturn": (10, 0, 20)}
OWN = {"Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
       "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]}
NATURAL = {
    "Sun": ({"Moon", "Mars", "Jupiter"}, {"Mercury"}, {"Venus", "Saturn"}),
    "Moon": ({"Sun", "Mercury"}, {"Mars", "Jupiter", "Venus", "Saturn"}, set()),
    "Mars": ({"Sun", "Moon", "Jupiter"}, {"Venus", "Saturn"}, {"Mercury"}),
    "Mercury": ({"Sun", "Venus"}, {"Mars", "Jupiter", "Saturn"}, {"Moon"}),
    "Jupiter": ({"Sun", "Moon", "Mars"}, {"Saturn"}, {"Mercury", "Venus"}),
    "Venus": ({"Mercury", "Saturn"}, {"Mars", "Jupiter"}, {"Sun", "Moon"}),
    "Saturn": ({"Mercury", "Venus"}, {"Jupiter"}, {"Sun", "Moon", "Mars"}),
}
COMBUST_ORB = {"Moon": (12, 12), "Mars": (17, 17), "Mercury": (14, 12),
               "Jupiter": (11, 11), "Venus": (10, 8), "Saturn": (15, 15)}
SPECIAL_ASPECTS = {"Mars": [4, 7, 8], "Jupiter": [5, 7, 9],
                   "Saturn": [3, 7, 10], "Rahu": [5, 7, 9], "Ketu": [5, 7, 9]}
NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
DIG_BALA_HOUSE = {"Sun": 10, "Mars": 10, "Jupiter": 1, "Mercury": 1,
                  "Moon": 4, "Venus": 4, "Saturn": 7}

# Ashtakavarga (BPHS): houses counted from each contributor where the planet
# gets a bindu. Totals: Su48 Mo49 Ma39 Me54 Ju56 Ve52 Sa39 = SAV 337.
CONTRIBUTORS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                "Saturn", "Lagna"]
BAV_RULES = {
    "Sun": {"Sun": [1, 2, 4, 7, 8, 9, 10, 11], "Moon": [3, 6, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11], "Mercury": [3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [5, 6, 9, 11], "Venus": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [3, 4, 6, 10, 11, 12]},
    "Moon": {"Sun": [3, 6, 7, 8, 10, 11], "Moon": [1, 3, 6, 7, 10, 11],
             "Mars": [2, 3, 5, 6, 9, 10, 11], "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
             "Jupiter": [1, 4, 7, 8, 10, 11, 12], "Venus": [3, 4, 5, 7, 9, 10, 11],
             "Saturn": [3, 5, 6, 11], "Lagna": [3, 6, 10, 11]},
    "Mars": {"Sun": [3, 5, 6, 10, 11], "Moon": [3, 6, 11],
             "Mars": [1, 2, 4, 7, 8, 10, 11], "Mercury": [3, 5, 6, 11],
             "Jupiter": [6, 10, 11, 12], "Venus": [6, 8, 11, 12],
             "Saturn": [1, 4, 7, 8, 9, 10, 11], "Lagna": [1, 3, 6, 10, 11]},
    "Mercury": {"Sun": [5, 6, 9, 11, 12], "Moon": [2, 4, 6, 8, 10, 11],
                "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
                "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
                "Jupiter": [6, 8, 11, 12], "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
                "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
                "Lagna": [1, 2, 4, 6, 8, 10, 11]},
    "Jupiter": {"Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Moon": [2, 5, 7, 9, 11],
                "Mars": [1, 2, 4, 7, 8, 10, 11],
                "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
                "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
                "Venus": [2, 5, 6, 9, 10, 11], "Saturn": [3, 5, 6, 12],
                "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11]},
    "Venus": {"Sun": [8, 11, 12], "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
              "Mars": [3, 5, 6, 9, 11, 12], "Mercury": [3, 5, 6, 9, 11],
              "Jupiter": [5, 8, 9, 10, 11],
              "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
              "Saturn": [3, 4, 5, 8, 9, 10, 11],
              "Lagna": [1, 2, 3, 4, 5, 8, 9, 11]},
    "Saturn": {"Sun": [1, 2, 4, 7, 8, 10, 11], "Moon": [3, 6, 11],
               "Mars": [3, 5, 6, 10, 11, 12], "Mercury": [6, 8, 9, 10, 11, 12],
               "Jupiter": [5, 6, 11, 12], "Venus": [6, 11, 12],
               "Saturn": [3, 5, 6, 11], "Lagna": [1, 3, 4, 6, 10, 11]},
}
KAKSHYA_LORDS = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury",
                 "Moon", "Lagna"]

# Classical gochar from the natal Moon (Phaladeepika): favourable house -> vedha house
GOCHAR_VEDHA = {
    "Sun": {3: 9, 6: 12, 10: 4, 11: 5},
    "Moon": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "Mars": {3: 12, 6: 9, 11: 5},
    "Mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    "Jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    "Venus": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 3, 12: 6},
    "Saturn": {3: 12, 6: 9, 11: 5},
    "Rahu": {3: 12, 6: 9, 11: 5},
    "Ketu": {3: 12, 6: 9, 11: 5},
}
NO_VEDHA_PAIRS = {frozenset(("Sun", "Saturn")), frozenset(("Moon", "Mercury"))}

HORA_ORDER = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
WEEKDAY_LORD = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]  # Mon..Sun
WEEKDAY_NAME = ["Monday (Somvar)", "Tuesday (Mangalvar)", "Wednesday (Budhvar)",
                "Thursday (Guruvar)", "Friday (Shukravar)", "Saturday (Shanivar)",
                "Sunday (Ravivar)"]
CHOGHADIYA = {"Sun": "Udveg", "Venus": "Chal", "Mercury": "Labh",
              "Moon": "Amrit", "Saturn": "Kaal", "Jupiter": "Shubh",
              "Mars": "Rog"}
CHOG_QUALITY = {"Amrit": "best", "Shubh": "good", "Labh": "good",
                "Chal": "neutral (ok for travel)", "Udveg": "avoid",
                "Kaal": "avoid", "Rog": "avoid"}
RAHU_KAAL_PART = [2, 7, 5, 6, 4, 3, 8]   # Mon..Sun, 1-based eighth of the day
YAMAGANDA_PART = [4, 3, 2, 1, 7, 6, 5]
GULIKA_PART = [6, 5, 4, 3, 2, 1, 7]
TARA = ["Janma (mixed)", "Sampat (good)", "Vipat (bad)", "Kshema (good)",
        "Pratyari (bad)", "Sadhaka (good)", "Naidhana/Vadha (bad)",
        "Mitra (good)", "Parama Mitra (good)"]

AYANAMSAS = {}
if HAVE_SWE:
    AYANAMSAS = {"lahiri": swe.SIDM_LAHIRI, "kp": swe.SIDM_KRISHNAMURTI,
                 "raman": swe.SIDM_RAMAN, "yukteshwar": swe.SIDM_YUKTESHWAR,
                 "true_chitra": swe.SIDM_TRUE_CITRA}

VARGAS = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
VARGA_NAMES = {1: "Rashi", 2: "Hora (wealth)", 3: "Drekkana (siblings)",
               4: "Chaturthamsa (property)", 7: "Saptamsa (children)",
               9: "Navamsa (spouse, dharma, strength)", 10: "Dasamsa (career)",
               12: "Dwadasamsa (parents)", 16: "Shodasamsa (vehicles, comforts)",
               20: "Vimsamsa (spiritual)", 24: "Chaturvimsamsa (education)",
               27: "Bhamsa (strength)", 30: "Trimsamsa (misfortune)",
               40: "Khavedamsa", 45: "Akshavedamsa", 60: "Shashtiamsa (karma)"}

# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

J2000 = datetime(2000, 1, 1, 12, 0, 0)


def jd_from_utc(dt):
    return 2451545.0 + (dt - J2000).total_seconds() / 86400.0


def utc_from_jd(jd):
    return J2000 + timedelta(days=jd - 2451545.0)


def norm(x):
    return x % 360.0


def sign_of(lon):
    return int(norm(lon) // 30) % 12


def deg_in_sign(lon):
    return norm(lon) % 30.0


def dms(x):
    x = abs(x)
    d = int(x)
    m = int((x - d) * 60)
    s = int(round(((x - d) * 60 - m) * 60))
    if s == 60:
        s, m = 0, m + 1
    if m == 60:
        m, d = 0, d + 1
    return f"{d:02d}°{m:02d}'{s:02d}\""


def fmt_lon(lon):
    return f"{SIGNS[sign_of(lon)]} {dms(deg_in_sign(lon))}"


def house_from(sign, ref_sign):
    return (sign - ref_sign) % 12 + 1


def ang_dist(a, b):
    d = abs(norm(a) - norm(b)) % 360
    return min(d, 360 - d)


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


class TZ:
    """Fixed offset (+5:30, 5.5, -04:00) or IANA zone (Asia/Kolkata).

    IANA zones apply historical offsets automatically, e.g. Indian War Time
    (UTC+6:30) for most of 1942-1945 and LMT/Madras time before 1906.
    """

    def __init__(self, spec):
        self.spec = spec
        self.fixed = None
        self.zone = None
        m = re.fullmatch(r"\s*(?:UTC|GMT)?\s*([+-]?)(\d{1,2})(?::?(\d{2}))?\s*", spec)
        if m:
            sign = -1 if m.group(1) == "-" else 1
            self.fixed = timedelta(hours=sign * int(m.group(2)),
                                   minutes=sign * int(m.group(3) or 0))
            return
        try:
            self.fixed = timedelta(hours=float(spec))
            return
        except ValueError:
            pass
        if zoneinfo is None:
            raise SystemExit("zoneinfo unavailable: pass a numeric --tz like +5:30")
        self.zone = zoneinfo.ZoneInfo(spec)

    def offset(self, local_naive):
        if self.fixed is not None:
            return self.fixed
        return local_naive.replace(tzinfo=self.zone).utcoffset()

    def to_utc(self, local_naive):
        return local_naive - self.offset(local_naive)

    def from_utc(self, utc_naive):
        if self.fixed is not None:
            return utc_naive + self.fixed
        return (utc_naive.replace(tzinfo=timezone.utc)
                .astimezone(self.zone).replace(tzinfo=None))

    @staticmethod
    def fmt_offset(td):
        mins = int(round(td.total_seconds() / 60))
        sign = "+" if mins >= 0 else "-"
        mins = abs(mins)
        return f"UTC{sign}{mins // 60:02d}:{mins % 60:02d}"


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def parse_time(s):
    s = s.strip().upper().replace(".", ":")
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p", "%I:%M%p"):
        try:
            t = datetime.strptime(s, fmt)
            return t.hour, t.minute, t.second
        except ValueError:
            continue
    raise SystemExit(f"Cannot parse time '{s}'. Use HH:MM (24h) or 'HH:MM AM'.")


def parse_moment(s, default_time="12:00"):
    """'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM' (local)."""
    if "T" in s or " " in s.strip():
        d, t = re.split(r"[T ]", s.strip(), maxsplit=1)
    else:
        d, t = s.strip(), default_time
    h, m, sec = parse_time(t)
    return parse_date(d).replace(hour=h, minute=m, second=sec)


def fmt_local(dt, with_date=True):
    return dt.strftime("%Y-%m-%d %H:%M") if with_date else dt.strftime("%H:%M")


# --------------------------------------------------------------------------
# Astronomy
# --------------------------------------------------------------------------

class Ephem:
    def __init__(self, ayanamsa="lahiri", node="mean", hindu_sunrise=False):
        if not HAVE_SWE:
            raise SystemExit(
                "pyswisseph is not installed. Run scripts/setup.sh (or "
                "`pip install pyswisseph`) and use the python it prints. "
                "Only the `dasha` command works without it (with --moon-lon).")
        if ayanamsa not in AYANAMSAS:
            raise SystemExit(f"Unknown ayanamsa {ayanamsa}; use one of {list(AYANAMSAS)}")
        swe.set_sid_mode(AYANAMSAS[ayanamsa])
        self.ayanamsa = ayanamsa
        self.node = node
        self.flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        self.rise_flags = swe.BIT_HINDU_RISING if hindu_sunrise else 0
        self.ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
                    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
                    "Venus": swe.VENUS, "Saturn": swe.SATURN,
                    "Rahu": swe.MEAN_NODE if node == "mean" else swe.TRUE_NODE}

    def lon(self, jd, p):
        if p == "Ketu":
            return norm(self.lon(jd, "Rahu") + 180)
        return swe.calc_ut(jd, self.ids[p], self.flags)[0][0]

    def lon_speed(self, jd, p):
        if p == "Ketu":
            lon, sp = self.lon_speed(jd, "Rahu")
            return norm(lon + 180), sp
        r = swe.calc_ut(jd, self.ids[p], self.flags)[0]
        return r[0], r[3]

    def planets(self, jd):
        out = {}
        for p in PLANETS:
            lon, sp = self.lon_speed(jd, p)
            out[p] = {"lon": lon, "speed": sp}
        return out

    def ayanamsa_value(self, jd):
        return swe.get_ayanamsa_ut(jd)

    def asc_mc(self, jd, lat, lon):
        try:
            cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
            sysname = "Placidus"
        except Exception:
            cusps, ascmc = swe.houses_ex(jd, lat, lon, b"O", swe.FLG_SIDEREAL)
            sysname = "Porphyry (Placidus undefined at this latitude)"
        return ascmc[0], ascmc[1], list(cusps)[:12], sysname

    def asc(self, jd, lat, lon):
        return self.asc_mc(jd, lat, lon)[0]

    def sun_event(self, jd_start, lat, lon, rise=True):
        rsmi = (swe.CALC_RISE if rise else swe.CALC_SET) | self.rise_flags
        res, tret = swe.rise_trans(jd_start, swe.SUN, rsmi, (lon, lat, 0.0),
                                   0.0, 0.0, swe.FLG_MOSEPH)
        if res != 0:
            return None
        return tret[0]


def find_change(fn, a, b, iters=40):
    """fn(jd) -> value; returns jd in (a, b] where fn first differs from fn(a)."""
    va = fn(a)
    for _ in range(iters):
        m = (a + b) / 2
        if fn(m) == va:
            a = m
        else:
            b = m
    return b


def scan_changes(fn, jd0, jd1, step):
    """All moments in [jd0, jd1] where fn's discrete value changes."""
    events = []
    t = jd0
    v = fn(t)
    while t < jd1:
        t2 = min(t + step, jd1)
        v2 = fn(t2)
        if v2 != v:
            tc = find_change(fn, t, t2)
            events.append((tc, v, fn(tc)))
            v = fn(tc)
            t = tc
            continue
        t = t2
    return events


# --------------------------------------------------------------------------
# Jyotish building blocks
# --------------------------------------------------------------------------

def nakshatra_info(lon):
    lon = norm(lon)
    idx = int(lon // NAK_SPAN)
    within = lon - idx * NAK_SPAN
    pada = int(within // (NAK_SPAN / 4)) + 1
    lord = DASHA_ORDER[idx % 9]
    # KP sub and sub-sub lords
    sub, subsub = None, None
    start_i = DASHA_ORDER.index(lord)
    acc = 0.0
    for k in range(9):
        L = DASHA_ORDER[(start_i + k) % 9]
        span = NAK_SPAN * DASHA_YEARS[L] / 120.0
        if within < acc + span or k == 8:
            sub = L
            inner = within - acc
            acc2 = 0.0
            si = DASHA_ORDER.index(L)
            for j in range(9):
                L2 = DASHA_ORDER[(si + j) % 9]
                span2 = span * DASHA_YEARS[L2] / 120.0
                if inner < acc2 + span2 or j == 8:
                    subsub = L2
                    break
                acc2 += span2
            break
        acc += span
    return {"index": idx, "name": NAKSHATRAS[idx], "pada": min(pada, 4),
            "lord": lord, "sub": sub, "subsub": subsub,
            "fraction_elapsed": within / NAK_SPAN}


def varga_sign(lon, n):
    lon = norm(lon)
    s = int(lon // 30) % 12
    d = min(lon % 30.0, 29.9999999)
    odd = (s % 2 == 0)           # Aries, Gemini ... are odd signs
    movable, fixed = s % 3 == 0, s % 3 == 1
    if n == 1:
        return s
    if n == 2:                   # Parashari hora: Leo / Cancer
        return (4 if d < 15 else 3) if odd else (3 if d < 15 else 4)
    if n == 3:
        return (s + [0, 4, 8][int(d // 10)]) % 12
    if n == 4:
        return (s + [0, 3, 6, 9][int(d // 7.5)]) % 12
    if n == 7:
        start = s if odd else s + 6
        return (start + int(d // (30 / 7))) % 12
    if n == 9:
        return int(lon * 9 // 30) % 12
    if n == 10:
        start = s if odd else s + 8
        return (start + int(d // 3)) % 12
    if n == 12:
        return (s + int(d // 2.5)) % 12
    if n == 16:
        start = 0 if movable else (4 if fixed else 8)
        return (start + int(d // 1.875)) % 12
    if n == 20:
        start = 0 if movable else (8 if fixed else 4)
        return (start + int(d // 1.5)) % 12
    if n == 24:
        start = 4 if odd else 3
        return (start + int(d // 1.25)) % 12
    if n == 27:
        return int(lon * 27 // 30) % 12
    if n == 30:
        if odd:
            for lim, sg in ((5, 0), (10, 10), (18, 8), (25, 2), (30, 6)):
                if d < lim:
                    return sg
        else:
            for lim, sg in ((5, 1), (12, 5), (20, 11), (25, 9), (30, 7)):
                if d < lim:
                    return sg
    if n == 40:
        start = 0 if odd else 6
        return (start + int(d // 0.75)) % 12
    if n == 45:
        start = 0 if movable else (4 if fixed else 8)
        return (start + int(d // (30 / 45))) % 12
    if n == 60:
        return (s + int(d // 0.5)) % 12
    raise ValueError(f"Unsupported varga D{n}")


def natural_rel(p, q):
    if p == q:
        return "self"
    fr, neu, en = NATURAL[p]
    if q in fr:
        return "friend"
    if q in en:
        return "enemy"
    return "neutral"


def compound_rel(p, q, sign_p, sign_q):
    nat = natural_rel(p, q)
    h = house_from(sign_q, sign_p)
    temp_friend = h in (2, 3, 4, 10, 11, 12)
    table_ = {("friend", True): "Great friend (Adhimitra)",
              ("friend", False): "Neutral (Sama)",
              ("neutral", True): "Friend (Mitra)",
              ("neutral", False): "Enemy (Shatru)",
              ("enemy", True): "Neutral (Sama)",
              ("enemy", False): "Great enemy (Adhishatru)"}
    return table_[(nat, temp_friend)]


def dignity(p, lon, signs):
    s = sign_of(lon)
    d = deg_in_sign(lon)
    if p in ("Rahu", "Ketu"):
        ex = 1 if p == "Rahu" else 7
        if s == ex:
            return "Exalted (common view: Rahu-Taurus / Ketu-Scorpio)"
        if s == (ex + 6) % 12:
            return "Debilitated (common view)"
        if (p == "Rahu" and s == 10) or (p == "Ketu" and s == 7):
            return "Co-ruled sign"
        return f"In {SIGN_LORD[s]}'s sign (acts like its dispositor)"
    exs, exd = EXALT[p]
    mt = MOOLATRIKONA[p]
    if s == exs and mt[0] == exs:      # Moon / Mercury: exaltation then MT
        if d < mt[1]:
            return "Exalted" + (" (deep)" if abs(d - exd) < 1 else "")
        if d < mt[2]:
            return "Moolatrikona"
        return "Own sign"
    if s == exs:
        return "Exalted" + (" (deep)" if abs(d - exd) < 1 else "")
    if s == (exs + 6) % 12:
        return "Debilitated" + (" (deep)" if abs(d - exd) < 1 else "")
    if s == mt[0] and mt[1] <= d < mt[2]:
        return "Moolatrikona"
    if s in OWN[p]:
        return "Own sign"
    lord = SIGN_LORD[s]
    return f"{compound_rel(p, lord, s, signs[lord])} in {lord}'s sign"


def combustion(p, lon, sun_lon, retro):
    if p not in COMBUST_ORB:
        return None
    orb = COMBUST_ORB[p][1 if retro else 0]
    dist = ang_dist(lon, sun_lon)
    return dist if dist <= orb else None


def baladi_avastha(lon):
    s = sign_of(lon)
    d = deg_in_sign(lon)
    names = ["Bala (infant, 25%)", "Kumara (youth, 50%)", "Yuva (adult, 100%)",
             "Vriddha (old, ~10%)", "Mrita (dead, ~0%)"]
    i = min(int(d // 6), 4)
    return names[i] if s % 2 == 0 else names[4 - i]


def aspected_signs(p, s):
    return [(s + n - 1) % 12 for n in SPECIAL_ASPECTS.get(p, [7])]


def owned_houses(p, lagna_sign):
    return sorted(house_from(sg, lagna_sign) for sg in OWN.get(p, []))


def functional_tags(p, houses):
    hs = set(houses)
    tags = []
    if hs & {4, 7, 10} and hs & {5, 9}:
        tags.append("YOGAKARAKA (owns kendra + trikona)")
    if 1 in hs:
        tags.append("Lagna lord (always important, protective)")
    if hs & {5, 9} and not (hs & {4, 7, 10}):
        tags.append("Trikona lord - functional benefic")
    if 8 in hs and 1 not in hs and p not in ("Sun", "Moon"):
        tags.append("8th lord - functional malefic / sudden changes")
    if hs & {3, 6, 11} and not (hs & {1, 5, 9}):
        tags.append("Trishadaya lord (3/6/11) - functional malefic, but upachaya growth")
    if hs & {2, 7}:
        tags.append("Maraka house lord (2/7) - health care in its periods, not death")
    if hs & {4, 7, 10} and p in NATURAL_BENEFICS and not (hs & {1, 5, 9}):
        tags.append("Kendradhipati dosha (natural benefic owning a kendra)")
    if 12 in hs and len(hs) == 1:
        tags.append("12th lord - results depend on placement")
    return tags


def ashtakavarga(signs):
    bav = {p: [0] * 12 for p in SEVEN}
    contrib = {p: {c: [0] * 12 for c in CONTRIBUTORS} for p in SEVEN}
    for p in SEVEN:
        for c, houses in BAV_RULES[p].items():
            for h in houses:
                sg = (signs[c] + h - 1) % 12
                bav[p][sg] += 1
                contrib[p][c][sg] = 1
    sav = [sum(bav[p][s] for p in SEVEN) for s in range(12)]
    assert sum(sav) == 337, "Ashtakavarga table error"
    return bav, sav, contrib


def chara_karakas(lons):
    names7 = ["AK (Atmakaraka - soul)", "AmK (Amatyakaraka - career)",
              "BK (Bhratrikaraka - siblings/guru)", "MK (Matrikaraka - mother)",
              "PK (Putrakaraka - children)", "GK (Gnatikaraka - rivals/disease)",
              "DK (Darakaraka - spouse)"]
    deg = sorted(SEVEN, key=lambda p: deg_in_sign(lons[p]), reverse=True)
    seven = list(zip(names7, deg))
    names8 = ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"]
    cand = {p: deg_in_sign(lons[p]) for p in SEVEN}
    cand["Rahu"] = 30 - deg_in_sign(lons["Rahu"])
    deg8 = sorted(cand, key=lambda p: cand[p], reverse=True)
    eight = list(zip(names8, deg8))
    return seven, eight


def arudha(house, lagna_sign, signs):
    hs = (lagna_sign + house - 1) % 12
    lord = SIGN_LORD[hs]
    ls = signs[lord]
    n = house_from(ls, hs)
    a = (ls + n - 1) % 12
    if a == hs or a == (hs + 6) % 12:
        a = (a + 9) % 12
    return a


# --------------------------------------------------------------------------
# Vimshottari dasha
# --------------------------------------------------------------------------

class Vimshottari:
    LEVELS = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma",
              "Prana", "Deha"]

    def __init__(self, moon_lon, birth_jd, year_days=365.2425):
        self.year_days = year_days
        n = nakshatra_info(moon_lon)
        lord = n["lord"]
        frac = n["fraction_elapsed"]
        start = birth_jd - frac * DASHA_YEARS[lord] * year_days
        self.birth_jd = birth_jd
        self.balance_years = (1 - frac) * DASHA_YEARS[lord]
        self.first_lord = lord
        self.mds = []
        i = DASHA_ORDER.index(lord)
        t = start
        for k in range(11):
            L = DASHA_ORDER[(i + k) % 9]
            dur = DASHA_YEARS[L] * year_days
            self.mds.append((L, t, t + dur))
            t += dur

    @staticmethod
    def sub(lord, a, b):
        total = b - a
        i = DASHA_ORDER.index(lord)
        t = a
        out = []
        for k in range(9):
            L = DASHA_ORDER[(i + k) % 9]
            d = total * DASHA_YEARS[L] / 120.0
            out.append((L, t, t + d))
            t += d
        return out

    def path(self, jd, depth=5):
        """[(lord, start, end)] from Mahadasha down to `depth` levels."""
        res = []
        periods = self.mds
        for _ in range(depth):
            hit = next((p for p in periods if p[1] <= jd < p[2]), None)
            if hit is None:
                break
            res.append(hit)
            periods = self.sub(*hit)
        return res

    def periods_in(self, jd0, jd1, level):
        """All periods of `level` (1=MD ... 6) overlapping [jd0, jd1)."""
        out = []

        def rec(periods, lvl, chain):
            for p in periods:
                if p[2] <= jd0 or p[1] >= jd1:
                    continue
                c = chain + [p[0]]
                if lvl == level:
                    out.append((c, p[1], p[2]))
                else:
                    rec(self.sub(*p), lvl + 1, c)
        rec(self.mds, 1, [])
        return out


# --------------------------------------------------------------------------
# Natal chart
# --------------------------------------------------------------------------

class Natal:
    def __init__(self, args):
        self.args = args
        self.eph = Ephem(args.ayanamsa, args.node, args.hindu_sunrise)
        self.tz = TZ(args.tz)
        h, m, s = parse_time(args.time)
        self.local = parse_date(args.date).replace(hour=h, minute=m, second=s)
        self.offset = self.tz.offset(self.local)
        self.utc = self.local - self.offset
        self.jd = jd_from_utc(self.utc)
        self.lat, self.lon = args.lat, args.lon
        self.compute(self.jd)

    def compute(self, jd):
        e = self.eph
        self.pl = e.planets(jd)
        self.lons = {p: self.pl[p]["lon"] for p in PLANETS}
        self.asc_lon, self.mc_lon, self.cusps, self.cusp_sys = e.asc_mc(jd, self.lat, self.lon)
        self.lagna = sign_of(self.asc_lon)
        self.signs = {p: sign_of(self.lons[p]) for p in PLANETS}
        self.signs["Lagna"] = self.lagna
        self.moon_sign = self.signs["Moon"]
        self.dasha = Vimshottari(self.lons["Moon"], jd, self.args.dasha_year)

    def retro(self, p):
        if p in ("Rahu", "Ketu"):
            return self.pl[p]["speed"] < 0
        return self.pl[p]["speed"] < 0

    def local_of(self, jd, tz=None):
        return (tz or self.tz).from_utc(utc_from_jd(jd))


def panchang_at(eph, jd):
    sun, moon = eph.lon(jd, "Sun"), eph.lon(jd, "Moon")
    elong = norm(moon - sun)
    t = int(elong // 12)
    paksha = "Shukla" if t < 15 else "Krishna"
    tn = t % 15
    if t == 14:
        tname = "Purnima"
    elif t == 29:
        tname = "Amavasya"
    else:
        tname = TITHIS[tn]
    yoga = YOGAS[int(norm(sun + moon) // NAK_SPAN) % 27]
    k = int(elong // 6)
    if k == 0:
        karana = "Kimstughna"
    elif k <= 56:
        karana = KARANA_MOVABLE[(k - 1) % 7]
    else:
        karana = ["Shakuni", "Chatushpada", "Naga"][k - 57]
    nk = nakshatra_info(moon)
    full = tname if t in (14, 29) else f"{paksha} {tname}"
    return {"tithi_index": t, "tithi": full, "paksha": paksha,
            "yoga": yoga, "karana": karana, "nakshatra": nk["name"],
            "pada": nk["pada"], "nak_index": nk["index"]}


def vedic_day(eph, local_naive, tz, lat, lon):
    """Sunrise-based weekday for a local moment. Returns (weekday_idx, sunrise_jd)."""
    midnight = local_naive.replace(hour=0, minute=0, second=0)
    jd_mid = jd_from_utc(tz.to_utc(midnight))
    sr = eph.sun_event(jd_mid, lat, lon, True)
    jd_now = jd_from_utc(tz.to_utc(local_naive))
    wd = local_naive.weekday()
    if sr is not None and jd_now < sr:
        wd = (wd - 1) % 7
        sr = eph.sun_event(jd_mid - 1, lat, lon, True)
    return wd, sr


def sade_sati_windows(eph, moon_sign, jd0, jd1):
    segs = []
    sat_sign = lambda j: sign_of(eph.lon(j, "Saturn"))
    events = scan_changes(sat_sign, jd0, jd1, 5.0)
    start = jd0
    cur = sat_sign(jd0)
    for tc, _, new in events:
        segs.append((start, tc, cur))
        start, cur = tc, new
    segs.append((start, jd1, cur))
    phase = {(moon_sign - 1) % 12: "Phase 1 (12th from Moon - rising)",
             moon_sign: "Phase 2 (over Moon - peak)",
             (moon_sign + 1) % 12: "Phase 3 (2nd from Moon - setting)"}
    dhaiya = {(moon_sign + 3) % 12: "Dhaiya / Kantaka Shani (4th from Moon)",
              (moon_sign + 7) % 12: "Ashtama Shani / Dhaiya (8th from Moon)"}
    cycles, cur_cycle = [], []
    small = []
    for a, b, sg in segs:
        if sg in phase:
            cur_cycle.append((a, b, phase[sg], sg))
        else:
            if cur_cycle:
                cycles.append(cur_cycle)
                cur_cycle = []
            if sg in dhaiya:
                small.append((a, b, dhaiya[sg], sg))
    if cur_cycle:
        cycles.append(cur_cycle)
    merged = []
    for cyc in cycles:
        if merged and cyc[0][0] - merged[-1][-1][1] < 400:
            merged[-1].extend(cyc)
        else:
            merged.append(list(cyc))
    return merged, small


# --------------------------------------------------------------------------
# Report sections
# --------------------------------------------------------------------------

def south_chart(placements, lagna_sign, title):
    """placements: dict sign -> [labels]. Fixed-sign South Indian grid."""
    grid_signs = [[11, 0, 1, 2], [10, None, None, 3], [9, None, None, 4],
                  [8, 7, 6, 5]]
    rows = []
    for r in grid_signs:
        row = []
        for sg in r:
            if sg is None:
                row.append(" ")
            else:
                lab = placements.get(sg, [])
                cell = SIGNS[sg][:3]
                if sg == lagna_sign:
                    cell += " [Lagna]"
                if lab:
                    cell += ": " + " ".join(lab)
                row.append(cell)
        rows.append(row)
    return f"**{title}** (South-Indian style, signs fixed)\n\n" + table(
        ["", "", "", ""], rows)


def house_list(signs_by_planet, lagna_sign, title, extra=None):
    rows = []
    for h in range(1, 13):
        sg = (lagna_sign + h - 1) % 12
        occ = [p for p, s in signs_by_planet.items() if s == sg and p != "Lagna"]
        rows.append([h, f"{SIGNS[sg]} ({SIGNS_HI[sg]})", SIGN_LORD[sg],
                     ", ".join(occ) or "-"] + ([extra[h]] if extra else []))
    hdr = ["House", "Sign", "Lord", "Occupants"] + (["SAV"] if extra else [])
    return f"**{title}**\n\n" + table(hdr, rows)


def detect_yogas(n):
    """Rule-based yoga/dosha CANDIDATES. The reader must still judge strength."""
    S = n.signs
    L = n.lagna
    M = n.moon_sign
    lons = n.lons
    out = []
    house = {p: house_from(S[p], L) for p in PLANETS}
    lord_of = {h: SIGN_LORD[(L + h - 1) % 12] for h in range(1, 13)}

    def asp(p, sg):
        return sg in aspected_signs(p, S[p])

    def assoc(a, b):
        if a == b:
            return None
        if S[a] == S[b]:
            return "conjunction"
        if asp(a, S[b]) and asp(b, S[a]):
            return "mutual aspect"
        if S[a] in OWN.get(b, []) and S[b] in OWN.get(a, []):
            return "sign exchange (parivartana)"
        if asp(a, S[b]):
            return f"{a} aspects {b}"
        if asp(b, S[a]):
            return f"{b} aspects {a}"
        return None

    # Gajakesari
    hj = house_from(S["Jupiter"], M)
    if hj in (1, 4, 7, 10):
        out.append(("Gajakesari yoga", f"Jupiter in house {hj} from Moon. "
                    "Strong only if Jupiter is not debilitated/combust and well placed."))
    # Budhaditya
    if S["Sun"] == S["Mercury"]:
        c = combustion("Mercury", lons["Mercury"], lons["Sun"], n.retro("Mercury"))
        out.append(("Budha-Aditya yoga", f"Sun+Mercury in house {house['Sun']}"
                    + (f"; Mercury combust ({c:.1f}° from Sun) - very common, judge by house/sign" if c else "")))
    # Chandra-Mangala
    if S["Moon"] == S["Mars"] or house_from(S["Mars"], M) == 7:
        out.append(("Chandra-Mangala yoga", "Moon and Mars conjunct/opposite: earning drive, emotional heat."))
    # Pancha Mahapurusha
    pm = {"Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
          "Venus": "Malavya", "Saturn": "Shasha"}
    for p, y in pm.items():
        dg = dignity(p, lons[p], S)
        if (dg.startswith("Exalted") or dg in ("Own sign", "Moolatrikona")):
            if house[p] in (1, 4, 7, 10):
                out.append((f"{y} (Pancha Mahapurusha) yoga",
                            f"{p} {dg} in kendra house {house[p]} from Lagna."))
            elif house_from(S[p], M) in (1, 4, 7, 10):
                out.append((f"{y} yoga from Moon (weaker)",
                            f"{p} {dg} in kendra from Moon."))
    # Raj yogas
    kendra_lords = {lord_of[h] for h in (1, 4, 7, 10)}
    trikona_lords = {lord_of[h] for h in (1, 5, 9)}
    seen = set()
    for p in SEVEN:
        oh = owned_houses(p, L)
        if set(oh) & {4, 7, 10} and set(oh) & {5, 9}:
            out.append(("Yogakaraka planet", f"{p} owns houses {oh}; its dasha/placement is key "
                        f"(placed in house {house[p]}, {dignity(p, lons[p], S)})."))
    for a in kendra_lords:
        for b in trikona_lords:
            key = frozenset((a, b))
            if a == b or key in seen:
                continue
            seen.add(key)
            r = assoc(a, b)
            if r:
                out.append(("Raj yoga (kendra-trikona lords)",
                            f"{a} (lord {owned_houses(a, L)}) & {b} (lord {owned_houses(b, L)}): {r}."))
    # Dhana yoga
    wealth = {2: lord_of[2], 11: lord_of[11]}
    for h, a in wealth.items():
        for h2 in (1, 5, 9, 2, 11):
            b = lord_of[h2]
            key = frozenset((a, b, "dhana"))
            if a == b or key in seen or h2 == h:
                continue
            seen.add(key)
            r = assoc(a, b)
            if r:
                out.append(("Dhana yoga candidate",
                            f"{ordinal(h)} lord {a} with {ordinal(h2)} lord {b}: {r}."))
    # Viparita Raj
    for h, nm in ((6, "Harsha"), (8, "Sarala"), (12, "Vimala")):
        p = lord_of[h]
        if house[p] in (6, 8, 12):
            out.append((f"Viparita Raj yoga ({nm})", f"{ordinal(h)} lord {p} in house {house[p]}: gains through adversity; strongest if unafflicted and not also a trikona lord."))
    # Parivartana
    for i, a in enumerate(SEVEN):
        for b in SEVEN[i + 1:]:
            if S[a] in OWN[b] and S[b] in OWN[a]:
                hs = {house[a], house[b]}
                kind = ("Dainya (involves 6/8/12)" if hs & {6, 8, 12}
                        else "Khala (involves 3)" if 3 in hs else "Maha")
                out.append(("Parivartana (exchange) yoga", f"{a} (house {house[a]}) <-> {b} (house {house[b]}): {kind}."))
    # Neecha bhanga
    for p in SEVEN:
        if not dignity(p, lons[p], S).startswith("Debilitated"):
            continue
        ds = S[p]
        reasons = []
        disp = SIGN_LORD[ds]
        ex_lord = SIGN_LORD[EXALT[p][0]]
        exalted_here = [q for q in SEVEN if EXALT[q][0] == ds]
        for q, why in [(disp, "dispositor (lord of debilitation sign)"),
                       (ex_lord, "lord of its exaltation sign")] + [
                (q, "planet exalted in that sign") for q in exalted_here]:
            hl, hm = house_from(S[q], L), house_from(S[q], M)
            if hl in (1, 4, 7, 10) or hm in (1, 4, 7, 10):
                reasons.append(f"{why} {q} in kendra (L{hl}/M{hm})")
        if asp(disp, ds) and disp != p:
            reasons.append(f"aspected by dispositor {disp}")
        if varga_sign(lons[p], 9) == EXALT[p][0]:
            reasons.append("exalted in navamsa")
        if S[disp] in OWN[p]:
            reasons.append(f"exchange with dispositor {disp}")
        out.append(("Debilitated planet" + (" - NEECHA BHANGA candidate" if reasons else ""),
                    f"{p} in {SIGNS[ds]} (house {house[p]}). " +
                    ("; ".join(reasons) if reasons else "No standard cancellation found.")))
    # Moon-based
    others = [p for p in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")]
    in2 = [p for p in others if house_from(S[p], M) == 2]
    in12 = [p for p in others if house_from(S[p], M) == 12]
    if in2 and in12:
        out.append(("Durudhara yoga", f"Planets 2nd ({', '.join(in2)}) and 12th ({', '.join(in12)}) from Moon."))
    elif in2:
        out.append(("Sunapha yoga", f"{', '.join(in2)} in 2nd from Moon."))
    elif in12:
        out.append(("Anapha yoga", f"{', '.join(in12)} in 12th from Moon."))
    else:
        cancel = [p for p in others + ["Sun"] if house_from(S[p], L) in (1, 4, 7, 10) and p != "Sun"]
        conj = [p for p in others if S[p] == M]
        out.append(("Kemadruma yoga candidate",
                    "No planet in 2nd/12th from Moon. " +
                    (f"Cancellation factors: planets in kendra from Lagna {cancel}; "
                     f"conjunct Moon {conj}." if cancel or conj else "No common cancellation found.")))
    adhi = [p for p in ("Mercury", "Jupiter", "Venus") if house_from(S[p], M) in (6, 7, 8)]
    if adhi:
        out.append(("Adhi yoga" + (" (full)" if len(adhi) == 3 else " (partial)"),
                    f"Benefics in 6/7/8 from Moon: {', '.join(adhi)}."))
    am = [p for p in ("Mercury", "Jupiter", "Venus") if house[p] == 10 or house_from(S[p], M) == 10]
    if am:
        out.append(("Amala yoga", f"Natural benefic in 10th from Lagna/Moon: {', '.join(am)}."))
    # Kaal Sarp (modern concept)
    rahu = lons["Rahu"]
    sides = [(norm(lons[p] - rahu) < 180) for p in SEVEN]
    if all(sides) or not any(sides):
        out.append(("Kaal Sarp (modern, non-classical)",
                    "All 7 planets on one side of the Rahu-Ketu axis. Not in BPHS; never use it to frighten."))
    # Manglik
    mh = {"Lagna": house["Mars"], "Moon": house_from(S["Mars"], M),
          "Venus": house_from(S["Mars"], S["Venus"])}
    hits = [k for k, v in mh.items() if v in (1, 2, 4, 7, 8, 12)]
    if hits:
        canc = []
        dgm = dignity("Mars", lons["Mars"], S)
        if dgm.startswith("Exalted") or dgm in ("Own sign", "Moolatrikona"):
            canc.append("Mars in own/exalted sign")
        if S["Mars"] == S["Jupiter"] or asp("Jupiter", S["Mars"]):
            canc.append("Jupiter conjunct/aspects Mars")
        out.append(("Manglik (Kuja) dosha check",
                    f"Mars in house {mh['Lagna']} from Lagna, {mh['Moon']} from Moon, {mh['Venus']} from Venus; "
                    f"counts from: {', '.join(hits)}. "
                    + (f"Cancellation factors: {'; '.join(canc)}. " if canc else "")
                    + "Very common (~40-50% of charts by some counts); match with partner's chart, never a verdict alone."))
    # Combinations with nodes
    for a, b, nm in (("Jupiter", "Rahu", "Guru-Chandal"), ("Jupiter", "Ketu", "Guru-Ketu (spiritual/unconventional)"),
                     ("Saturn", "Rahu", "Shani-Rahu (Shrapit, folk term)"),
                     ("Sun", "Rahu", "Grahan (Sun-Rahu)"), ("Sun", "Ketu", "Grahan (Sun-Ketu)"),
                     ("Moon", "Rahu", "Grahan (Moon-Rahu)"), ("Moon", "Ketu", "Grahan (Moon-Ketu)")):
        if S[a] == S[b]:
            out.append((f"{nm} combination", f"{a} with {b} in house {house[a]} ({ang_dist(lons[a], lons[b]):.1f}° apart)."))
    # Graha yuddha
    war = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    for i, a in enumerate(war):
        for b in war[i + 1:]:
            if ang_dist(lons[a], lons[b]) < 1.0:
                out.append(("Graha yuddha (planetary war)", f"{a} & {b} within {ang_dist(lons[a], lons[b]):.2f}°; the one with lower latitude/longitude loses (check with software)."))
    # Vargottama
    vg = [p for p in PLANETS if varga_sign(lons[p], 9) == S[p]]
    if varga_sign(n.asc_lon, 9) == L:
        vg.append("Lagna")
    if vg:
        out.append(("Vargottama", f"Same sign in D1 and D9 (extra strength): {', '.join(vg)}."))
    return out


def transit_snapshot(n, jd, bav, sav, contrib):
    e = n.eph
    tp = e.planets(jd)
    tsigns = {p: sign_of(tp[p]["lon"]) for p in PLANETS}
    rows = []
    for p in PLANETS:
        lon = tp[p]["lon"]
        sg = tsigns[p]
        hm = house_from(sg, n.moon_sign)
        hl = house_from(sg, n.lagna)
        b = bav[p][sg] if p in bav else "-"
        kak = KAKSHYA_LORDS[int(deg_in_sign(lon) // 3.75)]
        kak_ok = "-"
        if p in contrib:
            kak_ok = "yes" if contrib[p][kak][sg] else "no"
        g = GOCHAR_VEDHA.get(p, {})
        if hm in g:
            v = g[hm]
            blockers = [q for q in PLANETS if q != p and house_from(tsigns[q], n.moon_sign) == v
                        and frozenset((p, q)) not in NO_VEDHA_PAIRS]
            gs = "favourable" + (f", VEDHA by {','.join(blockers)}" if blockers else "")
        else:
            gs = "unfavourable"
        rows.append([p, fmt_lon(lon) + (" R" if tp[p]["speed"] < 0 and p not in ("Rahu", "Ketu") else ""),
                     NAKSHATRAS[int(norm(lon) // NAK_SPAN)], hl, hm, gs, b, sav[sg],
                     f"{kak} ({kak_ok})"])
    return tsigns, tp, table(["Planet", "Transit position", "Nakshatra", "H from Lagna",
                              "H from Moon", "Classical gochar (from Moon)", "Own BAV bindus",
                              "SAV of sign", "Kakshya lord (bindu?)"], rows)


def birth_time_sensitivity(n):
    e = n.eph
    base_l = n.lagna
    base_d9 = varga_sign(n.asc_lon, 9)
    base_d10 = varga_sign(n.asc_lon, 10)
    lat, lon = n.lat, n.lon
    step = 1.0 / 1440 * 2
    fn_l = lambda j: sign_of(e.asc(j, lat, lon))
    fn_9 = lambda j: varga_sign(e.asc(j, lat, lon), 9)
    fn_10 = lambda j: varga_sign(e.asc(j, lat, lon), 10)
    fn_nk = lambda j: (nakshatra_info(e.lon(j, "Moon"))["index"],
                       nakshatra_info(e.lon(j, "Moon"))["pada"])

    def window(fn, span_min):
        span = span_min / 1440.0
        f = scan_changes(fn, n.jd, n.jd + span, step)
        b = scan_changes(lambda j: fn(2 * n.jd - j), n.jd, n.jd + span, step)
        after = (f[0][0] - n.jd) * 1440 if f else None
        before = (b[0][0] - n.jd) * 1440 if b else None
        return before, after

    rows = []
    for nm, fn, span in (("Lagna sign (D1)", fn_l, 180), ("Navamsa lagna (D9)", fn_9, 40),
                         ("Dasamsa lagna (D10)", fn_10, 40),
                         ("Moon nakshatra-pada", fn_nk, 600)):
        b, a = window(fn, span)
        rows.append([nm, f"-{b:.1f} min" if b else f"> -{span} min",
                     f"+{a:.1f} min" if a else f"> +{span} min"])
    moon_speed = n.pl["Moon"]["speed"]  # deg/day
    md_lord = n.dasha.first_lord
    days_per_min = (moon_speed / 1440.0) / NAK_SPAN * DASHA_YEARS[md_lord] * n.args.dasha_year
    note = (f"Each minute of birth-time error shifts every Vimshottari date by about "
            f"{days_per_min:.1f} days (Moon moves {moon_speed:.2f}°/day). "
            f"Asc is {deg_in_sign(n.asc_lon):.2f}° into {SIGNS[base_l]}.")
    return table(["Factor", "Unchanged if real birth was earlier by up to",
                  "...or later by up to"], rows), note


def cmd_chart(args):
    n = Natal(args)
    e = n.eph
    out = []
    asof_local = parse_moment(args.asof) if args.asof else n.tz.from_utc(datetime.utcnow())
    asof_jd = jd_from_utc(n.tz.to_utc(asof_local))
    nm = args.name or "Native"

    # 1. Inputs
    off = TZ.fmt_offset(n.offset)
    war = ""
    if n.tz.zone is not None and str(n.tz.zone) in ("Asia/Kolkata", "Asia/Calcutta") \
            and n.offset != timedelta(hours=5, minutes=30):
        war = (" **Note: historical offset applied (not +05:30) - e.g. Indian War Time "
               "1942-45 or pre-1906 local/Madras time. Confirm the recorded clock time "
               "was the official time of that day.**")
    out.append(f"# Kundali calculation sheet - {nm}\n")
    out.append(table(["Item", "Value"], [
        ["Birth (local)", f"{n.local:%Y-%m-%d %H:%M:%S} ({args.place or 'place n/a'})"],
        ["Time zone used", f"{args.tz} -> {off}{war}"],
        ["Birth (UTC)", f"{n.utc:%Y-%m-%d %H:%M:%S}"],
        ["Coordinates", f"{args.lat:.4f} N, {args.lon:.4f} E (negative = S/W)"],
        ["Julian day (UT)", f"{n.jd:.6f}"],
        ["Ayanamsa", f"{args.ayanamsa} = {dms(e.ayanamsa_value(n.jd))}"],
        ["Node / dasha year", f"{args.node} node / {args.dasha_year} days"],
        ["Analysis date (as-of)", f"{asof_local:%Y-%m-%d %H:%M}"],
    ]))

    # 2. Panchang & avakahada
    wd, sr_jd = vedic_day(e, n.local, n.tz, n.lat, n.lon)
    ss_jd = e.sun_event(sr_jd, n.lat, n.lon, False) if sr_jd else None
    pan = panchang_at(e, n.jd)
    day_birth = (sr_jd is not None and ss_jd is not None and sr_jd <= n.jd < ss_jd)
    mn = nakshatra_info(n.lons["Moon"])
    out.append("\n## 1. Panchang and basic details at birth\n")
    out.append(table(["Item", "Value"], [
        ["Vedic weekday (sunrise-based)", WEEKDAY_NAME[wd] + f", lord {WEEKDAY_LORD[wd]}"],
        ["Sunrise / sunset that day", (f"{fmt_local(n.local_of(sr_jd), False)} / " if sr_jd else "n/a / ")
         + (fmt_local(n.local_of(ss_jd), False) if ss_jd else "n/a")],
        ["Day or night birth", "Day" if day_birth else "Night"],
        ["Tithi", pan["tithi"]], ["Yoga", pan["yoga"]], ["Karana", pan["karana"]],
        ["Lagna (Ascendant)", f"{fmt_lon(n.asc_lon)} ({SIGNS_HI[n.lagna]}), lord {SIGN_LORD[n.lagna]}"],
        ["Rashi (Moon sign)", f"{SIGNS[n.moon_sign]} ({SIGNS_HI[n.moon_sign]}), lord {SIGN_LORD[n.moon_sign]}"],
        ["Janma nakshatra", f"{mn['name']} pada {mn['pada']}, lord {mn['lord']}"],
        ["Sun sign (sidereal)", SIGNS[n.signs['Sun']]],
        ["Gana / Yoni / Nadi", f"{GANA[mn['index']]} / {YONI[mn['index']]} / {NADI[mn['index']]}"],
        ["Dasha balance at birth", f"{mn['lord']} {n.dasha.balance_years:.3f} years"],
    ]))

    # 3. Planets
    out.append("\n## 2. Planetary positions (sidereal)\n")
    rows = []
    sun = n.lons["Sun"]
    an = nakshatra_info(n.asc_lon)
    rows.append(["Lagna", fmt_lon(n.asc_lon), "", an["name"], an["pada"], an["lord"],
                 an["sub"], 1, house_from(n.lagna, n.moon_sign), "-", "-", "-",
                 SIGNS[varga_sign(n.asc_lon, 9)]])
    for p in PLANETS:
        lon = n.lons[p]
        nk = nakshatra_info(lon)
        r = n.retro(p) and p not in ("Rahu", "Ketu")
        c = combustion(p, lon, sun, r)
        rows.append([p, fmt_lon(lon), "R" if r else "", nk["name"], nk["pada"], nk["lord"],
                     nk["sub"], house_from(n.signs[p], n.lagna),
                     house_from(n.signs[p], n.moon_sign), dignity(p, lon, n.signs),
                     f"combust {c:.1f}°" if c is not None else "-",
                     baladi_avastha(lon) if p in SEVEN else "-",
                     SIGNS[varga_sign(lon, 9)]])
    out.append(table(["Body", "Longitude", "R", "Nakshatra", "Pada", "Nak lord", "KP sub",
                      "House (Lagna)", "House (Moon)", "Dignity", "Combust", "Avastha",
                      "D9 sign"], rows))
    out.append("\nRahu/Ketu always move backwards (not marked). Dignity for Rahu/Ketu has several traditions.")

    # 4. Houses, lordship, aspects
    signs_pl = {p: n.signs[p] for p in PLANETS}
    bav, sav, contrib = ashtakavarga(n.signs)
    sav_by_house = {h: sav[(n.lagna + h - 1) % 12] for h in range(1, 13)}
    out.append("\n## 3. Houses (whole-sign from Lagna)\n")
    out.append(house_list(signs_pl, n.lagna, "Lagna chart (D1) house by house", sav_by_house))
    plc = {}
    for p in PLANETS:
        plc.setdefault(n.signs[p], []).append(ABBR[p] + ("(R)" if n.retro(p) and p not in ("Rahu", "Ketu") else ""))
    out.append("\n" + south_chart(plc, n.lagna, "D1 Rashi chart"))
    out.append("\n" + house_list(signs_pl, n.moon_sign, "Chandra lagna (houses from Moon)"))

    out.append("\n**Lordship and functional nature for this Lagna** (rule-based tags - verify)\n")
    rows = []
    for p in SEVEN:
        oh = owned_houses(p, n.lagna)
        rows.append([p, ", ".join(map(str, oh)), house_from(n.signs[p], n.lagna),
                     "; ".join(functional_tags(p, oh)) or "-"])
    out.append(table(["Planet", "Owns houses", "Placed in", "Tags"], rows))

    out.append("\n**Aspects (graha drishti, whole sign)**\n")
    rows = []
    for p in PLANETS:
        asg = aspected_signs(p, n.signs[p])
        tgt = []
        for sg in asg:
            occ = [q for q in PLANETS if n.signs[q] == sg and q != p]
            tgt.append(f"H{house_from(sg, n.lagna)}" + (f"({','.join(occ)})" if occ else ""))
        rows.append([p, ", ".join(tgt)])
    out.append(table(["Planet", "Aspects houses (planets there)"], rows))
    out.append("Rahu/Ketu 5/7/9 aspects follow the popular view; some authorities use only the 7th.")

    rows = []
    for p in SEVEN:
        target = DIG_BALA_HOUSE[p]
        hh = house_from(n.signs[p], n.lagna)
        dist = min((hh - target) % 12, (target - hh) % 12)
        rows.append([p, f"strongest in H{target}", f"in H{hh}",
                     ["full", "strong", "good", "medium", "weak", "weak", "nil"][dist]])
    out.append("\n**Dig bala (directional strength, approximate by house)**\n")
    out.append(table(["Planet", "Ideal", "Actual", "Dig bala"], rows))

    # 5. Divisional charts
    out.append("\n## 4. Divisional charts (Shodashvarga)\n")
    hdr = ["Body"] + [f"D{v}" for v in VARGAS]
    rows = [["Lagna"] + [SIGNS[varga_sign(n.asc_lon, v)][:3] for v in VARGAS]]
    for p in PLANETS:
        rows.append([p] + [SIGNS[varga_sign(n.lons[p], v)][:3] for v in VARGAS])
    out.append(table(hdr, rows))
    out.append("\n" + ", ".join(f"D{k}={v}" for k, v in VARGA_NAMES.items()))
    for v in (9, 10):
        vl = varga_sign(n.asc_lon, v)
        vs = {p: varga_sign(n.lons[p], v) for p in PLANETS}
        out.append("\n" + house_list(vs, vl, f"D{v} {VARGA_NAMES[v]} - Lagna {SIGNS[vl]}"))
        rows = []
        for p in SEVEN:
            sg = vs[p]
            fake = (sg * 30 + 15.0) if p not in ("Moon", "Mercury") else (sg * 30 + 25.0)
            d_ = dignity(p, fake, vs)
            if sg == EXALT[p][0]:
                d_ = "Exalted"
            elif sg == (EXALT[p][0] + 6) % 12:
                d_ = "Debilitated"
            elif sg in OWN[p]:
                d_ = "Own sign"
            rows.append([p, SIGNS[sg], d_.split(" in ")[0]])
        out.append(f"\nD{v} sign dignity (sign-level only):\n\n" + table(["Planet", f"D{v} sign", "Sign-level dignity"], rows))
    vpl = {}
    for p in PLANETS:
        vpl.setdefault(varga_sign(n.lons[p], 9), []).append(ABBR[p])
    out.append("\n" + south_chart(vpl, varga_sign(n.asc_lon, 9), "D9 Navamsa chart"))

    # 6. KP
    out.append(f"\n## 5. KP: cusps ({n.cusp_sys}, {args.ayanamsa} ayanamsa) and significators\n")
    rows = []
    for i, c in enumerate(n.cusps, 1):
        nk = nakshatra_info(c)
        rows.append([i, fmt_lon(c), SIGN_LORD[sign_of(c)], nk["lord"], nk["sub"], nk["subsub"]])
    out.append(table(["Cusp", "Longitude", "Sign lord", "Star lord", "Sub lord", "Sub-sub"], rows))

    def bhava_of(lon):
        for i in range(12):
            a, b = n.cusps[i], n.cusps[(i + 1) % 12]
            if norm(lon - a) < norm(b - a):
                return i + 1
        return 12
    pb = {p: bhava_of(n.lons[p]) for p in PLANETS}
    star = {p: nakshatra_info(n.lons[p])["lord"] for p in PLANETS}
    rows = []
    for h in range(1, 13):
        occ = [p for p in PLANETS if pb[p] == h]
        owner = SIGN_LORD[sign_of(n.cusps[h - 1])]
        a_ = [p for p in PLANETS if star[p] in occ]
        c_ = [p for p in PLANETS if star[p] == owner]
        rows.append([h, ", ".join(a_) or "-", ", ".join(occ) or "-", ", ".join(c_) or "-", owner])
    out.append("\nPlanets' bhava (Placidus/chalit): " + ", ".join(f"{p} {pb[p]}" for p in PLANETS))
    out.append("\n" + table(["House", "A: in star of occupants", "B: occupants",
                             "C: in star of owner", "D: owner"], rows))
    out.append("Rahu/Ketu also signify the houses of their sign lord, star lord and conjunct/aspecting planets (KP rule).")

    # 7. Yogas
    out.append("\n## 6. Yoga / dosha candidates (rule-based - judge strength before predicting)\n")
    out.append(table(["Combination", "Details"], detect_yogas(n)))

    # 8. Jaimini
    seven, eight = chara_karakas(n.lons)
    out.append("\n## 7. Jaimini\n")
    out.append(table(["Karaka (7-karaka scheme)", "Planet"], seven))
    out.append("\n8-karaka scheme (with Rahu): " + ", ".join(f"{k}={p}" for k, p in eight))
    ak = seven[0][1]
    km = varga_sign(n.lons[ak], 9)
    rows = [[f"A{h} ({['Arudha Lagna AL', 'Dhanarudha', 'Vikramarudha', 'Matri/Sukha', 'Mantrarudha', 'Shatrupada', 'Darapada A7', 'Mrityupada', 'Bhagyapada', 'Rajyapada A10', 'Labhapada', 'Upapada UL'][h-1]})",
             SIGNS[arudha(h, n.lagna, n.signs)], house_from(arudha(h, n.lagna, n.signs), n.lagna)] for h in range(1, 13)]
    out.append("\n" + table(["Arudha", "Sign", "House from Lagna"], rows))
    out.append(f"\nKarakamsha (AK {ak} in D9): {SIGNS[km]} - house {house_from(km, n.lagna)} from D1 Lagna, "
               f"house {house_from(km, varga_sign(n.asc_lon, 9))} from D9 Lagna. "
               "Scorpio/Aquarius arudhas use Mars/Saturn as lord (dual-lordship variants exist).")

    # 9. Ashtakavarga
    out.append("\n## 8. Ashtakavarga\n")
    rows = []
    for p in SEVEN:
        rows.append([p] + bav[p] + [sum(bav[p])])
    rows.append(["**SAV**"] + sav + [sum(sav)])
    out.append(table(["BAV"] + [s[:3] for s in SIGNS] + ["Total"], rows))
    out.append("\nSAV by house from Lagna: " + ", ".join(f"H{h}={sav_by_house[h]}" for h in range(1, 13))
               + ". Average 28; >=30 strong, <=25 weak. Transits through high-SAV signs give better results.")

    # 10. Dasha
    d = n.dasha
    out.append("\n## 9. Vimshottari dasha\n")
    rows = []
    for L, a, b in d.mds:
        if b < n.jd:
            continue
        age_a = max(0, (a - n.jd) / 365.2425)
        rows.append([L, fmt_local(n.local_of(max(a, n.jd)))[:10], fmt_local(n.local_of(b))[:10],
                     f"{age_a:.1f}-{(b - n.jd) / 365.2425:.1f}"])
        if (a - n.jd) / 365.2425 > 100:
            break
    out.append(table(["Mahadasha", "From", "To", "Age"], rows))
    path = d.path(asof_jd, 6)
    out.append(f"\n**Running on {asof_local:%Y-%m-%d}:** " + " > ".join(
        f"{d.LEVELS[i]} {p[0]} ({fmt_local(n.local_of(p[1]))[:10]} to {fmt_local(n.local_of(p[2]))[:10]})"
        if i < 3 else f"{d.LEVELS[i]} {p[0]} ({fmt_local(n.local_of(p[1]))} to {fmt_local(n.local_of(p[2]))})"
        for i, p in enumerate(path)))
    horizon = asof_jd + 365.2425 * args.years
    out.append(f"\n**Antardashas from {asof_local:%Y} for the next {args.years} years**\n")
    rows = [[" > ".join(c), fmt_local(n.local_of(a))[:10], fmt_local(n.local_of(b))[:10]]
            for c, a, b in d.periods_in(asof_jd - 365, horizon, 2)]
    out.append(table(["MD > AD", "From", "To"], rows))
    out.append("\n**Pratyantardashas for the next 18 months**\n")
    rows = [[" > ".join(c), fmt_local(n.local_of(a))[:10], fmt_local(n.local_of(b))[:10]]
            for c, a, b in d.periods_in(asof_jd, asof_jd + 548, 3)]
    out.append(table(["MD > AD > PD", "From", "To"], rows))
    out.append("\n**Sookshma dashas for the next 60 days**\n")
    rows = [[" > ".join(c), fmt_local(n.local_of(a)), fmt_local(n.local_of(b))]
            for c, a, b in d.periods_in(asof_jd, asof_jd + 60, 4)]
    out.append(table(["MD > AD > PD > SD", "From", "To"], rows))

    # 11. Transits
    tsigns, tp, ttab = transit_snapshot(n, asof_jd, bav, sav, contrib)
    out.append(f"\n## 10. Transits (gochar) on {asof_local:%Y-%m-%d %H:%M}\n")
    out.append(ttab)
    cycles, small = sade_sati_windows(e, n.moon_sign, n.jd, n.jd + 365.2425 * 100)
    out.append(f"\n**Sade Sati cycles (natal Moon in {SIGNS[n.moon_sign]})**\n")
    rows = []
    for cyc in cycles:
        a, b = cyc[0][0], cyc[-1][1]
        cur = " **<- running**" if a <= asof_jd < b else ""
        detail = "; ".join(f"{SIGNS[sg][:3]} {fmt_local(n.local_of(x))[:10]}->{fmt_local(n.local_of(y))[:10]}"
                           for x, y, _, sg in cyc)
        rows.append([f"{fmt_local(n.local_of(a))[:10]} to {fmt_local(n.local_of(b))[:10]}{cur}", detail])
    out.append(table(["Sade Sati window", "Saturn segments (incl. retrograde re-entries)"], rows))
    rows = []
    for a, b, lab, sg in small:
        if b < asof_jd - 3650 or a > asof_jd + 365.2425 * 30:
            continue
        cur = " **<- running**" if a <= asof_jd < b else ""
        rows.append([lab, f"{fmt_local(n.local_of(a))[:10]} to {fmt_local(n.local_of(b))[:10]}{cur}"])
    if rows:
        out.append("\n" + table(["Saturn Dhaiya (+-10/30 years)", "Window"], rows))

    # 12. Sensitivity
    tab, note = birth_time_sensitivity(n)
    out.append("\n## 11. Birth-time sensitivity\n")
    out.append(tab)
    out.append("\n" + note)
    out.append("\nIf a factor flips within the uncertainty of the recorded time, say so and "
               "avoid fine predictions that depend on it (D9/D10 details, PD/Sookshma dates).")

    text = "\n".join(out)
    if args.json:
        data = {"lagna": SIGNS[n.lagna], "asc_lon": n.asc_lon, "moon_sign": SIGNS[n.moon_sign],
                "planets": {p: {"lon": n.lons[p], "sign": SIGNS[n.signs[p]],
                                "house": house_from(n.signs[p], n.lagna),
                                "nakshatra": nakshatra_info(n.lons[p])} for p in PLANETS},
                "dasha_now": [(p[0], p[1], p[2]) for p in path], "sav": sav,
                "bav": bav}
        print(json.dumps(data, indent=1, default=str))
    else:
        print(text)


# --------------------------------------------------------------------------
# Transits over a range
# --------------------------------------------------------------------------

def cmd_transits(args):
    n = Natal(args)
    e = n.eph
    at_tz = TZ(args.at_tz) if args.at_tz else n.tz
    at_lat = args.at_lat if args.at_lat is not None else n.lat
    at_lon = args.at_lon if args.at_lon is not None else n.lon
    d0 = parse_date(getattr(args, "from"))
    d1 = parse_date(args.to)
    jd0 = jd_from_utc(at_tz.to_utc(d0))
    jd1 = jd_from_utc(at_tz.to_utc(d1 + timedelta(days=1)))
    loc = lambda j: fmt_local(at_tz.from_utc(utc_from_jd(j)))
    out = [f"# Transits {d0:%Y-%m-%d} to {d1:%Y-%m-%d} for {args.name or 'native'} "
           f"(Lagna {SIGNS[n.lagna]}, Moon {SIGNS[n.moon_sign]}, {NAKSHATRAS[nakshatra_info(n.lons['Moon'])['index']]})\n"]
    natal_nak = nakshatra_info(n.lons["Moon"])["index"]
    _, sav, _ = ashtakavarga(n.signs)

    # Events
    ev = []
    steps = {"Sun": 1, "Mars": 1, "Mercury": 0.5, "Jupiter": 2, "Venus": 1,
             "Saturn": 3, "Rahu": 3, "Ketu": 3}
    for p, st in steps.items():
        for tc, a, b in scan_changes(lambda j, p=p: sign_of(e.lon(j, p)), jd0, jd1, st):
            ev.append((tc, f"{p} enters {SIGNS[b]} (H{house_from(b, n.lagna)} from Lagna, "
                           f"H{house_from(b, n.moon_sign)} from Moon, SAV {sav[b]})"))
        if p in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            for tc, a, b in scan_changes(lambda j, p=p: e.lon_speed(j, p)[1] < 0, jd0, jd1, st):
                ev.append((tc, f"{p} turns {'retrograde' if b else 'direct'} at {fmt_lon(e.lon(tc, p))}"))
    # Combustion periods for Mercury/Venus/Mars/Jupiter/Saturn
    for p in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        fn = lambda j, p=p: combustion(p, e.lon(j, p), e.lon(j, "Sun"), e.lon_speed(j, p)[1] < 0) is not None
        for tc, a, b in scan_changes(fn, jd0, jd1, 1):
            ev.append((tc, f"{p} {'becomes combust' if b else 'leaves combustion'}"))
    # Eclipses
    try:
        t = jd0
        while True:
            res, tret = swe.sol_eclipse_when_glob(t, swe.FLG_MOSEPH)
            if tret[0] > jd1:
                break
            sl = e.lon(tret[0], "Sun")
            ev.append((tret[0], f"SOLAR ECLIPSE at {fmt_lon(sl)} ({NAKSHATRAS[int(sl // NAK_SPAN)]}), "
                                f"natal H{house_from(sign_of(sl), n.lagna)} from Lagna (visibility varies by place)"))
            t = tret[0] + 20
        t = jd0
        while True:
            res, tret = swe.lun_eclipse_when(t, swe.FLG_MOSEPH)
            if tret[0] > jd1:
                break
            ml = e.lon(tret[0], "Moon")
            ev.append((tret[0], f"LUNAR ECLIPSE at {fmt_lon(ml)} ({NAKSHATRAS[int(ml // NAK_SPAN)]}), "
                                f"natal H{house_from(sign_of(ml), n.lagna)} from Lagna"))
            t = tret[0] + 20
    except Exception as ex:  # pragma: no cover
        ev.append((jd0, f"(eclipse search unavailable: {ex})"))
    ev.sort()
    out.append("## Events (local time at chosen place)\n")
    out.append(table(["When", "Event"], [[loc(t), s] for t, s in ev]) if ev else "No ingress/station events.")

    if args.monthly:
        out.append("\n## Month by month (positions on the 1st and 15th, running dashas)\n")
        rows = []
        cur = d0.replace(day=1)
        while cur <= d1:
            for dd in (1, 15):
                day = cur.replace(day=dd)
                if day < d0 - timedelta(days=15) or day > d1:
                    continue
                j = jd_from_utc(at_tz.to_utc(day.replace(hour=12)))
                pos = []
                for p in ("Sun", "Mars", "Mercury", "Venus", "Jupiter", "Saturn", "Rahu"):
                    lon, sp = e.lon_speed(j, p)
                    pos.append(f"{ABBR[p]} {SIGNS[sign_of(lon)][:3]}{'R' if sp < 0 and p != 'Rahu' else ''}"
                               f"(L{house_from(sign_of(lon), n.lagna)}/M{house_from(sign_of(lon), n.moon_sign)})")
                pth = n.dasha.path(j, 3)
                rows.append([f"{day:%Y-%m-%d}", " ".join(pos), " > ".join(p[0] for p in pth)])
            m = cur.month + 1
            cur = cur.replace(year=cur.year + (m > 12), month=(m - 1) % 12 + 1)
        out.append(table(["Date", "Planets: sign (house from Lagna / Moon)", "MD > AD > PD"], rows))
    else:
        out.append(f"\n## Day by day (Moon at local sunrise; natal nakshatra {NAKSHATRAS[natal_nak]})\n")
        rows = []
        day = d0
        while day <= d1:
            wd, sr = vedic_day(e, day.replace(hour=12), at_tz, at_lat, at_lon)
            j = sr or jd_from_utc(at_tz.to_utc(day.replace(hour=6)))
            ml = e.lon(j, "Moon")
            nk = nakshatra_info(ml)
            hm = house_from(sign_of(ml), n.moon_sign)
            tara = TARA[((nk["index"] - natal_nak) % 27) % 9]
            cbf = lambda h: ("CHANDRASHTAMA (8th) - caution" if h == 8 else
                             "good" if h in (1, 3, 6, 7, 10, 11) else
                             "weak" if h in (4, 12) else "mixed")
            cb = cbf(hm)
            # moon sign / nakshatra change during the day
            nxt = scan_changes(lambda x: sign_of(e.lon(x, "Moon")), j, j + 1, 0.25)
            chg = ""
            if nxt:
                tchg = fmt_local(at_tz.from_utc(utc_from_jd(nxt[0][0])), False)
                chg = f"; -> {SIGNS[nxt[0][2]][:3]} at {tchg}"
                cb += f" -> {cbf(house_from(nxt[0][2], n.moon_sign))} from {tchg}"
            nn = scan_changes(lambda x: nakshatra_info(e.lon(x, "Moon"))["index"], j, j + 1, 0.25)
            pan = panchang_at(e, j)
            pth = n.dasha.path(j, 4)
            if nn:
                tara += (f" -> {TARA[((nn[0][2] - natal_nak) % 27) % 9]} from "
                         f"{fmt_local(at_tz.from_utc(utc_from_jd(nn[0][0])), False)}")
            nkname = nk["name"] + (f" -> {NAKSHATRAS[nn[0][2]]}" if nn else "")
            rows.append([f"{day:%a %d %b %Y}", f"{SIGNS[sign_of(ml)][:3]}{chg}", nkname,
                         f"L{house_from(sign_of(ml), n.lagna)}/M{hm}", cb, tara, pan["tithi"],
                         " > ".join(p[0] for p in pth[2:])])
            day += timedelta(days=1)
        out.append(table(["Date", "Moon sign", "Nakshatra", "Moon house (Lagna/Moon)",
                          "Chandrabala", "Tarabala", "Tithi", "PD > Sookshma"], rows))
    print("\n".join(out))


# --------------------------------------------------------------------------
# One day, hour by hour
# --------------------------------------------------------------------------

def cmd_day(args):
    n = Natal(args)
    e = n.eph
    at_tz = TZ(args.at_tz) if args.at_tz else n.tz
    lat = args.at_lat if args.at_lat is not None else n.lat
    lon = args.at_lon if args.at_lon is not None else n.lon
    day = parse_date(args.day)
    loc = lambda j: at_tz.from_utc(utc_from_jd(j))
    jd_mid = jd_from_utc(at_tz.to_utc(day))
    sr = e.sun_event(jd_mid, lat, lon, True)
    ss = e.sun_event(sr, lat, lon, False)
    sr2 = e.sun_event(ss, lat, lon, True)
    wd = day.weekday()
    lord0 = WEEKDAY_LORD[wd]
    out = [f"# {day:%A %d %B %Y} - hour by hour for {args.name or 'native'}",
           f"Place: {lat:.4f}, {lon:.4f} ({args.at_tz or args.tz}). Vedic day runs sunrise to next sunrise.\n",
           table(["Item", "Value"], [
               ["Sunrise / Sunset / next Sunrise", f"{fmt_local(loc(sr), False)} / {fmt_local(loc(ss), False)} / {fmt_local(loc(sr2))}"],
               ["Weekday lord", lord0],
               ["Natal", f"Lagna {SIGNS[n.lagna]}, Moon {SIGNS[n.moon_sign]} ({NAKSHATRAS[nakshatra_info(n.lons['Moon'])['index']]})"],
           ])]

    # Panchang changes during the day
    natal_nak = nakshatra_info(n.lons["Moon"])["index"]
    pan = panchang_at(e, sr)
    ml = e.lon(sr, "Moon")
    hm = house_from(sign_of(ml), n.moon_sign)
    def tstamp(j):
        lt = loc(j)
        return fmt_local(lt, False) if lt.date() == day.date() else fmt_local(lt)
    head = [["At sunrise", pan["tithi"], f"{pan['nakshatra']} ({TARA[((pan['nak_index'] - natal_nak) % 27) % 9]})",
             f"{SIGNS[sign_of(ml)]} (H{hm} from natal Moon{' - CHANDRASHTAMA' if hm == 8 else ''})", pan["yoga"]]]
    evs = []
    for tc, a, b in scan_changes(lambda j: panchang_at(e, j)["tithi_index"], sr, sr2, 0.1):
        evs.append((tc, [tstamp(tc), "-> " + panchang_at(e, tc + 1e-4)["tithi"], "", "", ""]))
    for tc, a, b in scan_changes(lambda j: nakshatra_info(e.lon(j, "Moon"))["index"], sr, sr2, 0.1):
        evs.append((tc, [tstamp(tc), "", f"-> {NAKSHATRAS[b]} ({TARA[((b - natal_nak) % 27) % 9]})", "", ""]))
    for tc, a, b in scan_changes(lambda j: sign_of(e.lon(j, "Moon")), sr, sr2, 0.1):
        h2 = house_from(b, n.moon_sign)
        evs.append((tc, [tstamp(tc), "", "", f"-> {SIGNS[b]} (H{h2}{' - CHANDRASHTAMA' if h2 == 8 else ''})", ""]))
    for tc, a, b in scan_changes(lambda j: YOGAS.index(panchang_at(e, j)["yoga"]), sr, sr2, 0.1):
        evs.append((tc, [tstamp(tc), "", "", "", "-> " + YOGAS[b]]))
    rows = head + [r for _, r in sorted(evs, key=lambda x: x[0])]
    out.append("\n## Panchang through the day\n")
    out.append(table(["Time", "Tithi", "Nakshatra (tarabala)", "Moon sign (chandrabala)", "Yoga"], rows))

    # Kaal periods
    part = (ss - sr) / 8.0
    seg = lambda k: (sr + (k - 1) * part, sr + k * part)
    rk, yg, gk = seg(RAHU_KAAL_PART[wd]), seg(YAMAGANDA_PART[wd]), seg(GULIKA_PART[wd])
    mu = (ss - sr) / 15.0
    ab = (sr + 7 * mu, sr + 8 * mu)
    out.append("\n## Inauspicious / auspicious windows\n")
    out.append(table(["Window", "From", "To", "Use"], [
        ["Rahu Kaal", fmt_local(loc(rk[0]), False), fmt_local(loc(rk[1]), False), "avoid starting new work"],
        ["Yamaganda", fmt_local(loc(yg[0]), False), fmt_local(loc(yg[1]), False), "avoid new starts"],
        ["Gulika Kaal", fmt_local(loc(gk[0]), False), fmt_local(loc(gk[1]), False), "avoid (repeats what is begun)"],
        ["Abhijit muhurta", fmt_local(loc(ab[0]), False), fmt_local(loc(ab[1]), False),
         "auspicious midday window" + (" (traditionally skipped on Wednesday)" if wd == 2 else "")],
    ]))

    # Choghadiya
    idx = HORA_ORDER.index(lord0)
    chog = []
    dpart, npart = (ss - sr) / 8, (sr2 - ss) / 8
    for k in range(8):
        pl = HORA_ORDER[(idx + k) % 7]
        chog.append(("Day", sr + k * dpart, sr + (k + 1) * dpart, CHOGHADIYA[pl]))
    nidx = (idx + 5) % 7
    for k in range(8):
        pl = HORA_ORDER[(nidx - 2 * k) % 7]
        chog.append(("Night", ss + k * npart, ss + (k + 1) * npart, CHOGHADIYA[pl]))

    # Rising sign windows
    asc_ev = scan_changes(lambda j: sign_of(e.asc(j, lat, lon)), sr, sr2, 1 / 144)
    asc_bounds = [(sr, sign_of(e.asc(sr, lat, lon)))] + [(t, b) for t, a, b in asc_ev]

    def asc_at(j):
        sgn = asc_bounds[0][1]
        for t, b in asc_bounds:
            if t <= j:
                sgn = b
        return sgn

    natal_in = {}
    for p in PLANETS:
        natal_in.setdefault(n.signs[p], []).append(ABBR[p])

    # Horas merged table
    rows = []
    for k in range(24):
        if k < 12:
            a = sr + k * (ss - sr) / 12
            b = sr + (k + 1) * (ss - sr) / 12
        else:
            a = ss + (k - 12) * (sr2 - ss) / 12
            b = ss + (k - 11) * (sr2 - ss) / 12
        pl = HORA_ORDER[(idx + k) % 7]
        mid = (a + b) / 2
        cg = [c[3] for c in chog if c[1] < b and c[2] > a]
        flags = []
        for nm_, w in (("Rahu Kaal", rk), ("Yamaganda", yg), ("Gulika", gk), ("Abhijit", ab)):
            if w[0] < b and w[1] > a:
                flags.append(nm_)
        rs = asc_at(mid)
        oh = owned_houses(pl, n.lagna)
        rows.append([f"{fmt_local(loc(a), False)}-{fmt_local(loc(b), False)}",
                     f"{pl} (natal lord of {','.join(map(str, oh))}; in H{house_from(n.signs[pl], n.lagna)})",
                     "/".join(dict.fromkeys(cg)), ", ".join(flags) or "-",
                     f"{SIGNS[rs][:3]} = natal H{house_from(rs, n.lagna)}"
                     + (f" ({' '.join(natal_in[rs])})" if rs in natal_in else "")])
    out.append("\n## Hour by hour (hora + choghadiya + rising sign)\n")
    out.append(table(["Time", "Hora lord (its natal role)", "Choghadiya", "Flags",
                      "Rising sign at mid-hora"], rows))
    out.append("\nChoghadiya quality: " + ", ".join(f"{k}={v}" for k, v in CHOG_QUALITY.items()))

    rows = []
    for t, b in asc_bounds:
        rows.append([fmt_local(loc(t), False), SIGNS[b], house_from(b, n.lagna),
                     " ".join(natal_in.get(b, [])) or "-"])
    out.append("\n## Rising-sign (lagna) windows\n")
    out.append(table(["From", "Rising sign", "= natal house", "Natal planets there"], rows))

    # Dashas in the day
    rows = [[" > ".join(c[2:]), fmt_local(loc(a)), fmt_local(loc(b))]
            for c, a, b in n.dasha.periods_in(sr, sr2, 5)]
    out.append("\n## Prana dashas during this day (only as reliable as the birth time)\n")
    pth = n.dasha.path(sr, 3)
    out.append("Running: " + " > ".join(p[0] for p in pth) + "\n")
    out.append(table(["PD > Sookshma > Prana", "From", "To"], rows))
    print("\n".join(out))


# --------------------------------------------------------------------------
# Dasha only / Varshphal
# --------------------------------------------------------------------------

def cmd_dasha(args):
    tz = TZ(args.tz)
    h, m, s = parse_time(args.time)
    local = parse_date(args.date).replace(hour=h, minute=m, second=s)
    jd = jd_from_utc(tz.to_utc(local))
    if args.moon_lon is not None:
        moon = args.moon_lon
    else:
        e = Ephem(args.ayanamsa, args.node)
        moon = e.lon(jd, "Moon")
    d = Vimshottari(moon, jd, args.dasha_year)
    jd0 = jd_from_utc(tz.to_utc(parse_date(getattr(args, "from")))) if getattr(args, "from") else jd
    jd1 = jd_from_utc(tz.to_utc(parse_date(args.to))) if args.to else jd + 120 * 365.25
    nk = nakshatra_info(moon)
    print(f"Moon {fmt_lon(moon)} - {nk['name']} pada {nk['pada']} - balance {d.first_lord} {d.balance_years:.4f} y\n")
    loc = lambda j: fmt_local(tz.from_utc(utc_from_jd(j)))
    rows = [[" > ".join(c), loc(max(a, jd)), loc(b)] for c, a, b in d.periods_in(max(jd0, jd), jd1, args.level)]
    print(table([" > ".join(Vimshottari.LEVELS[:args.level]), "From", "To"], rows))


def cmd_varshphal(args):
    n = Natal(args)
    e = n.eph
    year = args.year
    sun0 = n.lons["Sun"]
    try:
        guess_local = n.local.replace(year=year)
    except ValueError:
        guess_local = n.local.replace(year=year, day=28)
    j = jd_from_utc(n.tz.to_utc(guess_local))
    for _ in range(30):
        lon, sp = e.lon_speed(j, "Sun")
        diff = ((sun0 - lon + 180) % 360) - 180
        if abs(diff) < 1e-7:
            break
        j += diff / sp
    at_lat = args.at_lat if args.at_lat is not None else n.lat
    at_lon = args.at_lon if args.at_lon is not None else n.lon
    at_tz = TZ(args.at_tz) if args.at_tz else n.tz
    asc = e.asc(j, at_lat, at_lon)
    vl = sign_of(asc)
    age = year - n.local.year
    muntha = (n.lagna + age) % 12
    pl = e.planets(j)
    out = [f"# Varshphal (Tajik solar return) {year}-{year + 1} for {args.name or 'native'}",
           table(["Item", "Value"], [
               ["Solar return moment", f"{fmt_local(at_tz.from_utc(utc_from_jd(j)))} ({args.at_tz or args.tz})"],
               ["Completed age", age],
               ["Varsha lagna", f"{fmt_lon(asc)} ({SIGNS_HI[vl]}), lord {SIGN_LORD[vl]}"],
               ["Muntha", f"{SIGNS[muntha]} - house {house_from(muntha, vl)} in varsha chart, lord {SIGN_LORD[muntha]}"],
               ["Natal lagna lord", SIGN_LORD[n.lagna]],
           ]), ""]
    rows = [[p, fmt_lon(pl[p]["lon"]) + (" R" if pl[p]["speed"] < 0 and p not in ("Rahu", "Ketu") else ""),
             house_from(sign_of(pl[p]["lon"]), vl), house_from(sign_of(pl[p]["lon"]), n.lagna)] for p in PLANETS]
    out.append(table(["Planet", "Position", "House in varsha chart", "House from natal Lagna"], rows))
    out.append("\nMuntha in 1,2,3,9,10,11 of the varsha chart is favourable; 5 mixed; 4,6,7,8,12 needs care. "
               "Choose the year lord (Varsheshwar) from the five office-bearers per references/05-timing.md.")
    print("\n".join(out))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def add_birth(p, need_swe=True):
    p.add_argument("--date", required=True, help="birth date YYYY-MM-DD")
    p.add_argument("--time", required=True, help="birth time HH:MM[:SS] 24h, or '06:40 AM'")
    p.add_argument("--tz", required=True, help="IANA zone (Asia/Kolkata) or offset (+5:30)")
    if need_swe:
        p.add_argument("--lat", type=float, required=True, help="latitude, north positive")
        p.add_argument("--lon", type=float, required=True, help="longitude, east positive")
    p.add_argument("--name", default=None)
    p.add_argument("--place", default=None)
    p.add_argument("--ayanamsa", default="lahiri", choices=["lahiri", "kp", "raman", "yukteshwar", "true_chitra"])
    p.add_argument("--node", default="mean", choices=["mean", "true"])
    p.add_argument("--dasha-year", type=float, default=365.2425,
                   help="days per dasha year (365.2425 default; 365.25 or 360 in some software)")
    p.add_argument("--hindu-sunrise", action="store_true",
                   help="sunrise at disc centre without refraction (some Indian software)")


def add_at(p):
    p.add_argument("--at-lat", type=float, default=None, help="current location latitude (default birth place)")
    p.add_argument("--at-lon", type=float, default=None)
    p.add_argument("--at-tz", default=None, help="current location time zone (default birth tz)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chart", help="full natal calculation sheet")
    add_birth(c)
    c.add_argument("--asof", default=None, help="analysis date YYYY-MM-DD[THH:MM] (default now)")
    c.add_argument("--years", type=int, default=12, help="years of antardashas to list")
    c.add_argument("--json", action="store_true")
    c.set_defaults(fn=cmd_chart)

    t = sub.add_parser("transits", help="transit events + daily or monthly table")
    add_birth(t)
    add_at(t)
    t.add_argument("--from", required=True)
    t.add_argument("--to", required=True)
    t.add_argument("--monthly", action="store_true", help="month-by-month instead of daily")
    t.set_defaults(fn=cmd_transits)

    d = sub.add_parser("day", help="one day hour by hour")
    add_birth(d)
    add_at(d)
    d.add_argument("--day", required=True, help="YYYY-MM-DD")
    d.set_defaults(fn=cmd_day)

    v = sub.add_parser("dasha", help="Vimshottari periods (works without pyswisseph via --moon-lon)")
    add_birth(v, need_swe=False)
    v.add_argument("--lat", type=float, default=0.0)
    v.add_argument("--lon", type=float, default=0.0)
    v.add_argument("--moon-lon", type=float, default=None, help="sidereal Moon longitude 0-360 from the report")
    v.add_argument("--from", default=None)
    v.add_argument("--to", default=None)
    v.add_argument("--level", type=int, default=2, choices=[1, 2, 3, 4, 5, 6])
    v.set_defaults(fn=cmd_dasha)

    y = sub.add_parser("varshphal", help="Tajik solar return")
    add_birth(y)
    add_at(y)
    y.add_argument("--year", type=int, required=True)
    y.set_defaults(fn=cmd_varshphal)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
