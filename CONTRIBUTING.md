# Contributing to `fastapi-autogen-team`

## Pull Request Policy
- Never push directly to `main`.
- All changes must go through an isolated feature branch and pull request.
- Ensure all CI checks pass before requesting review.

## Quality Checks (Rust Profile)
```bash
cargo fmt --all -- --check && cargo clippy --workspace --all-targets -- -D warnings && cargo test --workspace
```
