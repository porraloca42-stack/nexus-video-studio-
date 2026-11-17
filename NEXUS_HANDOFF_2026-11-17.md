# NEXUS VIDEO STUDIO — HANDOFF DE CONTINUIDADE
Data: 17/11/2026 (America/Sao_Paulo)
Branch: main
Repositório: https://github.com/porraloca42-stack/nexus-video-studio-

## Instrução prioritária para o próximo chat
Antes de qualquer ação técnica:
1. Leia este arquivo integralmente.
2. Leia o `NEXUS_MASTER_STATE.md` atual diretamente da branch `main`.
3. Confira o HEAD atual do repositório e o status do CI para os commits listados abaixo.
4. Leia os arquivos relevantes no GitHub antes de modificá-los.
5. Continue exatamente do ponto registrado aqui. Não peça ao usuário para repetir contexto.

O arquivo de estado anexado pelo usuário em chats anteriores pode estar desatualizado. O arquivo canônico é o que está no GitHub.

## Objetivo e princípios
Construir um estúdio audiovisual com IA capaz de compreender roteiros, pesquisar bibliotecas, avaliar cenas e produzir MP4 profissional. Prioridade máxima: inteligência audiovisual, coerência semântica, movimento físico observável, continuidade, qualidade editorial e estabilidade.
O usuário não programa; execute alterações diretamente no GitHub. Faça mudanças incrementais, testes e registro. Nunca declare concluído sem validação.
Separar sempre: implementado, gravado no GitHub, CI testado, implantado, inferido em GPU e validado visualmente com MP4.

## Restrições de custo e autorização
- Meta desejada pelo usuário: até US$0.50 por vídeo completo.
- Não iniciar novas inferências GPU pagas, benchmark Modal, API paga ou qualquer custo variável sem autorização explícita do usuário.
- O usuário autorizou continuar trabalho que não tenha custo: análise, arquitetura, código, testes automatizados sem chamadas externas pagas, pesquisa e documentação.
- Nenhuma nova geração GPU foi iniciada nesta etapa. Custo adicional nesta etapa: US$0.
- Não confundir licença open-weight ou ComfyUI gratuito com custo zero de computação.

## Estado da arquitetura existente
- Aplicação Streamlit em `app.py`.
- Diretor/storyboard Gemini em `nexus/director.py`.
- Narração Fish Audio S2.1 Pro Free, via `nexus/audio.py`; Fish é obrigatório no fluxo padrão.
- Keyframes: Cloudflare Workers AI FLUX.2 Klein.
- Animação: worker Modal com LTX-Video 0.9.8 2B distilled, em `nexus/modal_i2v.py`, configuração em `nexus/ltx_config.py`.
- Composição: Remotion em `remotion/`, orquestração `nexus/remote_render_job.py`.
- Auditoria multimodal final em `nexus/visual_review.py`; três quadros por cena (início/meio/fim) enviados em uma chamada já existente ao Gemini.
- Diagnóstico técnico de congelamento por FFmpeg em `nexus/video_quality.py`; não é avaliação semântica.
- LTX 0.9.8 permanece como pipeline/fallback atual. LTX-2.5/ComfyUI ainda não implementados nem validados.

## Trabalho já implementado antes desta sessão
1. Prompts LTX exigem `video_motion_prompt` em inglês, com uma ação física principal observável e progressão cronológica; não repetir a imagem estática.
2. O Remotion não aplica zoom/pan/shake sintético sobre clipes LTX gerados; transforms ficam para fallback de imagem estática.
3. FLUX.2 Klein suporta até quatro imagens de referência para identidade do personagem e valida assinatura MIME.
4. Diretor define continuidade visual e protagonista quando aplicável.
5. Worker LTX usa 0.9.8 distilled multi-scale, schedule 7+3 em L40S, com guard de orçamento GPU.
6. Diagnóstico FFmpeg de congelamento por clipe, exibido no relatório Streamlit; limiar de alerta inicial 40%; sem retry automático.
7. Smoke test Modal mede tempo de chamada, carregamento, inferência e estimativa GPU e extrai quadros inicial/meio/fim.
8. Auditoria multimétrica final: semantic_score, matches_narration, motion_progression_score, action_observed, continuity_score, temporal_progression, issues e critical_issues. Índice editorial na UI: 40% semântica, 35% movimento, 25% continuidade. Revisão ausente falha conservadoramente.
9. SYSTEM do diretor foi atualizado para UMA ação física principal por cena curta, com progressão início → execução → resultado; um microevento ambiental secundário pode existir.
10. Pesquisas registradas em `NEXUS_MASTER_STATE.md` sobre LTX-2.5 22B distilled, 8 steps, requisitos VRAM, ComfyUI, licença e custos Modal. LTX-2.5 não é atualização de versão trivial e requer protótipo separado.

## Trabalho executado na sessão atual — 17/11/2026
O usuário disse: “Blz, se não tem custo manda ver, prossiga”.
Foi feita leitura do `NEXUS_MASTER_STATE.md` e de `nexus/director.py` diretamente do GitHub.
O anexo `NEXUS_MASTER_STATE.md` disponível no chat estava truncado/antigo; o arquivo atual da branch main é a referência.

### Alteração implementada
Arquivo `nexus/director.py`:
- Criada função `build_storyboard_preflight(plan)`.
- A função calcula:
  - `scene_count`
  - `unique_action_ratio`
  - `unique_search_ratio`
  - `unique_shot_types`
  - `unique_settings`
  - `warnings`
  - `method = deterministic_text_checks_no_external_calls`
- Detecta repetição literal de `visual_action` e `asset_search_query`.
- Sinaliza baixa variedade de tipos de plano quando há pelo menos 6 cenas e no máximo 2 tipos distintos.
- Sinaliza ambientes repetidos quando, com pelo menos 6 cenas, menos de 50% dos ambientes forem distintos.
- O relatório é anexado ao plano como `preflight_report` no fim de `create_storyboard`.
- É uma heurística barata sobre texto/metadados, não uma avaliação visual/semântica real. Não reprova storyboard, não modifica cenas, não chama Gemini, não usa GPU.

Commits:
- `4d815134598c86833d37ededab3c7bda7899ce58` — implementação.
- `94b79809671e5f30225f1bbe44c9e2c9578f5b6e` — testes.
- `b6f5ae730210489d8c786440236c17a9b782d521` — atualização do `NEXUS_MASTER_STATE.md` com o registro.

Testes adicionados em `tests/test_director_scene_count_repair.py`:
- repetição de ação/busca principal é sinalizada;
- storyboard com ações/buscas distintas retorna índice 1.0.
Os testes ainda NÃO foram executados/confirmados por CI.

### Estado de validação no momento da troca
- Código gravado em `main`: sim.
- Testes adicionados: sim.
- CI: pendente; chamada a status do commit retornou lista vazia de statuses, portanto não declarar CI aprovado.
- Streamlit deploy: não verificado.
- Modal deploy: não verificado.
- Geração de vídeo real: não executada.
- Validação audiovisual humana: não executada.
- Custo adicional de GPU/API: US$0.

## Próximas ações obrigatórias para o novo chat
1. Ler novamente `NEXUS_MASTER_STATE.md`, este handoff e o HEAD atual da branch main.
2. Descobrir como acompanhar workflow runs/CI no GitHub usando ferramentas disponíveis. A integração já mostrou `fetch_commit_workflow_runs`, mas sua descrição diz que filtra runs disparados por pull request; não confiar nela para runs de push. `get_commit_combined_status` retornou statuses vazios para commit `b6f5ae7...`. Investigar forma correta sem inventar resultado.
3. Se o CI falhar, ler logs do job, corrigir causa específica e repetir testes. Se não for possível rodar CI, ser transparente.
4. Continuar a evolução da inteligência audiovisual do diretor sem chamadas adicionais ao Gemini desnecessárias:
   - interpretar roteiro completo e mapear tese, afirmações, beats emocionais e promessa;
   - criar visual treatment bible por vídeo (estilo, paleta, protagonista, cenário, luz, gramática de câmera);
   - associar cada trecho de narração a uma ação filmável ou metáfora visual reconhecível;
   - variar planos, distância, ambientes e composição sem quebrar continuidade;
   - validar cobertura, repetição e viabilidade antes de gerar keyframes/clipes;
   - escolher/avaliar keyframes e candidatos;
   - usar auditoria final já existente para orientar correções seletivas com limite rígido de custo.
5. Inspecionar a UI para decidir como exibir o `preflight_report` de forma útil e não poluída. Atualmente o relatório está anexado ao objeto de plano, mas ainda não foi verificado se é exposto na interface.
6. Preparar integração ComfyUI + LTX-2.5 como worker/protótipo isolado, sem substituir o LTX 0.9.8. Primeiro mapear API/workflow oficial, dependências, pesos e arquitetura; criar testes de contrato/mock sem GPU. Não iniciar inferência ou deployment pago sem aprovação.
7. Preservar o objetivo de qualidade profissional e custo de até US$0.50/vídeo, mas não afirmar que o orçamento está alcançado sem benchmark completo e reconciliação da cobrança.

## Orientação de comunicação ao usuário
Responder em português brasileiro, com clareza e sem exagerar. O usuário quer que o assistente seja o engenheiro responsável, não quer instruções para programar. Reportar sempre o que foi feito e o que continua pendente. Não dizer “concluído” quando só está implementado.

## Retomada posterior — exposição da pré-validação do storyboard (17/11/2026, 09:56 BRT)
- Foram lidos integralmente, diretamente de `main`, este handoff e o `NEXUS_MASTER_STATE.md` (1784 linhas na versão consultada).
- HEAD antes das alterações: `50a0a70c51de9c40648218772f672a362f1cecc9`.
- A pré-validação já existia em `nexus/director.py`, mas não aparecia na interface. Foi inspecionado o fluxo do expander de planejamento em `app.py`.
- Implementado: seção compacta **Pré-validação audiovisual** no expander existente, com variedade textual de ações/buscas, tipos de plano, ambientes e avisos. A UI explicita que a análise é heurística, não inspeciona quadros e não substitui a revisão visual.
- Teste de contrato adicionado em `tests/test_app_import_resilience.py`.
- Commits: `355d493ba1047e34a9df9d0a8fb8f7aec852f4fa` e `9b4326ced1eb14f34fb055512aec8aab4f82a839`.
- Releitura pós-commit confirmou os dois arquivos atualizados na branch `main`. O commit mais recente observado após os patches era `9b4326c`; a atualização documental subsequente do master state gerou commit `17373a6d3b7bba80e22c17c7755884edcd25761c1`.
- CI: ainda não confirmado. `get_commit_combined_status` retornou lista vazia para `9b4326c`; o wrapper `fetch_commit_workflow_runs` disponível filtra execuções de pull request e também retornou vazio. O workflow de regressão contém gatilho push para `main`, mas não foi possível obter a execução de push nem os logs com as ferramentas disponíveis.
- Sem deploy Streamlit ou validação visual mobile nesta etapa. Nenhuma chamada Gemini/Cloudflare/Fish, inferência Modal/GPU ou renderização paga foi iniciada; custo variável adicional US$0.
- Próximo passo exato: localizar o run de push correspondente a `9b4326c` e confirmar os três jobs (`unit-tests`, `remotion-typecheck`, `commons-live-smoke`). Se CI verde, continuar a inteligência audiovisual apenas com mudanças locais/testes gratuitos. Não iniciar GPU ou APIs pagas sem nova autorização explícita.



## Retomada posterior — pré-validação contra ações/buscas quase repetidas (17/11/2026)
- HEAD observado antes desta alteração: `926bae8f5c0baad5077be45f232ad37ccc2fda0d`. O estado canônico foi relido diretamente de `main`; o anexo do chat estava desatualizado.
- Problema identificado: a pré-validação existente detectava apenas repetição literal, permitindo que ações/buscas com pequenas diferenças de palavras passassem sem aviso.
- Alteração em `nexus/director.py`: adicionada comparação lexical por sobreposição de conjuntos de termos informativos, com limiar conservador (4 termos compartilhados e 80% de sobreposição sobre o menor conjunto). Repetições exatamente iguais não geram aviso duplicado.
- Relatório ampliado com cobertura de ações e prompts de movimento, pares de ações semelhantes e pares de buscas semelhantes. A heurística não entende sinônimos nem semântica e não reprova o storyboard automaticamente.
- Alteração em `app.py`: interface apresenta cobertura e contagem de pares potencialmente semelhantes, mantendo a explicação de limitações.
- Testes atualizados/adicionados em `tests/test_director_scene_count_repair.py` e `tests/test_app_import_resilience.py`.
- Commits: `87380c4`, `f096421`, `6c2f931`, `7b50d6d`, `464ca0f`.
- Código gravado em `main`: sim. Releitura pós-commit e CI ainda pendentes no momento deste registro. Não foi possível executar testes localmente porque o clone do repositório falhou por indisponibilidade de DNS; a integração GitHub disponível não lista execuções de Actions disparadas por push. Status CI: desconhecido, não aprovado.
- Sem deploy Streamlit/Modal, sem teste visual mobile, sem chamadas pagas, sem GPU e sem MP4. Custo variável adicional: US$0.

### Próximas ações
1. Confirmar HEAD e reler os arquivos alterados na branch `main`.
2. Verificar CI por qualquer endpoint/ação GitHub disponível que inclua eventos push. Se continuar inacessível, registrar como desconhecido.
3. Corrigir qualquer falha de CI somente após obter logs concretos; não supor falhas.
4. Próxima prioridade de engenharia: melhorar cobertura narrativa e especificidade filmável das cenas com verificações locais/testes determinísticos, sem alegar compreensão semântica real por heurística lexical.
5. Manter LTX 0.9.8 como pipeline atual; protótipo LTX-2.5/ComfyUI permanece isolado e sem inferência paga.
6. Nenhuma chamada Gemini/Cloudflare/Fish/Modal, geração GPU ou benchmark pago sem autorização explícita adicional.


### Complemento — verificação de ação física explícita (17/11/2026)
- A pré-validação também identifica prompts `video_motion_prompt` sem nenhum verbo de movimento físico reconhecido por uma lista lexical controlada. Retorna `motion_action_coverage_ratio` e `motion_scenes_without_recognized_action`, além de aviso com os números das cenas.
- A interface mostra a proporção de prompts com verbo físico reconhecido. Isso é apenas uma triagem lexical: não prova que o sujeito se move, que a ação é coerente com a fala, nem que o vídeo gerado executa o movimento. Um verbo pode se referir à câmera ou ao ambiente; sinônimos não listados podem ser falsos negativos.
- A normalização foi ajustada para preservar letras acentuadas do português. Teste adicionado para pares semelhantes com termos como “portão metálico” e para prompt sem verbo físico reconhecido.
- Commits adicionais: `6769d06` (normalização Unicode), `f8af365` (teste de português acentuado), `8161dd2` (detecção lexical de ação física), `875ea44` (teste do prompt estático), `3bf05cd` (métrica na UI), `6b8accc` (contrato UI).
- Código e testes foram gravados na branch main. Ainda não há execução de testes/CI confirmada, deploy ou validação visual. Nenhuma API paga, GPU ou renderização foi chamada; custo variável adicional: US$0.


Próximo passo exato: confirmar HEAD, reler todos os arquivos alterados e consultar novamente o CI. A integração atual não lista runs de push; se não houver evidência nova, CI permanece desconhecido. Não executar chamadas pagas, deploy Modal ou render de produção sem autorização adicional.


## Continuação — base ComfyUI para protótipo LTX-2.5 sem GPU (17/11/2026)
- Pesquisa oficial registrada em `NEXUS_LTX25_COMFYUI_PLAN.md`. O workflow oficial I2V two-stage usa LTX-2.5 22B BF16, upscale espacial 2×, refine 3 passos, imagem inicial opcional e gera áudio/vídeo. Frames devem ser 1+8n; defaults consultados são 24 fps e 960×544 paisagem. O NEXUS precisará adaptar para vertical.
- LTX-2.5 requer pelo menos 32 GB VRAM; A100 80 GB/H100 são recomendadas. A L40S 48 GB atual está acima do mínimo, mas não há prova de que o workflow caiba com margem ou atenda o orçamento. Não executar inferência sem autorização explícita.
- Criado `nexus/comfyui_client.py`, cliente HTTP isolado e mockável, com upload, submit, history polling, timeout sem retry automático, extração de vídeo e download.
- Criado `tests/test_comfyui_client.py` com testes sem rede/GPU.
- Commit base do cliente: `92a9001`; testes: `2a126e5`; plano: `70f47fc`; adendo de estado do plano: `c236599`.
- Cliente genérico implementado; LTX-2.5 NÃO está integrado. Workflow API exportado, patcher de nós, worker Modal, custom node pins, deploy e teste de inferência ainda não existem.
- CI permanece desconhecido: status combinado sem registros e wrapper de runs filtra apenas PR; clone local falhou por DNS. Não declarar testes aprovados.
- Custo: sem downloads de pesos, sem ComfyUI iniciado, sem Modal/GPU, sem API paga e sem MP4. Custo variável adicional: US$0.

### Próximos passos sem custo
1. Verificar HEAD e reler módulo/testes/documentação.
2. Confirmar CI quando houver endpoint disponível; caso contrário, manter como desconhecido.
3. Obter/exportar o workflow oficial para formato API e fixar IDs/nós usados; criar patcher de parâmetros e testes de contrato, sem executar ComfyUI.
4. Criar worker Modal isolado somente após testes de contrato e revisão de dependências/pesos. Não fazer deploy ou download de modelos sem autorização explícita.
5. Preservar LTX 0.9.8 como fallback e não alterar o pipeline padrão.


### Complemento — patch seguro de workflow API (17/11/2026)
- `nexus/comfyui_client.py` agora inclui `patch_api_workflow(workflow, bindings)`: cria cópia profunda do grafo e altera somente inputs explicitamente mapeados. Rejeita nós/inputs inexistentes, bindings incompletos e inputs que já estejam conectados por links, evitando quebrar silenciosamente a topologia.
- Testes adicionais verificam isolamento do grafo original, alteração de widgets, rejeição de links e referências desconhecidas.
- Commits: `273c047` (patcher), `9cb0830` (testes).
- O arquivo `.github/workflows/tests.yml` foi inspecionado: a job de regressão compila `nexus` e executa `python -m unittest discover -s tests -v`, portanto o novo arquivo de teste entra na descoberta padrão. Isso confirma a configuração do workflow, não o resultado de uma execução.


Nota de CI: o workflow de regressão usa Python 3.11, compila `nexus` e executa descoberta unittest em `tests/`; a inclusão dos novos testes está coberta pela configuração, mas a execução real ainda não foi consultada/confirmada.


## Decisão arquitetural definitiva — sem projeto paralelo (17/11/2026)
A decisão anterior de “worker/protótipo isolado” foi refinada após alinhamento com o usuário. LTX-2.5/ComfyUI é o destino definitivo dentro do NEXUS oficial. Não criar outro repositório, produto duplicado ou etapa futura de portabilidade. Um runtime/worker separado pode existir por isolamento técnico, mas seu código, workflow, testes, deploy e telemetria ficam no mesmo repositório e sob o mesmo contrato do NEXUS. LTX-0.9.8 é somente fallback temporário até validação do novo motor.

### Contrato comum de motor implementado
- Novo `nexus/video_engine.py`: Protocol `VideoEngine`, adaptador `LTX098VideoEngine` e resolução explícita de motores. O motor padrão continua sendo LTX 0.9.8; selecionar LTX-2.5 antes da integração do workflow API gera erro explícito. Nenhum fallback silencioso.
- `nexus/remote_render_job.py` passa a delegar a animação através do contrato comum, mantendo um wrapper de compatibilidade para o ponto de chamada existente.
- Novo `tests/test_video_engine.py`: quatro testes determinísticos do contrato e da resolução.
- Commits: `8cea3cc` (contrato), `3ef2c0d` (testes), `a2ca6c4` (orquestrador usa contrato).
- Próximo passo: exportar/versionar o workflow ComfyUI em formato API, validar o grafo e implementar o adaptador LTX-2.5 dentro do mesmo repositório/contrato. O workflow visual não é API prompt; não inventar IDs de nós nem bindings.
- Validação: commits gravados; releitura pós-commit e execução dos testes/CI ainda pendentes. Deploy, GPU, download de pesos, benchmark e MP4 não executados. Custo variável adicional: US$0.


### Fonte LTX-2.5 fixada no repositório oficial — 17/11/2026
- Fixada a revisão upstream `db476dacc1469b2f17ccc5735693916afcb6fac1` do workflow oficial two-stage distilled em `workflows/ltx25/source_manifest.json`. O manifesto registra a URL de origem/licença, ID do workflow, 20 nós de topo, 34 links, seis subgrafos, defaults de 24 fps/121 frames/960×544 e a restrição `1 + 8n`.
- A inspeção do JSON upstream confirmou que o arquivo é um workflow visual com seis subgrafos, não um API prompt pronto. Por segurança, o manifesto marca `api_prompt_exported=false`; o patcher não será executado contra o grafo visual nem serão inventados IDs/inputs.
- A adaptação NEXUS registrada mantém 9:16, clipes de 2–5s, Fish Audio como voz oficial, descarte do áudio LTX e composição Remotion.
- Testes em `tests/test_ltx25_workflow_manifest.py` protegem a revisão fixada, a distinção visual/API e os requisitos de adaptação.
- Commits: `dbbaf1b` (manifesto) e `71d5a61` (testes). A execução CI do commit ainda precisa ser consultada; nenhum modelo foi baixado e nenhuma GPU/ComfyUI foi iniciada.
