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


### Correção da suíte e validação CI — 17/11/2026
- O primeiro CI do contrato comum encontrou um teste desatualizado em `tests/test_visual_review_normalization.py`: o fixture da auditoria multimodal usava apenas um quadro e omitia `motion_progression_score`, `action_observed` e `continuity_score`, embora a auditoria agora avalie três quadros temporais e esses campos façam parte do contrato. O código de produção normalizou corretamente campos ausentes como zero; o teste ainda esperava valores antigos.
- Corrigido o fixture para fornecer início/meio/fim e todos os campos de resposta esperados, incluindo a progressão temporal. A correção alterou apenas o teste, não a lógica de auditoria.
- Um primeiro commit de fixture ainda falhou por apontar para o bloco de texto temporal em vez da primeira parte `inlineData`; a asserção foi corrigida para localizar a parte de imagem pelo campo, sem depender da posição no array.
- Commit final do ajuste de teste: `6731ed3` (precedido por `1016215`).
- CI GitHub Actions #878, run `44091549701`, commit `6731ed34867b08b1c63f62354167c200f854811b`: **148 testes Python passaram**; `remotion-typecheck` passou; `commons-live-smoke` passou. Execução concluída com sucesso.
- A validação acima cobre o HEAD `6731ed3`. Commits documentais posteriores podem disparar nova execução e devem ser verificados separadamente.
- Investigação do export API: a implementação oficial do ComfyUI frontend `graphToPrompt` (revisão `196dd85cde3314dffdc33b41caa3e5d9be432ffb`) expande subgrafos via `ExecutableNodeDTO.getInnerNodes()`, resolve conexões/widget values e emite `class_type` + `inputs`. Isso confirma que o grafo visual com seis subgrafos não pode ser convertido por simples renomeação de campos; a exportação/API deve preservar a resolução de conexões e nós internos.


## Retomada — exportador API e regressão de arrays (17/11/2026)
- HEAD de entrada: e5eadb605609cacd5c0d8544f267029e0e073204. CI #885 confirmou 153 testes Python, Remotion typecheck e Commons smoke com sucesso.
- A implementação oficial graphToPrompt foi lida na revisão ComfyUI frontend 196dd85cde3314dffdc33b41caa3e5d9be432ffb. A exportação expande subgrafos por ExecutableNodeDTO.getInnerNodes(), resolve links e widget values, ignora nós bypass/never/virtual e serializa widgets de array em objeto com __value__.
- O patcher do cliente NEXUS foi ajustado para preservar esse contrato em bindings que atualizem widgets de array. Teste determinístico incluído. Commits: e5b3246e71660ccc9800fb3e5c65c9db610fc838 e 2d0a8068c72430cc4dd6cded0f5d49a981968ccd.
- CI #887, run 44092812673, no commit 2d0a806: 154 testes Python passaram, Remotion typecheck passou e Commons live smoke passou.
- O workflow visual fixado contém seis subgrafos. Input Parameters inclui GemmaAPITextEncode e um caminho externo acionado por chave LTX; não configurar chave nem assumir custo zero. O caminho local também depende dos modelos Gemma encoder/enhancer.
- Próximo bloqueio: obter um API prompt realmente exportado por uma instância ComfyUI compatível com as versões pinadas, ou executar fielmente o exportador oficial com o runtime gráfico e extensões corretas. Não gerar um grafo API manual a partir do JSON visual nem inventar node IDs/classes. Sem inferência/GPU/download/deploy/API paga; custo adicional US$0.



## Correção da referência de frontend ComfyUI — 17/11/2026
- O workflow visual original registra frontendVersion 1.48.7. A primeira investigação consultou uma revisão posterior (1.61.2), útil apenas como comparação, e não como referência de compatibilidade do workflow.
- Referência correta confirmada: tag oficial ComfyUI_frontend v1.48.7, commit 6d6af63c00f132cd25dc29307fc56bd2c094fa22. A função graphToPrompt e a classe ExecutableNodeDTO foram relidas nessa revisão. O manifesto workflows/ltx25/source_manifest.json foi corrigido para essa versão.
- O teste do manifesto agora verifica tag e versão. CI #895 (run 44094091786) e #896 (run 44094125992) passaram com 154 testes Python, Remotion typecheck e Commons live smoke. O run #894 falhou transitoriamente porque o manifesto foi atualizado antes do teste; a execução seguinte após atualizar o teste passou.
- O código do cliente NEXUS continua compatível com o encapsulamento de widgets array como __value__. O API prompt real ainda não foi exportado; a integração segue bloqueada até exportação oficial/runtime e validação dos bindings. Sem GPU, download de pesos, deploy, API paga ou render. Custo variável adicional US$0.


## Retomada — revisão da arquitetura faceless e custo por cena (17/11/2026)
- O usuário contestou a decisão de investir no LTX-2.5 sem comparar alternativas comerciais de baixo custo. Foi realizada pesquisa em documentação oficial de Revid, Crayo, Pictory, InVideo, Fliki, VEED, Cloudflare e Modal. Relatório: `NEXUS_FACELESS_VIDEO_ARCHITECTURE_RESEARCH_2026-11-17.md`.
- Padrão público confirmado: roteamento por cena entre stock, imagens IA animadas, motion graphics, mídia própria/gameplay e AI video; os produtos expõem densidade visual e controles de animação; Revid recomenda guardar vídeo premium para 1–2 cenas hero.
- Auditoria de código confirma que NEXUS já gera imagens FLUX.2 Klein, mas encaminha todas as cenas para um único lote LTX-0.9.8. Worker atual usa L40S e limite GPU estimado de US$0.42; não usa T4 nem está configurado para animar apenas o hook.
- Remotion atual aplica transformações 2D e alguns efeitos CSS; não implementa mapa de profundidade/parallax 2.5D, overlays de vídeo alpha, sound effects por beat nem legendas word-level no componente inspecionado. `depthLayers` é atualmente metadado.
- 512×910 de origem é escalado para 720×1280; não deve ser anunciado como 4K. Estimativa de 14 imagens: ~US$0.00804 com dois tiles de saída por imagem, sujeita a confirmar o tile metering/Neurons real. Cloudflare oferece 10k Neurons/dia gratuitos compartilhados com o uso da conta.
- Modal T4 a US$0.000164/s significa que US$0.005 cobre cerca de 30.5s de GPU faturável antes de CPU/memória; ainda não há benchmark NEXUS em T4. Timeout 60s limita a invocação/lote e pode incluir startup; não garante custo fixo. Spend limit US$30 não significa cobrança zero; a documentação separa Workspace budget e Spend limit. Recomendação de proteção a avaliar: Workspace budget rígido + Spend limit US$0.
- A alegação de US$0.02 por vídeo completo não foi comprovada para concorrentes; custos internos não são públicos.
- **Estado de decisão:** não remover LTX-0.9.8; pausar nova implementação/adoção de LTX-2.5 até validar rota híbrida por cena. Próxima etapa sem custo: mocks, roteador de mídia, camadas Remotion e contabilidade de custo. Nenhum gasto variável executado.
- HEAD quando este handoff foi atualizado: consultar branch main; documentação de pesquisa adicionada sem alterações ao pipeline de produção.


## Continuação — pipeline editorial em quatro cérebros aprovado (17/11/2026)
- O usuário aprovou adicionar ao NEXUS a cadeia editorial de quatro cérebros: (1) estrategista de retenção com três hooks, seleção, arco e loop; (2) roteirista de micro-ritmo com unidades-alvo de 2,5–3,5s como heurística; (3) diretor de fotografia que traduz fala em metáforas visuais e trava uma bíblia visual por vídeo; (4) editor que alinha áudio final e sincroniza cortes, movimentos, SFX, legendas e música.
- A proposta foi registrada no relatório NEXUS_FACELESS_VIDEO_ARCHITECTURE_RESEARCH_2026-11-17.md (commit 92204b323c7ab8764cbe448a1ade731c1960db82) e no NEXUS_MASTER_STATE.md (commit 53393f09d9ffba18b7e3dedd2fcdd819311b2bc1).
- Ressalva factual: trata-se de arquitetura-alvo aprovada para o NEXUS, não de engenharia interna comprovada dos apps pagos. Whisper oferece timestamps por palavra em modo experimental; isso não basta para localizar sílaba tônica. Avaliar forced alignment/nível fonético e prosódia antes de prometer sincronismo silábico.
- Implementação em código: não. Teste com áudio real, teste de retenção/A-B, deploy e MP4: não. Nenhuma API paga, GPU, download de pesos ou render de produção foi executado; custo variável adicional US$0.
- Próxima etapa gratuita: especificar schemas JSON e testes determinísticos por estágio, depois integrar um cérebro de cada vez. Preservar motor atual e roteamento híbrido; não reativar gasto de GPU sem autorização explícita.



## Implementação inicial dos contratos dos quatro cérebros — 17/11/2026
- Criado `nexus/editorial_pipeline.py`, módulo stdlib-only e sem efeitos externos, com contratos versionados e validadores independentes para: estrategista de retenção, roteirista de micro-ritmo, diretor de fotografia e editor de sincronização.
- Brain 1 valida três ângulos distintos de hook (curiosidade, perda/oportunidade e quebra de padrão), seleção, justificativa, promessa, payoff e arco.
- Brain 2 valida blocos de fala, duração-alvo (0,5–8s aceita para não transformar a heurística 2,5–3,5s em bloqueio rígido), função narrativa, intenção vocal, ênfases, pausas e reconstrução fiel de full_narration.
- Brain 3 valida bíblia visual e direção por beat, incluindo metáfora, ação observável, continuidade e rota de mídia híbrida.
- Brain 4 valida duração do áudio, alinhamento por palavra/fonema, timestamps ordenados, âncoras de edição, eventos de legenda e mixagem. Uma âncora fonêmica é rejeitada se o artefato declarar apenas alinhamento por palavra; isso evita prometer precisão que a ferramenta não forneceu.
- Validação cruzada: cada micro-bloco deve ter direção visual; âncoras devem apontar para blocos existentes; o hook selecionado deve aparecer na fala de abertura.
- Criado `tests/test_editorial_pipeline.py` com fixtures determinísticas e cobertura dos quatro contratos e das referências cruzadas.
- Commits: `76c0b57` (contratos), `f19748f` (testes iniciais), `fe586c0` (validação cruzada), `b2631cf` (testes cruzados).
- CI #908, run `44098118981`, no commit `f19748f`: 170 testes Python passaram; Remotion typecheck e Commons smoke passaram. A suíte desse run antecede os três testes de validação cruzada adicionados nos commits seguintes.
- CI #910, run `44098265445`, commit `b2631cf`: unit-tests e Remotion typecheck concluídos com sucesso; Commons live smoke ainda estava em andamento na última consulta. Resultado final do run ainda pendente.
- Estado: contratos e testes implementados no GitHub; ainda não integrados ao fluxo de geração Gemini nem ao Remotion; sem teste com áudio real, sem retenção A/B, sem deploy ou MP4 validado.
- Nenhuma API Gemini/Fish/Cloudflare, inferência Modal/GPU, download de modelo ou render de produção foi executado por esta etapa. Custo variável adicional US$0.
- Próxima etapa: pesquisar e especificar os artefatos reais de cada cérebro e integrar primeiro Brain 1 em modo shadow/dry-run, mantendo o storyboard atual como fonte de produção até comparar e aprovar resultados. Não introduzir chamadas adicionais de API nem custo variável sem autorização específica.



## Pesquisa técnica complementar — Revid, Crayo e alinhamento de fala (17/11/2026)
- Revid publica API v3 workflow-driven: o cliente seleciona um fluxo (script-to-video, prompt-to-video, static-background, article/audio/music-to-video, entre outros), fornece source e configura media/voice/captions/music/options/render. A documentação afirma que uma requisição de render coordena visuais, voz, legendas e música; há endpoint de estimativa de créditos e cada render soma 10 créditos de base às gerações. Isso demonstra uma interface de orquestração unificada, não prova que o backend execute um único modelo ou quatro LLMs especializados.
- A página pública de faceless do Revid enumera seis classes visuais: imagens IA animadas (padrão), AI video, stock video, motion graphics, mídia do usuário e gameplay. Também descreve estilo global aplicado às cenas e voz/legendas/música/SFX. Tratar como funcionalidades e comportamento declarados pelo fornecedor, não engenharia interna verificada.
- Crayo documenta timeline multipista com vídeo, captions, texto, áudio e efeitos; cutaways com ducking automático; zooms com easing, transições, LUTs, speed ramps e keyframes de câmera. Também descreve legendas editáveis com timing word-level e destaque de palavras-chave. Isso reforça o contrato de timeline do NEXUS; não comprova o algoritmo interno de sincronização.
- OpenAI Whisper expõe word_timestamps por cross-attention + dynamic time warping e a CLI marca a opção como experimental. O resultado é alinhamento estimado por palavra, não alinhamento fonético nem identificação da sílaba tônica.
- WhisperX aplica forced alignment com modelos wav2vec2 para refinar os tempos de palavra e pode retornar alinhamentos em nível de caractere. A documentação lista limitações: palavras fora do vocabulário do alinhador podem ficar sem tempo, fala sobreposta é problemática e é necessário modelo de alinhamento apropriado ao idioma. Alinhamento de caracteres não equivale a sílaba tônica; prosódia/ênfase é uma etapa distinta.
- Consequência para o NEXUS: manter o contrato atual capaz de representar alinhamento word ou phoneme, mas não instalar nem baixar modelos agora. Antes de escolher implementação, comparar suporte real a pt-BR, cobertura de números/nomes, licença, dependências, RAM/CPU/GPU, velocidade e custo. Validar timestamps contra áudio final Fish Audio e amostras anotadas manualmente. Cortes devem usar âncoras editoriais com confiança, não disparar mecanicamente em cada palavra.
- Fontes públicas:
  - Revid API docs: https://www.revid.ai/docs
  - Revid faceless workflow: https://www.revid.ai/tools/faceless-video
  - Crayo editor: https://crayo.ai/features/video-editor
  - OpenAI Whisper word timestamps: https://github.com/openai/whisper/blob/main/whisper/transcribe.py
  - WhisperX forced alignment and limitations: https://github.com/m-bain/whisperX
- Nenhum endpoint Revid/Crayo foi chamado; nenhuma conta criada; nenhum modelo baixado; nenhuma chamada paga, GPU ou render foi executado.



## Pesquisa complementar aprofundada — estrutura faceless e alinhamento pt-BR (17/11/2026)
- A página pública do Revid Faceless descreve dois modos que não devem ser confundidos: Script-to-video lê o texto fornecido palavra por palavra; Prompt-to-video recebe um tema/ideia e escreve o roteiro. No fluxo script-first, o fornecedor declara que divide o texto em passagens curtas e dá a cada passagem um visual próprio.
- A mesma página descreve uma estrutura editorial em quatro partes: Hook (10–20% do roteiro), Setup (15–20%), Payoff (50–60%) e Close (10–15%), com fechamento que pode apontar de volta para a abertura. Isso é uma recomendação pública de produto do Revid, não prova de quatro LLMs ou de uma cadeia interna de quatro agentes.
- Revid também declara seleção de seis classes de mídia por vídeo (imagens IA animadas, AI video, stock, motion graphics, mídia própria e gameplay), estilo visual global, brand kit reutilizável, estimativa de créditos antes da geração e edição posterior para trocar/regenerar uma cena sem recomeçar o vídeo. Essas capacidades reforçam as prioridades de roteamento, pré-orçamento, continuidade de marca e regeneração seletiva no NEXUS.
- Revid API docs atuais consultadas: v3.14.0. O endpoint de render recebe workflow e source; retorna PID e o processamento ocorre em background com webhook/polling. A API descreve uma chamada de render por vídeo coordenando visuais, voice-over, captions e música, além de endpoints separados para timeline/edit jobs, cálculo de créditos, arquivos e publicação. Isso é contrato público de API, não descrição do número de serviços/modelos privados.
- WhisperX README atual: forced alignment com wav2vec2 produz word-level timing; o README explica que o alinhamento forçado gera segmentação phone-level internamente e admite saída de caracteres (return_char_alignments). O suporte de alinhador é específico por idioma.
- WhisperX alignment.py inclui português (pt) com jonatasgrosman/wav2vec2-large-xlsr-53-portuguese como modelo HF padrão. Esse checkpoint é português geral (Common Voice), Apache-2.0, entrada 16 kHz e cerca de 1.26 GB segundo os arquivos públicos. Não presumir que seja otimizado para sotaque pt-BR.
- Candidato alternativo pt-BR: ProgramadorArtificial/wav2vec2-large-xlsr-53-portuguese, Apache-2.0, declara treino com Common Voice 13, FalaBrasil, MLS Portuguese, TTS-Portuguese-Corpus, VoxForge e dados brasileiros adicionais; a página reporta WER 11.7% no teste e 9.5% na validação. Esses números são auto-relatados e medem reconhecimento, não precisão de forced alignment nem performance sobre a voz Fish Audio. É candidato para comparação, não escolha validada.
- Decisão de engenharia: manter o contrato com níveis word/character/phoneme distintos. WhisperX pode fornecer word/character alignment; não declarar saída fonêmica apenas porque o modelo usa fonemas internamente. Para a sílaba tônica, ainda precisamos de detecção de acento lexical/prosódico e validação acústica; nem word timestamps nem character timestamps resolvem isso automaticamente.
- Auditoria adicional do Remotion atual (remotion/src/NexusVideo.tsx): há uma trilha de narração e uma de música com volume fixo 0.12. Não há ainda trilha de captions, SFX, ducking dinâmico nem consumo dos caption_events/audio_mix_events do contrato editorial. A timeline visual de cenas já usa Sequence, mas os eventos de áudio/texto não existem no componente atual. Próximo trabalho de composição deve ser multifaixa com eventos explícitos, não efeitos indiscriminados.
- Fontes públicas:
  - Revid faceless workflow e estrutura editorial: https://www.revid.ai/tools/faceless-video
  - Revid API v3.14.0: https://www.revid.ai/docs
  - WhisperX README/alinhamento e limitações: https://github.com/m-bain/whisperX
  - WhisperX alinhadores por idioma: https://github.com/m-bain/whisperX/blob/main/whisperx/alignment.py
  - Modelo pt geral: https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-portuguese
  - Modelo pt-BR candidato: https://huggingface.co/ProgramadorArtificial/wav2vec2-large-xlsr-53-portuguese
- Sem downloads de modelos, instalação de WhisperX, chamadas externas de API, GPU, deploy ou render real nesta pesquisa.



## Expansão dos contratos, prompts e runner dos quatro cérebros — 17/11/2026
- nexus/editorial_pipeline.py agora diferencia alinhamento word, character e phoneme. Para níveis finos, exige arrays de timestamps correspondentes; âncoras não podem declarar precisão superior à evidência disponível. Âncoras word precisam corresponder a palavra e intervalo do alinhador. A descoberta do WhisperX motivou essa distinção: saída de palavra/caractere não deve ser chamada de saída fonêmica.
- O módulo também oferece micro_script_advisories (2,5–3,5s como orientação não bloqueante) e run_four_brain_pipeline com quatro executores injetados. O runner aplica validação após cada cérebro, encerra a cadeia no primeiro artefato inválido e exige o asset/duração reais da narração antes do cérebro 4. Não descobre credenciais nem chama serviços.
- Criado nexus/editorial_prompts.py com builders independentes para os quatro prompts: estratégia de retenção; micro-roteiro; direção visual/metáforas e roteamento; timeline/alinhamento e edição. Os builders são puros e não fazem chamadas Gemini.
- Testes atualizados para alinhamento word/character/phoneme, âncoras e runner. CI #928, run 44099325976, commit c204031df1e55fe12c0e4a2c9d85d230eaebcef4: **184 testes Python passaram**; Remotion typecheck passou; Commons live smoke passou. Execução concluída com sucesso.
- Commits adicionais: 9abaec0 (granularidade de alinhamento), da301c3/d8caace (prompts com granularidade), 9801d4c/c204031 (testes de caracteres e prompts).
- Estado: contratos, prompts, runner e testes estão no GitHub e validados em CI. Ainda não conectados ao create_storyboard, aos executores Gemini/Fish nem ao Remotion; não há vídeo real nem comparação de retenção.
- Auditoria Remotion: ainda só há narração e música fixa em volume 0.12; sem captions, SFX ou ducking dinâmico. Próxima etapa de composição: adicionar eventos tipados para captions/SFX/mix e fazer Remotion consumi-los com fixtures sintéticas e testes de render local.
- Nenhuma chamada Gemini/Fish/Cloudflare, download de modelo, inferência Modal/GPU, deploy ou render de produção executado. Custo variável adicional US$0.
- Limite de autorização: a permissão de pesquisa cobre investigação pública aprofundada; não autoriza compras, assinaturas, API paga, inferência, download de pesos ou deploy com custo sem aprovação de orçamento específica.



## Primeira integração audiovisual multifaixa no Remotion — 17/11/2026
- Remotion agora aceita tipos opcionais para CaptionEvent/CaptionWord, SoundEffectEvent e AudioMixEvent, mantendo compatibilidade com manifestos antigos sem esses campos.
- NexusVideo.tsx renderiza legendas sincronizadas em Sequence, com destaque da palavra ativa/ênfase e posições top/center/bottom; reproduz SFX em seus intervalos; aplica volumes de música por evento de mixagem, usando o menor volume quando eventos se sobrepõem e mantendo o padrão 0.12 fora dos eventos.
- nexus/remotion_renderer.py transporta caption_events, sfx_events e audio_mix_events do edit_timeline para camelCase do manifesto, copia arquivos de música/SFX para a pasta do job e rejeita intervalos/arquivos inválidos. O manifesto também inclui musicVolume.
- nexus/editorial_pipeline.py valida estrutura e limites de tempo para captions, palavras, SFX e mixagem; a prompt do Brain 4 agora pede explicitamente esses eventos.
- Testes de regressão cobrem o mapeamento de manifestos, cópia de assets, intervalos de palavras, SFX fora da duração e volumes de mixagem.
- CI #943, run 44100007415, commit 83083a7359419c97059c854760d1852cce26d793: **190 testes Python passaram**; Remotion typecheck passou; Commons live smoke passou. Execução concluída com sucesso.
- A primeira execução #941 falhou por duas causas de teste/fixture: JSON literal não escapado em uma f-string de prompt e expectativa de nome de arquivo SFX anterior à normalização. Ambos foram corrigidos; #943 passou.
- Estado: suporte de dados e renderização de captions/SFX/ducking implementado e validado por testes Python + typecheck. Ainda NÃO foi feito render real do Remotion com assets temporizados; portanto sincronismo visual/sonoro e qualidade final continuam não validados em MP4.
- Não foram gerados áudio/visuais, nem chamados Gemini/Fish/Cloudflare, nem iniciada GPU, download de modelo, deploy ou render de produção. Custo variável adicional US$0.
- Próximo passo: preparar um manifesto sintético com áudio e SFX de teste localizados, executar render local de validação e inspecionar sincronismo quadro a quadro. Isso não exige serviços pagos, mas só deve ser executado em ambiente local/CI com dependências Remotion disponíveis; não declarar a camada audiovisual validada até inspecionar o MP4.



## Suavização do ducking de música — 17/11/2026
- Eventos de mixagem agora aceitam fade_in_seconds e fade_out_seconds (padrão 0.12s), limitados a 2s e sem exceder a duração do evento.
- Remotion interpola o volume da música entre o nível base e o volume reduzido, aplicando envelopes de entrada/saída para evitar mudanças bruscas nos limites dos eventos. Eventos simultâneos continuam usando o menor volume calculado.
- Manifesto Python transmite os fades em camelCase; prompt do Brain 4 inclui os campos; testes verificam valores e rejeição de fades maiores que o evento.
- CI #953, run 44100380076, commit 2a27062459e877d849197f1e5944e5f28fb7bea1: 191 testes Python passaram e Remotion typecheck passou; Commons live smoke estava em andamento na última consulta.
- Ainda sem render real do Remotion; sincronismo audiovisual em MP4 permanece não validado. Sem APIs pagas, downloads de modelos, GPU, deploy ou render de produção; custo variável adicional US$0.

## Validação sintética multifaixa — 17/11/2026
- Criado `scripts/validate_remotion_render.py`: gera WAVs determinísticos de narração, música e SFX; constrói um manifesto com duas palavras temporizadas, um evento SFX e ducking com fades; renderiza MP4 vertical de 4s no Remotion.
- A inspeção automatizada extrai frames em dois momentos de destaque de palavra e um momento sem legenda; verifica presença visual do destaque. Também usa FFmpeg para medir bandas de frequência e confirmar redução/restauração da música e presença do SFX no intervalo programado.
- O workflow `.github/workflows/tests.yml` ganhou o job `remotion-synthetic-render`, com Node 22, dependências Remotion, Chrome Headless Shell e FFmpeg; preserva o MP4 como artifact por 7 dias. O job é CPU-only e não usa APIs externas, GPU ou mídia paga.
- Commits: `43c289de3e5e266138635cc123fae23eaa4c0110` (script) e `52b055939d737c5904ce46649afdd06c06af0ebe` (workflow).
- Estado após o push: implementação gravada na branch main; execução do novo job e MP4 ainda aguardam resultado verificável. O status combinado consultado não retornou checks; portanto não afirmar que o render foi executado ou passou.
- A máquina desta sessão não tem checkout local do repositório nem dependências Remotion instaladas; a tentativa de acesso direto ao GitHub pela rede local falhou por indisponibilidade de DNS. A validação foi encaminhada ao GitHub Actions, sem contornar isso com downloads ou serviços pagos.
- Nenhuma API Gemini/Fish/Cloudflare, inferência Modal/GPU, modelo, deploy ou render de produção foi acionado. Custo variável externo adicional: US$0. O artifact sintético, quando o job concluir, valida apenas o comportamento técnico básico dos eventos, não qualidade de conteúdo nem sincronismo em produção.
- Próxima etapa: consultar o resultado real do job e inspecionar o MP4/artifact. Se passar, registrar a validação sintética; depois preparar um teste controlado com narração Fish Audio real apenas com autorização explícita para eventual custo.

### Controle de execução do render sintético
- O job `remotion-synthetic-render` foi restringido: roda somente por acionamento manual (`workflow_dispatch`) ou quando um push contém `[run-remotion-validation]` na mensagem do commit. Assim, não será executado automaticamente em todos os pushes/PRs.
- Commit de habilitação pontual: `108410748fc872314ebf32f2a95bbf2a77476b8b`. O push foi marcado com o token de execução para solicitar esta validação aprovada.
- A consulta ao endpoint de status do commit ainda não retornou checks; a execução efetiva do job permanece sem confirmação nesta sessão.
- O job usa runner hospedado do GitHub Actions; o consumo de minutos pode estar sujeito à franquia/plano da conta. Não há chamadas a APIs pagas, GPU, download de pesos ou deploy.

## Continuidade entre chats e correção do teste sintético — 17/11/2026
- Criado `NEXUS_NEW_CHAT_BOOTSTRAP.md` com instruções obrigatórias para o próximo chat: ler master state e handoff na branch main, conferir commits/CI, preservar arquitetura aprovada e retomar a próxima ação pendente.
- O bootstrap explica que o anexo antigo de `NEXUS_MASTER_STATE.md` pode estar desatualizado e que a versão GitHub main é a fonte oficial.
- Revisão do script `scripts/validate_remotion_render.py` encontrou um defeito: o diretório temporário de fixtures era removido antes da extração dos frames de inspeção. Corrigido no commit `1425f46c283a00c438dc7716f18336cd0e900277`: os frames agora usam diretório de inspeção separado e persistente durante o job.
- Commit do bootstrap: `cc58c3a5174b13c5a1e4a48a13ea2dd3b71cac34`.
- Próximo passo: disparar novamente o job sintético com commit marker após a correção, e obter resultado/artifact. A integração GitHub disponível não oferece listagem de runs disparados por push nem dispatch explícito; status combinado até aqui retornou vazio. Não inferir sucesso.
- O job permanece restrito a `workflow_dispatch` ou push com `[run-remotion-validation]`; runner hospedado pode consumir minutos da franquia GitHub. Sem APIs pagas, GPU, modelos ou deploy.
- Continuidade: manter este arquivo, `NEXUS_HANDOFF_2026-11-17.md` e `NEXUS_NEW_CHAT_BOOTSTRAP.md` sincronizados a cada marco relevante. Esses registros reduzem perda de contexto, mas o próximo chat ainda deve verificar o estado vivo do GitHub.

### Reexecução após correção do fixture — 17/11/2026
- Push marker criado após a correção do diretório de frames: `b5d374eaadc148260a78b8fc2d849d8af9b7c7e6` (`[run-remotion-validation]`).
- O job `remotion-synthetic-render` deve ser disparado por esse push, pois o workflow filtra a mensagem do commit.
- A integração GitHub consultada retornou status combinado vazio e não expõe runs de push (a ação `fetch_commit_workflow_runs` retorna apenas execuções de pull request). Resultado do job, logs e artifact continuam sem confirmação.
- Próxima ação: abrir GitHub Actions no repositório e localizar a execução do commit acima; conferir o job `remotion-synthetic-render` e artifact `nexus-remotion-synthetic-validation`. Não declarar sucesso até obter evidência.


## Checkpoint adicional — correção de import e disparo da validação — 17/11/2026
- O log do run #969 (44106516739), job `remotion-synthetic-render`, mostrou `ModuleNotFoundError: No module named 'nexus'` ao importar `nexus.remotion_renderer` no script sintético.
- A raiz do repositório foi adicionada a `sys.path` antes do import em `scripts/validate_remotion_render.py`, commit `178ffe1bcb26a5a9ebbbbf69c08979ebfb555df7`.
- Run #973 (44113431413): unit-tests, Remotion typecheck e Commons live smoke passaram; render sintético foi skipped porque o commit de correção não continha o marcador requerido.
- Commit de documentação/disparo: `cc86d8b9ad78c2c0d3c9b2d081e481d741fd87c8`, com `[run-remotion-validation]`. Aguardar e inspecionar o job e artifact antes de afirmar sucesso.
- Nenhum serviço pago, GPU, deploy ou render de produção foi acionado. Runner hospedado pode consumir minutos da franquia.


## Continuação — diagnóstico do MP4 sintético — 17/11/2026
- Run #974: MP4 sintético foi gerado e anexado como artifact #14342431166, mas o job falhou no critério de ducking (antes -34.6dB; durante -38.7dB). Unit tests, typecheck e Commons smoke passaram.
- MP4 inspecionado: H.264 720x1280, 30fps, 4s, AAC 48kHz. Frame de palavra destacada conferido visualmente; as verificações de legenda passaram. Teste SFX não foi alcançado.
- Suspeita técnica: bandas de teste próximas (narração 440Hz, música 220Hz) e filtros de 190–250Hz podem contaminar a medição de música atenuada com vazamento da narração. Não alterar o algoritmo de ducking sem evidência.
- Fixture ajustado no commit `549bb44e51e2375cf0f08b826749565bfc104c96`: narração 1100Hz, música 220Hz, SFX 3000Hz; banda SFX 2800–3200Hz. Commit contém o marcador para nova execução sintética.
- Próximo passo: conferir run desse commit, logs, métricas, artifact; se passar, registrar os limites da validação sintética. Ainda não há validação do áudio multifaixa.


## Marco validado — render sintético multifaixa — 17/11/2026
- Run #977 / `44114553978`, commit `549bb44e51e2375cf0f08b826749565bfc104c96`: quatro jobs passaram (unit-tests, typecheck, Commons smoke, Remotion synthetic render).
- Métricas do script: música -36.1dB antes, -50.6dB durante ducking, -36.1dB após; SFX -45.7dB antes e -30.0dB ativo; pixels dourados de destaque: 2249 e 1773; caption_off=0.
- Artifact #14342476549 baixado e inspecionado. MP4 H.264 720x1280, 30fps, AAC estéreo 48kHz, 4.011s; frame com destaque de palavra conferido visualmente.
- Conclusão: validação sintética multifaixa passou. Não extrapolar para voz real, sincronismo fonético, vídeos de 40–50s, integração Streamlit ou render de produção. O adapter Remotion segue isolado.
- Nenhuma API paga, GPU, modelo, deploy ou render de produção foi acionado.
- Próxima etapa de engenharia: planejar integração controlada do adapter Remotion ao fluxo do app, com teste de regressão e fallback preservado; não ativar APIs pagas sem orçamento/autorização.


## Correção arquitetural e próximo passo — 17/11/2026
- Correção: Remotion já está no caminho padrão indireto: `app.py` → `render_on_github()` → workflow `nexus-render-worker.yml` → `nexus.remote_render_job.main()` → `render_video_remotion()`. Não descrever o adapter como desconectado; produção externa ainda não foi validada.
- Lacuna real: app.py não chama o runner/prompts dos quatro cérebros; director.py não monta `edit_timeline`. Sem esse campo, `build_remotion_manifest()` recebe timeline vazia, então o teste sintético de captions/SFX/ducking ainda não prova que esses eventos chegam aos vídeos reais.
- Próxima tarefa: desenhar e testar offline a ponte entre o plano atual e os contratos dos quatro cérebros, mantendo fallback atual e sem chamadas pagas. Só habilitar executores externos após autorização específica.


## Checkpoint — alinhamento Fish Audio preservado — 17/11/2026
- Implementado em `nexus/audio.py`: retorno opcional de segmentos de alinhamento Fish, latest snapshot por `chunk_seq`, offsets globais via `chunk_audio_offset_sec`; retorno legado permanece compatível.
- Worker remoto inclui os segmentos no relatório criptografado, sem chamada adicional de API. Granularidade registrada como `provider_segments`, sem fingir confiança, palavra ou fonema.
- CI #991 / `44115678230`: 193 testes passaram, typecheck passou e Commons smoke passou. Commits da etapa: `ee917342`, `b5eb9d81`, `0b7d840d`, `a672b4bc`, `a6711e61`.
- Brain 4 ainda não consome esses segmentos. Próximo: ajustar o contrato para aceitar evidência sem confidence e classificar apenas segmentos realmente unitários como word-level; depois preparar o executor com mocks. Não adicionar chamada Gemini real sem autorização específica.


## Checkpoint — ponte de alinhamento para Brain 4 — 17/11/2026
- Worker preserva segmentos Fish e só os converte para `word_timestamps` quando cada item é uma palavra individual; frases e pontuação isolada não são promovidas. Sem confidence inventada.
- Contrato e prompt Brain 4 ajustados: confidence opcional, um token por word timestamp, instrução explícita para não inventar precisão/confiança.
- CI #1002 / `44116215338`: 198 testes Python passaram, typecheck e Commons smoke passaram; render sintético skipped (sem alteração de renderer).
- Próximo: executor Brain 4 testável com mocks, conectado ao worker após áudio Fish. A chamada real Gemini deve ficar desabilitada até autorização de custo; produção ainda não gera `edit_timeline`.


## Checkpoint — runner entrega alinhamento ao Brain 4 — 17/11/2026
- `run_four_brain_pipeline()` recebe timestamps de palavra opcionais, aplica a normalização estrita e os passa ao executor do Brain 4. Teste confirma a propagação sem rede.
- CI #1007: unit-tests e typecheck passaram; Commons smoke ainda estava em execução na última consulta; synthetic render skipped.
- Próximo: preparar executor Brain 4 com mocks e integração desativada por padrão. A chamada Gemini adicional por render só deve ser habilitada com autorização de custo.


## Checkpoint — ponte opt-in Brain 4 no worker — 17/11/2026
- `nexus/editorial_executors.py`: novo `run_brain4_for_storyboard()` adapta cenas existentes, usa callable explicitamente injetado, valida `edit_timeline` e confere asset/duração do áudio.
- `nexus/remote_render_job.py`: `main(editorial_model_call=None)` e `apply_optional_brain4()`; sem injeção, status disabled e plano original preservado. Com injeção, exige timestamps word-level reais; sem eles falha antes de chamar o modelo. App padrão não injeta callable; Gemini não é chamado.
- CI #1017 / `44118108425`: 202 testes Python, typecheck e Commons smoke passaram; synthetic multitrack skipped.
- Workflow Remotion demo #119 / `44118084308`: typecheck e adapter tests passaram; render demo manual de 50s skipped; teste sintético de integração de 4s estava em andamento.
- Ponte mockada e validada; não implantada como executor Gemini nem habilitada no fluxo de produção. Próximo: concluir validação do MP4 sintético; depois desenhar o fornecimento seguro do callable Gemini com feature flag e orçamento explícito, mantendo desabilitado por padrão.


## Validação adicional — adapter Python → Remotion — 17/11/2026
- Workflow #119 / `44118084308` passou. O adapter Python construiu o manifesto e Remotion gerou MP4 sintético 4.011s; FFprobe confirmou H.264 720×1280 + AAC. Artifact #14344496316.
- Demo manual 50s foi skipped; teste de integração usa still/áudio sintéticos, sem serviços externos. Não equivale a render real nem prova timeline Brain 4.


## Checkpoint — proteção de timestamps Brain 4 — 17/11/2026
- Brain 4 não pode alterar timestamps Fish, declarar phoneme/character sem evidência ou inserir palavras de legenda com tempos diferentes dos originais.
- CI #1022: 203 testes passaram, typecheck e Commons smoke passaram; synthetic multitrack skipped.
- Workflow #119 também passou: adapter Python → Remotion produziu MP4 sintético 4.011s H.264/AAC 720×1280, artifact #14344496316.
- Próxima etapa técnica: teste de integração offline que alimenta uma timeline Brain 4 válida no `build_remotion_manifest()`, incluindo captions, SFX e ducking, para provar a passagem dos dados ao manifest sem Gemini/serviços pagos.


## Etapa seguinte — teste Brain 4 → Remotion — 17/11/2026
- Novo teste offline conecta timeline Brain 4 simulada ao `build_remotion_manifest()` e verifica captions/word timing, SFX, ducking e fades no manifest.
- CI #1030 e workflow Remotion demo #120 estavam em execução na última consulta. Não marcar a integração como validada até ambos terminarem.


## Resultado CI — Brain 4 → manifest — 17/11/2026
- CI #1030: 205 testes Python passaram, typecheck e Commons smoke passaram. Teste de transporte de captions/word timing, SFX, ducking e fades do Brain 4 para o manifest Remotion aprovado.
- Workflow demo #120 ainda executava MP4 sintético via Remotion; verificar o resultado antes de considerar o trajeto render validado.


## Novo teste do hook de worker — 17/11/2026
- Teste cobre caminho opt-in de `apply_optional_brain4()` com executor mockado e confirma que o worker continua default-off no relatório.
- CI #1037 / `44119171372` estava em execução; aguardar resultado.
- Workflow Remotion #120 passou: MP4 sintético 4.011s H.264/AAC 720×1280, artifact #14344765828. É teste sintético, não produção.


## CI #1037 e render Brain 4 sintético — 17/11/2026
- CI #1037: 206 testes Python, typecheck e Commons smoke passaram. Hook worker testado com executor mockado; fluxo padrão continua disabled.
- `scripts/validate_remotion_render.py` agora usa `run_brain4_for_storyboard()` e timeline simulada validada antes de gerar manifest e MP4 sintético; nenhum modelo/API externo.
- Commit `e1f8737447fe14fb7114617dc9681200bf5742f0`. Próximo: executar com marcador `[run-remotion-validation]` e verificar MP4, captions, SFX e ducking.


## Resultado — render sintético ponta a ponta Brain 4 → Remotion — 17/11/2026
- CI #1045 passou integralmente: 206 testes Python, typecheck, Commons smoke e render sintético.
- Timeline Brain 4 determinística/mockada passou pelo adapter real, manifest e Remotion. MP4 H.264/AAC, 4.011s.
- Medidas: palavras destacadas 2249/1773 pixels dourados; caption off 0; música -36.1 dB antes, -50.6 dB ducked, -36.1 dB depois (14.5 dB de redução); SFX -45.7 dB antes, -30.0 dB ativo (15.7 dB acima). Artifact #14343349831.
- Workflow demo #121 passou (adapter Python → Remotion + FFprobe). Demo 50s manual skipped.
- Validação ainda é sintética e mockada; Gemini real/produção não habilitados. Próximo: revisão visual do artifact e preparar plano de integração Gemini com orçamento aprovado.


## Revisão visual do artifact Brain 4 sintético — 17/11/2026
- Artifact #14343349831 foi baixado e frames em 0.8s, 1.5s e 2.7s foram vistos: highlight dourado alterna corretamente entre NEXUS/valida e some após a legenda. Fundo gráfico de teste estável.
- FFprobe: H.264 720×1280, AAC, 4.011s. Ducking 14.5 dB; SFX +15.7 dB; recuperação da música confirmada.
- Só valida fixture sintético; não comprova cenas reais nem sincronismo com fala Fish.


## Brain 4 Gemini opt-in — implementação aguardando CI — 17/11/2026
- Novo helper Gemini usa system prompt dedicado e limite de uma geração/um modelo por vídeo. Sem retry ou failover de geração para controlar custo.
- UI Streamlit tem checkbox explícito, desmarcado por padrão, somente no modo de render compatível. Flag é enviada dentro das credenciais criptografadas; worker só cria executor se true. Sem chave, interrompe antes de gerar imagens.
- Testes adicionados em director JSON recovery, worker e GitHub renderer. CI #1061 / run `44120993502` em andamento. Sem chamada real Gemini/produção até aprovação.


## Resultado CI — integração Gemini opt-in Brain 4 — 17/11/2026
- CI #1061 / run `44120993502` passou: 209 testes Python, compileall, Remotion typecheck e Commons live smoke; synthetic render skipped por ausência de marcador.
- Testes cobrem o helper Gemini (um único POST, JSON timeline), transporte criptografado da flag, default-off e proteção quando a chave falta.
- UI checkbox desmarcado por padrão; worker só ativa Brain 4 quando a opção criptografada está true. Ainda não houve chamada Gemini real nem render de produção.
- Próximo: rodar regressão sintética Remotion após mudanças e fazer uma validação controlada com usuário selecionando Brain 4, sem iniciar job real até confirmar orçamento/uso da chave.


## Regressão sintética pós Brain 4 — 17/11/2026
- CI #1067 passou: 209 testes, compileall, typecheck, Commons smoke e Remotion synthetic MP4. Artifact #14345002405; 4.011s H.264/AAC, word highlight, captions, ducking e SFX aprovados.
- UI mostra status Brain 4 no detalhe do vídeo. Commit `72f4721f77d02ad22f5203c8f54c5a243e062797`; conferir CI subsequente.
- Ainda sem chamada Gemini real ou render de produção.


## Status Brain 4 na UI — CI aprovado — 17/11/2026
- Commit `72f4721f77d02ad22f5203c8f54c5a243e062797`, CI #1068 aprovado: 209 testes, compileall, typecheck e Commons smoke.
- Tela de resultado apresenta status Brain 4 conforme report criptografado do worker. Render sintético skipped (alteração de UI).
- Integração Gemini continua opt-in e sem teste real de API/produção.



## Continuidade — smoke test isolado Brain 4 Gemini — 17/11/2026
- Releitura obrigatória feita no início desta etapa: master state e este handoff diretamente da branch main, além do bootstrap, commits recentes e Actions.
- Runs mais recentes antes da implementação: #1069–#1074, todos concluídos com sucesso. Integração Gemini opt-in já estava em CI, mas nunca tinha sido exercitada com chamada Gemini real.
- Criado `nexus/brain4_smoke_test.py`: fixture de 4s, duas cenas, oito timestamps word-level sintéticos e adaptação para `run_brain4_for_storyboard()`. Sem chamadas ao importar; a função faz somente uma geração quando invocada. A resposta passa pelo mesmo validador e pelas mesmas proteções de precisão/timestamps usadas pelo worker.
- Criado `tests/test_brain4_smoke_test.py` com testes offline para callable único, saída contratualmente válida, rejeição de timestamps alterados e ausência de chave.
- Em `app.py`, adicionado botão **“Testar Brain 4 — sem produzir vídeo”** junto ao checkbox de opt-in. O botão é separado de “Produzir vídeo completo”; não despacha worker, não chama Fish/Cloudflare/Modal, não gera imagens e não renderiza MP4. Requer clique explícito e GEMINI_API_KEY. A geração fica limitada a um modelo e uma tentativa, sem retry/failover.
- Commits: `12315a240f80a0d431425c32bc7d512684d4887c`, `eb3c2d30b892625e703b72eb2200a4a233b3918e`, `49da8bebd94b38d79075acd824f271ca4a0ae4a2`.
- CI #1075 (helper), #1076 (testes) e #1077 (UI) foi encontrado no Actions; na hora do registro, #1075 e #1076 estavam em execução e #1077 aguardava fila. Confirmar os três resultados e ler logs se algum falhar.
- Nenhuma chamada Gemini real, produção, deploy, GPU ou serviço de mídia foi acionado. Deploy Streamlit não verificado.
- Próxima ação: confirmar CI. Depois, o usuário pode acionar o botão no Streamlit para uma geração controlada com fixture sintético; não presumir que o app já recebeu deploy. Analisar o resultado e só então planejar primeiro render completo com orçamento explícito.
- Limite: sucesso nesse smoke test valida o contrato do Brain 4 com entrada sintética, não qualidade de áudio real, edição perceptual, qualidade visual ou equivalência competitiva.



## Direção competitiva e CI do smoke test — 17/11/2026
- Benchmark Revid AI atualizado por pesquisa de fontes oficiais: script/link → vídeo, roteamento de mídia por cena, AI image/video/stock/motion graphics, vozes, captions, música, timeline editor, export até 4K, publicação, automação e API/MCP/CLI; fornecedor declara biblioteca de ~2,77M vídeos/posts com dados públicos de engajamento e 100+ ferramentas. Fontes: https://www.revid.ai/ai-instructions ; https://www.revid.ai/faq ; https://www.revid.ai/docs/workflows/script-to-video ; https://www.revid.ai/pricing. Tratar como claims do fornecedor, não avaliação independente.
- Objetivo NEXUS: resultado profissional em cada etapa. Diferenciar qualidade editorial, semântica por cena, movimento físico observável, continuidade, áudio, edição e export. Não perseguir feature checklist antes de validar qualidade real.
- Gap de produto relevante a médio prazo: editor/timeline visual para correção por cena, histórico, prévia e export multi-formato; não afirmar paridade/superioridade até comparação com renders equivalentes.
- CI do smoke isolado: run #1081 / `44122780273`, commit `223f97a071befdfb18a0be5cf3393f9c59749753` passou: 212 testes Python, Remotion typecheck e Commons live smoke; synthetic render skipped. A falha em #1076/#1077 era apenas expectativa textual incorreta no teste de rejeição; correção aprovada em #1081.
- Botão isolado está commitado e testado em CI, mas ainda depende do deploy Streamlit e do clique explícito do usuário para chamar Gemini. Nenhuma chamada real foi feita. Próximo: verificar deploy/instância; solicitar que o usuário acione o botão se estiver disponível; revisar JSON/contagens e erros. Depois planejar primeiro vídeo real com limite de custo aprovado.


## Retomada verificada — CI documental concluído; deploy ainda pendente — 17/11/2026
- HEAD da branch `main`: `a9b3d4fd72eba3b81451034859a0791a30256656`.
- CI #1082 / `44123082031` (commit `d18e3f4`), #1083 / `44123091378` (commit `8b2608b`) e #1084 / `44123106001` (commit `a9b3d4f`) foram conferidos: todos concluídos com sucesso. Em cada um, unit-tests, Remotion typecheck e Commons live smoke passaram; synthetic render skipped.
- CI #1076 e #1077 tiveram uma falha de teste por texto esperado incorreto na asserção da mensagem de rejeição de timestamp. Logs inspecionados; correção registrada no commit `223f97a`, CI #1081 / `44122780273` aprovado (212 testes Python, typecheck e Commons smoke).
- `app.py` foi relido nas linhas 580–630: botão isolado está no modo Cloudflare + Modal I2V + Remotion, exige clique e `GEMINI_API_KEY`, faz uma geração no fixture sintético e não dispara serviços de mídia ou render.
- Deploy Streamlit segue sem confirmação; não foi possível identificar URL pública inequívoca a partir do repositório. Não presumir sincronização com a main.
- Próxima ação: usuário fornecer/confirmar a URL da aplicação Streamlit; verificar a instância e localizar o botão. Aguardar clique explícito do usuário para a chamada Gemini real. Sem produção, GPU ou custos de serviços externos nesta etapa.


## Continuidade — CIs documentais verdes; acesso ao Streamlit inconclusivo — 17/11/2026
- URL já registrada no master state: https://htykbebk3hceoen5bvopax.streamlit.app/ . Não pedir ao usuário para repeti-la.
- CI #1085 (`44129937870`), #1086 (`44129946819`) e #1087 (`44129956495`) dos commits de atualização documental concluíram com sucesso.
- Tentativa de abrir a raiz e `/_stcore/health` via navegador falhou; DNS também não resolveu no ambiente de execução. Isso não permite concluir que o Streamlit esteja indisponível; somente que a verificação externa não foi possível.
- Botão está no código da main, mas deploy e visibilidade na instância publicada ainda não foram comprovados. Não executar Gemini sem clique explícito; não iniciar produção ou custos externos.


## CHECKPOINT DE CONTINUIDADE — PROTOCOLO OBRIGATÓRIO — 17/11/2026, 14:06:50 (America/Sao_Paulo)

- O usuário determinou que todo chat novo deve informar quando os dados foram atualizados e consultados, declarar o ponto exato de continuação e pedir confirmação antes de prosseguir.
- Protocolo completo registrado no fim de `NEXUS_MASTER_STATE.md`. Aplicar também as regras resumidas em `NEXUS_NEW_CHAT_BOOTSTRAP.md`.
- Regra de abertura: ler os três documentos diretamente da `main`, verificar HEAD/commits/Actions, montar relatório de retomada com timestamps distintos (consulta atual vs último checkpoint) e parar aguardando confirmação explícita.
- Regra durante o trabalho: checkpoint timestampado após cada etapa significativa; manter master, handoff e bootstrap sincronizados; registrar evidências e estados separados; não declarar concluído sem validação.
- Estado desta atualização: protocolo em documentação; ainda depende da confirmação de CI dos commits documentais. Não altera código de produção, não dispara APIs pagas, deploy ou render.
- Próxima ação: verificar os três commits e respectivos checks no GitHub Actions; então informar ao usuário os SHAs e o resultado real. O chat seguinte deve executar o relatório de retomada e aguardar confirmação antes de qualquer alteração.


## ORDEM PERMANENTE — CHECKPOINT A CADA PROCESSO — 17/11/2026, 14:08:02 (America/Sao_Paulo)

**Sempre atualizar a cada processo e sempre registrar data e horário. Sem exceção.** Cada unidade de trabalho (consulta, análise, decisão, edição, teste, workflow, revisão, correção ou bloqueio) exige checkpoint imediatamente ao terminar e antes de iniciar a próxima. Registrar timestamp America/Sao_Paulo, ação, resultado/evidência, arquivos/commits/IDs, estado real, limitações, pendências e próxima ação. Atualizar o handoff e master state; manter bootstrap sincronizado quando mudar o procedimento ou ponto operacional. Relê-los na main. Se GitHub estiver indisponível, declarar o bloqueio e manter registro visível na resposta; nunca fingir salvamento. Não limitar a regra a “etapas significativas” ou ao encerramento.

- Timestamp da ordem: 2026-11-17T14:08:02-03:00 (UTC−03:00).
- Confirmação de leitura do estado anterior: os três documentos foram consultados diretamente na main; SHAs antes desta atualização: master `465714c25013b41e4c1451640854a225403bd75a`, handoff `0d150d61349e2a892019b4cb47300006a4654a49`, bootstrap `9dd8880cd531171150bce4ba0e5da8d554e71bf0`.
- Commits de protocolo já gravados antes desta regra estrita: `82d7f52` (master), `3a8a0fa` (handoff), `0fd6ae7` (bootstrap).
- Estado: regra estrita sendo persistida nesta etapa; não houve alteração de código de produção nem execução paga.


## Checkpoint de execução da regra absoluta — 17/11/2026, 14:08:32 (America/Sao_Paulo)
- A ordem do usuário foi reforçada para exigir registro imediato após **todo processo/unidade de trabalho**, sem limitar a “etapas significativas”. Inclui consultas, análises, decisões, alterações, testes, workflows, revisões, correções e bloqueios.
- Tentativa inicial de atualização do bootstrap falhou por ausência do SHA no argumento da operação; a falha foi identificada e corrigida consultando novamente o arquivo na main e atualizando com SHA atual. Não foi ocultada.
- Bootstrap atualizado no commit `292218e008ef7f73e8a1d22bdcb80b6c3584b4bf`.
- Master state e handoff receberam a regra estrita nesta sequência; confirmar SHAs atuais por leitura direta.
- Nenhum código de produção, deploy, API paga, GPU ou render foi executado.
- Próxima ação: verificar os três arquivos na main e o CI dos commits documentais; depois reportar evidências e o ponto exato de retomada.
- Timestamp do checkpoint: 2026-11-17T14:08:32-03:00 (UTC−03:00).


## Checkpoint de retomada e auditoria GitHub — 2026-11-17T14:13:50-03:00 (America/Sao_Paulo)
- Consulta atual ao GitHub: 2026-11-17T14:13:50-03:00; branch `main`; HEAD `8a4ab1c198caf7cc60c6c1f3648cf4fa3f32a403` (`docs: sync bootstrap with latest strict checkpoint`).
- Último checkpoint documental anterior: bootstrap em `2026-11-17T14:08:47-03:00`; master state e handoff em `2026-11-17T14:08:32-03:00`. Esta atualização sincroniza os três documentos.
- Comparação desde o HEAD técnico `a9b3d4fd72eba3b81451034859a0791a30256656`: 16 commits à frente, sem alterações de código; somente `NEXUS_MASTER_STATE.md`, `NEXUS_HANDOFF_2026-11-17.md` e `NEXUS_NEW_CHAT_BOOTSTRAP.md` foram modificados.
- CI push confirmado diretamente pela coleção de workflow runs/check-runs: #1097 (`44133649126`, commit `292218e0`), #1098 (`44133688344`, `cab66998`), #1099 (`44133701387`, `6e56171a`) e #1100 (`44133729013`, `8a4ab1c1`) concluídos com sucesso. Em todos: `unit-tests`, `remotion-typecheck` e `commons-live-smoke` passaram; `remotion-synthetic-render` foi skipped por ausência do marcador. O check-run mais recente #1100 está verde; o endpoint de combined status não contém status contexts e não deve ser usado isoladamente para inferir falha.
- Código atual relido: `app.py` (blob `da114a3`), `nexus/director.py` (blob `19df93c`), `nexus/remote_render_job.py` (blob `079941e`) e `nexus/brain4_smoke_test.py` (blob `ee0b8b1`). O botão **“Testar Brain 4 — sem produzir vídeo”** está implementado na main e separado da produção; checkbox de Brain 4 segue default-off. O smoke usa fixture sintético de 4s, duas cenas e oito timestamps; uma geração Gemini, sem Fish Audio, Cloudflare, Modal, GPU, worker ou render. Exige clique explícito e `GEMINI_API_KEY`.
- Tentativa de verificar a URL Streamlit registrada (`https://htykbebk3hceoen5bvopax.streamlit.app/`) e `/_stcore/health` não foi acessível pelas ferramentas de navegação. Isso **não prova indisponibilidade**; deploy e presença do botão na instância publicada continuam não confirmados.
- Estado separado: Brain 4 e smoke **implementados e commitados**; CI mais recente **aprovado**; deploy Streamlit **não confirmado**; chamada Gemini real **não executada**; vídeo de produção **não renderizado/não validado**. Nenhuma API paga, GPU ou render foi acionado nesta auditoria; custo variável adicional US$0.
- Próxima ação exata: usuário abrir a URL Streamlit já registrada e verificar se o botão aparece. Se estiver presente, o clique executa uma chamada Gemini limitada a uma geração e pode consumir cota/crédito da API; só fazer esse clique quando o usuário decidir autorizar essa chamada. Depois compartilhar o resultado exibido. Se o botão não aparecer, enviar captura da tela/estado do app para diagnosticar o deploy. Não iniciar produção nem GPU nesta etapa.


## Resultado final do CI do checkpoint de retomada — 2026-11-17T14:15:22-03:00 (America/Sao_Paulo)
- GitHub Actions #1101 / run `44134707594`, commit `ed0e4c3336642e5c5f188767a5e1b0e155470ecf`: concluído com sucesso. `unit-tests`, `commons-live-smoke` e `remotion-typecheck` passaram; `remotion-synthetic-render` foi skipped corretamente por não haver marcador de render sintético.
- Evidência: run `https://github.com/porraloca42-stack/nexus-video-studio-/actions/runs/44134707594`; todos os jobs relevantes estão `completed/success`.
- O commit documental `868d7469e186a79c57d1b7ef0812b61c19f823ea` apenas sincronizou novamente o checkpoint e usa `[skip ci]`; não contém alterações de código. O CI #1101 validou o commit de conteúdo anterior `ed0e4c3`.
- Estado final da auditoria: CI #1097–#1101 aprovado; implementação Brain 4/fixture smoke permanece no código main; deploy Streamlit não confirmado; Gemini real não executado; vídeo de produção não renderizado nem validado. Custo variável adicional US$0.
- Próxima ação exata: usuário abrir a URL Streamlit registrada e verificar o botão **“Testar Brain 4 — sem produzir vídeo”**. O clique faz uma única geração Gemini e pode consumir cota/crédito; não será acionado pelo assistente. Compartilhar o resultado ou uma captura se o botão não aparecer.


## Checkpoint diagnóstico inicial do erro de importação Brain 4 — 2026-11-17T14:22:02-03:00 (America/Sao_Paulo)
- Consulta GitHub em `2026-11-17T14:21:35-03:00`; branch `main`; HEAD `794d9551703a1c8ae8968254f382844661e3ed4a` (sem novos commits desde o checkpoint anterior). Documentos lidos diretamente da main: master SHA `e16422da5922c74fdc794c8b912e43f025fabb0e`, handoff `9dfd7ddebd5f60bb0ebbee0935214838b25d8608`, bootstrap `6786faf621cc89077a3d8802d6121876b2ce696c`.
- Auditoria de código: `nexus/director.py` na main (blob `19df93c`) contém `generate_editorial_json`; `nexus/brain4_smoke_test.py` (blob `ee0b8b1`) faz import local dessa função dentro do caminho de execução. `app.py` (blob `da114a3`) recarrega apenas `nexus.brain4_smoke_test` via `importlib.reload`; não recarrega `nexus.director`.
- Hipótese técnica principal, ainda não confirmada: processo Streamlit manteve `nexus.director` antigo em `sys.modules`; recarregar somente o smoke helper não atualiza a referência do módulo diretor. O erro reportado (símbolo ausente embora presente no arquivo atual) é compatível com cache de módulo/processo ou instância implantada com código misturado/desatualizado. Não afirmar ainda que esta seja a causa definitiva.
- Comparação GitHub `a9b3d4f...` → HEAD atual: 20 commits à frente, mas somente os três documentos de continuidade mudaram; nenhum código de produção foi alterado desde o baseline técnico. CI #1101 (`44134707594`) continua sendo o último workflow observado, sucesso nos jobs relevantes; não há execução CI nova após ele.
- Evidência do usuário: a UI publicada mostrou botão e devolveu `cannot import name 'generate_editorial_json' from 'nexus.director'`. Isso comprova falha real em runtime; não comprova chamada Gemini. Nenhum vídeo, GPU ou serviço de mídia foi iniciado pelo assistente.
- Estado: hipótese registrada; nenhuma alteração de código, deploy, chamada paga, GPU ou render nesta etapa. Próxima ação: inspecionar testes existentes do smoke e o carregamento/import do pacote; desenhar correção mínima com teste de regressão para módulo já carregado e só então editar em branch/PR.
- Timestamp deste checkpoint: `2026-11-17T14:22:02-03:00` (UTC−03:00).


## Checkpoint de inspeção dos testes e desenho da correção — 2026-11-17T14:22:37-03:00 (America/Sao_Paulo)
- Consulta GitHub: `2026-11-17T14:22:37-03:00`; HEAD `0c8167cfdf5a81a6bc036b8e4a9f52d7e01ed7f0` (checkpoint documental anterior). Master `5742fc5219209aa07692464d28e67521220c2e64`, handoff `2a04d5ed8767af73e729e0764791c57355b09e8e`, bootstrap `7822afa71a2403b9fbd8ef5b3200acfc46774634`; os três contêm o checkpoint de 14:22:02.
- Inspecionados `tests/test_brain4_smoke_test.py`, `tests/test_app_import_resilience.py`, `nexus/brain4_smoke_test.py`, `nexus/__init__.py` e cabeçalho de `app.py`. Testes atuais cobrem geração mockada, validação do fixture e chave ausente, mas não simulam módulo diretor antigo em cache.
- `app.py` já tem comentário/precedente explícito de Streamlit Cloud manter módulo importado antigo e usa `importlib.reload` para `nexus.audio`. A tela recarrega o helper Brain 4, porém o helper faz `from nexus.director import generate_editorial_json` sem recarregar `nexus.director`. Isso fortalece a hipótese de cache de módulo como causa provável.
- Correção planejada: no caminho live do helper, importar `nexus.director` por `importlib`, recarregar o módulo e validar que `generate_editorial_json` é callable antes de montar o `model_call`; manter o caminho injetado/mockado sem reload nem rede. Acrescentar teste de regressão que simule o módulo cached sem o símbolo e confirme que a recarga fornece a função, com exatamente uma chamada mockada e zero Gemini real.
- Nenhum código alterado, nenhuma chamada API paga, nenhum deploy ou render. Próxima ação: criar branch, aplicar mudança mínima no helper e teste, revisar diff e disparar CI.
- Timestamp: `2026-11-17T14:22:37-03:00` (UTC−03:00).


## Checkpoint — branch de correção criada — 2026-11-17T14:23:04-03:00 (America/Sao_Paulo)
- Criada no GitHub a branch `fix/brain4-reload-director-module` a partir da main HEAD `359bd1a246e841fb07b0c850ed7f7228f4dfa6b9`.
- Nenhum arquivo de código foi alterado ainda; nenhuma execução de teste, chamada Gemini, deploy, GPU ou render foi iniciada.
- Próxima ação: aplicar alteração mínima em `nexus/brain4_smoke_test.py` e teste de regressão em `tests/test_brain4_smoke_test.py`; revisar diff antes de abrir PR.
- Timestamp: `2026-11-17T14:23:04-03:00` (UTC−03:00).


## Checkpoint — correção e teste de regressão implementados em branch — 2026-11-17T14:23:46-03:00 (America/Sao_Paulo)
- Branch `fix/brain4-reload-director-module`; commit `633beed014fb05fd586d510fe1d3fa2e31b92127` (`fix: reload cached director for Brain 4 smoke test`).
- Arquivos alterados na branch: `nexus/brain4_smoke_test.py` (importa e recarrega `nexus.director` antes de resolver `generate_editorial_json`; valida callable e apresenta erro diagnóstico com caminho do módulo se ausente) e `tests/test_brain4_smoke_test.py` (novo teste mockado que simula módulo antigo em cache e exige exatamente uma invocação do gerador fake).
- O caminho de teste com `model_call` injetado permanece sem reload e sem rede. O caminho live continua com uma única geração Gemini; nenhuma chamada real foi feita. Nenhum vídeo, serviço de mídia, GPU ou render iniciado.
- Uma tentativa de montar o patch via ferramenta falhou por erro de sintaxe no script antes de qualquer escrita; script corrigido e commit efetivamente criado. Estado final da edição confirmado pelo retorno do GitHub: atualização da branch bem-sucedida.
- Testes ainda não executados; CI ainda não disparado; nenhuma PR aberta; deploy não realizado. Próxima ação: reler os dois arquivos na branch, comparar diff com main, abrir PR para acionar CI e analisar todos os jobs.
- Main no momento do checkpoint: `64cbeb496ff83d696a64011173ad41f0b7f90d25`. Timestamp: `2026-11-17T14:23:46-03:00` (UTC−03:00).


## Checkpoint — sincronização da branch de correção com main — 2026-11-17T14:24:42-03:00 (America/Sao_Paulo)
- O diff da branch inicial continha apenas os dois arquivos esperados (helper e teste), mas estava 2 commits documentais atrás da main. Uma atualização fast-forward foi rejeitada pelo GitHub (não alterou a branch); o conteúdo foi reaplicado sobre a árvore atual da main e a referência foi atualizada com force-with-lease/expected SHA, preservando o trabalho e incluindo os documentos atuais.
- Branch `fix/brain4-reload-director-module` agora aponta para `72dc3138b473fe5ed3880521e829937b73e606c8`, baseado na main `405fb9f8ab62a510bbd22689c75635798855bddf` e contendo a alteração de código/teste.
- Nenhum teste ou CI executado ainda; nenhuma PR, deploy, Gemini, GPU ou render. Próxima ação: confirmar compare branch/main (somente 1 commit à frente, sem divergência), revisar o diff completo e abrir PR.
- Timestamp: `2026-11-17T14:24:42-03:00` (UTC−03:00).


## Checkpoint — branch alinhada ao último checkpoint documental — 2026-11-17T14:25:19-03:00 (America/Sao_Paulo)
- Após o checkpoint documental anterior, a main avançou somente com documentação. A branch foi novamente rebaseada sobre a main `43dfef3889bab15ee06f394a15b73e5a95a2ed62`, preservando os dois arquivos de código/teste; novo HEAD da branch `29d2fb01101570c3bd6caf6121d1700da8a77659`.
- A tentativa de atualização sem force anteriormente foi rejeitada por não-fast-forward; nenhuma alteração foi perdida. A atualização seguinte usou `force=true` com `expected_sha` da branch, concluindo o force-with-lease.
- Próxima ação: verificar compare branch/main e abrir PR. Testes/CI ainda pendentes; nenhuma chamada Gemini, deploy, GPU ou render.
- Timestamp: `2026-11-17T14:25:19-03:00` (UTC−03:00).


## Checkpoint — PR de correção Brain 4 aberto — 2026-11-17T14:25:45-03:00 (America/Sao_Paulo)
- PR #3 aberto: https://github.com/porraloca42-stack/nexus-video-studio-/pull/3 ; título `Fix Brain 4 smoke test with stale Streamlit director module`.
- Base `main` em `e4040956f742691a8ec0749f9003b0af18c7d3b2`; branch `fix/brain4-reload-director-module` em `29d2fb01101570c3bd6caf6121d1700da8a77659`. PR contém 2 arquivos, 46 adições e 2 remoções; apenas helper e teste.
- GitHub retornou PR aberto, ainda não merged e mergeable `false` no instante de criação (estado inicial/checagens pendentes; investigar checks e atualizar metadata antes de qualquer merge).
- CI/testes ainda pendentes. Nenhuma chamada Gemini real, produção, GPU ou render. Próxima ação: consultar workflow disparado pelo PR #3, jobs e logs; corrigir se necessário e não fazer merge antes de CI verde.
- Timestamp: `2026-11-17T14:25:45-03:00` (UTC−03:00).


## Checkpoint — CI do PR #3 em execução — 2026-11-17T14:26:25-03:00 (America/Sao_Paulo)
- PR #3 / run `44136877385` (workflow #1108, evento `pull_request`, commit da branch `29d2fb01101570c3bd6caf6121d1700da8a77659`) está `in_progress`.
- Jobs observados: `unit-tests` em execução após compile application modules concluído; `remotion-typecheck` em execução durante instalação de dependências; `commons-live-smoke` em execução durante instalação de FFmpeg/requests; `remotion-synthetic-render` `skipped` corretamente.
- Nenhum job foi declarado aprovado/reprovado ainda. Próxima ação: consultar conclusão do run e inspecionar logs de `unit-tests` primeiro; corrigir qualquer falha antes de merge.
- Nenhuma chamada Gemini real, render de produção, GPU ou serviços de mídia foi acionada.
- Timestamp: `2026-11-17T14:26:25-03:00` (UTC−03:00). Atualização documental usa `[skip ci]` para não criar workflow concorrente.


## Checkpoint — primeira execução do CI do PR #3 falhou no teste novo — 2026-11-17T14:27:10-03:00 (America/Sao_Paulo)
- Run #1108 / `44136877385`, commit da PR `29d2fb01101570c3bd6caf6121d1700da8a77659`: `unit-tests` **failure**, `remotion-typecheck` **success**, `commons-live-smoke` ainda `in_progress` no momento da consulta, `remotion-synthetic-render` **skipped**.
- Log do job `unit-tests` (ID `134228700402`) inspecionado: 213 testes executados; 1 erro no teste novo `test_live_smoke_reloads_cached_director_before_resolving_generator`. O mock de `importlib.import_module` afetou a resolução do segundo patch, que tentou acessar `reload` no objeto simulado (`AttributeError: namespace ... does not have attribute 'reload'`). A falha está no harness do teste, não no código de produção. Nenhuma chamada Gemini foi feita.
- Correção planejada: no teste, usar `patch.object` diretamente no objeto `importlib` para mockar `import_module` e `reload`, evitando resolução de targets por caminho enquanto o próprio import está sendo simulado. Depois, atualizar a branch/PR e aguardar CI completo novamente.
- PR #3 permanece aberto e não pode ser mergeado. Nenhum deploy de produção, GPU ou render de vídeo foi iniciado.
- Timestamp: `2026-11-17T14:27:10-03:00` (UTC−03:00). Atualização documental `[skip ci]` para não disparar workflow concorrente.


## Checkpoint — harness do teste de regressão corrigido — 2026-11-17T14:27:43-03:00 (America/Sao_Paulo)
- Atualizada a branch `fix/brain4-reload-director-module`; commit `445322eda04549ac745f568b7739585ca277747a` (`test: isolate Brain 4 reload mocks`).
- Arquivo alterado: `tests/test_brain4_smoke_test.py`. O teste agora usa `patch.object` diretamente no módulo `importlib` para simular `import_module` e `reload`, evitando que a resolução textual do segundo mock seja interceptada pelo primeiro.
- O código de produção do helper não mudou nesta correção do harness. Teste local não foi executado neste ambiente; aguardar nova execução do CI da PR #3 para validação real.
- PR #3 permanece aberto. Próxima ação: verificar que a PR recebeu o novo head, aguardar novo workflow `pull_request`, ler logs do job Python e confirmar também `commons-live-smoke`.
- Nenhuma chamada Gemini, deploy, GPU ou render de produção.
- Timestamp: `2026-11-17T14:27:43-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Checkpoint — regressão corrigida; Python e Remotion aprovados — 2026-11-17T14:28:32-03:00 (America/Sao_Paulo)
- PR #3 / workflow #1110 / run `44137245208`, head `445322eda04549ac745f568b7739585ca277747a`.
- `unit-tests` **success**: logs confirm `Ran 213 tests in 3.074s` / `OK`; novo teste `test_live_smoke_reloads_cached_director_before_resolving_generator` passou. `remotion-typecheck` **success**. `remotion-synthetic-render` **skipped** corretamente.
- `commons-live-smoke` ainda `in_progress` no momento do checkpoint; não declarar CI integralmente aprovado até terminar.
- Evidência: job unit-tests ID `134230022210`; typecheck ID `134230021978`; Commons job ID `134230022537`. Run: https://github.com/porraloca42-stack/nexus-video-studio-/actions/runs/44137245208 .
- PR #3 continua aberto; nenhum merge/deploy. Nenhuma chamada Gemini real, produção, GPU ou render foi iniciada.
- Próxima ação: aguardar conclusão de `commons-live-smoke`, depois revisar estado de merge da PR e decidir merge seguro.
- Timestamp: `2026-11-17T14:28:32-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Checkpoint — correção Brain 4 integrada à main — 2026-11-17T14:29:16-03:00 (America/Sao_Paulo)
- PR #3 foi aprovado pelos checks e integrado por squash. Merge commit: `9125e73cc177c952b4b5b13f44c0726db79d98e5`; PR: https://github.com/porraloca42-stack/nexus-video-studio-/pull/3 .
- Run #1110 / `44137245208` concluído `success`: `unit-tests` success (213 testes, incluindo regressão do cache), `remotion-typecheck` success, `commons-live-smoke` success (2 candidatos aceitos; um vídeo CC BY 3.0 baixado e decodificado); `remotion-synthetic-render` skipped corretamente.
- Código de correção agora integrado na `main`: helper recarrega `nexus.director` antes de buscar `generate_editorial_json`; valida callable e fornece diagnóstico do caminho se o símbolo ainda estiver ausente; teste de regressão com mock garante reload e uma invocação mockada.
- Estados: **implementado** e **commitado na main**; CI da PR **aprovado**; **deploy Streamlit ainda não confirmado**; **Gemini real não executado**; **vídeo de produção não renderizado nem validado**. Nenhuma chamada paga, GPU, Modal, Cloudflare ou Fish Audio foi iniciada por esta correção.
- Próxima ação: confirmar HEAD e os arquivos na main, verificar novo CI do commit de merge e deployment Streamlit; depois orientar o usuário a recarregar o app e repetir o teste Brain 4 (isso fará uma chamada Gemini real e exige decisão explícita do usuário).
- Timestamp: `2026-11-17T14:29:16-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Resultado do CI no commit de merge e estado de implantação — 2026-11-17T14:30:06-03:00 (America/Sao_Paulo)
- GitHub Actions #1111 / run `44137507191`, head/merge commit `9125e73cc177c952b4b5b13f44c0726db79d98e5`: `completed/success`.
- Jobs: `unit-tests` success; `remotion-typecheck` success; `commons-live-smoke` success; `remotion-synthetic-render` skipped corretamente por ausência do marcador. O CI da PR #3 (#1110) também passou integralmente.
- Main atual inclui a correção. Arquivos relidos e verificados: `nexus/brain4_smoke_test.py` (blob `2e5c698`) contém reload do diretor e validação callable; `tests/test_brain4_smoke_test.py` (blob `dd82926`) contém teste de regressão.
- Tentativa de abrir `https://htykbebk3hceoen5bvopax.streamlit.app/` via navegador não foi acessível; isso não confirma falha nem sucesso de deploy. **Deploy Streamlit ainda não confirmado.**
- Estados: correção implementada/commitada na main; CI da PR e CI do merge aprovados; deploy não confirmado; Gemini real não executado; vídeo de produção não renderizado nem validado.
- Próxima ação: usuário recarregar a aplicação publicada (reabrir/refresh após a sincronização automática do Streamlit Cloud) e, quando estiver disposto a consumir uma chamada Gemini, executar novamente `Testar Brain 4 — sem produzir vídeo`. A resposta deve ser compartilhada para validação. Não marcar checkbox nem iniciar produção.
- Nenhuma chamada Gemini real, inferência GPU, render de produção ou custo de serviço de mídia foi acionado pelo assistente.
- Timestamp: `2026-11-17T14:30:06-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Evidência runtime — Brain 4 passou do import; Gemini devolveu HTTP 503 — 2026-11-17T14:53:06-03:00 (America/Sao_Paulo)
- Screenshot recebido do usuário após acionar `Testar Brain 4 — sem produzir vídeo`: o app exibiu `O teste Brain 4 não foi aprovado: O Gemini está temporariamente sobrecarregado ou indisponível... (gemini-3.5-flash-lite (HTTP 503))`.
- Interpretação sustentada pela tela: a chamada avançou além do import `generate_editorial_json`, portanto o erro de import anterior não se repetiu nessa execução. O Brain 4 ainda **não foi validado** porque o endpoint Gemini retornou 503; não há sinal de falha do contrato/timeline nem de render.
- Revisão de código na main: `app.py` chama `run_brain4_live_smoke_test`; `nexus/brain4_smoke_test.py` recarrega `nexus.director` e invoca `generate_editorial_json`; essa função chama `_request(... max_models=1, attempts_per_model=1 ...)`, portanto o smoke foi intencionalmente limitado a uma chamada/modelo. A mensagem de erro genérica no ramo 503 diz `Tentei novamente e recorri a outros modelos compatíveis`, o que é impreciso para o smoke limitado a uma chamada. A tela nomeia somente `gemini-3.5-flash-lite (HTTP 503)`.
- Decisão técnica: não ampliar tentativas/modelos automaticamente (preserva limite aprovado de uma geração e evita consumo/custo extra). Fazer correção pequena apenas no texto do erro para distinguir o smoke limitado de caminhos que realmente tentam vários modelos; adicionar teste unitário que verifica HTTP 503, uma única requisição e mensagem sem alegação falsa de retry/failover.
- Estado: correção de import na main e CI #1111 aprovados; screenshot confirma erro externo de disponibilidade Gemini nesta tentativa; nenhum vídeo foi produzido. Próximo passo é correção textual/teste, PR e CI; depois, quando o serviço estiver disponível, o usuário poderá repetir o smoke manualmente. Não disparar nova chamada Gemini automaticamente.
- Timestamp: `2026-11-17T14:53:06-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Checkpoint — correção de diagnóstico HTTP 503 Brain 4 em branch — 2026-11-17T14:54:18-03:00 (America/Sao_Paulo)
- Branch `fix/brain4-smoke-503-message` criada a partir da main `e2040c3c22373a5b3adfbd8a1b6e35b05c57d5fa`.
- Commit de branch `f698a0121599cbcbbdeca7c2422c653c2c096f82`: ajuste de mensagem no ramo 503 de `_request` quando `max_models=1` e `attempts_per_model=1`; agora explica que Brain 4 fez uma única chamada ao modelo indicado e não tentou failover. Caminhos de múltiplas tentativas/modelos mantêm a mensagem existente.
- Teste novo em `tests/test_director_json_recovery.py`: injeta HTTP 503, verifica uma única requisição e garante que a mensagem não alegue retry/failover.
- Nenhuma chamada real ao Gemini, nenhuma alteração na política de tentativas/custo, nenhum render ou deploy. Testes ainda pendentes; PR ainda não aberta.
- Próxima ação: reler diff na branch, abrir PR, executar CI e corrigir qualquer falha antes de merge.
- Timestamp: `2026-11-17T14:54:18-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Checkpoint — PR #4 para diagnóstico HTTP 503 aberto — 2026-11-17T14:55:07-03:00 (America/Sao_Paulo)
- PR #4 aberta: https://github.com/porraloca42-stack/nexus-video-studio-/pull/4 ; branch `fix/brain4-smoke-503-message`, head `14268b3429497321be795871b8e24ad84f19fdab`, base `main` `04e980528d28f2ad9bfe2a328668411f2f3ef708`.
- Alterações: `nexus/director.py` (mensagem específica e verdadeira para caminho com uma única chamada/modelo) e `tests/test_director_json_recovery.py` (teste 503, uma requisição e sem alegação falsa de retry/failover). Compare confirma branch 1 commit à frente, sem divergência; 2 arquivos, 35 adições.
- PR criada; checks ainda não consultados/concluídos. Não fazer merge até CI verde. Nenhuma chamada Gemini real, nenhuma mudança de retry/custo, nenhum render ou deploy.
- Próxima ação: aguardar workflow da PR #4, inspecionar todos os jobs e logs, então integrar somente se aprovado.
- Timestamp: `2026-11-17T14:55:07-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Checkpoint — CI da PR #4 parcialmente concluído — 2026-11-17T14:55:42-03:00 (America/Sao_Paulo)
- PR #4 / run `44142220191` (workflow #1112), head `14268b3429497321be795871b8e24ad84f19fdab`, status `in_progress`.
- `remotion-typecheck` success; `remotion-synthetic-render` skipped corretamente; `unit-tests` e `commons-live-smoke` ainda em execução. Não declarar CI completo.
- Próxima ação: consultar logs/resultados dos dois jobs pendentes; só então considerar merge.
- Nenhuma chamada Gemini real, deploy ou render de produção. Nenhuma alteração adicional ao código após commit da PR.
- Timestamp: `2026-11-17T14:55:42-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Checkpoint final — PR #4 integrada e CI do merge aprovado — 2026-11-17T14:57:02-03:00 (America/Sao_Paulo)
- PR #4 integrada por squash em `b38151058b0f6f53020542ff7fd6ffd79f2b410b`: https://github.com/porraloca42-stack/nexus-video-studio-/pull/4 .
- CI da PR #4 / run `44142220191` (#1112): success em todos os jobs relevantes; `unit-tests` executou 214 testes / OK, incluindo regressão HTTP 503; `remotion-typecheck` success; `commons-live-smoke` success; `remotion-synthetic-render` skipped corretamente.
- CI do commit de merge #1113 / run `44142405400`: `completed/success`.
- `nexus/director.py` na main agora informa corretamente que o smoke Brain 4 faz uma única chamada ao modelo indicado e não tenta outros modelos em caso de HTTP 503; os caminhos com retry/failover multi-modelo preservam o comportamento anterior. Nenhuma ampliação de chamadas ou custo.
- Estados: correção de import integrada e CI aprovada; correção textual 503 integrada e CI aprovada; deploy Streamlit não confirmado; teste real do Brain 4 ainda não passou devido indisponibilidade 503 do Gemini; vídeo de produção não renderizado/validado. Nenhuma chamada Gemini real iniciada pelo assistente.
- Próxima ação: esperar o Gemini voltar e o usuário executar manualmente o botão de teste mais uma vez; conferir se recebe validação positiva. Não iniciar produção nem repetir chamadas automaticamente.
- Timestamp: `2026-11-17T14:57:02-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Resultado real — Brain 4 smoke test aprovado pelo usuário — 2026-11-17T15:01:40-03:00 (America/Sao_Paulo)
- Usuário enviou screenshot do Streamlit após repetir `Testar Brain 4 — sem produzir vídeo`.
- UI confirmou literalmente: `Brain 4 respondeu e a timeline passou pela validação contratual.`
- Métricas exibidas: `alignment_level=word`; `caption_event_count=2`; `edit_anchor_count=2`; `audio_mix_event_count=1`; fixture sintética de 4.0s; `sfx_event_count=0`; nenhum vídeo produzido.
- Marco validado: o caminho isolado Brain 4 completou chamada real Gemini e validação do contrato/timeline. Isso confirma a funcionalidade isolada no ambiente Streamlit em execução.
- Limites da evidência: não valida ainda sincronização com timestamps reais Fish Audio, integração no render final, efeitos sonoros reais, Cloudflare/Modal, Remotion final, MP4 ou qualidade audiovisual end-to-end. A fixture foi sintética e de 4s.
- Estado atualizado: Brain 4 isolado **implementado, integrado, CI aprovado e smoke live validado**. Produção de vídeo completa ainda não executada nem validada. Deploy Streamlit ainda sem confirmação independente por status do provedor, embora a tela observada pelo usuário demonstre que a interface em execução contém o botão e o resultado de sucesso.
- Próximo marco: planejar/autorizar uma produção end-to-end controlada, com roteiro e narração reais, antes de acionar serviços externos potencialmente pagos (Fish Audio, Cloudflare, Modal/GPU e render). Não iniciar produção nem custos automaticamente.
- Timestamp: `2026-11-17T15:01:40-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Checkpoint de retomada — auditoria para produção controlada — 2026-11-17T15:08:30-03:00 (America/Sao_Paulo)
- Main auditada novamente: HEAD anterior `534a6d6ba346352e4f7a88a6255c8dda815c6601`; repositório `porraloca42-stack/nexus-video-studio-`.
- Confirmações de código na main: correção do reload `nexus.director` no smoke Brain 4; diagnóstico HTTP 503 verdadeiro para caminho de uma chamada; integração opt-in Brain 4 no `app.py` e transporte cifrado de `brain4_enabled`/credenciais em `nexus/github_renderer.py`; worker usa timestamps nativos Fish Audio, aplica Brain 4 após narração real e antes das imagens, valida timeline e encaminha caption/SFX/mix para manifesto Remotion.
- CI do commit de merge #1113 / run `44142405400`: success; CI da PR #4 / run `44142220191`: success, 214 testes Python, typecheck e Commons smoke.
- Validação adicional já existente: Remotion demo run `44119421068` success; adapter Python construiu manifesto e Remotion gerou MP4 sintético, com validação de streams/duração. A etapa de demo manual de 50s foi `skipped`; esse run não executou Cloudflare nem Modal nem Fish Audio. Artefato `nexus-remotion-demos` ainda estava disponível na consulta.
- Teste `tests/test_remote_render_job.py` cobre a orquestração completa com mocks: Fish Audio, timestamps, Brain 4 opt-in, imagens, Modal clips, Remotion, FFprobe e criptografia. Isso é teste automatizado de integração simulada, não execução live dos provedores.
- Fluxo padrão no app: `Imagens originais · Cloudflare + Modal I2V + Remotion`; requer Streamlit Secrets `GITHUB_ACTIONS_TOKEN`, `CLOUDFLARE_API_TOKEN`, `FISH_API_KEY` e voz selecionada; requer GitHub Actions Secrets `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`; Brain 4 de produção também exige `GEMINI_API_KEY` e checkbox opt-in. Presença/validade desses Secrets e voz ativa não podem ser inspecionadas pelo conector; não inferir que estão configurados.
- `modal_worker.py` usa LTX-Video 0.9.8 distilled em L40S; budget interno GPU `US$0.42`, reservando `US$0.08` para CPU/memória/variação, com guard antes/depois de cada cena. O limite é uma proteção do componente GPU, não garantia de custo total do vídeo nem garantia de completar todas as cenas abaixo do teto.
- Não foram encontrados runs recentes (na listagem dos 100 runs mais recentes) de `nexus-live-pipeline-smoke.yml`, `modal-deploy.yml` ou `nexus-render-worker.yml`. Portanto deploy do worker Modal, disponibilidade de credenciais e produção real ainda não confirmados.
- Estado atualizado: Brain 4 isolado **implementado, integrado, CI aprovado e smoke live validado pelo usuário** (Gemini real + timeline contratual em fixture sintética de 4s). Manifesto Brain4→Remotion tem teste de integração e Remotion já gerou MP4 sintético. Pipeline Cloudflare→Modal→Remotion live ainda não validado; Fish Audio real + timestamps + Brain4 + I2V + MP4 de 40–50s ainda não executados juntos. MP4 de produção e auditoria visual final ainda pendentes.
- Próxima sequência: (1) validar/preparar secrets e deploy Modal; (2) rodar o smoke live de uma cena Cloudflare→Modal→Remotion, que consome geração de imagem e GPU; (3) corrigir eventuais falhas; (4) somente então executar um piloto real de 40–50s com Fish Audio e Brain 4 ativado, conferindo consumo Modal e Workers AI; (5) inspecionar MP4 e auditoria visual antes de declarar produção validada.
- Nenhum novo job live, GPU, Fish Audio, Cloudflare, Gemini ou render foi iniciado nesta auditoria. Nenhum custo adicional gerado.
- Timestamp: `2026-11-17T15:08:30-03:00` (UTC−03:00). Atualização documental `[skip ci]`.


## Checkpoint — PR #5 Gemini 503 retry integrada e CI verde — 2026-11-17T15:26:48-03:00 (America/Sao_Paulo)
- Diagnóstico da execução de produção 44145957454: o worker concluiu a narração Fish Audio antes de Brain 4; a chamada Gemini retornou HTTP 503 em gemini-3.5-flash-lite; o job falhou em apply_optional_brain4 antes de chamar geração Cloudflare de imagens ou Modal/LTX. O log mostra que Fish Audio foi acionado; eventual consumo/crédito Fish Audio é possível. Nenhum consumo Cloudflare/Modal nessa execução foi evidenciado.
- PR #5 integrada por squash em 5a007dfb94bc14d5b03b99106b8fab6ebabd1f43: https://github.com/porraloca42-stack/nexus-video-studio-/pull/5 .
- Mudança em nexus/director.py: Brain 4 agora faz no máximo 2 tentativas no mesmo modelo selecionado, com espera de 2s, apenas para HTTP 500/502/503/504. Não faz failover silencioso de modelo no caminho Brain 4. Se as duas tentativas falharem, erro explica claramente que o mesmo modelo foi tentado duas vezes.
- Testes adicionados em tests/test_director_json_recovery.py: 503 seguido de resposta válida recupera; dois 503 terminam com mensagem honesta e exatamente duas chamadas. CI da PR #5 / run 44146623660: success. CI do merge / run 44147824239: success; unit-tests, remotion-typecheck, commons-live-smoke success; remotion-synthetic-render skipped corretamente.
- Auditoria da voz exibida como “clone elevenlabs”: o nome aparece como rótulo/título de uma entrada do catálogo curado na categoria ElevenLabs de nexus/voice_catalog.py. Porém, os IDs de todas as três categorias (CapCut, ElevenLabs, Licenciadas Fish) são carregados via get_fish_voice e sintetizados pelo endpoint Fish Audio /v1/tts/stream/with-timestamp, modelo s2.1-pro-free, usando reference_id. O rótulo “ElevenLabs” é agrupamento/metadado do catálogo, não indicação de chamada à API ElevenLabs. A interface transmite o mesmo ID de voz em fish_voice_id e NEXUS_VOICE; o worker entrega esse ID a make_voice, que chama Fish Audio. Não há fallback para ElevenLabs nem Edge TTS nesse caminho.
- A execução 44145957454 já havia passado por Fish Audio antes do 503; a identidade exata/metadata da voz “clone elevenlabs” selecionada não pode ser confirmada somente pelo log sem expor/inspecionar credenciais e ID privado. O caminho do provedor, contudo, está confirmado pelo código.
- Estados: retry Brain 4 implementado, integrado e CI aprovado; Streamlit pode ainda precisar sincronizar/reiniciar para carregar o merge, sem confirmação independente de deploy; pipeline real Fish Audio→Brain4→Cloudflare→Modal→Remotion ainda não validado; nenhum MP4 de produção foi produzido/validado nesta correção.
- Nenhuma nova chamada Gemini live, Fish Audio, Cloudflare, Modal/GPU ou render foi iniciada pelo assistente. Nenhum custo novo foi gerado nesta etapa.
- Próximo passo seguro: verificar que o app Streamlit carregou a versão integrada e então, com autorização explícita do usuário para eventuais custos, fazer uma única produção controlada. A correção só retenta Gemini uma vez; não garante que o serviço esteja saudável nem que o restante do pipeline esteja implantado.
- Timestamp: 2026-11-17T15:26:48-03:00 (UTC−03:00). Atualização documental [skip ci].


## Continuidade — identificador de build do Streamlit — 2026-11-17
- O usuário confirmou que o app não possui informação de versão visível; pedir screenshot sem identificador não permite comprovar qual commit está rodando.
- Criada a branch `fix/streamlit-runtime-build-indicator`.
- `nexus/build_info.py`: identifica primeiro o SHA do checkout local por `git rev-parse HEAD`; usa variáveis de ambiente conhecidas apenas como fallback; não consulta o HEAD remoto.
- `app.py`: Perfil passa a exibir SHA curto, origem e link para o commit completo; sem fonte confiável, informa que a versão não foi identificada.
- `tests/test_build_info.py`: quatro casos unitários cobrindo checkout, fallback, valor inválido e ausência do Git.
- Não houve chamadas externas pagas, produção, deploy ou GPU. CI ainda precisa executar; a alteração ainda não foi integrada nem observada no Streamlit.
- Próxima ação: abrir PR, aguardar CI, corrigir eventuais falhas e integrar apenas com checks aprovados. Depois da sincronização automática do Streamlit, conferir o SHA no Perfil.
