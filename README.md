# Research Artifact Standards

A community-maintained registry of principles and concrete implementations for the **creation and evaluation of research artifacts**.

Standards are structured using a [LinkML](https://linkml.io/) schema (`schema.yml`) and stored in `data.yml`. Each standard consists of:

- **Principles** — general, implementation-independent requirements or desirable properties of a research artifact.
- **Implementations** — concrete mechanisms that satisfy a principle, each with:
  - *Creation guidance* — how artifact authors should apply the implementation.
  - *Evaluation checks* — human-review criteria and machine-executable checks for evaluators.

Principles and implementations can be tagged by study type and artifact type to indicate where they apply.

## Validate

Install dependencies and validate `data.yml` against the schema locally:

```bash
pip install -r requirements.txt
linkml-validate -s schema.yml data.yml
```

Validation also runs automatically on every pull request via GitHub Actions.

## Contribute

Contributions of new principles, implementations, or checks are welcome. Please open a pull request with your additions to `data.yml`; the CI workflow will validate the changes automatically.
