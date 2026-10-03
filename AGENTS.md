# Independent plugin repository

This repository belongs to its developer. Keep only their own complete plugins
under `plugins/`; `hello-world` is a deletable starter. No official source,
catalogue, publisher keys, release credentials or wiki belongs here.

Read DEVELOPMENT.md and docs/UPSTREAM.md before changing tooling. Preserve the
public Plugin API v1 SDK, manifest/UI schemas, canonical package digest and v2
signature envelope. The host owns lifecycle, gateway, permissions, isolation and
installation. Do not copy runtime code or import host internals into plugins.

Use stable IDs, least privilege, Conventional Commits and focused branches.
Keep private signing keys outside Git. Never rewrite published package bytes or
release records. New signing identities must be developer-owned community keys.

Run all commands in the CI workflow; do not weaken checks to pass. Add behavior
tests for plugins and real package/security regression tests for tooling changes.
Document what was actually tested, including any Linux/host limitations.
