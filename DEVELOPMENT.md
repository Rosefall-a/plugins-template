# Develop plugins in your own repository

This checkout is yours. Use it for personal, private, experimental or public
third-party plugins. It includes the actual Plugin API v1.1 SDK and package tools;
you do not need the upstream plugin repository to build or publish. It does not
include official plugins, maintained examples, official signing keys or a wiki.

## 1. Prepare your fork

Install Git and Python **3.12 or newer**. Node.js **22 or newer** is needed to validate the starter JavaScript. npm is
needed when you add a frontend build. Use a standard released Unnamed Tracking
deployment for installation and UI testing. Check that it provides
**Settings → Plugins** and the capabilities your plugin needs. If support is
missing, building packages still works locally, but installation or the affected
feature must wait for a supporting host release. Follow
[the host-feature contribution guide](#11-propose-a-missing-host-feature).
The reproducible host contract used by CI is recorded in
[provenance](docs/UPSTREAM.md); a CI revision is not proof of release availability.

Fork the template and clone your fork, not the original:

```sh
git clone https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS or
`.\.venv\Scripts\Activate.ps1` in PowerShell. If shell activation is unavailable,
invoke `.venv/bin/python` or `.venv\Scripts\python.exe` explicitly.

```sh
python -m pip install -r requirements-dev.txt
python tools/check_source_layout.py
python -m pytest
python tools/build_packages.py
python tools/distribution.py --root .validation --check-source
```

The initial `publishers/registry.json` has no identities. Unsigned local builds
work without keys or GitHub credentials. `catalogue.json` uses `base_url: "auto"`:
GitHub Actions uses your repository; local builds use `origin` and its default
branch. If neither is available, previews use `https://plugins.example.invalid`
and cannot be downloaded from that placeholder. For non-GitHub hosting, set your
own absolute HTTPS `base_url`. Set `PLUGIN_CATALOGUE_BRANCH` if your publication
branch differs from the remote's default (Actions otherwise uses `main`).

## 2. Create your first plugin

1. Choose a stable ID under your own namespace, for example `yourname.my-plugin`.
   Lowercase letters, digits, dots, underscores and hyphens are supported; start
   with a letter/digit. Keep IDs within **64 characters** for the current runtime,
   even though the exported manifest schema permits 128. Do not use an official
   namespace. IDs distinguish installations and dependencies; a name change is
   not a reason to change the ID.
2. Choose the display name and your publisher label, for example `My Plugin` and
   `Your Name`. The name belongs in the manifest. The publisher belongs in
   `release.json`, not an invented `manifest.author` or `manifest.publisher` field.
3. Create the source directory with the supplied adapter:

   ```sh
   python tools/new_plugin.py my-plugin --id yourname.my-plugin --name "My Plugin" --publisher "Your Name"
   ```

   This generates a real minimal source contract and updates identities, version
   and release metadata. It rejects existing IDs/directories and works after
   deleting `hello-world`. To adapt an existing plugin, use `--from plugins/my-plugin`; audit the copied
   code, UI titles, permissions and asset references before keeping them.
4. Edit `plugins/my-plugin/manifest.json`. The first version is `0.1.0`.
   Keep `entrypoint: "plugin:main"`, `manifest_version: 1`, SDK compatibility,
   application compatibility, `capabilities`, `permissions`, `dependencies`, UI
   IDs and storage quota accurate. Source integrity uses 64 zeroes and null
   signature/key ID; the builder computes real integrity in the package.
   Both manifest and UI declare `api_contract_version: "1.1.0"`. The generated
   SDK range `>=1.1.0,<1.2.0` excludes old hosts. Adapting source with `--from`
   updates these declarations; review its behavior and validate the real plugin,
   because a version marker alone does not migrate an old interface.
5. Start with no optional capabilities. Add only what your implementation uses,
   with matching permission references and specific rationales. See section 3.
6. Implement the plugin in `plugin.py`. The starter sends `lifecycle.ready` using
   the bundled `sdk.plugin_protocol.request` and keeps its worker alive. Its
   `greet(values)` action returns a JSON object. Change the greeting to a small
   feature, for example `return {"message": f"Welcome, {name}!"}`. Diagnostics
   go to stderr; stdout is the JSON-line protocol. Never import host modules.
7. Keep `ui.json` only if needed. The starter declares a `greet` action with
   `handler: "plugin:greet"` and a `hello` page. Match all action/page/settings/menu
   IDs with `manifest.ui`. A headless plugin can remove `ui.json` and empty those
   declarations. For custom frontend assets, see section 5.
8. Add ordinary settings only if needed. Add `plugin.settings` permission and
   settings fields/IDs in `ui.json` and the manifest. Read them with
   `request("settings.get", "plugin.settings", {"key": "greeting"})`. The host
   saves settings; there is no public `settings.put` gateway method.
9. Add tests in `tests/test_my_plugin.py`. Load your module with `importlib.util`
   like `tests/test_template.py`, then assert its feature's returned value and
   invalid-input behavior. For gateway features, unit-test expected calls and
   denied/error responses; also exercise real grants in your host deployment.
10. Update your plugin README and `release.json` (publisher, notes, tags, optional
    packaged icon path and update policy). Remove the original starter directory
    after your new plugin validates. Do not leave incomplete directories under
    `plugins/`: discovery deliberately fails rather than omitting them.
11. Validate and test:

    ```sh
    python tools/check_source_layout.py
    python -m pytest
    python -m ruff check .
    ```

12. Build, validate and verify the resulting package:

    ```sh
    python tools/build_frontends.py --install
    python tools/build_packages.py
    python tools/validate_packages.py --full .validation/dist/yourname.my-plugin-0.1.0.utp
    python tools/verify_packages.py .validation/dist/yourname.my-plugin-0.1.0.utp
    python tools/distribution.py --root .validation --check-source
    ```

13. Inspect it as a ZIP without executing it:

    ```sh
    python -m zipfile --list .validation/dist/yourname.my-plugin-0.1.0.utp
    python -m zipfile --extract .validation/dist/yourname.my-plugin-0.1.0.utp .validation/inspect
    ```

    Inspect `.validation/inspect/manifest.json`, `payload/plugin.py`, bundled SDK,
    `payload/ui.json` and `payload/distribution.json`. Do not modify/repack a signed
    archive. Upload the original `.utp` to your disposable host (section 8).

## 3. Capabilities, permission review and the public API

Declarations request authority; the host decides effective grants for each
installation and caller. A denied grant is an error to handle, not permission to
scrape internal endpoints. Versions refer to capability semantics, currently v1.
Declare each required capability in both arrays:

```json
{
  "capabilities": [{"name": "plugin.storage", "version": 1}],
  "permissions": [{
    "capability": {"name": "plugin.storage", "version": 1},
    "rationale": "Save this plugin's per-user greeting preferences."
  }]
}
```

`lifecycle.ready` is a runtime protocol method, not a grantable manifest
capability. The greeting starter needs no user-data permissions.

| Need | Actual capability / mechanism |
| --- | --- |
| Plugin-owned state | `plugin.storage`: `storage.get`, `storage.put`, `storage.delete`, `storage.keys` |
| Ordinary configuration | `plugin.settings`: `settings.get`, host settings UI |
| Credentials | `plugin.storage`, write-only host secret endpoint/bridge, or explicit action saving brokered storage; no `plugin.secrets` capability |
| Game library | `games.read`: `games.list`, `games.metadata.search` |
| Documents | `documents.read`: `documents.list`, `documents.read`; opaque owned document IDs, not filesystem paths |
| Media | `media.read`: `media.list`; `media.write`: `media.import`, `media.sync` in this host's dispatcher |
| Own sessions | `sessions.read`, `sessions.revoke`: list/revoke/revoke_all; never substitute a browser-supplied user ID |
| Administrative sessions | `sessions.admin.read`, `sessions.admin.revoke`: admin list/revoke/revoke_all/revoke_user; role checks still apply |
| Session GeoIP | `sessions.geoip.read`: `sessions.geoip.status` |
| Notifications | `notifications.send`: `notifications.send` |
| Delivery provider registration | `notification_providers.register`: register/unregister; `notification_providers.deliver` is separately reviewed delivery authority |
| Events | `events.subscribe`: `events.poll` |
| Background work | `tasks.background`: runtime tasks.subscribe/unsubscribe/subscribers/request; current delegated task request is bounded to `media.sync` with target-user grants |
| Network | `network.outbound`: `network.request`, currently bounded GET JSON, eight-second timeout, 4 MiB response, no redirects; only Accept/Authorization/X-Emby-Token headers |
| Namespaced backend API | `backend.routes.plugin`: declared routes below `/api/plugins/<id>/`; domain grants remain separate |
| Host API routes | `backend.routes.host`: exceptional authority for direct `/api/...`; cannot claim plugin-management paths |
| Navigation | `frontend.navigation.main`, `.settings`, `.admin`; exact declared placement |
| Settings and context surfaces | `frontend.settings`, `frontend.context.game`, `.media`, `.documents` |
| Widgets and extensions | `frontend.page.extend`, UI contributions to host-supported targets; `app.global` uses `frontend.overlay` |
| Overlays/dialogs/browser routes | `frontend.overlay`, `frontend.dialog`, `frontend.routes` |
| Replace Home/Settings | `frontend.page.replace.home`, `.settings`; separate high-impact review |
| Native Vue/JS | `frontend.native`: critical browser/host-context authority |
| Site-wide install metadata | `frontend.pwa`: current host additionally requires an official verified v2 publisher; not an independent-template entitlement |

The complete enum is in `tools/schemas/manifest-v1.schema.json`. Some names such
as `users.read`, `users.profile.read`, `games.write`, `media.import` and
`sessions.geoip.configure` are represented in contracts but do not imply a
same-named dispatch method exists. This tested core has no general users gateway
or arbitrary database API. Use only documented implemented operations; do not
invent `users.list` or a general REST proxy. Broad family grants (`games`,
`media`, `sessions`, `notifications`, `frontend.navigation`, `backend.routes`) and
`api.full` exist, but prefer narrow children. `api.full` does not grant arbitrary
filesystem access or native browser execution.

Calls use `request(method, capability, payload)` from `sdk/plugin_protocol.py`.
The host injects authenticated action context. User-owned state must use that
identity, not a form user ID. Gateway results use objects; library list methods
return `items` in this host. Bound your limits, validate input, and handle missing
values and permission errors. Capability risk and elevated reauthentication are
host decisions; catalogue metadata cannot assign them.

Updates that request new permissions require review. Signing never grants them.
Test both consent and denial, multiple users, disabled contributions and changes
to scopes in your real host instance.

## 4. Store state and secrets through the host boundary

Use brokered plugin storage for durable state:

```python
import json
from sdk.plugin_protocol import request

request("storage.put", "plugin.storage", {
    "key": "preferences/greeting", "value": json.dumps({"schema_version": 1, "text": "Hello"})
})
raw = request("storage.get", "plugin.storage", {"key": "preferences/greeting"}).get("value")
saved = json.loads(raw) if raw is not None else None
```

Keys are installation-owned, not automatically private to each user. Namespace
per-user data using the host-authenticated `_plugin_context.user_id`; handle its
actual normalized representation in your action and require a valid identity.
The `host/` namespace is reserved. Declare a modest `storage.quota_mb`; it is
capacity metadata, not a filesystem permission.

For API tokens, passwords, keys or webhook credentials, declare a secret field
and an explicit save flow. The current sandbox bridge method is
**`plugin.save-secret`**, not `plugin.store-secret`. It sends `{key, value}` to
`PUT /api/plugins/<plugin-id>/secrets/<key>`, subject to live `plugin.storage`
approval, and returns `{saved: true}`. There is no public browser read endpoint.
The runtime broker stores the UTF-8 value under `secrets/<key>`; Python reads it
with `storage.get`. An explicit action may instead validate and save a
destination-bound JSON credential via `storage.put`, returning only success.

```python
token = request("storage.get", "plugin.storage", {"key": "secrets/api_key"}).get("value")
# Use it only for the configured, validated destination. Never return or log it.
```

Ordinary settings reject secret fields. Do not return a credential in status,
settings, action results, errors, logs or browser storage. Clear input after save.
Bind credentials to the intended server/user; require a new save when either
changes. Recheck live network grants before outbound requests and refuse
credential forwarding to redirects. Test leaks and denied access.

This is write-only from the browser and brokered runtime storage; it is **not a
promise of encryption at rest or confidentiality from code with the same plugin's
storage grant**. A `secrets/` key name is not a cryptographic boundary. The current
bubblewrap runtime deliberately masks persistent files under `PLUGIN_DATA_DIR`;
read secrets through `storage.get`, not that filesystem path.

Never scrape environment variables, read host database credentials, access
arbitrary host files, embed secrets in source, or commit credentials in manifests
or configuration. Signing seeds are separate from plugin credentials and stay
outside both the checkout and package. Disable/restart/update retains plugin
data; explicit purge/uninstall removes it. Design data migrations to remain
readable by a rollback version; rolling code back does not roll data back.

## 5. Add UI and backend APIs

Follow [the v1.1 integration guide](docs/V1_1.md) for native shared controls,
live theme updates, scoped settings/sidebar placement, shortcuts and schedules.
The exported JSON schemas are the exact machine-readable contracts.

The starter uses a small sandboxed frontend to display the result of its Python
action. Declarative buttons dispatch actions, but the current host does not
display their returned JSON. For simpler forms, use declarative `ui.json` pages,
actions and settings. The host renders
them and filters by lifecycle/grants. Pages reference action/settings/table/dialog
IDs. `pages[].components` is not a v1 field. Main navigation needs
`frontend.navigation.main` and `navigation: {"sidebar": true}` on a declared page.

The exported UI schema also supports menus, tables, dialogs, routes,
`extensions`, `contextual_actions`, `document_readers`, overlays,
`page_replacements`, `settings_sections` and navigation contributions. Home
widgets use the `home.after-widgets` extension slot, global buttons use
`app.global`, and media extensions use `media.detail.after-header`. Declare supported
targets and narrow grants; these contribution arrays are in `ui.json`, while
manifest `ui` lists only settings/actions/pages/menus IDs. Media contexts use
`frontend.context.media`; media data access remains `media.read`/`media.write`.
See `tools/schemas/ui-v1.schema.json` for the exact fields and allowed targets.

For a sandboxed bundle, declare
`"frontend": {"entry": "frontend/index.html", "inline_assets": true}` and bundle
local HTML/JS/CSS. The host uses an opaque `sandbox="allow-scripts"` iframe.
Approved interaction goes through the `postMessage` bridge; there is no general
cookie, host DOM or private backend access. Use script click handlers rather than
HTML form submission: the sandbox does not grant `allow-forms`. Generate request
IDs with `crypto.getRandomValues`; `crypto.randomUUID` depends on a secure context
and may be unavailable in a sandbox on a local development host. Send a unique
`requestId`:

```javascript
parent.postMessage({
  type: "plugin-api-request", requestId: Array.from(crypto.getRandomValues(new Uint32Array(4))).join("-"),
  method: "plugin.run-action", payload: {actionId: "greet", values: {name: "Developer"}}
}, "*");
```

Receive `plugin-api-response` with the matching requestId, `result` or `error`.
Validate `event.source === parent`, correlate responses, impose a timeout and
handle denial. Other current bridge methods include `plugin.save-settings`,
`plugin.save-secret` and `plugin.download-document` (requires scoped documents).

For a frontend build, keep tooling under e.g. `plugins/my-plugin/ui-src/`, commit
`package.json` and `package-lock.json`, and make its build emit local files into
`../frontend/` or `../native/`. Declare **build and test scripts**. The template's
`python tools/build_frontends.py --install` runs npm ci, declared lint/typecheck,
tests and build, then JS syntax checks. Static assets need no npm project. The starter has bridge-response unit tests;
add behavior/browser tests appropriate to your UI. Packaging does not run bundlers
implicitly; build before packaging. Do not depend on the official plugins or a
remote CDN for bundled frontend dependencies.

Native modules require `frontend.native` plus scoped contribution permissions:

```json
{"native_frontend": {"entry": "native/hello.js", "styles": []}}
```

```javascript
export function activate(context) {
  const { h, defineComponent } = context.vue;
  context.registerComponent("hello", defineComponent({
    setup() { return () => h("p", { class: "my-plugin" }, "Hello"); }
  }));
  context.onCleanup(() => { /* dispose timers/listeners you created */ });
}
```

Native code executes with host DOM/browser authority and is explicitly
privileged. Scope CSS, dispose resources, test denial/unmount/reactivation and
never import private frontend modules. Native approval does not bypass backend
ownership or domain permissions. Use declarative/sandboxed UI when sufficient.

For an authenticated backend JSON route, declare `backend.routes.plugin` plus
any data capabilities and add a `backend_routes` manifest entry:

```json
{"backend_routes": [{"id": "greeting", "scope": "plugin", "path": "greeting", "methods": ["GET"], "handler": "plugin:greeting_route", "authorization": "authenticated"}]}
```

```python
from sdk.plugin_protocol import route_response, route_query_value

def greeting_route(route_request: dict) -> dict:
    name = (route_query_value(route_request, "name") or "world")[:80]
    return route_response({"message": f"Hello, {name}!"})
```

This mounts at `/api/plugins/<id>/greeting`. The host supplies normalized
query/path/context dictionaries, authentication, live grants and output bounds.
Use `authorization: "admin"` for admin routes. Return `{status_code, body}`, not
a FastAPI response. Reserved management paths cannot be claimed. Browser routes
and backend routes have different declarations and grants.

## 6. Validate, package and version

```text
source → source validation/tests → frontend build if present
       → build + full manifest/UI/handler validation → .utp
       → optional Ed25519 signature → package/signature/catalogue checks → install
```

`python tools/build_packages.py` writes `.validation/dist/<id>-<version>.utp`,
`.validation/releases/<id>.json` and `.validation/list.json`. Each ZIP contains
root `manifest.json` and `payload/` with Python, SDK, README, UI and bundled
frontend/native/PWA assets, optional declared icon, distribution metadata and
the v2 manifest-binding envelope. Development previews are ignored by Git.
Do not put credentials or live data in package source directories.

Change the version in **`plugins/<name>/manifest.json` only**. Use stable
`MAJOR.MINOR.PATCH`, no leading zeroes or prerelease suffixes. Raise it above the
latest published release. Generated metadata, filenames and manifests take that
version automatically; root pyproject version is unrelated to plugin versions.

The upstream automatic policy also remains available: if source changed without
an explicit newer version, Conventional Commit `feat:` yields a minor bump,
`!`/`BREAKING CHANGE:` a major bump, and other changes a patch. Shared SDK changes
affect consumers. Unchanged source reuses its immutable release. Preview versions
are computed against published history and do not edit source. Signed publication
advances source manifests and appends history. Major automatic releases default
to no automatic update; explicit `release.json.automatic_update` policy still
applies. Starter policy is false to require review.

Use `dependencies: [{"plugin_id": "yourname.other", "version_range": "^1.0.0",
"optional": false}]` for host plugin dependencies, not pip/npm dependencies.
The host validates installed versions and the dependency graph. Compatibility
ranges support `*`, exact versions, caret/tilde, comparisons and comma conjunctions;
the local validator checks syntax. Keep Python code self-contained; the builder
does not install arbitrary Python wheels into workers.

Published artifacts are immutable. Keep all older `dist/*.utp` and release records.
Never edit a signed ZIP or reuse a version for changed bytes. Package payload
SHA-256 differs from complete archive `package_sha256`; use the right hash when
checking downloads. Source schema export provenance is recorded in docs/UPSTREAM.md.

## 7. Sign with your own publisher identity

Signing establishes that bytes and the bound manifest match the holder of the
registered Ed25519 key. It does not establish safe behavior, official status,
permission approval or default host trust.

Choose an owned namespace, exact publisher label and unique key ID. Create an
access-controlled directory **outside your checkout**. On Windows restrict its
ACLs; POSIX creation uses owner-only permissions. Generate once:

```sh
python tools/create_signing_identity.py --key-directory ../my-private-plugin-keys --key-id yourname-1 --publisher "Your Name" --prefix yourname.
```

The tool refuses to overwrite keys, writes the private seed outside Git, adds
only the public base64 key and its SHA-256/scope to `publishers/registry.json`,
and always uses `channel: "community"`. Match each `release.json.publisher` to
the registered label. Scope prefixes must cover every plugin you sign.

Load the seed into environment variables without printing it. PowerShell:

```powershell
$env:PLUGIN_SIGNING_KEY_ID = 'yourname-1'
$env:PLUGIN_SIGNING_KEY_B64 = (Get-Content -Raw ../my-private-plugin-keys/yourname-1.private-seed.b64).Trim()
```

POSIX shell:

```sh
export PLUGIN_SIGNING_KEY_ID=yourname-1
export PLUGIN_SIGNING_KEY_B64="$(cat ../my-private-plugin-keys/yourname-1.private-seed.b64)"
```

Commit source/tooling/catalogue/public-key changes first; publication rejects a
dirty source snapshot. Then:

```sh
python tools/build_packages.py --publish
python tools/verify_packages.py dist/yourname.my-plugin-0.1.0.utp
python tools/validate_packages.py --full dist/yourname.my-plugin-0.1.0.utp
python tools/distribution.py --check-source
```

`--require-signing` is the existing alias for `--publish`. Both require an active,
registered, matching scoped key. Missing, revoked, mismatched or out-of-scope
keys fail. Configured invalid credentials never fall back to unsigned. Ordinary
builds are signed if valid key variables are present; otherwise they are unsigned.

New signatures use `v2:<base64-signature>` over ASCII
`plugin-package-v2:<canonical-payload-sha256>`. Sorted path/NUL/bytes/NUL hashing
includes `package-signature-v2.json`, binding the complete manifest and key ID.
Verification preserves upstream legacy v1 reviewed-pin handling, but this template
ships no legacy packages or keys. Do not change these contracts.

The host distinguishes **Official**, **Verified** and **Unverified** publisher
status. Its reviewed key registry has official/demo/community channels. A signed
community package becomes Verified only when the deployment independently trusts
the matching key and scope. A signature or your own registry cannot grant
Official status. Unknown/unsigned packages use the unverified consent path where
host policy permits; a known invalid signature is rejected. A verified/official
publisher still needs capability consent. Request deployment review of your
public record in the host's `trusted_publishers.json`; never tell users to trust
a key solely because a catalogue contains it. Follow rotation policy: register
the new key, publish new versions, retain historical retiring keys as reviewed,
revoke when needed, and never rewrite old archives.

For GitHub Actions, add **your own** repository secrets `PLUGIN_SIGNING_KEY_ID`
and `PLUGIN_SIGNING_KEY_B64` in Settings → Secrets and variables → Actions.
Commit the public registry first. Do not paste private keys into issues/logs.
Normal PR CI needs no secrets. The manually dispatched release workflow needs
these two secrets and uploads a signed snapshot; it performs no automatic push,
official publication or release creation. Download/review its artifact and commit
its generated manifests, packages/history/list together before hosting them.

## 8. Install, enable, use, update and uninstall locally

Use a disposable instance of a standard released Unnamed Tracking version and
account. Confirm **Settings → Plugins** exists and check release compatibility
before attempting installation. Missing host support requires a supporting
release; see [section 11](#11-propose-a-missing-host-feature). Host setup owns
its PostgreSQL, runtime/container and frontend; this repository does not replace
them. Building packages works on Windows; worker execution uses Linux POSIX
resource/process controls. Do not enable reduced isolation in production merely
to make a plugin work.

1. Open **Settings → Plugins → Install plugin**; select/upload your `.utp`.
2. Preview the package's actual identity, version, compatibility, dependencies,
   hashes, packaged README, signing status and permission rationales. Approve only
   intended grants, including explicit unverified consent when applicable.
3. Configure ordinary settings and save secrets explicitly. Enable/start if the
   installation flow leaves it disabled. Open the plugin detail page; run its
   greeting action and confirm the message. Check ready/running diagnostics.
4. Deny a permission in a feature that uses one and confirm it cannot read data.
   Disable the plugin and confirm actions/contributions stop. Re-enable and
   confirm saved data remains.
5. Change your source feature and raise its single manifest version. Build a new
   package, then use the host update preview/upload flow. Review permission deltas;
   new authority needs approval. Confirm the new greeting and retained data.
6. Exercise rollback if relevant. Code rollback does not restore saved data.
7. Uninstall and confirm the plugin's UI, workers and private state disappear.
   Purge/uninstall is destructive; use only disposable development data.

For automated **contract and runtime tier** checking, obtain the public tested
host source and run:

```sh
python tools/check_host_contract.py --host-root /path/to/plugin-enabled-host
# Linux only; needs host-supported runtime isolation or an explicit development policy:
python tools/check_host_contract.py --host-root /path/to/plugin-enabled-host --lifecycle
```

The first uses actual host models, verifier and installation registry; no host
fixtures are imported into plugin payloads. The second executes the starter's
real worker/action, checks pending-install rejection, disable/re-enable and
a changed-feature version update, then uninstalls. It is not a substitute for authenticated
HTTP permission consent or a real browser UI test. Add integration tests for your
own plugin's permissions/services and follow the manual checklist above.

`python tools/check_host_http.py --host-root /path/to/plugin-enabled-host` additionally
builds a fresh independent plugin and exercises the real PostgreSQL-backed HTTP
installer, unsigned consent, community signing, enable/actions, permission-changing
updates, write-only secret save, brokered secret reads and uninstall. It requires
the host's backend requirements plus `POSTGRES_*` pointing to an **empty disposable
database**; it migrates that database and creates a disposable admin. It uses
the explicit host-supported `NONBUBBLE_ENV` development process mode and owns no
production configuration. CI provisions its own service database for this check.

## 9. Publish your own repository/catalogue

Add as many complete independent plugins as needed under `plugins/`. Configure
your publisher identities and `catalogue.json.name`. Leave `base_url: "auto"`
for GitHub raw hosting or set an owned absolute HTTPS URL without credentials,
query or fragment. Preview catalogue URLs refer to eventual publication, not to
the ignored `.validation` path; upload bytes before advertising them.

```text
plugins/my-plugin/       authored source
plugins/another-plugin/  authored source
dist/<id>-<version>.utp  immutable signed publication
releases/<id>.json       append-only history
list.json               generated catalogue v1
```

Build/test, commit source, run `--publish`, verify, then commit **dist, releases,
list.json and resolved source manifest versions together**. Push only to your
repository. For GitHub Releases, create your own tag/release and upload the same
committed `.utp` files, list and histories. Before uploading tagged assets, run
`python tools/build_packages.py --publish --reuse-published`; it refuses a tag
whose source snapshot has not already been published. No automatic workflow
publishes to any upstream repository.

Serve packages/history first, compare downloaded archive SHA-256 with
`package_sha256`, verify signatures and only then replace the mutable list.
For raw GitHub, the endpoint is your repository's
`https://raw.githubusercontent.com/YOUR-ACCOUNT/YOUR-REPOSITORY/BRANCH/list.json`.
Keep old versioned URLs and bytes available. Private repository raw URLs need
authentication; the current catalogue downloader does not accept GitHub tokens
in URLs. Use manual local installation or an accessible HTTPS service consistent
with the host policy. Do not expose private plugin contents accidentally.

Users add/enable that HTTPS endpoint in **Settings → Plugins → Catalogues**.
The administrative API is `POST /api/plugins/catalogues` with `{name, url}`.
Adding a catalogue establishes neither publisher trust nor capability grants.
Users should verify the public key through an independent channel, actual
package hashes/manifest, requested permissions, source and upgrade behavior.

The builder generates catalogue v1 with exact manifests, payload/archive hashes,
signing metadata, README, notes, update policy and complete ordered history. The
host uses compatible version updates and consent rules; `automatic_update` is
eligibility, not unconditional approval. The current list is bounded to 1 MiB;
use multiple catalogues if needed while preserving release history. This generator
packages your local sources; it is not a remote aggregator or official catalogue.

## 10. CI and troubleshooting

`.github/workflows/ci.yml` blocks on source schemas/IDs/versions/handlers,
Python tests/lint, declared frontend checks/builds, package integrity, signature
regressions, catalogue consistency, immutable published history, actual host
contract, Linux starter lifecycle and authenticated PostgreSQL-backed acceptance.
PR builds upload packages without secrets.
Published history checks apply once history exists; an empty new template has
nothing historical to compare. CI must leave maintained source clean.

Release signing is opt-in via workflow_dispatch; it fails if your own required
identity is missing. It does not make ordinary fork CI depend on signing secrets.
The public host checkout is pinned for reproducibility; updating it requires
reviewing/re-exporting schemas and rerunning contract tests. Source tools and SDK
remain fully local; no official plugin repository checkout is used by CI.

Common failures: duplicate IDs/incomplete source directories; UI IDs not matching
the manifest; absent handler/bundled entry; unsupported ranges; missing npm lock
or build/test scripts; publisher label/scope mismatch; dirty signed source;
changing bytes under a published version; trying an unverified package without
host consent; an installed release missing plugin support or a required API. Fix the
contract or configuration; do not disable validators or silently broaden grants.

Record the exact host version, platform, checks and manual lifecycle evidence in
your release review. See [validation evidence](docs/VALIDATION.md) for the template's
tested scope and limitations.

## 11. Propose a missing host feature

If your plugin needs a capability, UI contribution, route or runtime behavior
that the released application does not expose, propose the smallest general
extension to the [main application](https://github.com/Rosefall-a/unnamed_tracking_app).
Open the PR against its `main` branch and follow that repository's AGENTS.md,
contribution instructions and tests. This template's repository is for plugin
development; host behavior belongs in the application.

First confirm the gap against the installed release and current application
source. Try the supported SDK/gateway methods and UI mechanisms. An enum or
schema field alone does not establish a working host implementation. Record a
small reproduction and the expected behavior; discuss a substantial API or
permission change with maintainers before building a large implementation.

Include these points in the PR description:

- **What changes:** the proposed public contract and host behavior, the plugin
  use case, and a concrete before/after example. Identify the smallest reusable
  API rather than adding behavior tied to one third-party plugin.
- **Why it is needed:** the blocked user workflow, which supported APIs you
  tried, why they cannot provide it, and who else could use the extension.
- **Alternatives considered:** explain the actual options and why each was less
  suitable for this use case. Compare existing declarative/sandboxed UI, a
  narrower gateway method or scoped route, an external integration, and a core
  application feature where relevant. Include concrete limitations or measured
  tradeoffs; do not invent failed alternatives or assume broader access is better.
- **Permissions and isolation:** which capability and scope are needed, how
  consent and denial work, which users/resources may be accessed, how secrets
  stay in brokered storage, and how the host validates requests. Reading host
  credentials, private files or databases directly is not a supported workaround.
- **Compatibility:** SDK/schema changes, dependency and version requirements,
  behavior on older hosts, migration/rollback behavior, and any breaking changes.
- **Validation:** meaningful host tests for success, denial, invalid input and
  relevant lifecycle behavior; plugin-side tests and a real installation/use
  walkthrough. Include screenshots for UI changes and exact test commands.

A useful PR outline is:

```markdown
## Change
[Public API and before/after behavior.]

## Motivation
[Blocked plugin workflow and evidence that the existing API is insufficient.]

## Alternatives considered
[Options tried, their tradeoffs, and why the proposed change fits better.]

## Permissions and compatibility
[Scope, consent, isolation, supported versions and migration behavior.]

## Validation
[Tests, commands and manual lifecycle/UI evidence.]
```

Update the real host contract and any affected shared tooling together. Export
schemas from the application and bring aligned generic changes into this
template and the plugin tooling repository where needed. Do not implement a
private SDK, compatibility shim or extra permission merely to bypass the gap.

After the feature is merged **and released**, test your plugin against that
standard release. Set `application_version_range` (and `sdk_version_range` if
needed) in `manifest.json` to the versions you actually support, increment the
plugin version, then validate/build/sign again. Document the required host
release in the plugin README. A merged PR or passing development CI does not
mean an older installed release already supports the feature.
