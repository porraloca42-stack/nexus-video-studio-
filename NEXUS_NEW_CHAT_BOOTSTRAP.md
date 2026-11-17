# NEXUS VIDEO STUDIO — BOOTSTRAP PARA NOVOS CHATS

Última revisão: 2026-11-17T17:03:58-03:00 (America/Sao_Paulo)
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

## Estado vigente resumido — 2026-11-17T17:01:49-03:00 (America/Sao_Paulo)
Consultar o bloco operacional completo no início de NEXUS_MASTER_STATE.md. Em resumo:
- Brain 4 isolado: smoke real Gemini aprovado pelo usuário em fixture de 4s; não valida vídeo completo.
- Remotion multifaixa: MP4 sintético de 4s validado.
- Smoke live de uma cena Cloudflare → Modal/LTX → Remotion: passou tecnicamente em 17/11 às 15:58:59 BRT; movimento quase estático e GPU não identificada (gpu_name=null).
- Produção completa de 40–50s com Fish Audio + Brain 4 + render: ainda não validada.
- PR #9 continua aberta, não mergeada e não implantada; CI #1135 passou nos jobs aplicáveis, render sintético skipped.
- PR #10 continua aberta, não mergeada e não implantada. A revisão detectou que a comparação antiga poderia confundir A10 e A100; foi substituída por padrões com limites de token e testes para A10G/A100.
- CI #1154 falhou em commit intermediário por NameError (`markers`); correção gravada no head `eb7269bfa339dc13ff0704e6b5fa91c2fb8fbba7`. CI #1155 / run 44165173593 está em andamento: Remotion typecheck success; unit-tests e Commons live smoke pendentes; render sintético skipped. Não declarar CI verde até concluir.
- PR #10 propõe validar identidade CUDA antes de carregar pesos e remover a estimativa de custo falsa do smoke. As alterações permanecem apenas na branch da PR até eventual merge.
- Modal: painel do usuário mostrou gasto acumulado de US$1.50, majoritariamente H100; código versionado declara L40S; deployment ativo permanece não identificado. Deploy e nova inferência pagos bloqueados sem autorização.
- Build indicator Streamlit integrado pela PR #6; confirmar SHA no app publicado.

## Próxima sequência autorizada sem custo
1. Aguardar CI #1155 e inspecionar logs de eventual falha.
2. Revisar o diff final da PR #10 após CI verde; manter PRs abertas até solicitação explícita de merge.
3. Atualizar Master State e handoff com timestamp preciso após cada marco.
4. Não executar deploy, Modal/GPU ou APIs pagas sem autorização específica e limite de custo.

## Fonte de verdade
- NEXUS_MASTER_STATE.md na branch main é a fonte operacional atual.
- NEXUS_HANDOFF_2026-11-17.md é o diário de continuidade; o último checkpoint é o mais relevante.
- Anexos locais/antigos, memórias e resumos não substituem o GitHub.
- Este bootstrap é apenas um roteador para as fontes atuais; não mantenha aqui uma cópia extensa de checkpoints antigos.
