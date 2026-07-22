# Assistant

The `assistant` CLI uses LLMs to support systematic literature review activities:

- `study-selection` screens primary-study records against title and abstract;
- `study-qa` assesses the quality of study PDFs against user-defined criteria.

The assistant complements the existing [`search`](../search/index.md) and
[`deduplicate`](../deduplication/index.md) commands and allows for faster iteration over the results
of those stages. However, the two provided CLIs do not replace review decisions:
LLM results must be inspected if only because they can be left blank when a
criterion cannot be scored reliably.

## Next Steps

- New here? Start with [Installation](getting-started/installation.md) and
  [Usage](getting-started/usage.md).
- Looking for every option? See the [CLI reference](getting-started/cli-reference.md).
