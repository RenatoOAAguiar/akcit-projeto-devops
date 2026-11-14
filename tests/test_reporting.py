from devops_lab.reporting import diagnosis_markdown, review_markdown


def test_review_leads_with_finding_and_collapses_metadata():
    result = {
        "verdict": "block",
        "summary": "O desconto está sendo somado ao subtotal.",
        "findings": ["pricing.py: subtraia o desconto."],
        "mode": "generative",
        "model": "model",
        "head_sha": "commit",
    }
    report = review_markdown(result)
    assert report.index("O desconto") < report.index("<details>")
    assert report.index("pricing.py") < report.index("<details>")
    assert "Master of Merges" not in report
    assert "sem IA generativa" not in report


def test_duplicate_rule_evidence_remains_available_but_not_repeated_in_comment():
    findings = [
        "pricing.py: a operação esperada é total = amount - discount.",
        "pricing.py: amount + discount deve ser amount - discount.",
    ]
    result = {
        "verdict": "block",
        "summary": "Desconto incorreto.",
        "findings": findings,
        "mode": "generative",
        "head_sha": "commit",
    }
    report = review_markdown(result)
    assert report.count("- pricing.py:") == 1
    assert len(result["findings"]) == 2


def test_review_does_not_hide_rule_when_llm_misses_the_bug():
    result = {
        "verdict": "block",
        "summary": "Modelo não apontou falhas.",
        "findings": ["pricing.py: a operação esperada é total = amount - discount."],
        "mode": "generative",
        "head_sha": "commit",
    }
    assert "operação esperada" in review_markdown(result)


def test_local_mode_is_clearly_identified():
    result = {
        "verdict": "approve",
        "summary": "Regra verificada.",
        "findings": [],
        "mode": "rules",
        "head_sha": "local",
    }
    assert "sem IA generativa" in review_markdown(result)
    assert "OFFLINE" in diagnosis_markdown("Sem modelo.", {"mode": "offline", "commit": "local"})


def test_diagnosis_unwraps_model_markdown_and_preserves_python_fence():
    raw = "```markdown\n# Problema\nSoma incorreta.\n```python\ntotal = amount - discount\n```\n```"
    report = diagnosis_markdown(raw, {"mode": "generative", "model": "model", "commit": "sha"})
    assert "```markdown" not in report
    assert "### Problema" in report
    assert "```python\ntotal = amount - discount\n```" in report
    assert "OFFLINE" not in report


def test_diagnosis_preserves_a_regular_python_code_block():
    text = "### Correção\n\n```python\ntotal = amount - discount\n```"
    assert text in diagnosis_markdown(text, {"mode": "generative", "commit": "sha"})
