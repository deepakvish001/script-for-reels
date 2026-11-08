# Daily Build System (just-in-time research → script → proof → shoot → post)

**Rule:** jis din post hai, uska research **usi din ya ek din pehle**. Isse har video mein latest
news, latest data aur latest status jaata hai.

| Post | Build kab | Kitna time |
|---|---|---|
| 🎬 Reel (Mon / Wed / Fri / Sun) | Usi din subah (ya pichhli raat) | Research + script + proof ~1.5 h, shoot 20 min, edit 1–1.5 h |
| 📺 Long-form (Tue / Thu / Sat) | Ek din pehle shaam | Research + script + proof ~3 h; agle din shoot 1 h, edit 4–5 h |

---

## Step 1: Topic lock (10 min)

1. Trend scan (15 min, [`00-90-day-growth-plan.md`](00-90-day-growth-plan.md#4-trend-scan-har-build-se-pehle-15-min)).
2. Koi badi news hai jismein "hidden system" angle ho aur 2 reliable sources hon? → news-peg topic.
   Nahi toh [topic bank](01-content-calendar-12-weeks.md) se us din ke pillar ka topic.
3. [`../scripts/INDEX.md`](../scripts/INDEX.md) check karo: yeh topic pehle kisi reel ya long-form
   mein aa chuka hai? Haan toh **dusra topic**. Content repeat nahi hoga.

## Step 2: Research (reel 45 min, long-form 2 h)

- Har claim ka **primary source** dhoondho: court order, government PDF, research paper, company
  filing, official data. News report tab jab primary na mile (aur news ke liye 2 alag sources).
- Har source se **exact line copy karo** (jo screenshot mein highlight hogi). Apne shabdon mein nahi,
  page par jaisa likha hai waisa.
- Live cheezein (case status, AQI, price) ke saath likho "as of <date>".
- Jo number 2 sources mein alag-alag hai, woh range mein bolo ya line hata do.

## Step 3: Script ([proof format](../templates/proof-script-template.md))

- Folder: `scripts/YYYY-MM-DD-<topic>-<reel|long>/` (date = **post** date)
- `script.md`: sirf bolne wali lines. Har factual line ke neeche 🔗 link + 🖼️ marker
  `<!--proof:L07-->`. Opinion / sawaal / joke wali lines par 🗣️ "source nahi" likho.
- `sources.json`: har marker ke liye url, exact highlight text, PDF ho toh page.

## Step 4: Proof capture (10 min)

```bash
python tools/proof/capture.py scripts/<folder>/
```

- `proof/report.md` mein har line **ok** honi chahiye.
- `text-not-found` = quote galat ya page badal gaya → quote theek karo ya line hatao.
- `failed` = site nahi khuli → doosra source dhoondho, ya network allow karo
  ([`../tools/proof/README.md`](../tools/proof/README.md)).
- **Gate:** jab tak saari factual lines ka screenshot nahi bana, shoot mat karo.

## Step 5: Shoot → edit → post

- Editor har 🖼️ screenshot ko us line par 2–3 sec screen par dikhaye (zoom on highlight).
- Reel: IG par post, **wahi file** YT Shorts par (title = hook, description = sources).
- Long-form: description mein saare links (`capture.py <folder> --links`).
- `scripts/INDEX.md` mein status **posted** karo.

---

## Claude se kaise bolein

| Aap likho | Claude kya karega |
|---|---|
| "Aaj ki reel banao" | Trend scan → topic (INDEX check) → research → reel script + sources.json → capture → PR |
| "Kal ka long-form banao" | Same, long-form ke liye (steelman + aapke liye + comment sawaal ke saath) |
| "Is hafte ke topics batao" | 7 slots ke topic suggestions (final research har din JIT) |
| "<folder> ka proof dobara chalao" | `capture.py` dobara, report ke saath |
