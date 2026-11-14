"""Comentários de revisão com o problema em destaque e metadados recolhidos."""

import re


def _details(mode: str, model: str | None, commit: str, reason: str = "") -> str:
    label = "IA generativa" if mode == "generative" else mode
    text = (
        "<details>\n<summary>Detalhes da análise</summary>\n\n"
        f"Origem: {label} · Modelo: `{model or 'nenhum'}`\n\n"
        f"Commit: `{commit}`\n"
    )
    if reason:
        text += f"\n{reason}\n"
    return text + "\n</details>\n"


def review_markdown(result: dict) -> str:
    status = "Alterações necessárias" if result["verdict"] == "block" else "Revisão concluída"
    report = f"**{status}**\n\n{result['summary']}\n"
    findings = list(dict.fromkeys(result["findings"]))
    # A evidência da regra continua no JSON; evitar repetir o mesmo defeito no comentário.
    if len(findings) > 1 and any("amount + discount" in finding for finding in findings):
        findings = [item for item in findings if "a operação esperada é total = amount" not in item]
    if findings:
        report += "\n" + "\n".join(f"- {item}" for item in findings) + "\n"
    if result["mode"] == "rules":
        report += "\nAnálise por regras locais, sem IA generativa.\n"
    return report + "\n" + _details(result["mode"], result.get("model"), result["head_sha"])


def diagnosis_markdown(diagnosis: str, metadata: dict) -> str:
    text = diagnosis.strip()
    # Alguns modelos envolvem todo o Markdown em uma cerca, inclusive cercas Python internas.
    lines = text.splitlines()
    if len(lines) > 1 and lines[0].strip() in {"```markdown", "```md", "```"}:
        if lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()
    text = re.sub(r"(?m)^#{1,6}\s+", "### ", text)
    prefix = "" if metadata["mode"] == "generative" else "**OFFLINE — sem IA generativa.**\n\n"
    return (
        prefix
        + text
        + "\n\n"
        + _details(
            metadata["mode"],
            metadata.get("model"),
            metadata["commit"],
            metadata.get("fallback_reason", ""),
        )
    )
