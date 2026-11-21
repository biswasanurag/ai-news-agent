import re

LEAKED_LABELS = ["unverified_claim", "(confirmed)", "(reported)", "(rumor)", "confidence:"]


def extract_urls(text: str) -> set[str]:
    return {u.rstrip(".,;:") for u in re.findall(r"https?://[^\s)\]>]+", text)}


def run_checks(body: str, shortlist: list[dict], max_words: int, deep_read: int) -> list[str]:
    """Return a list of problems found in the digest (empty list = all good)."""
    problems = []
    lowered = body.lower()

    words = len(body.split())
    if words > max_words:
        problems.append(f"Too long: {words} words (limit {max_words})")

    # Grounding: every link must come from the data we gave the writer.
    allowed = {i["link"] for s in shortlist for i in s["items"]}
    used = extract_urls(body)
    invented = used - allowed
    if invented:
        problems.append(f"Links not in shortlist: {sorted(invented)}")

    # Coverage: every shortlisted story should appear (via at least one of its links).
    for s in shortlist:
        links = {i["link"] for i in s["items"]}
        if not (links & used):
            problems.append(f"Story missing from digest: {s['headline']}")

    for label in LEAKED_LABELS:
        if label in lowered:
            problems.append(f"Internal label leaked into text: {label}")

    if lowered.count("why it matters") < deep_read:
        problems.append("Fewer 'Why it matters' lines than top stories")

    return problems