from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "superpowers" / "specs" / "2026-04-14-retract-ripple-design.md"


def test_retract_ripple_spec_declares_recompute_and_flip_contract():
    text = SPEC.read_text(encoding="utf-8")
    required = [
        "Retraction Watch",
        "Cochrane CDSR",
        "re-pool",
        "flip_rule_A",
        "flip_rule_B",
        "flip_rule_C",
        "data/recomputed_effects.csv",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []


def test_retract_ripple_spec_has_stats_and_source_safety_gates():
    text = SPEC.read_text(encoding="utf-8")
    required = [
        "HKSJ",
        "t-distribution",
        "k_after_removal = 1",
        "k_after_removal = 2",
        "tolerance 1e-6",
        "No paywalled content",
        "TruthCert",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []
