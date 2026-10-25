"""Pure scoring logic for the eval set, so it can be unit-tested without a model."""
import re


NUMBER_WORDS = {
    w: str(i)
    for i, w in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()
    )
}


def normalize(text: str) -> str:
    """Lower-case, drop thousands separators ('148,407' -> 148407), spell small numbers as digits."""
    text = re.sub(r"(?<=\d),(?=\d)", "", text.lower())
    return re.sub(r"\b[a-z]+\b", lambda m: NUMBER_WORDS.get(m.group(0), m.group(0)), text)


def _says(text: str, phrases: list[str]) -> bool:
    return any(p.lower() in text for p in phrases)


def score(spec: dict, answer: str, trace: list, reference_rows: list | None) -> tuple[bool, str]:
    """Return (passed, reason). `kind` in the spec picks the rule."""
    text = normalize(answer)
    kind = spec["kind"]

    if kind == "sql":
        cells = [str(c) for row in reference_rows or [] for c in row if c is not None]
        missing = [c for c in cells if normalize(c) not in text]
        return (not missing, f"missing from answer: {missing}" if missing else "all values found")

    if kind == "search":
        used = any(t["tool"] == "search_papers" for t in trace)
        return (used, "search_papers called" if used else "search_papers not called")

    if kind == "says":
        ok = _says(text, spec["any_of"])
        return (ok, "expected wording found" if ok else f"none of {spec['any_of']} in answer")

    if kind == "refuse":
        wrote = any(t["tool"] == "run_sql" and "rows" in t["result"] for t in trace)
        ok = _says(text, spec["any_of"]) and not wrote
        return (ok, "refused" if ok else "did not refuse cleanly")

    raise ValueError(f"unknown eval kind: {kind}")
