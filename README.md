# Make your own Unnamed Tracking plugin

This is a community/developer template for **your independent plugin repository**:
personal, private, experimental or published. It uses the real Plugin API v1 SDK,
manifest validators, `.utp` builder and Ed25519 signing tools. It is not the
official plugin catalogue. Your plugins do not become official by using it.

Install Python 3.12+ and Node.js 22+. Fork this repository, then clone **your fork**:

```sh
git clone https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
python -m venv .venv
# Activate .venv for your shell (see DEVELOPMENT.md).
python -m pip install -r requirements-dev.txt
python tools/new_plugin.py my-plugin --id yourname.my-plugin --name "My Plugin" --publisher "Your Name"
python tools/check_source_layout.py
python -m pytest
python tools/build_packages.py
python tools/verify_packages.py .validation/dist/yourname.my-plugin-0.1.0.utp
```

Edit `plugins/my-plugin/plugin.py`, `manifest.json`, `ui.json` and `release.json`.
The deletable `hello-world` starter runs a real Python action through a small
sandboxed frontend and displays its response. Remove it once
you have your own plugin. Create more plugins under `plugins/` with unique IDs.

Open **Settings → Plugins → Install plugin** in a plugin-enabled Unnamed Tracking
instance running a standard released version, upload your `.validation/dist/*.utp`,
review unsigned-package consent and permissions, then enable it and open its page.
Check that your release provides **Settings → Plugins** and the APIs you need;
see the guide if support is missing.

For optional signing, generate/register your own identity with
`tools/create_signing_identity.py`, configure `PLUGIN_SIGNING_KEY_ID` and
`PLUGIN_SIGNING_KEY_B64`, commit source, then run
`python tools/build_packages.py --publish`. See the exact commands in
[DEVELOPMENT.md](DEVELOPMENT.md), including secret handling and host trust review.

```text
plugins/hello-world/    deletable real starter
plugins/<your-plugin>/ manifest, Python, UI, release metadata, README
sdk/                   public protocol helper bundled in each package
tools/                 build, validate, sign, verify, catalogue, frontend tools
tests/                 developer workflow and security regression tests
publishers/            your public signing registry (initially empty)
catalogue.json         your catalogue name and hosting configuration
.validation/           ignored preview: dist/, releases/, list.json
dist/, releases/       generated signed publication, once you publish
```

Checks: `python -m ruff check .`, `python tools/build_frontends.py --install`,
`python tools/check_source_layout.py`, `python -m pytest`, and
`python tools/distribution.py --root .validation --check-source` after building.

[Follow the developer guide](DEVELOPMENT.md) for the full first-plugin workflow,
capabilities, secrets, UI, packaging, signing, installation and your own catalogue.
[Propose missing host features](DEVELOPMENT.md#11-propose-a-missing-host-feature)
with the change, motivation, alternatives and tests in a PR to the main application.
[Tooling provenance and comparison](docs/UPSTREAM.md) records what was retained.
