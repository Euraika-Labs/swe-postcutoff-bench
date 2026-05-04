# swe-postcutoff-bench

A contamination-controlled, **multi-language** agentic-coding benchmark.

## What this is

A curated set of bug-fix tasks from real GitHub issues filed **after October 2024** in widely-used open-source repositories across **Python, JavaScript/TypeScript, Java, Go, Rust, C/C++, and Ruby**. Each task ships with:

- The original issue text
- The repository at the bug commit
- The reference fix patch (for grading reference, NOT given to the agent)
- A `FAIL_TO_PASS` test set (failing on the bug commit, passing after the fix)
- A `PASS_TO_PASS` test set (passing on the bug commit, must remain passing after fix)
- A language-specific runner config (which test framework, how to install deps, how to run tests)

The format is deliberately compatible with [SWE-bench Verified](https://www.swebench.com/) for the Python tasks, but extends to other languages via a `runner` field that specifies the test execution recipe per language.

## Why this exists

Published SWE-bench Verified results have a **training-data contamination problem**. SWE-bench Verified was released August 2024 with 500 publicly-curated GitHub issue + PR-fix pairs. Coder-specialized models trained on GitHub through 2024-2025 have plausibly seen many of these reference patches as training data. Apparent strong results cannot be cleanly attributed to capability vs memorization.

Two specific gaps in the existing benchmark landscape:

1. **Contamination**: Pre-October-2024 fix PRs are very likely in any modern coding model's training set.
2. **Python monoculture**: SWE-bench is Python-only. A coding agent's "real" capability includes navigating Java enterprise codebases, Next.js apps, Go services, and Rust crates. Python-only benchmarks reward narrow, language-specific tool-use training.

This benchmark addresses both: post-October-2024 issues, multi-language coverage.

## Status

🚧 v0.1 in active development — curation tooling and initial task set being built (May 2026).

## Language coverage (target)

Each language gets ~5-15 tasks in v0.1; ~50-100 in v1.0.

| Language | Frameworks/repos targeted | Test framework |
|---|---|---|
| **Python** | Django, astropy, matplotlib, scikit-learn, pytest, pandas, FastAPI | pytest |
| **TypeScript / JavaScript** | Next.js (Vercel), React, TypeScript itself, Vite, NestJS, Drizzle | vitest, jest, playwright |
| **Java** | Spring Boot, Quarkus, Hibernate, JUnit, Apache Maven plugins | maven (`mvn test`), gradle |
| **Go** | Kubernetes, Hugo, Gin, Cobra, Bubbletea | `go test` |
| **Rust** | tokio, axum, serde, clap, ratatui | `cargo test` |
| **Ruby** | Rails, Jekyll, RSpec | `bundle exec rspec`, `bundle exec rake test` |
| **C / C++** | CPython interpreter, OpenSSL, libcurl | per-project (ctest, custom) |

## Schema

Each task is a JSON record with the SWE-bench Verified field set, plus a `language` and `runner` block:

```json
{
  "instance_id": "vercel__next.js-65432",
  "repo": "vercel/next.js",
  "language": "typescript",
  "base_commit": "<sha>",
  "patch": "<unified diff of the fix; for grading reference only>",
  "test_patch": "<unified diff that adds/modifies tests>",
  "problem_statement": "<original issue text>",
  "FAIL_TO_PASS": ["test/router/some-fail.test.ts::should redirect with 308", "..."],
  "PASS_TO_PASS": ["test/build/build.test.ts::should compile", "..."],
  "created_at": "2025-03-15T10:23:00Z",
  "difficulty": "15 min - 1 hour",
  "runner": {
    "kind": "node",
    "node_version": "20",
    "install": "pnpm install --frozen-lockfile",
    "test_cmd": "pnpm test --filter <package>",
    "test_id_separator": "::",
    "image": "docker.io/node:20-bookworm"
  }
}
```

Per-language runner specs:

| `runner.kind` | Required fields | Notes |
|---|---|---|
| `python` | `python_version`, `install`, `test_cmd` | Default: pytest, instance_id-style test IDs |
| `node` | `node_version`, `install`, `test_cmd` | npm/yarn/pnpm; vitest/jest/mocha |
| `java` | `java_version`, `build_tool` (maven/gradle), `test_cmd` | maven `surefire-reports/` parsed for results |
| `go` | `go_version`, `test_cmd` | `go test -run` per FAIL_TO_PASS pattern |
| `rust` | `rust_version`, `test_cmd` | `cargo test <name>` per FAIL_TO_PASS |
| `ruby` | `ruby_version`, `bundler_version`, `test_cmd` | `bundle exec rspec` or `rake test` |
| `c` / `cpp` | `build_tool` (cmake/make/configure), `test_cmd` | per-project; ctest preferred |

`created_at` MUST be after `2024-10-31` for a task to be included.

## Running the benchmark

The benchmark is designed to be drop-in compatible with the SWE-bench tooling for Python tasks, plus per-language runners we provide for non-Python:

```bash
# Clone
git clone https://github.com/Euraika-Labs/swe-postcutoff-bench
cd swe-postcutoff-bench

# Install runner (Python-based dispatcher that calls per-language test cmds)
pip install -e .

# Run a single task (any language)
swe-pcb run --task-file tasks/vercel__next.js-65432.json --patch <my-patch.diff>

# Run a full subset
swe-pcb run --tasks-dir tasks/ --filter language=typescript
```

Each runner pulls a Docker image scoped to the language (preventing cross-task dependency pollution), checks out the repo at `base_commit`, applies the candidate patch, runs the test command, and parses pass/fail per `FAIL_TO_PASS` and `PASS_TO_PASS` test IDs.

## Methodology

### Selection criteria

For each candidate issue:

1. **Filed after 2024-10-31** (the latest training cutoff among models we expected to test)
2. **Closed by a merged fix PR** with explicit `FAIL_TO_PASS` test cases
3. **Long-horizon stratified** — reference patch ≥ 30 lines OR ≥ 2 files touched
4. **Verified gradable** — pytest/cargo/mvn at the bug commit reproduces the failure; applying the reference patch makes the failing test(s) pass without regressions
5. **Single-issue scope** — no bundled feature changes or refactor sprawl

### Anti-cheating

We DO NOT publish reference patches in plain text in the repo README — they're inside the JSON records, intended for grader reference only. Solutions submitted to the leaderboard (when one exists) will be human-spot-checked for verbatim copies of reference patches.

For non-Python languages where dependency installation is heavy (Maven downloads, Gradle, npm install in Next.js, Cargo build), each language uses a Docker base image with framework deps pre-fetched, so test runs don't time out on dependency resolution.

## License

MIT — same as the rest of the Euraika-Labs research artifacts. See [LICENSE](./LICENSE).

## Citation

If you use this benchmark, please cite:

```bibtex
@misc{swe-postcutoff-bench-2026,
  title={swe-postcutoff-bench: A Contamination-Controlled Multi-Language Agentic-Coding Benchmark},
  author={Vergeer, Bert and Euraika-Labs Research},
  year={2026},
  url={https://github.com/Euraika-Labs/swe-postcutoff-bench}
}
```

## Related work

- [SWE-bench](https://www.swebench.com/) — Python-only, pre-cutoff; this benchmark extends it
- [SWE-bench Multilingual](https://www.swebench.com/multilingual.html) — multi-lang but the same contamination concern
- [LiveCodeBench](https://livecodebench.github.io/) — single-shot competitive-programming with rolling post-cutoff items (different task type)

## Contributing

Pull requests welcome for new tasks. Each task PR should include:

1. The JSON record under `tasks/<instance_id>.json`
2. A verification log under `tasks/<instance_id>.verify.txt` showing the bug-commit test output and the post-fix test output
3. Confirmation that `created_at` is post-2024-10-31
4. A `runner` block matching the language

We will reject tasks that:
- Lack reproducible test failure on the bug commit
- Have ambiguous fixes (multiple correct patches without canonical test coverage)
- Include reference patches obviously generated by an LLM rather than a human PR
- Are sourced from a repo where the issue/PR pre-dates 2024-11-01
