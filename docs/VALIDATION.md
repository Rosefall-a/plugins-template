# Template validation evidence

Validation date: 3 October 2026. Revisions and architectural comparison are in
[UPSTREAM.md](UPSTREAM.md). Commands are in [DEVELOPMENT.md](../DEVELOPMENT.md).

## Passed locally

- Template pytest: **13 passed**, including real unsigned builds with an empty
  registry, current package validation, creating an independent second plugin,
  generating a disposable community signer, signing and verifying packages,
  explicit and Conventional Commit version increments, immutable historical
  bytes, tagged snapshot reuse, malformed IDs/versions/ranges/handlers,
  duplicate/incomplete plugins, mismatched scope/publisher/key, altered payloads,
  altered bound manifests and invalid signatures.
- Python lint (`python -m ruff check .`), source contract validation, frontend
  orchestration (no frontend bundle is needed by the declarative starter), package
  generation, full package validation, signature/integrity verification,
  catalogue/current-source consistency and whitespace checks.
- Actual pinned host models and verifier consumed the generated manifest/UI and
  `.utp`; its real registry installed and uninstalled the package on Windows.
- Linux real worker: pending-install rejection, ready/action, disable/re-enable,
  new package version with changed greeting, retained plugin state, uninstall.
- PostgreSQL-backed **authenticated host HTTP**: newly generated independent
  plugin; invalid ZIP rejection; unsigned preview and rejection without explicit
  consent; unsigned installation/use; trusted community signature installation;
  denied secret write without storage permission; disable/re-enable; update
  staged while old version remains active; explicit new permission approval;
  write-only secret save and brokered read without returning the credential;
  retained secret after disable/re-enable; uninstall and storage deletion.
  No official plugins, official keys, host fixtures or mocked gateway were used.
- Upstream generic fix: **66 focused tests passed**. Full Windows upstream suite
  had 193 passed and five environment failures because its Linux workflow-selector
  tests launch `bash`; no assertions changed. Its actual Linux GitHub Plugin checks
  and Plugin Manager integration workflows both passed on commit
  `30aa6723dae854a9552d5e50c4694ae31deb1358`.

## Scope and limitations

Linux runtime and authenticated tests deliberately used the host-supported
`NONBUBBLE_ENV=true` process mode, matching upstream acceptance. They prove real
worker/gateway/lifecycle behavior, not bubblewrap isolation, production container
hardening or a security audit of arbitrary plugins. Production isolation remains
owned/enforced by the application.

No private publisher key is shipped. Signed tests generate disposable identities
outside their checkouts. CI signing/rejection coverage needs no developer secrets;
the optional manual signed-release job requires the developer's own secrets.

Public package/catalogue hosting and developer-owned release secrets were not
exercised against a production account. Catalogue URLs and exact metadata/hashes
were validated locally. Browser interaction and custom frontend bundle behavior
must be recorded separately when tested; declarative UI/schema and actual host
action APIs were exercised. The host is the pinned plugin-enabled branch, not
ordinary main.

The template's normal CI includes blocking authenticated acceptance with a fresh
service database. Read the current PR checks for remote execution status; this
file does not claim a workflow passed before it actually runs.
