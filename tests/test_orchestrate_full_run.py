import json
from pathlib import Path

from leadgen import orchestrate_full_run as orch
from leadgen.models import Business


def test_stable_shard_is_valid():
    assert orch._stable_shard("abc") in {"A", "B", "C"}


def test_main_dry_run(tmp_path: Path):
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "targets:\n"
        "  - id: t1\n"
        "    query: dentists in miami\n"
        "    shard: A\n",
        encoding="utf-8",
    )

    rc = orch.main(
        [
            "--manifest",
            str(manifest),
            "--shard",
            "A",
            "--dry-run",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    summaries = list((tmp_path / "out").glob("run_*_a/summary.json"))
    assert summaries
    payload = json.loads(summaries[0].read_text(encoding="utf-8"))
    assert payload["shard"] == "A"
    assert payload["selected_target_ids"] == ["t1"]


def test_manifest_driven_shard_selection_without_explicit_shard(tmp_path: Path):
    target_id = "auto-shard-target"
    shard = orch._stable_shard(target_id)
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "targets:\n"
        f"  - id: {target_id}\n"
        "    query: dentists in miami\n",
        encoding="utf-8",
    )

    rc = orch.main(
        [
            "--manifest",
            str(manifest),
            "--shard",
            shard,
            "--dry-run",
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    summaries = list((tmp_path / "out").glob(f"run_*_{shard.lower()}/summary.json"))
    assert summaries


def test_run_target_propagates_sellable_and_quality_gate_failures(monkeypatch, tmp_path: Path):
    target = orch.Target(id="t1", query="dentists in miami", limit=5)

    monkeypatch.setattr(
        orch,
        "search_places",
        lambda query, limit, include_status=True: ([Business(name="Biz One")], "OK"),
    )

    monkeypatch.setattr(
        orch,
        "generate_pack",
        lambda **kwargs: {
            "lead_count": 1,
            "sellable": False,
            "quality_gate_failures": ["zeta_failure", "alpha_failure"],
        },
    )

    result = orch.run_target(
        target=target,
        shard="A",
        output_dir=tmp_path / "out",
        base_pack_dir=tmp_path / "packs",
        dry_run=False,
        timeout_seconds=30,
    )

    assert result.packed == 1
    assert result.sellable is False
    assert result.quality_gate_failures == ["alpha_failure", "zeta_failure"]
