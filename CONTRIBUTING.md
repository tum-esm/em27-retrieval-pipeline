# Contributing

All contributions that benefit the COCCON community are welcome. This includes bug fixes, documentation improvements, support for additional retrieval algorithms or spectrometers, and other improvements to the pipeline.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md) in all project interactions.

## Before You Start

- Search the existing [issues](https://github.com/tum-esm/em27-retrieval-pipeline/issues) before opening a new one.
- Open an issue before starting a substantial change so its scope and approach can be discussed.
- Small fixes and documentation improvements can be submitted directly as a pull request.

## Making Changes

- Keep changes focused and consistent with the existing code.
- Possibly add or update tests
- Update the documentation when changing user-facing behavior, configuration, or commands.
- Use concise, descriptive commit messages.

## Checks

Run the formatting, linting, and type checks relevant to your change:

```bash
ruff format --check .
ruff check .
pyright
```

For most changes, run the lightweight test suite:

```bash
pytest -m quick tests/
```

Run the CI-level tests when retrieval behavior, dispatching, file handling, or other pipeline workflows change:

```bash
pytest -m "quick or ci" tests/
```

The `complete` tests execute the retrieval algorithms and can take considerably
longer. Run them when changing retrieval-related behavior:

```bash
pytest -m complete tests/
```

Some integration and complete tests require a configured system and test data. See the [test guide](https://tum-esm.github.io/em27-retrieval-pipeline/guides/tests) for details.

## Pull Requests

When opening a pull request:

- Explain what changed and why.
- Link related issues.
- Highlight user-facing or breaking changes.
- Include documentation updates where needed.
