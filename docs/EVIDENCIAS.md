# Evidências do laboratório

Guarde as evidências em uma pasta pessoal fora do repositório. Inclua URL da PR, SHA do
commit, data e link da execução em cada registro. Artefatos de Actions têm retenção de 30 dias
neste projeto; faça o download antes de expirarem.

## Checklist de capturas

- [ ] `01-base-verde.png`: execução inicial de `main` com testes e entrega aprovados.
- [ ] `02-diff-falha.png`: aba Files changed com `amount - discount` trocado por `amount + discount`.
- [ ] `03-master-bloqueado.png`: parecer Master of Merges com modo, commit e defeito identificado.
- [ ] `04-testes-falhando.png`: log com `test_discount_is_subtracted`, esperado 90.00 e obtido 110.00.
- [ ] `05-diagnostico-ia.png`: diagnóstico generativo dos logs com causa e correção sugerida.
- [ ] `06-protecao-main.png`: checks obrigatórios e ausência de bypass, sem valores de secrets.
- [ ] `07-merge-impedido.png`: PR aberta mostrando o merge bloqueado pelos checks.
- [ ] `08-correcao.png`: diff do commit de correção e justificativa da revisão humana.
- [ ] `09-checks-verdes.png`: nova revisão e testes aprovados na mesma PR.
- [ ] `10-entrega.png`: artefato `.pyz` entregue em `main` e execução retornando 90.00.

No Windows, `Win+Shift+S` permite capturar a área relevante. Inclua o contexto da PR/execução;
evite capturar páginas de criação de chave, terminais com credenciais ou dados pessoais.
Capturas comprovam o estado observado e complementam os links e arquivos exportados.

## Salvar os comentários do agente

Na aba **Conversation** da PR, use os três pontos do comentário → **Copy link**. Salve os
links dos pareceres de bloqueio e aprovação e do diagnóstico. Copie também o texto para
um arquivo de evidências. Os pareceres são comentários da conversa, e não reviews inline.

Com GitHub CLI instalado e autenticado, uma exportação opcional em PowerShell:

```powershell
$prNumber = 1 # substitua pelo número real da PR
gh api --paginate --slurp "repos/RenatoOAAguiar/akcit-projeto-devops/issues/$prNumber/comments" | Out-File -Encoding utf8 pr-comments.json
gh api --paginate --slurp "repos/RenatoOAAguiar/akcit-projeto-devops/pulls/$prNumber/reviews" | Out-File -Encoding utf8 pr-reviews.json
gh api --paginate --slurp "repos/RenatoOAAguiar/akcit-projeto-devops/pulls/$prNumber/comments" | Out-File -Encoding utf8 pr-inline-comments.json
```

`--slurp` preserva as páginas como um array de arrays JSON. O primeiro arquivo contém os
comentários deste agente; os outros registram reviews de pessoas ou de outras ferramentas,
se existirem. O login do GitHub CLI não usa a chave do provedor de IA.

## Baixar logs e artefatos

Em **Actions → execução → Summary → Artifacts**, baixe:

| Artefato | Conteúdo |
| --- | --- |
| `testes-<run>-<tentativa>` | `pytest.log`, `junit.xml`, `coverage.xml`, `run.json` |
| `master-of-merges-<run>-<tentativa>` | `review.md`, `review.json` com modo, decisão e commit |
| `diagnostico-<run>-<tentativa>` | `analysis.md`, `analysis.json` e `prompt.txt` sanitizado |
| `aplicacao-<sha>` | `devops-lab.pyz`, entregue somente após CI verde em `main` |

No menu da execução, **Download log archive** salva os logs dos jobs. O parecer de revisão
é preservado mesmo se o gate reprovar; o diagnóstico é preservado mesmo se a IA obrigatória
ficar indisponível. Falhas anteriores à criação de evidências podem não gerar todos os arquivos.

## Registro de rastreabilidade

| Etapa | Commit | URL da execução | Resultado/mode | Arquivos/capturas |
| --- | --- | --- | --- | --- |
| Base | preencher | preencher | preencher | preencher |
| PR defeituosa | preencher | preencher | preencher | preencher |
| Parecer do Master | preencher | preencher | generative / rules / unavailable | preencher |
| Diagnóstico dos logs | preencher | preencher | generative / offline | preencher |
| Correção | preencher | preencher | preencher | preencher |
| Entrega | preencher | preencher | preencher | preencher |

Não apresente `rules` ou `offline` como IA generativa. Se o provedor estiver indisponível,
registre o impedimento e, se usada, a análise manual em outra ferramenta com a devida atribuição.
