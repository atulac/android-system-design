# Android System Design

Android interview practice: grouped questions, worked designs and a shared
concept reference.

Website: https://atulac.github.io/android-system-design/

## Current content

- 37 mobile question and reference entries in nine study groups.
- One worked countdown-timer design, including HLD, LLD and revision notes.
- Eleven concept entries with links back to the design decisions that use them.

Reported interviews, unverified practice notes and incomplete prompts are labeled
separately. Summaries are paraphrased; public discussion links are retained.
These are independent preparation notes, not an official Google question bank.
The code snippets describe proposed designs, not a compiled Android application.

## Edit and preview

The site is plain HTML and CSS. Reading it requires no JavaScript, account,
analytics service or external asset downloads.

Edit `catalog.json` to change the question list, then run:

```sh
python3 build.py
python3 -m unittest discover -s tests
python3 build.py --check
python3 -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000/ for a local preview.

Edit a worked lesson under `problems/` directly. Use this reading order:
problem, clarification questions, what each answer changes, HLD, LLD,
sample code, FAQs and concepts. Put diagrams beside the relevant HLD or LLD
explanation. Map each clarification to a concrete decision, including how an
alternative answer would change it. Include failure cases and tests in the LLD;
keep revision notes and references after the main reading path.
Add shared definitions to `concepts/index.html`, with a backlink to the lesson
section and a short explanation of what is different in that problem.
Do not mark a catalog question solved just because a related lesson exists.

Mermaid source is retained beside the pre-rendered SVGs. If a diagram changes,
regenerate its SVG with a local Mermaid renderer; do not add a runtime CDN
dependency. Keep the adjacent text explanation consistent with the diagram.

## Publication

GitHub Pages serves the root of `main`; `.nojekyll` keeps the site as static
files. All internal links are relative so project-path hosting works.
Run the checks above before pushing. Generated `index.html` and `questions.csv`
must be committed with catalog updates.

Publish only public material. Do not add private note links, private interview
records, local absolute paths, credentials or session artifacts.
No license has been selected; public visibility alone does not grant a reuse
license. External linked material belongs to its respective owners.
