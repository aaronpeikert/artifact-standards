"""Check cross-references that LinkML validation does not enforce.

Every tag CURIE used by a principle or implementation must be declared in
data.yml, and every standard, badge, and tag CURIE used in venues.yml must
resolve to an implementation, badge, or tag. Exits non-zero on dangling
references.
"""
import sys

import yaml


def main(data_path="data.yml", venues_path="venues.yml"):
    with open(data_path) as f:
        data = yaml.safe_load(f)
    with open(venues_path) as f:
        venues = yaml.safe_load(f)

    tags = {t["id"] for t in data.get("method_type_tags", []) + data.get("artifact_tags", [])}
    impls = {i["id"] for p in data["principles"] for i in p["implementations"]}
    errors = []

    def check_tags(owner, item):
        for tag in item.get("method_type_tags", []) + item.get("artifact_tags", []):
            if tag not in tags:
                errors.append(f"{owner}: unknown tag {tag}")

    for p in data["principles"]:
        check_tags(p["id"], p)
        for i in p["implementations"]:
            check_tags(i["id"], i)
            auto = (i.get("checks_guidance") or {}).get("automated") or {}
            check_ids = {c["id"] for c in auto.get("checks", [])}
            for rule in auto.get("combination_rules", []):
                for c in rule["checks"]:
                    if c not in check_ids:
                        errors.append(f"{rule['id']}: unknown check {c}")

    for v in venues.get("venues", []):
        badges = {b["id"] for b in v.get("badges", [])}
        for tag in v.get("eligible_artifact_tags", []):
            if tag not in tags:
                errors.append(f"{v['id']}: unknown tag {tag}")
        scopes = [(v["id"], v.get("required_standards", []))]
        for b in v.get("badges", []):
            scopes.append((b["id"], b.get("required_standards", [])))
            for inc in b.get("includes", []):
                if inc not in badges:
                    errors.append(f"{b['id']}: includes unknown badge {inc}")
        for owner, refs in scopes:
            for r in refs:
                if r["standard"] not in impls:
                    errors.append(f"{owner}: unknown standard {r['standard']}")
                for tag in r.get("applies_to_artifact_tags", []):
                    if tag not in tags:
                        errors.append(f"{owner}/{r['standard']}: unknown tag {tag}")

    for e in errors:
        print(e)
    print(f"{len(errors)} dangling reference(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
