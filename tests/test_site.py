import csv
import importlib.util
import io
import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.headings = []
        self.scripts = 0
        self.remote_assets = []
        self.section_stack = []
        self.top_sections = []
        self.id_sections = {}
        self.nav_links = {}
        self.active_nav = None
        self.decision_rows = []
        self.active_row = None
        self.diagram_sections = {}
        self.sample_sections = []
        self.pre_depth = 0
        self.feed(source)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "section":
            if not self.section_stack:
                self.top_sections.append(attrs.get("id"))
            self.section_stack.append(attrs.get("id"))
        if "id" in attrs:
            self.ids.append(attrs["id"])
            self.id_sections[attrs["id"]] = tuple(self.section_stack)
        if tag == "nav":
            self.active_nav = attrs.get("aria-label", "")
            self.nav_links[self.active_nav] = []
        if tag in {"a", "link"} and "href" in attrs:
            self.links.append(attrs["href"])
            if tag == "a" and self.active_nav is not None:
                self.nav_links[self.active_nav].append(attrs["href"])
            if tag == "a" and self.active_row is not None:
                self.active_row["links"].append(attrs["href"])
        if tag == "tr" and "data-question" in attrs:
            self.active_row = {"question": attrs["data-question"], "links": []}
            self.decision_rows.append(self.active_row)
        if "data-render" in attrs:
            self.diagram_sections[attrs["data-render"]] = tuple(self.section_stack)
        if tag == "pre":
            self.pre_depth += 1
        if tag == "code" and self.pre_depth and "data-mermaid" not in attrs:
            self.sample_sections.append(tuple(self.section_stack))
        if re.fullmatch("h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "script":
            self.scripts += 1
        if tag in {"link", "img", "script", "iframe"}:
            url = attrs.get("src", attrs.get("href", ""))
            if url.startswith(("https:", "http:", "//")):
                self.remote_assets.append(url)

    def handle_endtag(self, tag):
        if tag == "section":
            self.section_stack.pop()
        if tag == "nav":
            self.active_nav = None
        if tag == "tr":
            self.active_row = None
        if tag == "pre":
            self.pre_depth -= 1


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = build.load_catalog()
        cls.pages = {
            path: Document(path.read_text())
            for path in ROOT.rglob("*.html")
            if ".git" not in path.parts
        }

    def test_generated_files_match_the_catalog(self):
        self.assertEqual((ROOT / "index.html").read_bytes(), build.render_index(self.entries).encode())
        self.assertEqual((ROOT / "questions.csv").read_bytes(), build.render_csv(self.entries).encode())

    def test_public_csv_preserves_summaries_and_sources(self):
        rows = list(csv.DictReader(io.StringIO(build.render_csv(self.entries))))
        self.assertEqual(len(rows), len(self.entries))
        for row, entry in zip(rows, self.entries):
            self.assertEqual(row["Question summary (paraphrased)"], entry["question"])
            self.assertEqual(row["Original public link"], entry["source"] or "")
            self.assertEqual(row["Source note"], entry["note"])

    def test_catalog_rejects_duplicate_ids_and_private_sources(self):
        for change in (
            lambda rows: rows.append(rows[0].copy()),
            lambda rows: rows[0].update(source="https://app.notion.com/p/private"),
            lambda rows: rows[0].update(family="not-a-group"),
        ):
            rows = json.loads((ROOT / "catalog.json").read_text())
            change(rows)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "catalog.json"
                path.write_text(json.dumps(rows))
                with self.assertRaises(ValueError):
                    build.load_catalog(path)

    def test_every_local_link_resolves_including_fragment(self):
        for path, doc in self.pages.items():
            for link in doc.links:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc:
                    continue
                self.assertFalse(parsed.path.startswith("/"), f"Project-path unsafe: {link}")
                target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                if target.is_dir():
                    target /= "index.html"
                self.assertTrue(target.is_relative_to(ROOT), f"Outside site: {link}")
                self.assertTrue(target.is_file(), f"{path.relative_to(ROOT)} -> {link}")
                if parsed.fragment:
                    self.assertIn(unquote(parsed.fragment), self.pages[target].ids, f"{path.name} -> {link}")

    def test_semantics_and_offline_reading(self):
        for path, doc in self.pages.items():
            self.assertEqual(len(doc.ids), len(set(doc.ids)), path)
            self.assertEqual(doc.headings.count(1), 1, path)
            previous = 0
            for level in doc.headings:
                self.assertLessEqual(level, previous + 1, f"Skipped heading in {path}")
                previous = level
            self.assertEqual(doc.scripts, 0)
            self.assertEqual(doc.remote_assets, [])
            source = path.read_text()
            self.assertIn('lang="en"', source)
            self.assertNotIn("<foreignObject", source)
            self.assertNotRegex(source, r'on(?:click|load|error)\s*=')

    def test_public_material_excludes_private_data(self):
        for path in [*self.pages, ROOT / "catalog.json", ROOT / "questions.csv", ROOT / "README.md"]:
            self.assertNotRegex(path.read_text(), r"/Users/|file://|app\.notion\.com|notion\.so/|session-state|gh[pousr]_[A-Za-z0-9]{20,}")

    def test_lesson_covers_architecture_and_shared_concepts(self):
        lesson = ROOT / "problems/countdown-timer/index.html"
        doc = self.pages[lesson]
        for anchor in ["scope", "state", "time", "hld", "completion", "recovery", "implementation", "interfaces", "record", "commands", "race", "commit-gap", "proof", "revision", "sources"]:
            self.assertIn(anchor, doc.ids)
        self.assertIn("High-level design (HLD)", lesson.read_text())
        self.assertIn("Low-level design (LLD)", lesson.read_text())
        wiki = self.pages[ROOT / "concepts/index.html"]
        backlinks = [link for link in wiki.links if link.startswith("../problems/countdown-timer/")]
        self.assertGreaterEqual(len(backlinks), 11)
        self.assertTrue(any("concepts/index.html#clocks" in link for link in doc.links))

    def test_lesson_and_navigation_follow_the_requested_reading_order(self):
        doc = self.pages[ROOT / "problems/countdown-timer/index.html"]
        expected = ["scope", "clarifications", "decisions", "hld", "implementation", "code", "faqs", "concepts"]
        self.assertEqual(doc.top_sections, expected + ["revision", "sources"])
        nav = doc.nav_links["Progressive learning stages"]
        self.assertEqual([urlsplit(link).fragment for link in nav[:8]], expected)
        self.assertEqual({name: path[0] for name, path in doc.diagram_sections.items()},
                         {"delivery": "hld", "work": "hld", "states": "implementation", "recovery": "implementation"})
        self.assertEqual(len(doc.sample_sections), 3)
        self.assertTrue(all(path == ("code",) for path in doc.sample_sections))
        for anchor in ["q-delay", "q-clocks", "q-sleep", "q-pending", "q-alarm-process", "q-guarantee", "q-notification", "q-reboot", "q-off", "commit-gap", "notification-gap", "curiosity"]:
            self.assertEqual(doc.id_sections[anchor][0], "faqs", anchor)

    def test_each_clarification_maps_to_a_design_decision(self):
        doc = self.pages[ROOT / "problems/countdown-timer/index.html"]
        questions = {anchor for anchor in doc.ids if anchor.startswith("clarify-")}
        mapped = [row["question"] for row in doc.decision_rows]
        self.assertEqual(len(mapped), len(set(mapped)))
        self.assertEqual(set(mapped), questions)
        self.assertEqual(len(questions), 8)
        for row in doc.decision_rows:
            anchors = [urlsplit(link).fragment for link in row["links"]]
            self.assertEqual(anchors[0], row["question"])
            self.assertGreaterEqual(len(anchors), 2)
            for target in anchors[1:]:
                self.assertIn(doc.id_sections[target][0], {"hld", "implementation"})


if __name__ == "__main__":
    unittest.main()
