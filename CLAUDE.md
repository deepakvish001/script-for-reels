# Instructions for Claude in this repo

This repo is a script-writing playbook for Hinglish analysis/explainer videos (Instagram Reels,
YouTube Shorts, and long-form YouTube). It was built by studying the creator Rishabh Bidhuri
(@rishabh.gujjar.38). The user wants to make "thoughtful, impactful, detailed analysis" videos
in both short and long form.

## Posting system (the user's rules, Nov 2026)

- **Cadence:** YouTube long-form 2–3 / week (Tue, Thu = flex, Sat). Instagram reels on alternate days
  (Mon, Wed, Fri, Sun), and the **same reel file** goes to YouTube Shorts. Nothing else is posted
  (no carousels, stories or community posts). Details: `growth/00-90-day-growth-plan.md`.
- **Every piece has different content.** A reel is never a clip, teaser or cut-down of a long-form.
  Check `scripts/INDEX.md` and the topic bank (`growth/01-content-calendar-12-weeks.md`, long and
  reel banks are separate) before picking a topic, and add every new piece to `scripts/INDEX.md`.
- **Just-in-time:** research and write a piece on its post date or the day before, never earlier,
  so it is current. Old drafts must be re-researched on D-1 before use. Process:
  `growth/02-daily-build-system.md`. "Aaj ki reel banao" / "kal ka long-form banao" means: trend
  scan → topic → research → proof-format script → capture → PR.
- **Proof format (compulsory):** the script holds only the spoken lines. Every factual line has a
  🔗 source link (deep link with `#:~:text=` or `#page=`) **and** a highlighted screenshot of that
  exact part of the original page / PDF. Both are compulsory. Opinion / question / joke lines are
  marked 🗣️. Template: `templates/proof-script-template.md`. Tool: `tools/proof/capture.py`
  (`--fill-links`, `--renumber`, `--links`). If a screenshot cannot be captured, say so plainly and
  do not present the line as proven; a line whose text is not found on the page must be fixed or cut.
- Capturing needs the source sites to be reachable from this machine. If they are blocked, tell
  the user which hosts failed and that they can allow them in the environment's network settings
  (or run the tool on their own computer).

## When the user asks for a script

1. Read `playbook/01-creator-dna.md` first, then the relevant framework:
   - **Instagram reel (default when the user just says "reel")**: 2–3 min phone-selfie
     mini-explainer, the creator's real format. Use `playbook/08-long-reel-framework.md` +
     `templates/long-reel-script-template.md`, and see `research/03-instagram-reels-analysis.md`
     and `research/04-instagram-reels-batch-2.md` for 10 real beat-by-beat examples. Pick the
     variant (mini-explainer, inspiration bridge, brand integration, follow-the-money,
     science→tradition, emotional story, pop-culture re-read, civic "kadwa sach") that fits the topic.
   - short (≤90s, standalone topic, never a clip of a long video): `playbook/02-short-form-framework.md` +
     `templates/short-reel-script-template.md`
   - long (8–30 min YouTube): `playbook/09-youtube-long-form-dna.md` (built from 16 real transcripts,
     see `research/05-youtube-long-form-transcripts.md`) + `playbook/03-long-form-framework.md` +
     `templates/long-video-script-template.md`. `scripts/week-01/long-01-lead-ka-zeher.md` is the reference example.
   - Use `playbook/10-humor-taunt-meme-bank.md` for light humour (punch up, never down).
   - For "what should I make next / growth" requests, follow `growth/00-90-day-growth-plan.md` and
     pick from `growth/01-content-calendar-12-weeks.md`. Do a fresh trend scan (web search) for
     news-peg slots, and only use news confirmed by 2 reliable sources.
2. Use hooks and lines from `playbook/04-hook-and-line-bank.md`. Adapt them to the topic, don't
   paste them verbatim.
3. Write in **Hinglish (Roman script)**: Hindi sentence structure with natural English nouns,
   conversational, addressing the viewer as "aap". Short, confident sentences.
4. Use the **proof format** (`templates/proof-script-template.md`): numbered spoken lines, each
   factual line followed by its 🔗 link and 🖼️ `<!--proof:ID-->` marker, with the exact highlight
   text in `sources.json`. The screenshot is the on-screen visual for that line.
5. Never invent statistics, quotes, or sources. Copy the highlight text exactly as the page has it.
   For news facts use 2 independent sources (two 🔗/🖼️ pairs under the line). When sources disagree,
   say a range or cut the line.
6. For long-form, always include a **steelman** section (the other side's strongest argument)
   and a **personal takeaway** for the viewer.
7. Do not list "shorts to cut" from a long-form: reels are separate topics.
8. Save each piece as a folder `scripts/YYYY-MM-DD-<topic>-<reel|long>/` (date = post date) with
   `script.md`, `sources.json` and `proof/`, and add it to `scripts/INDEX.md`.

## Guardrails

- No blanket statements about religions, castes, or communities. Discuss specific incidents,
  data, or policies.
- Don't put defamatory claims about named people in a script. Present them as sourced
  reporting or as open questions.
- Keep opinion and fact clearly separated ("mera maanna hai..." vs "RBI ke data ke mutabik...").
- Say "allegedly" or "aarop hai" out loud whenever the source does. A chain of associations
  (follow-the-money) is not proof of intent, so say so.
- Keep physics, biology and health claims accurate even in science→tradition reels. Frame them
  as parallels, not proof.
- Never write anything that contradicts established medical safety guidance (e.g. infant safe sleep,
  vaccines, prescribed medicines), even though the reference creator did (his SIDS claim). Add
  "doctor se salah lein" to any health-adjacent script.
- Sponsor segments must be disclosed (ASCI) and must not over-promise. No gambling, betting or
  "guaranteed returns" brands.
- Don't reproduce other creators' scripts verbatim. Use the techniques, write original lines.

## Adding more research

- Analysis of more of the creator's videos goes in `research/02-video-breakdowns.md`. Use
  YouTube links (Higgsfield `video_analysis_create` works with YouTube URLs).
- Instagram is not reachable from the cloud environment. See `research/00-access-notes.md`.
- When new patterns show up, update `playbook/01-creator-dna.md`.
