import hashlib
import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from devops_lab import diagnostics


@pytest.fixture(autouse=True)
def clean_llm_environment(monkeypatch):
    for name in ("LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def evidence(tmp_path):
    (tmp_path / "src/devops_lab").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "src/devops_lab/pricing.py").write_text(
        "total = amount + discount", encoding="utf-8"
    )
    (tmp_path / "tests/test_pricing.py").write_text("assert total == 90", encoding="utf-8")
    log = tmp_path / "pytest.log"
    log.write_text("FAILED test_discount_is_subtracted: 110 != 90", encoding="utf-8")
    return tmp_path, log


def fake_api(monkeypatch, response):
    class Opener:
        def open(self, request, timeout):
            if isinstance(response, Exception):
                raise response
            return BytesIO(json.dumps(response).encode("utf-8"))

    monkeypatch.setattr(diagnostics, "build_opener", lambda *args: Opener())


def test_redaction_removes_known_and_configured_secrets():
    text = "custom-value sk-123456789 ghp_ABC github_pat_X Bearer abc.def password=abc token: def"
    clean = diagnostics.redact(text, "custom-value")
    for secret in ["custom-value", "sk-123456789", "ghp_ABC", "github_pat_X", "abc", "def"]:
        assert secret not in clean
    assert "[REDACTED]" in clean


def test_prompt_limits_large_logs_after_redaction():
    log = "HEAD\n" + "x" * 40000 + "\nTAIL private-key"
    prompt = diagnostics.build_prompt(log, "source private-key", "test", "private-key")
    assert "private-key" not in prompt
    assert "HEAD" in prompt and "TAIL" in prompt and "truncado" in prompt
    assert len(prompt) < 25000


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/v1",
        "https://user:pw@example.com",
        "file:///tmp/x",
        "https://example.com?q=1",
        "https://example.com/#x",
        "https://",
    ],
)
def test_remote_endpoint_validation(url):
    with pytest.raises(ValueError, match="HTTPS"):
        diagnostics.ask_llm("prompt", url, "model", "key")


@pytest.mark.parametrize(("model", "key"), [("", "key"), ("model", "")])
def test_remote_configuration_is_required(model, key):
    with pytest.raises(ValueError, match="Configure"):
        diagnostics.ask_llm("prompt", "https://example.com/v1", model, key)


def test_llm_request_and_response(monkeypatch):
    captured = {}

    class Opener:
        def open(self, request, timeout):
            captured.update(
                url=request.full_url,
                payload=json.loads(request.data),
                headers=request.headers,
                timeout=timeout,
            )
            return BytesIO(b'{"choices":[{"message":{"content":"Diagnostico"}}]}')

    monkeypatch.setattr(diagnostics, "build_opener", lambda *args: Opener())
    assert diagnostics.ask_llm("evidence", "https://example.com/v1/", "model", "key") == (
        "Diagnostico"
    )
    assert captured["url"] == "https://example.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer key"
    assert captured["payload"]["messages"][1]["content"] == "evidence"
    assert captured["timeout"] == 90


def test_local_llm_does_not_require_key(monkeypatch):
    fake_api(monkeypatch, {"choices": [{"message": {"content": "Análise local"}}]})
    assert diagnostics.ask_llm("p", "http://localhost:11434/v1", "model", "") == "Análise local"


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (HTTPError("https://example.com", 429, "rate limit", {}, None), "HTTP 429"),
        (URLError("private key must not leak"), "indisponível"),
        (TimeoutError("timed out"), "indisponível"),
    ],
)
def test_api_errors_are_actionable_without_leaking_response(monkeypatch, error, message):
    fake_api(monkeypatch, error)
    with pytest.raises(ValueError, match=message) as exc:
        diagnostics.ask_llm("p", "https://example.com", "model", "key")
    assert "private key" not in str(exc.value)


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"choices": []},
        None,
        {"choices": [{"message": {"content": " "}}]},
        {"choices": [{"message": {"content": []}}]},
    ],
)
def test_malformed_responses_are_rejected(monkeypatch, response):
    fake_api(monkeypatch, response)
    with pytest.raises(ValueError):
        diagnostics.ask_llm("p", "https://example.com", "model", "key")


def test_redirect_is_refused():
    assert diagnostics.NoRedirect().redirect_request(None, None, 302, "", {}, "https://x") is None


def test_offline_does_not_invent_diagnosis():
    assert "inconclusivo" in diagnostics.offline_analysis(
        "ImportError", "total = amount + discount"
    )


def test_offline_report_and_prompt(evidence):
    root, log = evidence
    output = root / "analysis"
    assert (
        diagnostics.main(
            ["--log", str(log), "--root", str(root), "--output", str(output), "--mode", "offline"]
        )
        == 0
    )
    metadata = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
    assert metadata["mode"] == "offline" and metadata["model"] is None
    assert metadata["log_sha256"] == hashlib.sha256(log.read_bytes()).hexdigest()
    report = (output / "analysis.md").read_text(encoding="utf-8")
    assert "OFFLINE" in report and "90.00" in report and "110.00" in report
    assert (output / "prompt.txt").is_file()


def test_auto_fallback_is_explicit(evidence):
    root, log = evidence
    output = root / "analysis"
    assert diagnostics.main(["--log", str(log), "--root", str(root), "--output", str(output)]) == 0
    metadata = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
    assert metadata["mode"] == "offline"
    assert "Configure" in metadata["fallback_reason"]


def test_strict_llm_mode_fails_without_credentials(evidence):
    root, log = evidence
    assert (
        diagnostics.main(
            [
                "--log",
                str(log),
                "--root",
                str(root),
                "--output",
                str(root / "analysis"),
                "--mode",
                "llm",
            ]
        )
        == 1
    )


def test_generative_report_and_output_redaction(evidence, monkeypatch):
    root, log = evidence
    output = root / "analysis"
    monkeypatch.setenv("LLM_API_KEY", "test-private-key")
    fake_api(monkeypatch, {"choices": [{"message": {"content": "Sugestão test-private-key"}}]})
    assert (
        diagnostics.main(
            ["--log", str(log), "--root", str(root), "--output", str(output), "--mode", "llm"]
        )
        == 0
    )
    assert json.loads((output / "analysis.json").read_text())["mode"] == "generative"
    assert "test-private-key" not in (output / "analysis.md").read_text(encoding="utf-8")


def test_missing_evidence_fails_cleanly(tmp_path, capsys):
    assert diagnostics.main(["--log", str(tmp_path / "missing")]) == 2
    assert "Evidências não encontradas" in capsys.readouterr().err
