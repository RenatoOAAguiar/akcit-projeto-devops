import json
from io import BytesIO
from urllib.error import URLError

import pytest

from devops_lab import pr_review

CORRECT = "def calculate_total():\n    total = amount - discount\n    return total\n"
BROKEN = CORRECT.replace("amount - discount", "amount + discount")
SHA = "a" * 40


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("O teste não deve acessar a rede")

    monkeypatch.setattr(pr_review, "urlopen", no_network)


def context(source=CORRECT):
    return {"head_sha": SHA, "files": [], "pricing_source": source}


def event():
    return {
        "number": 1,
        "repository": {"full_name": "owner/repo"},
        "pull_request": {"head": {"sha": SHA}},
    }


def test_master_blocks_bug_without_executing_source():
    source = BROKEN + "\nraise RuntimeError('this must never execute')\n"
    result = pr_review.review(context(source), "rules")
    assert result["agent"] == "Master of Merges"
    assert result["verdict"] == "block"
    assert "110.00" in result["findings"][0]


def test_rules_approve_correct_formula_without_key():
    result = pr_review.review(context(), "auto")
    assert result["verdict"] == "approve" and result["mode"] == "rules"


@pytest.mark.parametrize("source", ["invalid python ???", "", CORRECT.replace("total", "output")])
def test_invalid_or_unrecognized_formula_blocks(source):
    assert pr_review.rule_findings(source, [])


def test_workflow_changes_and_removed_tests_require_review():
    files = [
        {"filename": ".github/workflows/ci.yml", "status": "modified"},
        {"filename": "tests/test_pricing.py", "status": "removed"},
    ]
    assert len(pr_review.rule_findings(CORRECT, files)) == 2


def test_llm_approval_does_not_override_business_rule(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "key")
    monkeypatch.setattr(
        pr_review,
        "ask_llm",
        lambda *args: json.dumps(
            {"verdict": "approve", "summary": "Parece correto", "findings": []}
        ),
    )
    result = pr_review.review(context(BROKEN), "llm")
    assert result["mode"] == "generative" and result["verdict"] == "block"


def test_llm_can_block_another_regression(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "key")
    monkeypatch.setattr(
        pr_review,
        "ask_llm",
        lambda *args: json.dumps(
            {"verdict": "block", "summary": "Uma validação foi removida", "findings": []}
        ),
    )
    result = pr_review.review(context(), "llm")
    assert result["verdict"] == "block" and "validação" in result["findings"][0]


def test_llm_approve_and_secret_redaction(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "private-value")

    def llm(prompt, *args):
        assert "private-value" not in prompt
        return json.dumps({"verdict": "approve", "summary": "ok private-value", "findings": []})

    monkeypatch.setattr(pr_review, "ask_llm", llm)
    data = context(CORRECT + "# private-value")
    result = pr_review.review(data, "auto")
    assert result["verdict"] == "approve"
    assert "private-value" not in result["summary"]


def test_large_diff_is_not_silently_truncated(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "key")
    with pytest.raises(ValueError, match="limite"):
        pr_review.review(context(CORRECT + "#" * 70000), "llm")


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        "[]",
        '{"verdict":"approve"}',
        '{"verdict":"maybe","summary":"ok","findings":[]}',
        '{"verdict":"approve","summary":"ok","findings":[42]}',
    ],
)
def test_invalid_llm_output_cannot_approve(text):
    with pytest.raises(ValueError):
        pr_review.parse_verdict(text)


def test_fenced_json_is_supported():
    text = '```json\n{"verdict":"approve","summary":"ok","findings":[]}\n```'
    assert pr_review.parse_verdict(text)["verdict"] == "approve"


def test_github_api_is_read_only_and_authenticated(monkeypatch):
    def open_request(request, timeout):
        assert request.get_method() == "GET"
        assert request.headers["Authorization"] == "Bearer token"
        return BytesIO(b'{"ok": true}')

    monkeypatch.setattr(pr_review, "urlopen", open_request)
    assert pr_review.api_get("/repos/owner/repo", "token") == {"ok": True}


def test_github_raw_source(monkeypatch):
    monkeypatch.setattr(pr_review, "urlopen", lambda *args, **kwargs: BytesIO(b"source"))
    assert pr_review.api_get("/source", "", raw=True) == "source"


def test_api_error_is_sanitized(monkeypatch):
    def fail(*args, **kwargs):
        raise URLError("secret")

    monkeypatch.setattr(pr_review, "urlopen", fail)
    with pytest.raises(ValueError, match="obter os dados"):
        pr_review.api_get("/source", "token")


def test_github_context_matches_exact_head(monkeypatch):
    replies = iter(
        [
            {"head": {"sha": SHA}, "changed_files": 1},
            [{"filename": pr_review.PRICING_PATH, "patch": "+ discount"}],
            CORRECT,
            {"head": {"sha": SHA}},
        ]
    )
    monkeypatch.setattr(pr_review, "api_get", lambda *args, **kwargs: next(replies))
    result = pr_review.github_context(event(), "token")
    assert result["head_sha"] == SHA and result["pricing_source"] == CORRECT


@pytest.mark.parametrize(
    "responses",
    [
        [{"head": {"sha": "b" * 40}, "changed_files": 1}],
        [{"head": {"sha": SHA}, "changed_files": 101}],
        [{"head": {"sha": SHA}, "changed_files": 1}, []],
        [{"head": {"sha": SHA}, "changed_files": 0}, [], CORRECT, {"head": {"sha": "b" * 40}}],
    ],
)
def test_incomplete_or_stale_pr_never_approves(monkeypatch, responses):
    replies = iter(responses)
    monkeypatch.setattr(pr_review, "api_get", lambda *args, **kwargs: next(replies))
    with pytest.raises(ValueError):
        pr_review.github_context(event(), "token")


def test_invalid_github_metadata_is_rejected():
    data = event()
    data["repository"]["full_name"] = "../evil"
    with pytest.raises(ValueError, match="inválidos"):
        pr_review.github_context(data, "")


@pytest.mark.parametrize(
    ("source", "exit_code", "verdict"), [(CORRECT, 0, "approve"), (BROKEN, 1, "block")]
)
def test_local_gate_status_and_report(tmp_path, source, exit_code, verdict):
    path = tmp_path / pr_review.PRICING_PATH
    path.parent.mkdir(parents=True)
    path.write_text(source, encoding="utf-8")
    output = tmp_path / "review"
    assert (
        pr_review.main(
            ["--local", "--root", str(tmp_path), "--output", str(output), "--mode", "rules"]
        )
        == exit_code
    )
    assert json.loads((output / "review.json").read_text())["verdict"] == verdict
    assert "Master of Merges" in (output / "review.md").read_text(encoding="utf-8")


def test_missing_key_blocks_when_genai_is_required(tmp_path):
    path = tmp_path / pr_review.PRICING_PATH
    path.parent.mkdir(parents=True)
    path.write_text(CORRECT, encoding="utf-8")
    output = tmp_path / "review"
    assert (
        pr_review.main(
            ["--local", "--root", str(tmp_path), "--output", str(output), "--mode", "llm"]
        )
        == 1
    )
    assert json.loads((output / "review.json").read_text())["mode"] == "unavailable"


def test_missing_event_and_local_fails_closed(tmp_path):
    assert pr_review.main(["--output", str(tmp_path)]) == 1


def test_event_cli_reads_context(tmp_path, monkeypatch):
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event()), encoding="utf-8")
    monkeypatch.setattr(pr_review, "github_context", lambda *args: context())
    assert (
        pr_review.main(["--event", str(path), "--output", str(tmp_path / "out"), "--mode", "rules"])
        == 0
    )
