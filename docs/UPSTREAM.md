# Tooling provenance and deliberate comparison

## Current v1.1 synchronization (5 October 2026)

SDK and exported schemas are synchronized with companion revision
`0f3483c6d35790ffddca99b6e40d065b90674006`. The public validator's current-contract
checks are retained for matching API declarations, shortcuts and host-managed
tasks; the template's independent catalogue/signing adaptations remain intact.
No official implementation, publisher identity, runtime or catalogue is copied.

Both blocking CI jobs now use public host revision
`6bae984ce7590903e9144e4301ffa1b0fe65c809`, whose complete seven-workflow CI passes.
The starter and generator explicitly target v1.1, exclude old hosts, and consume
the public appearance bridge. Branch checks publish `unsigned-dist`; signed
publication remains manual with developer-owned credentials.

The original provenance and adaptations below remain relevant history.

Inspected on 3 October 2026:

- Source: [plugin repository](https://github.com/Rosefall-a/unnamed_tracking_app_plugins),
  revision `8bc13e2ef97bc48a774b54490ee0f93744e6458c`.
- Template starting revision: `a9dbee4ae60c17c9d8aa5e3bd024aa60c7254ff4` (README only).
- Public host integration target: [host contract revision](https://github.com/Rosefall-a/unnamed_tracking_app/tree/83a6fadec8b725bf94bec4583faab48af2aa84dc),
  revision `83a6fadec8b725bf94bec4583faab48af2aa84dc`.
- Exported manifest/UI schemas originate at host
  `f1165fcc805e57ee428e7bc42fa6b83f4a6caf25`; current host conformance is tested
  separately. These are exported public contracts, not a replacement runtime.

The upstream SDK is retained verbatim. The original builder, distribution/release
selection, canonical payload format, registry validation, Ed25519 signing,
verification, static source checker and manifest/UI schemas are retained with
explicit adaptations below. The host remains responsible for runtime,
installation, gateway, permissions, trusted publisher review and UI rendering.

| Area | Source | Template |
| --- | --- | --- |
| Manifest/UI schemas and static validation | yes | yes |
| SDK and JSON-line runtime integration | yes | same SDK |
| `.utp` builder and canonical package integrity | yes | same contract |
| Signing and signature verification | yes | same v2 binding and registry checks |
| Capability/permission/dependency declarations | yes | same public schemas |
| Backend routes / sandbox and native UI payloads | yes | same packaging support |
| Version resolution and immutable release history | yes | same policy |
| Catalogue v1 generation and validation | yes | own catalogue only |
| Python tests and host conformance | yes | independent workflow/security coverage |
| Frontend checks/builds | plugin-specific | generic per-plugin npm scripts + static JS checks |
| Linux worker lifecycle | official/example-specific | real deletable starter, own-plugin manual acceptance |
| Official plugins | yes | **no** |
| Maintained examples / deprecated archives | yes | **no** |
| Official catalogue and publisher keys | yes | **no** |
| Automatic official publication | yes | **no** |
| Official wiki / MkDocs / screenshots | yes | **no** |
| Developer guide | source wiki | **rewritten DEVELOPMENT.md** |

## Adaptations

- Source discovery uses `plugins/` only. No source listings, retired packages,
  generated releases/catalogue or key files were copied. `hello-world` is a new,
  neutral and deletable actual Plugin API v1 action/page, not a catalogue fixture.
- Catalogue URLs derive from the developer's GitHub fork/default branch, or an
  explicitly owned HTTPS base. The offline preview fallback is a reserved invalid
  domain. Publisher labels are developer-authored release metadata.
- Signing uses generic `PLUGIN_SIGNING_KEY_ID/KEY_B64` only and community channel
  identities. Official/example channel selection and official-specific PWA
  provenance/version policy were removed; generic PWA asset validation remains.
  The real host retains its official-only site-wide PWA policy.
- `release_record` avoids loading signing identities for a package with no key
  ID. This tiny generic fix was squash-merged upstream in
  [PR #38](https://github.com/Rosefall-a/unnamed_tracking_app_plugins/pull/38)
  with regression coverage;
  unsigned previews can have an empty registry. Signed verification still needs
  the complete existing strict registry and cannot accept unknown keys.
- New source/signing/frontend helpers orchestrate the same machinery; they do not
  create a second SDK, host, version system, catalogue API or package format.
- Independent CI needs no credentials. Signed release snapshot generation is
  manual and requires developer-owned secrets. No automatic main-branch pushes
  or publishing to a catalogue is included. Public host conformance is pinned.
- Tests are appropriate to independent sources and developer-owned signers.
  Upstream product/example/browser/wiki tests were not copied because their
  subject plugins and documentation do not exist here. Package validation,
  signatures, lifecycle and histories remain blocking checks.

References to the upstream account occur only here and in the pinned public host
checkout in CI. They identify provenance/the application being tested, not this
repository's publisher, catalogue, signing identity or release target.

## Boundary checks

Documentation was checked against host runtime and frontend implementation,
including `plugin.save-secret` (the current bridge name), brokered storage and
native frontend authority. Contract enum presence alone is not documented as a
working gateway method. The pinned conformance revision is a test target;
developers install a standard released application with the required plugin
support. CI against a source revision does not establish availability in a
published release. See the developer guide's release check and host-feature PR
instructions when required support is missing.

Follow [DEVELOPMENT.md](../DEVELOPMENT.md) without fetching the upstream plugin
repository. See [VALIDATION.md](VALIDATION.md) for the exact exercised scope.
