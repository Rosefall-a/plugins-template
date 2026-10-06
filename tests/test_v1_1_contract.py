"""New developer sources use the current contract and validate live contribution grants."""

import json

import pytest

from sdk.plugin_protocol import API_CONTRACT_VERSION
from tools.distribution import ROOT, canonical_json, collect_payload
from tools.starter_ui import HTML, JAVASCRIPT
from tools.validate_packages import validate_current_contract


def contract():
    source = ROOT / "plugins/hello-world"
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    files, metadata = collect_payload(ROOT, source, manifest)
    files["distribution.json"] = canonical_json(
        {
            **metadata,
            "version": manifest["version"],
            "automatic_update": False,
        }
    )
    return manifest, files


def consent(manifest, name):
    reference = {"name": name, "version": 1}
    manifest["capabilities"].append(reference)
    manifest["permissions"].append(
        {"capability": reference, "rationale": "Exercise this declared contribution."}
    )


def test_starter_targets_v1_1_and_generated_assets_match():
    manifest, files = contract()
    assert manifest["api_contract_version"] == API_CONTRACT_VERSION == "1.1.0"
    assert manifest["sdk_version_range"] == ">=1.1.0,<1.2.0"
    assert json.loads(files["ui.json"])["api_contract_version"] == "1.1.0"
    assert files["frontend/index.html"].decode() == HTML
    assert files["frontend/hello.js"].decode() == JAVASCRIPT
    validate_current_contract(manifest, files)


def test_mismatched_ui_contract_is_rejected():
    manifest, files = contract()
    document = json.loads(files["ui.json"])
    document["api_contract_version"] = "1.0.0"
    files["ui.json"] = canonical_json(document)
    with pytest.raises(ValueError, match="contracts must match"):
        validate_current_contract(manifest, files)


def test_task_requires_explicit_background_consent_and_real_action():
    manifest, files = contract()
    manifest["scheduled_tasks"] = [{"id": "greeting", "name": "Greeting", "action_id": "greet"}]
    with pytest.raises(ValueError, match="explicit tasks.background"):
        validate_current_contract(manifest, files)
    consent(manifest, "tasks.background")
    validate_current_contract(manifest, files)
    manifest["scheduled_tasks"][0]["action_id"] = "missing"
    with pytest.raises(ValueError, match="action must exist"):
        validate_current_contract(manifest, files)


def test_shortcuts_need_explicit_consent_and_declared_targets():
    manifest, files = contract()
    document = json.loads(files["ui.json"])
    document["shortcuts"] = [
        {"id": "greeting", "label": "Say hello", "keys": ["Alt+H"], "action_id": "greet"}
    ]
    files["ui.json"] = canonical_json(document)
    with pytest.raises(ValueError, match="declared frontend/settings permissions"):
        validate_current_contract(manifest, files)
    consent(manifest, "frontend.shortcuts")
    validate_current_contract(manifest, files)
    document["shortcuts"][0]["action_id"] = "missing"
    files["ui.json"] = canonical_json(document)
    with pytest.raises(ValueError, match="undeclared destination"):
        validate_current_contract(manifest, files)
