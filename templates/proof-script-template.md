# Proof Script Template (reel + long-form, default format)

Script mein **sirf content** hota hai: jo line boli jaayegi, aur har factual line ka **link + highlighted
screenshot**. Dono compulsory. Editor wahi screenshot us line par screen par dikhata hai.

Folder: `scripts/YYYY-MM-DD-<topic>-<reel|long>/` → `script.md`, `sources.json`, `proof/`
Capture: `python tools/proof/capture.py scripts/<folder>/` ([details](../tools/proof/README.md))

---

## `script.md`

```markdown
# <Title>
**Format:** Reel (IG + YT Shorts) | Long-form (YouTube) · **Post:** <Day DD Mon YYYY>, 7 PM IST
**Research as of:** <YYYY-MM-DD HH:MM IST> · **Length:** ~<x> min · **Pillar:** <🔍/🧪/🧠/📰>
**Cover / thumbnail text:** "<4–6 shabd>"

## Script

**L01** · Hook
> "<bolne wali line>"

🗣️ Hook / opinion: source nahi

**L02**
> "<factual line>"

🔗 [<Publisher>, <date>: "<headline / document name>"](<deep link with #:~:text= or #page=>)
🖼️ <!--proof:L02-->⏳ screenshot pending

**L03**
> "<mera maanna hai ...>"

🗣️ Opinion: source nahi

...

## Caption / description
<line 1 sawaal> · Sources: <2–3 naam> · #tags
```

## `sources.json`

```json
{
  "script": "script.md",
  "sources": [
    {
      "id": "L02",
      "type": "html",
      "url": "https://example.org/article",
      "highlight": "exact sentence copied from the page",
      "publisher": "Example News",
      "date": "2026-11-05"
    },
    {
      "id": "L05",
      "type": "pdf",
      "url": "https://example.gov.in/report.pdf",
      "page": 12,
      "highlight": "exact sentence copied from the PDF",
      "publisher": "Ministry of X",
      "date": "2024-10-21"
    }
  ]
}
```

## Rules

1. **Har factual line** (number, date, naam, quote, "study kehti hai") = 🔗 + 🖼️. Bina proof ke line nahi.
2. Opinion, sawaal, joke, transition = 🗣️ (source nahi), aur bolte waqt **opinion jaisa** hi bolo
   ("mera maanna hai", "mujhe lagta hai").
3. `highlight` mein page ka **exact** text. Apni language mein paraphrase nahi.
4. Primary source pehle (court order, govt PDF, paper). News sirf tab, aur news fact ke liye 2 sources
   (doosra source line ke neeche ek aur 🔗 / 🖼️ pair).
5. Accused ke liye "aarop / CBI ka daawa / police ke mutabik". Naam tabhi jab zaroori ho.
6. Long-form mein: **doosri side**, **aapke liye** (takeaway), **comment sawaal** sections zaroor.
7. Health-adjacent ho toh last line: "Yeh medical advice nahi hai, doctor se salah lein."
