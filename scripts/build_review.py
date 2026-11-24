"""Build a review page that traces a venue's call for artifacts to the model.

Reads a mapping file (one row per passage of the call, located by anchor
phrases), resolves each row's model references against venues.yml and
data.yml, and writes a self-contained HTML page from a template.

    python scripts/build_review.py review/ase-2026/mapping.yml \
        review/template.html review/ase-2026/index.html \
        [--call-text call.txt]

With --call-text, every anchor is checked against a plain-text copy of the
call: both phrases must occur, in order, and rows must follow the call's
order. The call text itself is never written into the page.
"""
import argparse
import json
import re
import sys

import yaml

QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " "})


def normalize(text):
    return re.sub(r"\s+", " ", text.translate(QUOTES)).strip().lower()


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build(mapping_path, data_path, venues_path, call_text=None):
    mapping = load(mapping_path)
    data = load(data_path)
    venues = load(venues_path)["venues"]
    venue = next(v for v in venues if v["id"] == mapping["venue"])
    errors = []

    tags = {t["id"]: t for t in data.get("method_type_tags", []) + data.get("artifact_tags", [])}
    impls, principle_of = {}, {}
    for p in data["principles"]:
        for i in p["implementations"]:
            impls[i["id"]] = i
            principle_of[i["id"]] = p
    badges = {b["id"]: b for b in venue.get("badges", [])}

    def tag_name(curie):
        return tags[curie]["name"] if curie in tags else curie

    def text(value):
        return re.sub(r"\s+", " ", str(value)).strip() if value is not None else None

    # Every requirement the venue states, keyed "scope/standard".
    requirements = {}
    scopes = [("all", "All submissions", venue.get("required_standards", []))]
    scopes += [(b["id"], b["name"], b.get("required_standards", [])) for b in venue.get("badges", [])]
    for scope_id, scope_name, refs in scopes:
        for ref in refs:
            impl = impls.get(ref["standard"])
            if impl is None:
                errors.append(f"venue references unknown standard {ref['standard']}")
                continue
            checks = (impl.get("checks_guidance") or {})
            key = f"{scope_id}/{ref['standard']}"
            requirements[key] = {
                "kind": "standard",
                "key": key,
                "scope": scope_name,
                "scope_id": scope_id,
                "standard": ref["standard"],
                "name": impl["name"],
                "principle": re.sub(r"\s*—\s*Generic\s*$", "", principle_of[ref["standard"]]["name"]),
                "display_name": ref.get("display_name"),
                "generic_level": impl.get("check_level"),
                "venue_level": ref.get("check_level"),
                "applies_to": [tag_name(t) for t in ref.get("applies_to_artifact_tags", [])],
                "note": text(ref.get("note")),
                "parameters": [
                    {"name": p["name"], "value": str(p["value"]), "description": p.get("description")}
                    for p in ref.get("parameters", [])
                ],
                "guidance": text(impl["creation_guidance"]["description"]),
                "examples": impl["creation_guidance"].get("examples", []),
                "human_checks": [text(c["description"]) for c in checks.get("human", [])],
                "automated_checks": [
                    {"id": c["id"], "description": text(c["description"]), "command": text(c["command"])}
                    for c in (checks.get("automated") or {}).get("checks", [])
                ],
            }

    def resolve(ref):
        if ref.startswith("venue:"):
            field = ref[len("venue:"):]
            value = venue.get(field)
            if value is None:
                errors.append(f"unknown venue field {field}")
                return None
            if field == "eligible_artifact_tags":
                value = [tag_name(t) for t in value]
            labels = {"description": "Venue description", "badging_policy": "Badging policy",
                      "eligible_artifact_tags": "Eligible artifact types"}
            return {"kind": "venue", "key": ref, "label": labels.get(field, field),
                    "value": value if isinstance(value, list) else text(value)}
        if ref.startswith("badge:"):
            badge = badges.get(ref[len("badge:"):])
            if badge is None:
                errors.append(f"unknown badge {ref}")
                return None
            return {"kind": "badge", "key": ref, "name": badge["name"], "badge_kind": badge.get("kind", "badge"),
                    "description": text(badge.get("description")),
                    "includes": [badges[i]["name"] for i in badge.get("includes", []) if i in badges],
                    "requirement_count": len(badge.get("required_standards", []))}
        if ref not in requirements:
            errors.append(f"unknown requirement {ref} (not in venues.yml)")
            return None
        return {"kind": "ref", "key": ref}

    rows = []
    for row in mapping["rows"]:
        resolved = [r for r in (resolve(m) for m in row.get("model", [])) if r]
        rows.append({
            "id": row["id"],
            "section": row["section"],
            "anchor": row["anchor"],
            "summary": text(row["summary"]),
            "status": row["status"],
            "assessment": text(row.get("assessment")),
            "proposal": text(row.get("proposal")),
            "model": resolved,
        })

    if call_text is not None:
        haystack = normalize(call_text)
        last = -1
        for row in rows:
            start, end = (normalize(a) for a in row["anchor"])
            s = haystack.find(start)
            if s < 0:
                errors.append(f"{row['id']}: start anchor not found: {row['anchor'][0]!r}")
                continue
            if haystack.find(start, s + 1) >= 0:
                errors.append(f"{row['id']}: start anchor is ambiguous: {row['anchor'][0]!r}")
            if end and haystack.find(end, s) < 0:
                errors.append(f"{row['id']}: end anchor not found after start: {row['anchor'][1]!r}")
            if s < last:
                errors.append(f"{row['id']}: out of call order")
            last = s

    cited = {}
    for row in rows:
        for m in row["model"]:
            if m["kind"] == "ref":
                cited.setdefault(m["key"], []).append(row["id"])
    for key in requirements:
        if key not in cited:
            print(f"note: {key} is not cited by any row", file=sys.stderr)

    page = {
        "venue": {"id": venue["id"], "name": venue["name"], "url": venue.get("url")},
        "source": mapping["source"],
        "source_hash": mapping.get("source_hash", ""),
        "retrieved": str(mapping["retrieved"]),
        "requirements": requirements,
        "scopes": [{"id": s[0], "name": s[1]} for s in scopes],
        "rows": rows,
    }
    return page, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mapping")
    ap.add_argument("template")
    ap.add_argument("output")
    ap.add_argument("--data", default="data.yml")
    ap.add_argument("--venues", default="venues.yml")
    ap.add_argument("--call-text")
    args = ap.parse_args()

    call_text = None
    if args.call_text:
        with open(args.call_text, encoding="utf-8") as f:
            call_text = f.read()
    page, errors = build(args.mapping, args.data, args.venues, call_text)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        return 1

    with open(args.template, encoding="utf-8") as f:
        template = f.read()
    payload = json.dumps(page, ensure_ascii=False).replace("<", "\\u003c")
    marker = "/*__REVIEW_DATA__*/null"
    if marker not in template:
        print("error: template has no data marker", file=sys.stderr)
        return 1
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(template.replace(marker, payload))
    print(f"wrote {args.output}: {len(page['rows'])} rows, {len(page['requirements'])} venue requirements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
