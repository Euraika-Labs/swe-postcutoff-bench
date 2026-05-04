# Task schema (v0.1)

Each task is a single JSON file under `tasks/<instance_id>.json`.

## Required fields

| Field | Type | Description |
|---|---|---|
| `instance_id` | string | Unique ID, format `<org>__<repo>-<issue_number>` (compatible with SWE-bench) |
| `repo` | string | `<org>/<repo>` on GitHub |
| `language` | enum | `python` \| `typescript` \| `javascript` \| `java` \| `go` \| `rust` \| `ruby` \| `c` \| `cpp` |
| `base_commit` | string | Full SHA at which the bug exists (parent of fix PR's merge commit) |
| `patch` | string | Unified diff of the human reference fix (graded against, NOT shown to agent) |
| `test_patch` | string | Unified diff of test additions/changes (NOT shown to agent) |
| `problem_statement` | string | Original GitHub issue body (the only thing the agent sees) |
| `FAIL_TO_PASS` | array<string> | Test IDs that fail at base_commit and pass after fix |
| `PASS_TO_PASS` | array<string> | Test IDs that pass at base_commit and must remain passing |
| `created_at` | string | ISO timestamp of issue creation; MUST be > `2024-10-31T00:00:00Z` |
| `runner` | object | Per-language execution config (see below) |

## Optional fields

| Field | Type | Description |
|---|---|---|
| `difficulty` | string | Human estimate, e.g. `"15 min - 1 hour"`, `"1-4 hours"` |
| `tags` | array<string> | Free-form labels: `["regression", "edge-case", "performance"]` |
| `cve` | string | If the bug is security-relevant, the CVE ID |
| `notes` | string | Curator notes for reviewers |

## `runner` block (per-language)

### Python (`runner.kind: "python"`)

```json
{
  "kind": "python",
  "python_version": "3.11",
  "image": "ghcr.io/swe-bench/sweb.eval.x86_64.django__django-17890:latest",
  "install": "pip install -e .[test]",
  "test_cmd": "pytest -p no:cacheprovider --tb=short -v",
  "test_id_separator": "::"
}
```

### Node (TypeScript / JavaScript) (`runner.kind: "node"`)

```json
{
  "kind": "node",
  "node_version": "20",
  "package_manager": "pnpm",
  "image": "docker.io/node:20-bookworm",
  "install": "pnpm install --frozen-lockfile",
  "test_cmd": "pnpm exec vitest run --reporter=verbose --no-color",
  "test_id_separator": " > "
}
```

### Java (`runner.kind: "java"`)

```json
{
  "kind": "java",
  "java_version": "21",
  "build_tool": "maven",
  "image": "docker.io/maven:3.9-eclipse-temurin-21",
  "install": "mvn -B -q -DskipTests install",
  "test_cmd": "mvn -B test -Dtest=<TEST_PATTERN>",
  "test_id_separator": "#"
}
```

### Go (`runner.kind: "go"`)

```json
{
  "kind": "go",
  "go_version": "1.23",
  "image": "docker.io/golang:1.23-bookworm",
  "install": "go mod download",
  "test_cmd": "go test -run <TEST_PATTERN> ./...",
  "test_id_separator": "/"
}
```

### Rust (`runner.kind: "rust"`)

```json
{
  "kind": "rust",
  "rust_version": "1.82",
  "image": "docker.io/rust:1.82-bookworm",
  "install": "cargo fetch",
  "test_cmd": "cargo test <TEST_PATTERN> -- --nocapture",
  "test_id_separator": "::"
}
```

### Ruby (`runner.kind: "ruby"`)

```json
{
  "kind": "ruby",
  "ruby_version": "3.3",
  "bundler_version": "2.5",
  "image": "docker.io/ruby:3.3-bookworm",
  "install": "bundle install",
  "test_cmd": "bundle exec rspec <TEST_PATTERN>",
  "test_id_separator": " "
}
```

### C / C++ (`runner.kind: "c"` or `"cpp"`)

```json
{
  "kind": "cpp",
  "compiler": "gcc-13",
  "build_tool": "cmake",
  "image": "docker.io/gcc:13-bookworm",
  "install": "cmake -S . -B build -DBUILD_TESTING=ON && cmake --build build",
  "test_cmd": "ctest --test-dir build -R <TEST_PATTERN> -V",
  "test_id_separator": "::"
}
```

## Test ID format

`FAIL_TO_PASS` and `PASS_TO_PASS` arrays contain language-native test identifiers:

| Language | Example |
|---|---|
| Python | `tests/django/test_router.py::TestRouter::test_redirect` |
| TypeScript | `test/router.test.ts > Router > should redirect` |
| Java | `com.example.RouterTest#testRedirect` |
| Go | `internal/router/TestRedirect` |
| Rust | `router::tests::test_redirect` |
| Ruby | `spec/router_spec.rb:42` |

The `test_id_separator` field tells graders how to split nested IDs.

## Validation

Before a task is accepted into the dataset, our CI runs:

1. `gh api` check confirming `created_at > 2024-10-31`
2. Docker pull of the runner image
3. Checkout at `base_commit`, apply `test_patch`, run `test_cmd` → must produce the expected `FAIL_TO_PASS` failures
4. Apply reference `patch` on top → all `FAIL_TO_PASS` must now pass, all `PASS_TO_PASS` must still pass

A task that passes all 4 gets the `verified` label.
