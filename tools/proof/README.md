# Proof tool: har line ka link + highlighted screenshot

Har script folder (`scripts/YYYY-MM-DD-<topic>-<reel|long>/`) mein 3 cheezein hoti hain:

| File | Kya hai |
|---|---|
| `script.md` | Bolne wali lines. Har factual line ke neeche 🔗 link aur `<!--proof:L07-->` marker |
| `sources.json` | Har marker ka source: `url`, page par **exact text** jo highlight karna hai, PDF ho toh `page` |
| `proof/` | Tool yahan `L07.png` jaise screenshots banata hai, aur `report.md` (kya mila, kya nahi) |

## Chalana

```bash
pip install playwright pymupdf requests && playwright install chromium
```

```bash
python tools/proof/capture.py scripts/2026-11-10-paper-leak-business-long/
```

Tool kya karta hai:
- **Web page:** Chromium mein page kholta hai, exact line dhoondhta hai, us par **peela highlight +
  laal box** lagata hai, line ko screen ke beech mein laata hai, neeche URL + capture time ki patti
  lagata hai, aur screenshot save karta hai.
- **PDF:** PDF download karta hai, line dhoondhkar **asli highlight annotation** lagata hai, aur page ka
  wahi hissa image banata hai.
- Phir `script.md` mein marker ki jagah image laga deta hai.

Agar line page par **nahi mili** (website ne text badal diya), toh screenshot `L07-unverified.png`
naam se save hota hai aur script mein **nahi** lagta. Us line ko khud check karo: quote theek karo
ya line hata do.

Sirf links chahiye (editor / description ke liye):

```bash
python tools/proof/capture.py scripts/<folder>/ --links
```

Web links mein `#:~:text=...` laga hota hai. Chrome / Edge / Android par kholte hi wahi line
**highlight hokar** khulti hai.

## Cloud session mein network

Claude ki cloud session mein source websites tabhi khulti hain jab environment ka network unhe allow
kare. Agar `report.md` mein `ERR_TUNNEL_CONNECTION_FAILED` dikhe, toh environment settings mein
**Network access** badhao (ya domains add karo), phir dobara chalao. Steps:
<https://code.claude.com/docs/en/cloud-environments#network-access>
