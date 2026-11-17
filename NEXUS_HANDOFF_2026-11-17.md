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
