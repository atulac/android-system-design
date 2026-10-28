#!/usr/bin/env python3
"""Generate the problem index and public CSV using only the standard library."""

import argparse
import csv
import html
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FAMILIES = [
    ("foundations", "Android foundations", "Review the platform topics you need before attempting the larger designs. These entries are exercises and reference notes, not full system-design problems."),
    ("timers", "Timers and playback", "Start with a local state model and clocks. Then consider background completion, notifications and recovery. Stopwatch and media playback add different behavior; they are not alternate names for a countdown."),
    ("search", "Search and large lists", "Move from local state to asynchronous API results. Practice search and pagination before keyboard suggestions; the latter also introduces text processing."),
    ("libraries", "Libraries and concurrency", "Work on API contracts, ownership and concurrent callers. The image loader and location library require their own clarification questions; do not assume the same execution model."),
    ("device", "Device data and background work", "Discuss which Android component receives data and how long work may run. Separate historical interview wording from current platform restrictions."),
    ("sync", "Offline data and synchronization", "Start with settings and a todo list, then compare collaborative and larger data models. Decide how changes are represented before choosing a conflict-resolution strategy."),
    ("live", "Shared state and live connections", "Add multiple users, delayed acknowledgments and reconnects. Decide whether the screen is showing a requested change or confirmed remote state."),
    ("media", "Full app design", "Combine networking, storage and media handling in an app-level architecture. Keep client design distinct from a full backend infrastructure exercise."),
    ("review", "Design review and debugging", "Apply the earlier topics to existing systems. Form hypotheses, choose useful measurements and explain how you would verify an improvement."),
]


def load_catalog(path=ROOT / "catalog.json"):
    entries = json.loads(path.read_text())
    ids = set()
    families = {key for key, _, _ in FAMILIES}
    for row in entries:
        if row["id"] in ids:
            raise ValueError(f"Duplicate problem ID: {row['id']}")
        ids.add(row["id"])
        if row["family"] not in families:
            raise ValueError(f"Unknown family: {row['family']}")
        if row["evidence"] not in {"Interview report", "Practice notes"}:
            raise ValueError("Invalid provenance label")
        for field in ("name", "question", "kind", "note"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ValueError(f"Missing {field}: {row['id']}")
        source = row["source"]
        if source and (not source.startswith("https://") or "notion." in source):
            raise ValueError("Only public HTTPS sources belong in the catalog")
        if row.get("lesson") and not (ROOT / row["lesson"] / "index.html").is_file():
            raise ValueError(f"Missing lesson: {row['lesson']}")
    return entries


def render_index(entries):
    esc = html.escape
    nav = []
    sections = []
    for number, (key, title, description) in enumerate(FAMILIES, 1):
        nav.append(f'<li><a href="index.html#{key}"><span class="num">{number:02}</span>{esc(title)}</a></li>')
        problems = []
        for row in (item for item in entries if item["family"] == key):
            source = (
                f'<a href="{esc(row["source"], quote=True)}" aria-label="Source for {esc(row["name"], quote=True)}">Source discussion</a>'
                if row["source"] else "No public source link available."
            )
            lesson = (
                f'<p class="lesson-link"><a href="{esc(row["lesson"])}index.html">Related countdown walkthrough</a> <span class="source-note">Includes practice extensions; not an exact solution to every reported variant.</span></p>'
                if row.get("lesson") else ""
            )
            problems.append(f'''<article class="problem" id="{row["id"]}" aria-labelledby="{row["id"]}-title">
  <div class="problem-meta">{esc(row["evidence"])} <span aria-hidden="true">/</span> {esc(row["kind"])}</div>
  <h3 id="{row["id"]}-title">{esc(row["name"])}</h3>
  <p>{esc(row["question"])}</p>
  <details><summary>Source and scope</summary><p>{esc(row["note"])}</p><p class="source-note">{source}</p></details>
{lesson}
</article>''')
        sections.append(f'''<section class="stage family" id="{key}" aria-labelledby="{key}-title">
  <div class="stage-label">{number:02} / Study group</div>
  <h2 id="{key}-title">{esc(title)}</h2>
  <p class="family-intro">{esc(description)}</p>
  {"".join(problems)}
</section>''')
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Android system-design practice: grouped interview questions, a countdown timer walkthrough with HLD and LLD, and a linked concept reference.">
  <title>Android System Design</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip" href="index.html#main">Skip to problems</a>
<header class="site-head">
  <a class="brand" href="./index.html">Android System Design</a>
  <nav aria-label="Main navigation"><a href="./index.html" aria-current="page">Problems</a><a href="problems/countdown-timer/index.html">Countdown timer</a><a href="concepts/index.html">Concepts</a></nav>
</header>
<div class="layout">
  <aside class="rail" aria-label="Problem groups">
    <details class="contents"><summary>Study groups</summary>
    <p class="rail-title">Study order</p>
    <nav aria-label="Problem families"><ol>{"".join(nav)}</ol>
    <div class="rail-extra"><a href="index.html#about">About the questions</a><a href="questions.csv" download>Download question list</a></div></nav>
    </details>
  </aside>
  <main id="main">
    <div class="eyebrow">Interview preparation</div>
    <h1>Android System Design</h1>
    <p class="lead">Interview questions and design notes for Android developers, organized by topic.</p>
    <p>Begin with a countdown timer, then work through the groups below. The order moves from a single-device state model toward networked and collaborative apps. It is a suggested study order, not an interview difficulty rating.</p>
    <section class="start-here" aria-labelledby="start-title">
      <p class="stage-label">Available walkthrough</p>
      <h2 id="start-title"><a href="problems/countdown-timer/index.html">Countdown timer</a></h2>
      <p>The problem, clarification questions, what the answers change, HLD and LLD diagrams, sample code, FAQs and concepts.</p>
      <p class="start-links"><a href="problems/countdown-timer/index.html#scope">Read from the start</a><a href="problems/countdown-timer/index.html#revision">Revision notes</a><a href="concepts/index.html">Concept reference</a></p>
    </section>
    <p class="meta">{len(entries)} questions and reference topics. Only the countdown timer has a worked walkthrough so far.</p>
    <details class="study-notes"><summary>Using this with a study partner</summary><p>Choose a problem and ask clarification questions. Explain which decision each answer changes before drawing the HLD and LLD. Then try the code, discuss the FAQs and revisit the shared concepts. Compare your reasoning before reading a walkthrough.</p></details>
    {"".join(sections)}
    <section class="stage" id="about" aria-labelledby="about-title">
      <h2 id="about-title">About the questions</h2>
      <p><strong>Interview report</strong> means a candidate publicly described a Google interview. It is self-reported evidence, not an official question bank or a prediction of what you will be asked. Several entries can come from the same interview account.</p>
      <p><strong>Practice notes</strong> are saved exercises or topics whose Google attribution has not been independently verified. Entries marked <strong>Prompt missing</strong> retain only a title and need clarification. No worked solution is implied by listing a question.</p>
      <p>Question summaries are paraphrased. Source notes distinguish reported constraints from candidate choices and added practice variants. Private note links are not included. External discussions can move, require sign-in or become unavailable.</p>
      <h3>How the material is organized</h3>
      <p>Worked problems follow this order: problem, clarification questions, answer-to-decision mapping, high-level design, low-level design, sample code, FAQs and concepts. Diagrams sit beside the design they explain. The concept reference holds shared explanations and links back to their uses. The general reference structure was informed by <a href="https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery">Hello Interview</a>, <a href="https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews">ByteByteGo</a> and <a href="https://github.com/donnemartin/system-design-primer">System Design Primer</a>; their prose and diagrams are not reproduced here.</p>
      <p class="source-note">Published scope: the mobile questions and supporting topics in the supplied preparation list. Backend-only and scope-unclear entries from the broader research collection are excluded. Reviewed 28 October 2026. Independent study notes; not affiliated with Google or the referenced publishers.</p>
    </section>
    <footer class="footer-nav"><a href="index.html#main">Back to top</a><a href="questions.csv" download>Download question list (CSV)</a><a href="https://github.com/atulac/android-system-design">Source on GitHub</a></footer>
  </main>
</div>
</body>
</html>
'''


def render_csv(entries):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Name", "Family", "Type", "Question summary (paraphrased)", "Original public link", "Source note"])
    titles = {key: title for key, title, _ in FAMILIES}
    for row in entries:
        writer.writerow([row["name"], titles[row["family"]], f'{row["evidence"]} - {row["kind"]}', row["question"], row["source"] or "", row["note"]])
    return "\ufeff" + output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated files need updating")
    args = parser.parse_args()
    entries = load_catalog()
    outputs = {"index.html": render_index(entries), "questions.csv": render_csv(entries)}
    for name, text in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != text.encode("utf-8"):
                raise SystemExit(f"Out of date: {name}; run python3 build.py")
        else:
            path.write_bytes(text.encode("utf-8"))
    print(f'{"Checked" if args.check else "Generated"} index and CSV: {len(entries)} entries, {len(FAMILIES)} groups')


if __name__ == "__main__":
    main()
