"""BrandBox Coach Agent — synthesize natural replies from Help Center (no GPT)."""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

from .services import suggest_articles_for_query

_TRANSFER_RE = re.compile(
    r"\b("
    r"coach|human|person|transfer|agent|"
    r"speak\s+to|talk\s+to|real\s+(person|coach)|"
    r"live\s+coach|human\s+coach"
    r")\b",
    re.I,
)


def wants_human_coach(text: str) -> bool:
    return bool(_TRANSFER_RE.search(text or ""))


class _HTMLToText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._skip = True
        elif tag in {"li", "p", "br", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")
        elif tag == "div":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._skip = False
        elif tag in {"p", "li", "h1", "h2", "h3", "h4", "div"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip and data:
            self.parts.append(data)

    def text(self) -> str:
        raw = unescape("".join(self.parts))
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def html_to_text(html: str) -> str:
    parser = _HTMLToText()
    try:
        parser.feed(html or "")
        parser.close()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html or "")
    return parser.text()


def _extract_steps(text: str, limit: int = 8) -> list[str]:
    lines = [ln.strip(" •-\t") for ln in text.splitlines() if ln.strip()]
    steps: list[str] = []
    for ln in lines:
        # Skip very short / heading-like lines that are just titles
        if len(ln) < 12:
            continue
        # Prefer numbered / imperative-looking lines
        numbered = re.match(r"^\d+[\).\]]\s*(.+)$", ln)
        if numbered:
            steps.append(numbered.group(1).strip())
        elif ln[:1].isupper() and len(ln) < 220:
            steps.append(ln)
        if len(steps) >= limit:
            break
    if not steps:
        # Fallback: first sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for s in sentences:
            s = s.strip()
            if len(s) >= 20:
                steps.append(s)
            if len(steps) >= min(5, limit):
                break
    return steps[:limit]


def synthesize_agent_reply(question: str, request=None) -> dict:
    """
    Return {body, guide_title, guide_url, matches}.
    Natural step-by-step answer grounded on the top Help article.
    """
    matches = suggest_articles_for_query(question, limit=3)
    if not matches:
        return {
            "body": (
                "I couldn't find a matching guide for that yet. "
                "Try rephrasing, or browse the Help Center. "
                "If you still need a person, say “talk to a coach”."
            ),
            "guide_title": "",
            "guide_url": "",
            "matches": [],
        }

    article = matches[0]
    summary = (article.summary or "").strip()
    body_text = html_to_text(article.body or "")
    steps = _extract_steps(body_text or summary)

    intro = summary
    if not intro:
        intro = f"Here's how to handle “{article.title}”:"
    else:
        intro = intro.rstrip(".") + "."

    lines = [intro, ""]
    if steps:
        lines.append("Here's what to do:")
        for i, step in enumerate(steps[:6], start=1):
            lines.append(f"{i}. {step}")
    else:
        lines.append(f"Open the full guide for details on {article.title}.")

    lines.append("")
    lines.append('Need a person? Say “talk to a coach” and we’ll queue you when you’re eligible.')

    guide_url = ""
    if request is not None:
        guide_url = request.build_absolute_uri(article.get_absolute_url())
    else:
        guide_url = article.get_absolute_url()

    return {
        "body": "\n".join(lines).strip(),
        "guide_title": article.title,
        "guide_url": guide_url,
        "matches": [
            {
                "title": a.title,
                "url": (
                    request.build_absolute_uri(a.get_absolute_url())
                    if request is not None
                    else a.get_absolute_url()
                ),
                "summary": a.summary,
            }
            for a in matches
        ],
    }
