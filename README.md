# Research Artifact Standards

**Browse the standards:** [aaronpeikert.github.io/artifact-standards-site](https://aaronpeikert.github.io/artifact-standards-site/)

A community-maintained registry of principles and concrete implementations for the **creation and evaluation of research artifacts**.
This project was started during Dagstuhl 26381.

Standards are structured using a [LinkML](https://linkml.io/) schema (`schema.yml`) and stored in `data.yml`. Each standard consists of:

- **Principles** — general, implementation-independent requirements or desirable properties of a research artifact.
- **Implementations** — concrete mechanisms that satisfy a principle, each with:
  - *Creation guidance* — how artifact authors should apply the implementation.
  - *Evaluation checks* — human-review criteria and machine-executable checks for evaluators.

Principles and implementations can be tagged by method type and artifact type to indicate where they apply.

Venues (conferences, journals, workshops) are described in `venues.yml` (class `VenueRegistry`). A venue lists the implementations required for *every* artifact submission (`required_standards`) and, per badge or award it offers, the additional implementations needed for that badge (`badges`). Each reference can override the display name or check level, restrict the requirement to certain artifact tags, add a note paraphrasing the call, and set venue-specific `parameters` (e.g., a 30-minute time budget or the accepted archives for an automated check). See the ASE 2026 entry for a complete example.

## Validate

Install dependencies and validate `data.yml` against the schema locally:

```bash
pip install -r requirements.txt
linkml-validate -s schema.yml data.yml
linkml-validate -s schema.yml -C VenueRegistry venues.yml
python scripts/check_references.py data.yml venues.yml
```

LinkML does not check that the CURIEs used as tags or standard references exist; `scripts/check_references.py` does.

Validation also runs automatically on every pull request via GitHub Actions.

## Contribute

Contributions of new principles, implementations, or checks are welcome. Please open a pull request with your additions to `data.yml`; the CI workflow will validate the changes automatically.
