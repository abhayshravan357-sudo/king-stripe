"""Static HTML sanity and basic accessible-name checks without extra dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
PAGES = sorted([*ROOT.glob("*.html"), *ROOT.joinpath("collections").rglob("*.html")])
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.duplicates, self.links, self.img_errors, self.fields, self.labels = set(), [], [], [], [], set()
        self.label_depth = 0
        self.button_stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identifier = attrs.get("id")
        if identifier:
            if identifier in self.ids: self.duplicates.append(identifier)
            self.ids.add(identifier)
        if tag in {"a", "link"} and attrs.get("href"): self.links.append(attrs["href"])
        if tag in {"img", "area"} and "alt" not in attrs: self.img_errors.append(tag)
        if tag == "label":
            self.label_depth += 1
            if attrs.get("for"): self.labels.add(attrs["for"])
        if tag in {"input", "select", "textarea"} and attrs.get("type") != "hidden":
            self.fields.append((attrs.get("id"), attrs.get("aria-label"), attrs.get("aria-labelledby"), self.label_depth > 0))
        if tag == "button": self.button_stack.append([bool(attrs.get("aria-label") or attrs.get("aria-labelledby") or attrs.get("title")), False])
        if tag not in VOID: self._stack = getattr(self, "_stack", []) + [tag]

    def handle_endtag(self, tag):
        if tag == "label" and self.label_depth: self.label_depth -= 1
        if tag == "button" and self.button_stack:
            named, has_text = self.button_stack.pop()
            if not named and not has_text: self.img_errors.append("unnamed button")
        stack = getattr(self, "_stack", [])
        if tag in stack:
            index = len(stack) - 1 - stack[::-1].index(tag)
            self._stack = stack[:index]

    def handle_data(self, data):
        if data.strip():
            for button in self.button_stack: button[1] = True


def main():
    errors = []
    parsed = {}
    for page in PAGES:
        checker = Page()
        try: checker.feed(page.read_text(encoding="utf-8"))
        except Exception: errors.append(f"Could not parse {page.relative_to(ROOT)}"); continue
        parsed[page] = checker
        for duplicate in checker.duplicates: errors.append(f"Duplicate id in {page.relative_to(ROOT)}: {duplicate}")
        for element in checker.img_errors: errors.append(f"Missing accessible text in {page.relative_to(ROOT)}: {element}")
        for field_id, aria, labelledby, wrapped in checker.fields:
            if not (aria or labelledby or wrapped or (field_id and field_id in checker.labels)):
                errors.append(f"Unlabeled form control in {page.relative_to(ROOT)}")
    for page, checker in parsed.items():
        for href in checker.links:
            url = urlsplit(href)
            if url.scheme or url.netloc or href.startswith("//") or not url.path:
                if href.startswith("#") and url.fragment and unquote(url.fragment) not in checker.ids:
                    errors.append(f"Missing fragment target in {page.relative_to(ROOT)}: {href}")
                continue
            target = (page.parent / unquote(url.path)).resolve()
            if not target.exists(): errors.append(f"Missing local link in {page.relative_to(ROOT)}: {url.path}")
    if errors:
        print("Static HTML QA failed:")
        for error in errors: print(error)
        return 1
    print(f"PASS: {len(PAGES)} HTML pages; no duplicate IDs, missing local links, unlabeled controls, or missing image alt text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
