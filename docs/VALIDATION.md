# Template validation evidence

Validation date: 3 October 2026. Revisions and architectural comparison are in
[UPSTREAM.md](UPSTREAM.md). Commands are in [DEVELOPMENT.md](../DEVELOPMENT.md).

## Passed locally

- Template pytest: **14 passed**, including real unsigned builds with an empty
  registry, current package validation, creating an independent second plugin,
  generating a disposable community signer, signing and verifying packages,
  explicit and Conventional Commit version increments, immutable historical
  bytes, tagged snapshot reuse, malformed IDs/versions/ranges/handlers,
  duplicate/incomplete plugins, mismatched scope/publisher/key, altered payloads,
  altered bound manifests and invalid signatures.
- Python lint (`python -m ruff check .`), source contract validation, frontend
  orchestration (static starter JavaScript syntax and bridge behavior), package
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
- Fresh local Git clone: own virtual environment/dependencies, deleted starter,
  generated `alice.greeting`, changed Python feature, validated and built an
  unsigned package, generated Alice's private identity outside the checkout,
  published/verified three signed versions and their catalogue, and passed all
  14 tests. No source plugin checkout or official signing credentials required.
- Browser acceptance: built the pinned host frontend with Node.js 22 (Vue
  typecheck and Vite build passed), authenticated against the real PostgreSQL
  host, opened the installed/updated independent plugin's sandboxed frontend,
  entered `Developer`, clicked `Say hello`, and observed **Hello, Developer!**
  returned by the real Python worker through the host message bridge. This found
  and fixed the starter's use of form submission in a script-only sandbox.
  Afterwards uninstalled that plugin and confirmed it disappeared from the host
  list and its UI endpoint returned 404; stopped the disposable host/database.
  Bridge tests also cover wrong-frame/stale replies, error rendering and timeout
  recovery. The built-in catalogue was explicitly disabled in disposable HTTP
  acceptance; that host control is the only catalogue identity in the harness.
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
were validated locally. The starter sandbox UI was exercised; third-party npm
bundles, native modules and privileged PWA/browser integrations were not exercised
end-to-end. The host is the pinned plugin-enabled branch, not ordinary main.

The template's normal CI includes blocking authenticated acceptance with a fresh
service database. Both jobs passed on `427971f37367b8646bfa32d19359584490d84367`
([run](https://github.com/Rosefall-a/plugins-template/actions/runs/37131454212)).
Read the current PR checks for execution status after subsequent changes.
