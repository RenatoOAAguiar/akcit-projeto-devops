# Roteiro do experimento

## 1. Preparar e validar a base

Faça a instalação descrita no README. Nesta página, `python` representa o interpretador
da venv. No PowerShell, você pode substituir por `.venv\Scripts\python` em cada comando.

Para uma demonstração local automática, execute `python scripts/verify_lab.py`. O script
testa a base, introduz a falha, verifica testes e bloqueio, gera o diagnóstico offline,
corrige o código, confirma a aprovação e empacota a aplicação. O arquivo original é
restaurado ao final. Evidências ficam em `reports/validation/`. Essa demonstração não
abre uma PR nem consulta um modelo real; as etapas remotas estão nas seções seguintes.

```powershell
python scripts/lab.py status
python scripts/run_checks.py --output reports/baseline
python -m ruff check .
python -m ruff format --check .
python scripts/build_release.py
python dist/devops-lab.pyz --subtotal 100 --discount 10
```

O estado deve ser `correct`, todos os testes devem passar e o executável deve retornar
`90.00`. Não introduza a falha antes de publicar essa base: o revisor da primeira PR
precisa existir em `main`.

## 2. Publicar a base no GitHub

O remote esperado é `https://github.com/RenatoOAAguiar/akcit-projeto-devops.git`.
Confira com `git remote -v`. Estes comandos são para a publicação manual pelo responsável:

```powershell
git add .
git status --short
git commit -m "feat: add DevOps and GenAI laboratory"
git push -u origin main
```

Revise a lista de arquivos antes do commit. `reports/`, `.venv/`, `dist/`, `.cache/` e
arquivos `.env` estão no `.gitignore`. O arquivo `.env.example` contém apenas exemplos.
Na aba **Actions**, aguarde a execução inicial. `Qualidade e testes` e
`Entrega da aplicacao validada` devem ficar verdes. Baixe o artefato `aplicacao-<sha>`
e execute o `.pyz` para demonstrar a entrega.

## 3. Configurar a IA sem publicar a chave

O secret `LLM_API_KEY` já foi criado pelo responsável. Não recrie a chave em nenhum arquivo.
Em **Settings → Secrets and variables → Actions → Variables**, configure:

1. `LLM_MODEL`: modelo autorizado pela sua chave; o padrão é `gpt-4.1-mini`.
2. `LLM_BASE_URL`: mantenha `https://api.openai.com/v1` se a chave for OpenAI, ou use a URL
   compatível do seu provedor. Não coloque a chave nesta URL.
3. `REQUIRE_GENAI`: `true`, para que o Master of Merges só aprove após uma resposta válida de IA.

Para este experimento, abra a PR a partir de uma branch do próprio repositório. PRs de forks
não recebem o secret. Com `REQUIRE_GENAI=true`, elas ficam bloqueadas por indisponibilidade
da análise generativa; não recebem comentários com token de escrita. Em modo `auto`, sem
exigência de IA, a revisão estática continua funcionando. Não habilite envio de secrets a forks.

O revisor usa o código da base. A chave é entregue somente ao passo que chama o modelo.
Os testes não recebem `LLM_API_KEY`. O diagnóstico de logs com credenciais é restrito a
branches do próprio repositório. Não troque o evento por `pull_request_target` para testar forks.

## 4. Criar a PR com falha

```powershell
git switch -c lab/desconto-incorreto
python scripts/lab.py break
git diff -- src/devops_lab/pricing.py
python -m devops_lab.pr_review --local --mode rules --output reports/review-broken
python scripts/run_checks.py --output reports/broken
```

Os dois últimos comandos devem terminar com código 1. O revisor deve indicar **BLOQUEADO**;
os testes de desconto devem falhar. A alteração deve ser somente de `-` para `+` na linha
`total = amount - discount`. Os testes não devem ser alterados para aceitar o erro.

```powershell
git add src/devops_lab/pricing.py
git commit -m "test: introduce intentional discount regression"
git push -u origin lab/desconto-incorreto
```

No GitHub, abra **Pull requests → New pull request**, com base `main` e comparação
`lab/desconto-incorreto`. Título sugerido: `Laboratório: regressão intencional no desconto`.
Preencha o template e aguarde as duas automações:

- **Master of Merges**: analisa a PR, publica um parecer e reprova a alteração.
- **Qualidade e testes**: detecta a regressão. Depois, **Diagnostico da falha** analisa os
  logs e publica outra explicação com sugestão de correção.

O nome do agente aparece no título do parecer; o autor técnico é `github-actions[bot]`.
O comentário do revisor avalia alterações antes de qualquer merge; o comentário de
diagnóstico explica a execução de testes já realizada na PR.

## 5. Tornar o bloqueio obrigatório

Uma checagem vermelha não bloqueia por si só todas as opções de merge. Configure:

1. **Settings → Branches → Add classic branch protection rule**, padrão `main`.
2. Habilite **Require a pull request before merging**.
3. Habilite **Require status checks to pass before merging**.
4. Selecione os checks **Master of Merges** e **Qualidade e testes**, da aplicação GitHub Actions.
   Eles aparecem na busca depois de sua primeira execução na PR.
5. Habilite **Require branches to be up to date before merging**.
6. Habilite **Do not allow bypassing the above settings**, incluindo administradores.
7. Salve. Mantenha force push e exclusão da branch desabilitados.

Também é possível usar um ruleset equivalente, com status **Active**, alvo `main`, as duas
checagens obrigatórias e sem atores de bypass. Use uma única estratégia para facilitar a demonstração.
Não é necessário exigir uma aprovação humana numericamente se você é o único colaborador.

Volte à PR defeituosa. Confirme a mensagem de merge bloqueado e capture a tela com os checks
vermelhos. **Este é o caso solicitado: PR aberta, problema identificado e merge impedido.**
Não use opções administrativas de bypass durante o experimento.

## 6. Validar a análise e corrigir a mesma PR

Leia o parecer e o diagnóstico. Confira se o modelo aponta o operador, o teste e os valores
esperados. Não aceite uma sugestão de mudar o teste para esperar 110.00: a regra exige 90.00.
Colete as evidências da falha antes de corrigir.

```powershell
python scripts/lab.py fix
python scripts/run_checks.py --output reports/fixed
python -m devops_lab.pr_review --local --mode rules --output reports/review-fixed
git diff -- src/devops_lab/pricing.py
git add src/devops_lab/pricing.py
git commit -m "fix: subtract discount from subtotal"
git push
```

A mesma PR recebe uma nova execução e um novo comentário do Master of Merges. A regra
estática aprova a fórmula corrigida; a IA deve reavaliar o diff. Se não houver diferença
líquida em relação à base, o agente ainda verifica a regra do arquivo no commit atual.
Os comentários anteriores permanecem para evidência. Com os checks verdes e a proteção
satisfeita, o merge fica disponível. Após o merge, a entrega de `main` publica um novo `.pyz`.

## 7. Analisar os logs localmente

Sem credenciais locais, você pode validar a mecânica do diagnóstico:

```powershell
python -m devops_lab.diagnostics --log reports/broken/pytest.log --mode offline --output reports/analysis-offline
```

São gerados `analysis.md`, `analysis.json` e `prompt.txt`. O modo offline é uma regra
determinística, não uma evidência de uso de GenAI. Com as variáveis locais configuradas,
troque para `--mode llm`. Esse modo retorna código 1 se não houver análise generativa.
`--mode auto` pode gerar relatório offline ao falhar, identificando o motivo.

Para testar GenAI sem API, copie o conteúdo revisado de `prompt.txt` para uma ferramenta de
IA à qual já tenha acesso, registre ferramenta/modelo/data e salve a resposta separadamente.
Identifique essa análise como manual; ela não substitui a integração automática da PR.

O agente envia somente trechos dos logs, da regra de negócio e dos testes, ou o diff da PR.
Existe redação de formatos comuns de segredos; revise os dados antes de compartilhá-los.
Sugestões nunca são aplicadas automaticamente.

## 8. Coletar comentários, capturas e relato

Siga [EVIDENCIAS.md](EVIDENCIAS.md) e preencha [RELATO_FORUM.md](RELATO_FORUM.md).
Registre apenas resultados observados, com links das execuções reais. Os arquivos locais
em `reports/` não provam que uma execução ocorreu no GitHub.

## Problemas comuns

| Sintoma | Ação |
| --- | --- |
| `No module named devops_lab` | Use a venv e execute `python -m pip install -e .` |
| HTTP 401/403 na IA | Confira o secret, o provedor e o acesso ao modelo; não imprima a chave |
| HTTP 429 | Verifique cota/limites no provedor e tente novamente depois |
| Resposta de revisão inválida | Consulte o parecer; ajuste modelo/configuração. O gate continua bloqueado |
| Secret existe, mas API não funciona | Confira `LLM_BASE_URL` e `LLM_MODEL`; a chave não serve para todo provedor |
| Comentário recebe 403 | Use branch interna para o laboratório; confira políticas de Actions e `pull-requests: write` |
| Master não encontra seu módulo | Publique a base completa em `main` antes de abrir a PR |
| Check não aparece na proteção | Execute o workflow em uma PR primeiro e procure pelo nome do job |
| Merge continua permitido | Confira alvo `main`, regra ativa, checks obrigatórios e bypass administrativo |
| PR bloqueia após código corrigido | Leia o parecer atual, confira IA/cota e execute os jobs novamente; não desligue o gate |
