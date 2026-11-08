# Instructions for Claude in this repo

This repo is a script-writing playbook for Hinglish analysis/explainer videos (Instagram Reels,
YouTube Shorts, and long-form YouTube). It was built by studying the creator Rishabh Bidhuri
(@rishabh.gujjar.38). The user wants to make "thoughtful, impactful, detailed analysis" videos
in both short and long form.

## When the user asks for a script

1. Read `playbook/01-creator-dna.md` first, then the relevant framework:
   - **Instagram reel (default when the user just says "reel")**: 2–3 min phone-selfie
     mini-explainer, the creator's real format. Use `playbook/08-long-reel-framework.md` +
     `templates/long-reel-script-template.md`, and see `research/03-instagram-reels-analysis.md`
     and `research/04-instagram-reels-batch-2.md` for 10 real beat-by-beat examples. Pick the
     variant (mini-explainer, inspiration bridge, brand integration, follow-the-money,
     science→tradition, emotional story, pop-culture re-read, civic "kadwa sach") that fits the topic.
   - short (≤90s, Shorts or clips cut from long videos): `playbook/02-short-form-framework.md` +
     `templates/short-reel-script-template.md`
   - long (8–30 min YouTube): `playbook/03-long-form-framework.md` + `templates/long-video-script-template.md`
2. Use hooks and lines from `playbook/04-hook-and-line-bank.md`. Adapt them to the topic, don't
   paste them verbatim.
3. Write in **Hinglish (Roman script)**: Hindi sentence structure with natural English nouns,
   conversational, addressing the viewer as "aap". Short, confident sentences.
4. Use the **two-column format** (Voice | Visual) so an editor can cut from it directly.
5. Tag every factual claim with `[SRC: ...]`. If you aren't certain of a number or date, mark it
   `[VERIFY]` and name the primary source to check (NPCI, RBI, PIB, company filing, etc.).
   Never invent statistics, quotes, or sources.
6. For long-form, always include a **steelman** section (the other side's strongest argument)
   and a **personal takeaway** for the viewer.
7. For long-form, also list 3–5 shorts that can be cut from it.
8. Save new scripts to `scripts/YYYY-MM-DD-<topic>-<short|long>.md`.

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
- Don't reproduce other creators' scripts verbatim. Use the techniques, write original lines.

## Adding more research

- Analysis of more of the creator's videos goes in `research/02-video-breakdowns.md`. Use
  YouTube links (Higgsfield `video_analysis_create` works with YouTube URLs).
- Instagram is not reachable from the cloud environment. See `research/00-access-notes.md`.
- When new patterns show up, update `playbook/01-creator-dna.md`.
