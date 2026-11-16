#!/usr/bin/env python3
"""Import full blog posts from Substack into posts/<slug>.html.

Runs in the GitHub Pages workflow before the site is published. For each slug
below it asks Substack for the post, keeps only plain article markup, and
writes the result where the blog detail page looks for it. If a post cannot
be fetched, the copy already saved in the repository is kept. If there is no
saved copy, the page falls back to a link to Substack. A failed import never
breaks the deploy.

To add a post: add its slug here and add an entry to POSTS in index.html.
"""
import json, os, re, sys, time, urllib.request
from html.parser import HTMLParser

SUBSTACK = "https://aiagentssimplified.substack.com"
SLUGS = [
    "dont-learn-ai-agents-without-learning",
    "how-to-become-an-ai-engineer-the",
    "ai-engineering-from-scratch",
]
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts")

KEEP = {"p", "h1", "h2", "h3", "h4", "ul", "ol", "li", "blockquote", "pre", "code", "em", "strong",
        "b", "i", "u", "s", "a", "img", "figure", "figcaption", "hr", "br", "table", "thead",
        "tbody", "tr", "th", "td", "sup", "sub"}
VOID = {"img", "hr", "br"}
DROP_WITH_CONTENT = {"script", "style", "iframe", "form", "button", "svg", "noscript", "input", "source"}
# Substack widgets that make no sense outside Substack
DROP_CLASSES = ("subscription-widget", "subscribe-widget", "button-wrapper", "captioned-button",
                "image-link-expand", "poll-embed", "digest-post-embed", "embedded-post", "paywall")
ATTRS = {"a": {"href"}, "img": {"src", "alt", "width", "height"}, "th": {"colspan", "rowspan"},
         "td": {"colspan", "rowspan"}}


HTML_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Cleaner(HTMLParser):
    """Keeps a small set of article tags and drops everything else.

    While inside a dropped element, only that element's own tag name is
    counted, so unbalanced markup inside it cannot swallow the rest of the post.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.open = [], []
        self.skip_tag, self.skip_depth = None, 0

    def handle_starttag(self, tag, attrs):
        if self.skip_tag:
            if tag == self.skip_tag:
                self.skip_depth += 1
            return
        cls = dict(attrs).get("class") or ""
        if tag in DROP_WITH_CONTENT or any(c in cls for c in DROP_CLASSES):
            if tag not in HTML_VOID:
                self.skip_tag, self.skip_depth = tag, 1
            return
        if tag not in KEEP:
            return
        kept = []
        for k, v in attrs:
            if k not in ATTRS.get(tag, ()) or v is None:
                continue
            if k in ("href", "src") and not re.match(r"^(https?:|mailto:|#)", v.strip(), re.I):
                continue
            kept.append(' %s="%s"' % (k, v.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")))
        if tag == "img":
            kept.append(' loading="lazy"')
        self.out.append("<%s%s>" % (tag, "".join(kept)))
        if tag not in VOID:
            self.open.append(tag)

    def handle_startendtag(self, tag, attrs):
        if tag in HTML_VOID or not self.skip_tag:
            if not self.skip_tag:
                self.handle_starttag(tag, attrs)
                if tag in KEEP and tag not in VOID:
                    self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.skip_tag:
            if tag == self.skip_tag:
                self.skip_depth -= 1
                if self.skip_depth == 0:
                    self.skip_tag = None
            return
        if tag in KEEP and tag not in VOID and tag in self.open:
            while self.open:
                t = self.open.pop()
                self.out.append("</%s>" % t)
                if t == tag:
                    break

    def handle_data(self, data):
        if not self.skip_tag:
            self.out.append(data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def clean(html):
    c = Cleaner()
    c.feed(html)
    c.close()
    while c.open:
        c.out.append("</%s>" % c.open.pop())
    text = "".join(c.out)
    text = re.sub(r"<p>\s*</p>", "", text)
    return text.strip()


def fetch(slug, attempts=3):
    """Ask Substack for one post. Substack sometimes answers 403 to GitHub's servers, so try a few times."""
    req = urllib.request.Request("%s/api/v1/posts/%s" % (SUBSTACK, slug),
                                 headers={"User-Agent": "Mozilla/5.0 (site importer for hana-esf.github.io)",
                                          "Accept": "application/json"})
    for n in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if n == attempts - 1:
                raise
            time.sleep(5 * (n + 1))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ok = 0
    for slug in SLUGS:
        try:
            body = clean(fetch(slug).get("body_html") or "")
            if len(body) < 500:
                raise ValueError("post body is empty or too short (paywalled?)")
            with open(os.path.join(OUT_DIR, slug + ".html"), "w", encoding="utf-8") as f:
                f.write(body + "\n")
            ok += 1
            print("imported %s (%d characters)" % (slug, len(body)))
        except Exception as e:  # never fail the deploy because of an import
            print("skipped %s: %s" % (slug, e), file=sys.stderr)
    print("%d of %d posts imported" % (ok, len(SLUGS)))


if __name__ == "__main__":
    main()
