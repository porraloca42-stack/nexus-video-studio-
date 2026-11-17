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

