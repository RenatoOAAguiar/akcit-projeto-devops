# Laboratório DevOps com IA generativa

Aplicação Python de descontos com testes, CI/CD, diagnóstico de logs e revisão de PRs pelo
**Master of Merges**. Demonstra o diagnóstico de falhas em CI/CD com IA generativa, usando GitHub.

Repositório: <https://github.com/RenatoOAAguiar/akcit-projeto-devops>

O projeto começa correto. O comando `break` introduz um defeito real: somar o desconto ao
subtotal. Para uma compra de 100 com desconto de 10%, a versão defeituosa retorna 110.00;
a regra exige 90.00. Os testes e o revisor detectam a regressão de forma independente.

## Começar no Windows

Requer Python 3.11 ou superior; a CI usa Python 3.13. Execute na raiz do projeto:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt -e .
.venv\Scripts\python -m devops_lab --subtotal 100 --discount 10
.venv\Scripts\python scripts/run_checks.py --output reports/baseline
```

Não é necessário ativar a venv. Nos comandos abaixo, use o Python da venv, ou ative-a antes.
Em Linux/macOS, use `.venv/bin/python` no lugar de `.venv\Scripts\python`.

## Comandos principais

| Comando | Resultado |
| --- | --- |
| `python -m devops_lab --subtotal 100 --discount 10` | JSON com total `90.00` |
| `python scripts/run_checks.py --output reports/baseline` | Testes, cobertura, log, JUnit e metadados |
| `python -m ruff check .` | Validação de estilo e imports |
| `python -m ruff format --check .` | Verificação da formatação |
| `python scripts/lab.py break` | Introduz a soma indevida do desconto |
| `python -m devops_lab.pr_review --local --mode rules` | Revisão estática; saída 1 para bloquear |
| `python scripts/lab.py fix` | Restaura a subtração do desconto |
| `python scripts/lab.py status` | Mostra `correct` ou `broken` |
| `python scripts/verify_lab.py` | Valida todo o ciclo local, sem chamadas de IA nem operações GitHub |
| `python scripts/build_release.py` | Gera `dist/devops-lab.pyz` |
| `python dist/devops-lab.pyz --subtotal 100 --discount 10` | Executa a versão empacotada |

Testes usam pytest e pytest-cov, com cobertura mínima de 85%. Valores monetários usam
`Decimal`, arredondamento `ROUND_HALF_UP` e validação de limites. Os arquivos `tests/test_*.py`
incluem contratos de negócio, CLI, falhas de rede, respostas inválidas e decisões do revisor.

## Master of Merges

Ao abrir ou atualizar uma PR, o agente lê o diff e a regra de desconto, emite um parecer e
falha a checagem se encontrar um problema. Ele executa **a versão do revisor da branch base**;
o código proposto é lido pela API e não é executado pelo revisor. Os testes rodam em outro job.

- Com `LLM_API_KEY` configurada, usa IA generativa e uma regra estática para a falha conhecida.
- Sem chave, o modo `auto` usa apenas a regra estática, identificado como `rules`.
- Com a variável de Actions `REQUIRE_GENAI=true`, falha de configuração, cota, rede ou resposta
  inválida bloqueia a revisão. Uma resposta da IA nunca anula um defeito detectado pela regra.
- A regra estática cobre o contrato deste laboratório; não substitui uma revisão geral.

**Para impedir o merge, configure a proteção de `main` exigindo `Master of Merges` e
`Qualidade e testes`.** Um comentário sozinho não impede o merge. O roteiro está em
[docs/GUIA_LABORATORIO.md](docs/GUIA_LABORATORIO.md).

O bot publica comentários como `github-actions[bot]`, com o título **Master of Merges**.
Um nome e avatar próprios na conta do bot exigiriam um GitHub App separado.

## IA e configuração

O workflow referencia o secret **`LLM_API_KEY`**. A chave não deve aparecer no código,
em `.env` versionado, em uma Repository Variable, no histórico do terminal ou nas capturas.
Um repositório público pode usar Actions Secrets; a chave não é publicada com os arquivos.

| Configuração em Settings → Secrets and variables → Actions | Tipo | Valor |
| --- | --- | --- |
| `LLM_API_KEY` | Secret | Chave do seu provedor, já cadastrada no repositório |
| `LLM_BASE_URL` | Variable | Padrão: `https://api.openai.com/v1` |
| `LLM_MODEL` | Variable | Padrão: `gpt-4.1-mini`; ajuste para seu provedor |
| `REQUIRE_GENAI` | Variable | `true` para exigir análise generativa concluída |

A integração usa HTTP Chat Completions compatível com OpenAI. A chave precisa corresponder
ao endpoint e ao modelo. O agente não carrega `.env` automaticamente. Para execução local,
configure as variáveis no processo; o secret do GitHub só existe durante a execução remota.
Ollama local também é suportado em `http://localhost:11434/v1`, com um modelo instalado e
`LLM_MODEL` definido. Esse servidor local não fica acessível ao runner hospedado do GitHub.

## Organização e evidências

```text
src/devops_lab/       Aplicação, diagnóstico de logs e Master of Merges
tests/               Testes automatizados
scripts/             Injeção/correção da falha, execução e empacotamento
.github/workflows/   CI/CD e revisão obrigatória de PR
docs/                Roteiro, checklist de evidências e modelo de postagem
reports/             Evidências locais geradas, ignoradas pelo Git
dist/                Aplicação empacotada, ignorada pelo Git
```

Em `main`, a entrega só acontece após testes aprovados: a CI gera e verifica uma aplicação
`.pyz`, disponível como artefato. Isso demonstra entrega contínua de um executável Python;
não há infraestrutura externa de produção neste laboratório.

Siga o [guia completo](docs/GUIA_LABORATORIO.md), registre as evidências no
[checklist](docs/EVIDENCIAS.md) e preencha o [modelo de postagem](docs/RELATO_FORUM.md).

## Referências técnicas

- [Actions Secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Proteção de branches e checagens obrigatórias](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [API Chat Completions](https://developers.openai.com/api/reference/resources/chat)
- [Compatibilidade do Ollama](https://docs.ollama.com/api/openai-compatibility)
