# NEXUS VIDEO STUDIO — BOOTSTRAP PARA NOVOS CHATS

Última revisão: 2026-11-17T18:16:51-03:00 (America/Sao_Paulo)
Repositório: https://github.com/porraloca42-stack/nexus-video-studio-
Branch oficial: main

## REGRA CRÍTICA: NÃO RETOMAR CHECKPOINT OBSOLETO
Antes de qualquer resposta técnica, leia nesta ordem:
1. O bloco STATUS OPERACIONAL VIGENTE — SOBRESCREVE CHECKPOINTS HISTÓRICOS no início de NEXUS_MASTER_STATE.md, diretamente da branch main.
2. O checkpoint mais recente no final de NEXUS_HANDOFF_2026-11-17.md (ou handoff com data posterior, se existir).
3. O HEAD atual de main, os commits recentes e os checks/PRs relevantes no GitHub.
4. Só então leia arquivos de código relacionados à próxima ação.

**Não use os checkpoints históricos abaixo do bloco vigente como lista de tarefas.** Eles documentam decisões e acontecimentos passados, não pendências atuais. Nunca ressuscite tarefas de 16/11 ou estados antigos como “Brain 4 ainda não integrado”, “Remotion isolado”, “render sintético não validado” ou “precisa criar runner dos quatro cérebros” sem verificar o estado atual. Essas descrições aparecem em registros históricos e foram superadas por atualizações posteriores.

Se documentos divergirem, prevalecem: (1) código/refs e CI atuais no GitHub; (2) bloco operacional vigente do Master State; (3) último checkpoint do handoff; (4) registros históricos. Declare divergências em vez de inventar.

## Obrigação de retomada
Apresente um relatório com:
- horário local de São Paulo da consulta ao GitHub (ISO 8601 com UTC−03:00);
- timestamp exato do último checkpoint documental;
- HEAD de main e commit mais recente relevante;
- último trabalho concluído e evidências;
- CI/PR atuais;
- estados separados: implementado, commitado, CI testado, implantado, renderizado e validado visualmente;
- pendências e próxima ação concreta.

Não peça ao usuário para repetir informações registradas. Não declare deploy/produção/validação sem evidência.

## Regras de engenharia e custo
- Execute alterações técnicas diretamente no GitHub; o usuário não programa.
- Mudanças incrementais, revisão de diff e testes em cada etapa.
- Não fazer merge de PR sem pedido explícito do usuário.
- Não executar Gemini/Fish Audio/Cloudflare/Modal/GPU, downloads pagos, deploy ou render de produção sem autorização específica de custo.
- Um CI verde não comprova deployment, GPU efetiva, billing, movimento perceptível ou qualidade do MP4.
- Nunca expor secrets.
- Diferencie movimento real do sujeito, movimento de câmera e efeitos sintéticos. Não usar diferença de luminância start/end como prova suficiente de movimento.
- Responder em português, com clareza e sem alegar tarefas concluídas sem validação.

## Estado vigente resumido — 2026-11-17T17:56:28-03:00 (America/Sao_Paulo)
Consultar o bloco operacional completo no início de NEXUS_MASTER_STATE.md. Em resumo:
- Brain 4 isolado: smoke real Gemini aprovado pelo usuário em fixture de 4s; não valida vídeo completo.
- Remotion multifaixa: MP4 sintético de 4s validado.
- Smoke live de uma cena Cloudflare → Modal/LTX → Remotion: passou tecnicamente em 17/11 às 15:58:59 BRT; movimento quase estático e GPU não identificada (gpu_name=null).
- Produção completa de 40–50s com Fish Audio + Brain 4 + render: ainda não validada.
- PR #9 continua aberta, não mergeada e não implantada; CI #1135 passou nos jobs aplicáveis, render sintético skipped.
- PR #10 continua aberta, não mergeada e não implantada. A revisão detectou que a comparação antiga poderia confundir A10 e A100; foi substituída por padrões com limites de token e testes para A10G/A100.
- CI #1154 falhou em commit intermediário por NameError (markers); CI #1155 / run 44165173593 passou no head eb7269bfa339dc13ff0704e6b5fa91c2fb8fbba7 nos três jobs executados; render sintético skipped. Depois, PR #10 recebeu correção para aceitar A10G como tipo solicitado e testes adicionais. Novo head 402323ac23cd30286bb634c3c3966725f185c351; oito testes do validador passaram em execução local isolada. CI #1163/run 44173764665 passou no head anterior. Depois foi adicionada telemetria de cache Hugging Face ao worker e ao relatório smoke. Novo head ef102d4116da01e67c829efc0af7832b8510fd5c passou no CI #1174/run 44174426029: unit-tests, remotion-typecheck e commons-live-smoke success; remotion-synthetic-render skipped.
- PR #10 propõe validar identidade CUDA antes de carregar pesos e remover a estimativa de custo falsa do smoke. As alterações permanecem apenas na branch da PR até eventual merge.
- Modal: painel do usuário mostrou gasto acumulado de US$1.50, majoritariamente H100; código versionado declara L40S; deployment ativo permanece não identificado. Deploy e nova inferência pagos bloqueados sem autorização.
- Build indicator Streamlit integrado pela PR #6; confirmar SHA no app publicado.

## Próxima sequência autorizada sem custo
1. Aguardar e verificar CI do novo head 402323ac23cd30286bb634c3c3966725f185c351; não considerar a execução local como substituta do CI.
2. Manter PRs abertas até solicitação explícita de merge.
3. Atualizar Master State e handoff com timestamp preciso após cada marco.
4. Não executar deploy, Modal/GPU ou APIs pagas sem autorização específica e limite de custo.


## Atualização operacional — 2026-11-17T18:11:28-03:00 (America/Sao_Paulo)
- HEAD da main na retomada: `198cc21e7a2a39aff49db20fdfd9938ab7731521`.
- PR #11 revisada e branch sincronizada com a main pelo merge commit `8ad700537fae41199f1b506a5fc68b74173ed5d9`. CI #1182 / `44177472367`: unit-tests, Commons smoke e Remotion typecheck success; synthetic render skipped.
- PR #11 continua aberta e não mergeada. Branch sincronizada no head `a2b5d2c3a668cf36db0ee891854d3bb457ad8534`; CI #1190 / `44177875187` passou nos três jobs executados, synthetic render skipped. Compare após sync: 5 commits à frente, 0 atrás; GitHub reportou mergeable=true. Não executar deploy ou inferência GPU sem autorização específica; o smoke é manual e separado.
- PR #10 permanece aberta e não mergeada, head `ef102d4116da01e67c829efc0af7832b8510fd5c`, CI #1174 aprovado nos jobs executados.
- Última ação concluída: revisão estática, sincronização final e CI #1190 aprovado na PR #11. A PR permanece aberta; aguardar autorização explícita para merge. Próxima ação: aguardar autorização explícita para merge da PR #11; depois, tratar deploy e inferência como decisões separadas.
- Nenhuma operação paga ou implantação foi iniciada nesta retomada.

## Fonte de verdade
- NEXUS_MASTER_STATE.md na branch main é a fonte operacional atual.
- NEXUS_HANDOFF_2026-11-17.md é o diário de continuidade; o último checkpoint é o mais relevante.
- Anexos locais/antigos, memórias e resumos não substituem o GitHub.
- Este bootstrap é apenas um roteador para as fontes atuais; não mantenha aqui uma cópia extensa de checkpoints antigos.
