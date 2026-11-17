# NEXUS VIDEO STUDIO — BOOTSTRAP PARA NOVOS CHATS

Última revisão: 17/11/2026
Repositório oficial: https://github.com/porraloca42-stack/nexus-video-studio-
Branch: `main`

## Instrução obrigatória ao iniciar qualquer chat

Você é o engenheiro responsável pelo NEXUS VIDEO STUDIO. Antes de qualquer alteração técnica:

1. Leia `NEXUS_MASTER_STATE.md` diretamente da branch `main`.
2. Leia `NEXUS_HANDOFF_2026-11-17.md` (ou o handoff com data mais recente).
3. Consulte os commits recentes e o estado real do código/CI no GitHub. Os arquivos de contexto são registros, não substituem a verificação do repositório.
4. Identifique o último trabalho em andamento, o que foi implementado, o que foi testado, o que foi implantado e o que foi efetivamente validado.
5. Continue da próxima ação pendente, sem pedir ao usuário para repetir contexto já documentado.

Não use o arquivo `NEXUS_MASTER_STATE.md` enviado como anexo antigo como fonte de verdade. Ele pode estar desatualizado. A versão na branch `main` é a referência operacional.

## Regras de engenharia

- Faça alterações diretamente no GitHub; não peça ao usuário para programar.
- Trabalhe incrementalmente, uma alteração coerente por vez.
- Preserve decisões e funcionalidades aprovadas.
- Teste cada etapa e registre evidências verificáveis.
- Nunca declare concluído sem validação.
- Diferencie explicitamente: implementado, commitado, CI testado, implantado, renderizado e validado.
- Nunca alegue que acessou Streamlit, secrets, logs ou execução real se isso não foi possível.
- Não exponha nem copie secrets.
- Não faça compras, assinaturas, chamadas pagas, inferência de GPU, download de pesos, deploy ou render de produção sem autorização específica de custo.
- Pesquisa pública profunda está autorizada; isso não equivale a autorização para gastar.
- Responda em português, de forma direta e tecnicamente precisa.

## Decisões de arquitetura que devem ser preservadas

- Aplicativo pessoal em nuvem para vídeos verticais 9:16, alvo inicial 40–50s, 720p.
- Arquitetura híbrida de mídia: selecionar a rota visual por cena; não usar geração AI video em todas as cenas por padrão.
- Preservar o motor LTX-0.9.8/fallback atual. Não reabrir adoção do LTX-2.5 sem revisão específica.
- Quatro cérebros editoriais aprovados: estrategista de hook/retenção; roteirista de micro-ritmo; diretor de fotografia/roteamento; editor de ritmo e sincronização.
- Não conectar novos estágios a APIs pagas sem orçamento explícito. Os contratos, prompts e runner puros não autorizam chamadas externas automaticamente.
- Precisão temporal deve corresponder à evidência: word, character e phoneme são níveis distintos. Não alegar alinhamento de sílaba tônica a partir de timestamps de palavra/caractere.
- Não confundir suporte técnico de captions/SFX/ducking no Remotion com validação audiovisual em MP4 real.

## Estado conhecido no último handoff (17/11/2026)

- `nexus/editorial_pipeline.py`: contratos e validadores dos quatro cérebros, runner com executores injetados.
- `nexus/editorial_prompts.py`: quatro prompt builders puros.
- `remotion/src/NexusVideo.tsx`: suporte a captions temporizadas, SFX e ducking de música com fades.
- `nexus/remotion_renderer.py`: manifesto e cópia de assets multifaixa.
- CI anterior: 191 testes Python e Remotion typecheck passaram no run #953; o Commons smoke naquele run estava pendente na última leitura do estado.
- Não havia render MP4 sintético ou real inspecionado.
- Script de validação sintética criado em `scripts/validate_remotion_render.py`.
- Job `remotion-synthetic-render` adicionado em `.github/workflows/tests.yml`, condicionado a workflow_dispatch ou mensagem de commit com `[run-remotion-validation]`, para evitar execução em todo push.
- O job produz MP4 sintético de 4s com tons gerados, legendas word-highlight, SFX e ducking. Mede presença visual/sonora por FFmpeg/Pillow e preserva artifact por 7 dias.
- Correção recente: diretório usado para extrair frames foi separado do TemporaryDirectory da fixture, evitando tentativa de gravar frames em diretório já removido. Commit: `1425f46c283a00c438dc7716f18336cd0e900277`.
- A execução do job ainda não estava confirmada pela integração GitHub disponível. O conector de GitHub usado até então não expõe ação de dispatch/listagem de todos os workflow runs; status combinado retornou vazio. Não afirmar que job passou.
- Nenhuma API Gemini/Fish/Cloudflare, Modal/GPU, download de modelo, deploy ou render de produção foi acionado nesta etapa. Custo variável externo adicional: US$0. Minutos de runner hospedado podem depender da franquia GitHub.

## Próxima ação exata

1. Consultar o GitHub Actions para localizar o run de `NEXUS regression tests` que corresponde ao commit `108410748fc872314ebf32f2a95bbf2a77476b8b` ou à execução iniciada pelo push com `[run-remotion-validation]`.
2. Verificar especificamente o job `remotion-synthetic-render`. Obter logs, conclusão e artifact `nexus-remotion-synthetic-validation`.
3. Se falhar, diagnosticar pelos logs, corrigir o script/workflow no GitHub e repetir apenas a validação necessária.
4. Se passar, baixar e inspecionar o MP4, conferir duração, frames, palavras destacadas, SFX e envelope de música. Registrar métricas e resultado no master state/handoff.
5. Só depois considerar integração gradual com o fluxo de produção. Não ativar chamadas Gemini adicionais sem avaliação e autorização de orçamento.
6. Manter o pipeline atual de produção e fallback preservados até haver validação específica.

## Como usar este arquivo em um novo chat

Cole o conteúdo deste arquivo ou, preferencialmente, inicie o chat dentro do mesmo Project e peça:

“Retome o NEXUS VIDEO STUDIO. Leia NEXUS_NEW_CHAT_BOOTSTRAP.md, NEXUS_MASTER_STATE.md e o handoff mais recente diretamente do GitHub main; verifique os commits e CI atuais; depois continue da próxima ação exata, sem repetir trabalho concluído.”

Este bootstrap reduz perda de continuidade, mas não garante que a plataforma carregue automaticamente todo o histórico anterior. O repositório e seus registros são a fonte persistente de verdade.

## Atualização complementar — 17/11/2026
- O teste sintético teve correção do diretório temporário no commit `1425f46c283a00c438dc7716f18336cd0e900277`.
- Este bootstrap foi criado no commit `cc58c3a5174b13c5a1e4a48a13ea2dd3b71cac34`.
- Master state e handoff registraram essa mudança nos commits `875460450db3193c7c123faf055bf009846774bd` e `50ba514919fbd446dc0304eb456b21a027b0e945`.
- Próximo passo imediato: criar push marker `[run-remotion-validation]` após a correção e então verificar a execução do job/artifact pelo GitHub Actions.

- Solicitação de nova execução após a correção do teste: commit de push com marcador `[run-remotion-validation]` a ser consultado no Actions. A execução e o artifact só serão considerados confirmados após leitura do resultado real do job.

### Último checkpoint de sessão — 17/11/2026
- Push marker de reexecução após correção: `b5d374eaadc148260a78b8fc2d849d8af9b7c7e6`.
- Master state atualizado: `e092eaccb8e03a0f5376e0617d336e8984476f12`.
- Handoff atualizado: `f6ff90aa3fdf1d8abc915dfafa1868ed3c2975de`.
- CI status combinado permaneceu vazio; a integração de GitHub não lista push workflow runs. O próximo chat precisa conferir manualmente Actions e artifact antes de qualquer declaração de validação.


## Checkpoint atualizado — 17/11/2026
- A falha do run #969 foi diagnosticada nos logs: `ModuleNotFoundError: No module named 'nexus'` no script de render sintético.
- Correção de `sys.path` commitada em `178ffe1bcb26a5a9ebbbbf69c08979ebfb555df7`.
- Run #973: testes unitários, typecheck e Commons smoke passaram; o job sintético foi ignorado por falta do marcador no commit.
- O master state foi atualizado em `cc86d8b9ad78c2c0d3c9b2d081e481d741fd87c8`, cujo commit contém `[run-remotion-validation]` para disparar a validação restrita.
- Próxima ação: consultar o run criado por esse push, validar conclusão de `remotion-synthetic-render`, obter o artifact e inspecionar o MP4. Não declarar validação até essa inspeção.


## Estado mais recente — após primeira inspeção de MP4 — 17/11/2026
- O run #974 gerou MP4 sintético, mas falhou na asserção de ducking: -34.6dB antes e -38.7dB durante. O artifact #14342431166 foi inspecionado: MP4 4s, 720x1280, 30fps, H.264/AAC. Legendas destacadas foram verificadas; teste SFX ainda não foi alcançado.
- Hipótese de contaminação da medição por frequências próximas do fixture (narration 440Hz vs música 220Hz) foi tratada separando os tons: commit `549bb44e51e2375cf0f08b826749565bfc104c96` usa narração 1100Hz, música 220Hz e SFX 3000Hz, com banda SFX 2800–3200Hz.
- Próxima ação: verificar run disparado pelo commit com marcador, conferir resultado das três verificações de áudio/legendas e inspecionar artifact. Não declarar validação multifaixa antes disso.


## Último checkpoint validado — 17/11/2026
- Run #977 / `44114553978`, commit `549bb44e51e2375cf0f08b826749565bfc104c96`: unit-tests, Remotion typecheck, Commons smoke e render sintético multifaixa passaram.
- Métricas: ducking da música -36.1dB → -50.6dB → -36.1dB; SFX -45.7dB → -30.0dB; pixels de destaque word_one=2249, word_two=1773, caption_off=0.
- Artifact #14342476549 foi baixado e inspecionado: MP4 H.264 720x1280, 30fps, AAC 48kHz, 4.011s; frame de palavra destacada verificado visualmente.
- Estado: render sintético multifaixa validado. Não confundir com voz real, alinhamento fonético, vídeo final de 40–50s, integração com Streamlit, deploy ou produção. O adapter Remotion continua isolado.
- Próxima direção: estudar integração gradual do adapter ao app, preservando fallback, antes de qualquer alteração de fluxo produtivo; sem APIs pagas sem autorização explícita.


## Correção arquitetural importante — 17/11/2026
- Remotion está no fluxo padrão indireto via app.py → GitHub worker → `nexus.remote_render_job` → `render_video_remotion`; não está isolado do worker.
- Os quatro cérebros ainda não estão conectados ao app: app.py não importa o runner/prompts editoriais e director.py não cria `edit_timeline`. Sem timeline, captions word-highlight, SFX e ducking/fades não chegam comprovadamente ao MP4 de produção.
- Próxima etapa: preparar integração offline/testável dos contratos editoriais com o plano atual, sem executar chamadas externas ou custos. Preservar o caminho de produção e fallback até haver validação controlada.


## Último marco — alinhamento Fish Audio — 17/11/2026
- Fish Audio SSE agora preserva snapshots por chunk e offsets absolutos, com retorno opcional e compatibilidade retroativa. Worker inclui segmentos no relatório criptografado.
- CI #991: 193 testes Python passaram; typecheck e Commons smoke passaram. Render sintético não foi acionado nesta alteração.
- Segmentos são mantidos como `provider_segments`; não inventar confidence nem declarar palavra/fonema sem validação. Brain 4 ainda não está conectado a esses segmentos.
- Próximo: ajustar contrato Brain 4 para a evidência real do provedor e testar com executores simulados. Não executar chamada Gemini adicional sem autorização de custo.


## Último checkpoint — ponte Brain 4 — 17/11/2026
- Fish provider segments são preservados e promovidos a word timestamps apenas quando cada segmento é um token individual. Frases não são rotuladas como palavras; confidence não é inventada.
- Contrato e prompt Brain 4 ajustados para confidence opcional e granularidade comprovada. CI #1002: 198 testes Python, typecheck e Commons smoke passaram; render sintético skipped.
- Próxima ação: implementar executor Brain 4 no worker com mocks e sem chamada externa; manter Gemini real desabilitado até autorização explícita de custo. `edit_timeline` ainda não chega aos renders de produção.


## Continuidade — executor Brain 4 — 17/11/2026
- Runner puro dos quatro cérebros agora encaminha word timestamps validados ao executor Brain 4. Teste offline cobre a passagem dos dados.
- CI #1007: testes Python e typecheck passaram; Commons smoke pendente na última consulta.
- Ainda falta executor real Brain 4 e chamada no worker. Preparar com mocks; manter qualquer chamada Gemini extra desabilitada até autorização explícita.


## Checkpoint atual — Brain 4 opt-in — 17/11/2026
- Criada ponte `run_brain4_for_storyboard()` e integração opcional no worker via `editorial_model_call`. Sem callable, status disabled e comportamento atual preservado; app padrão não chama Gemini extra.
- Com callable injetado, Brain 4 usa storyboard existente + áudio final + word timestamps comprovados, valida `edit_timeline`, asset e duração. Sem word timestamps, recusa antes da chamada; não estima sincronismo.
- CI #1017: 202 testes Python, typecheck e Commons smoke passaram. Synthetic multitrack skipped.
- Workflow Remotion demo #119: adapter tests/typecheck passaram; demo manual 50s skipped; render sintético de integração 4s ainda em andamento.
- Estado: integração validada com mocks, não conectada ao app e sem Gemini real. Próximo: conferir MP4 sintético; manter chamadas pagas desabilitadas sem autorização.


## Validação do adapter Remotion — 17/11/2026
- Workflow #119 passou: manifest gerado pelo adapter Python real, render Remotion validado por FFprobe (H.264 720×1280, AAC, 4.011s). Artifact #14344496316.
- Render 50s manual skipped. Teste 4s sintético não representa produção real nem timeline Brain 4.


## Última validação — Brain 4 timing + Remotion adapter — 17/11/2026
- CI #1022: 203 testes Python, typecheck e Commons smoke passaram. Brain 4 está protegido contra drift de timestamps Fish, precisão fonética inventada e legendas fora dos tempos verificados.
- Workflow #119: MP4 sintético 4.011s via adapter Python real validado por FFprobe (H.264/AAC, 720×1280); artifact #14344496316.
- Brain 4 permanece opt-in/mockado; Gemini real desativado.
- Próxima ação: teste offline Brain4 timeline → `build_remotion_manifest()` com captions, SFX e ducking.


## Trabalho em andamento — Brain 4 → Remotion manifest — 17/11/2026
- Novo teste em `tests/test_remotion_renderer.py` verifica que a timeline validada do Brain 4 chega ao manifest Remotion com captions, palavras temporizadas, SFX e fades/ducking.
- CI #1030 e workflow demo #120 estão em execução; verificar resultados antes de prosseguir. Sem APIs pagas ou render de produção.


## Resultado mais recente — teste Brain 4 → manifest — 17/11/2026
- CI #1030 aprovado: 205 testes Python, Remotion typecheck e Commons smoke. A timeline Brain 4 validada chega ao manifest com captions, timestamps, SFX e fades/ducking.
- Workflow Remotion demo #120 ainda em andamento na última consulta; verificar MP4 sintético.


## Última alteração em validação — hook worker Brain 4 — 17/11/2026
- Teste novo comprova executor explicitamente injetado em `apply_optional_brain4()` e status disabled no relatório quando não há executor.
- Commit `3f721da8890c5b12fe7b01690e6156378350159b`; CI #1037 em andamento, conferir antes de prosseguir.
- Workflow Remotion #120 passou com MP4 sintético H.264/AAC 720×1280, 4.011s; artifact #14344765828.


## Checkpoint — validação sintética ponta a ponta Brain 4 — 17/11/2026
- CI #1037 aprovado: 206 testes Python, typecheck e Commons smoke. Teste do hook confirma injeção explícita e estado disabled por padrão.
- Script sintético agora passa pelo adapter Brain 4 com resposta determinística/mockada e render Remotion multifaixa. Commit `e1f8737447fe14fb7114617dc9681200bf5742f0`.
- Próxima ação: disparar workflow com marcador `[run-remotion-validation]`; verificar MP4 e métricas de legenda/SFX/ducking. Sem chamadas pagas.


## Último checkpoint validado — Brain 4 sintético → MP4 — 17/11/2026
- CI #1045 aprovado: 206 testes Python, typecheck, Commons smoke e render sintético Remotion.
- Pipeline exercitado: Brain 4 adapter com resposta mockada → validação de contrato → manifest Python → MP4 H.264/AAC 720×1280, 4.011s.
- Asserções de mídia: destaque captions 2249/1773 pixels, caption off 0; ducking música 14.5 dB com recuperação ao nível original; SFX 15.7 dB acima do nível de fundo. Artifact #14343349831.
- Workflow demo #121 também passou; render manual 50s skipped.
- Limite: não é Gemini real nem vídeo de produção. Próxima etapa: revisão visual do MP4 e plano de integração real condicionado a autorização de custo.


## Revisão visual concluída — MP4 sintético — 17/11/2026
- Artifact #14343349831 inspecionado: H.264/AAC, 720×1280, 4.011s. Frames confirmam destaque palavra por palavra (NEXUS → valida) e remoção da legenda fora do intervalo.
- Métricas: ducking música 14.5 dB e recuperação; SFX +15.7 dB. Limite: fixture gráfico sintético, não conteúdo real.
- Próxima etapa pendente: integração Gemini real em Brain 4 com feature flag default-off e orçamento autorizado; nenhuma chamada paga foi feita.


## Implementação em validação — Gemini real opt-in Brain 4 — 17/11/2026
- Helper Gemini Brain 4 dedicado, uma geração por vídeo (um modelo, sem retry/failover); retorno JSON timeline, não storyboard.
- Checkbox no app desmarcado por padrão; flag e modelo seguem criptografados ao worker. Worker recusa flag ativa sem GEMINI_API_KEY antes da geração de imagens.
- Testes adicionados; CI #1061 / `44120993502` em execução. Não houve chamada Gemini real nem render de produção. Conferir CI antes de prosseguir.


## CI aprovado — Brain 4 Gemini opt-in — 17/11/2026
- CI #1061 aprovado: 209 testes Python, compileall, Remotion typecheck e Commons smoke. Synthetic render skipped.
- Gemini Brain 4: helper dedicado com 1 modelo/1 geração por vídeo; worker lê flag criptografada; checkbox app desmarcado por padrão; exige chave quando habilitado.
- Testes de contrato JSON, uma única chamada, default-off, chave ausente e transporte criptografado aprovados.
- Nenhuma chamada Gemini real nem render de produção ocorreu. Próxima ação: regressão sintética Remotion, depois teste controlado com autorização explícita do uso da chave.


## Regressão aprovada — Brain 4 opt-in — 17/11/2026
- CI #1067 aprovado integralmente: 209 testes Python, compileall, typecheck, Commons smoke e MP4 sintético Remotion #14345002405 (4.011s). Captions, word highlight, ducking e SFX validados.
- App agora exibe status editorial retornado pelo worker. Commit UI `72f4721f77d02ad22f5203c8f54c5a243e062797`; conferir CI desse commit.
- Integração Gemini real ainda não chamada; checkbox opt-in permanece default-off.


## UI Brain 4 validada — 17/11/2026
- CI #1068 aprovado para commit `72f4721f77d02ad22f5203c8f54c5a243e062797`: 209 testes, compileall, typecheck e Commons smoke. Render sintético skipped (UI-only).
- Status do Brain 4 aparece no resultado do MP4 usando o report do worker. A feature continua opt-in/default-off; nenhuma chamada Gemini real ou produção foi feita.



## Atualização de continuidade — 17/11/2026: smoke test Brain 4
- HEAD recente: commits `12315a2` (helper de smoke test isolado), `eb3c2d3` (testes), `49da8be` (botão Streamlit).
- Leia a seção “Smoke test isolado do Brain 4 Gemini” do `NEXUS_MASTER_STATE.md` e a seção de continuidade mais recente do handoff.
- O botão **“Testar Brain 4 — sem produzir vídeo”** chama Gemini somente mediante clique explícito; usa fixture sintético de 4s e valida a timeline, sem Fish, Cloudflare, Modal, GPU, worker ou render.
- CI #1075–#1077 estava pendente na última consulta. Confirme cada execução no GitHub Actions e leia logs se falhar.
- Nenhuma chamada Gemini real foi feita e deploy Streamlit não foi verificado. Não afirmar que a função está disponível na instância publicada até confirmar deploy.
- Após CI verde, aguardar o usuário executar o botão no Streamlit; não acionar API Gemini por conta própria. Um render completo exigirá autorização de custos/execução separada.



## Direção de produto e checkpoint mais recente — 17/11/2026
- A ambição do projeto é competir com Revid AI e outros faceless apps de ponta em qualidade ponta a ponta; consulte a seção “Benchmark de produto faceless e direção de qualidade” no master state.
- Revid oficial anuncia roteiros/links para vídeos, escolha de mídia por cena, voz, captions, música, timeline editor, export até 4K, social publishing, automação e API/MCP/CLI; claims do fornecedor devem ser verificados e não equivalem a benchmark independente.
- CI #1081 / run `44122780273`, commit `223f97a071befdfb18a0be5cf3393f9c59749753`: sucesso, 212 testes Python, typecheck e Commons smoke; synthetic render skipped.
- O botão “Testar Brain 4 — sem produzir vídeo” está implementado e passou CI. Não foi executado contra Gemini real; deploy Streamlit não confirmado. O próximo chat deve verificar deploy e aguardar clique explícito do usuário antes de qualquer chamada Gemini.
- Nenhum vídeo de produção, inferência GPU ou custo de serviços externos foi iniciado nesta etapa.


## Checkpoint confirmado — 17/11/2026
- HEAD `main`: `a9b3d4fd72eba3b81451034859a0791a30256656`.
- CI documental #1082 (`44123082031`), #1083 (`44123091378`) e #1084 (`44123106001`) concluído com sucesso: testes Python, Remotion typecheck e Commons live smoke passaram; render sintético skipped.
- #1076/#1077 falharam por asserção com texto esperado incorreto; correção em `223f97a` aprovada no CI #1081 (`44122780273`): 212 testes Python, typecheck e Commons smoke.
- Botão `Testar Brain 4 — sem produzir vídeo` está no código da main, dentro do modo Cloudflare + Modal I2V + Remotion. Requer clique explícito e `GEMINI_API_KEY`; usa fixture sintético e não inicia serviços de mídia nem render.
- Deploy Streamlit não confirmado e URL pública não identificada no repositório. Solicitar ao usuário a URL da instância antes de afirmar que o botão foi publicado.
- Não executar Gemini sem clique explícito do usuário. Não iniciar vídeo completo, GPU ou serviços pagos sem autorização separada.


## Verificação mais recente — 17/11/2026
- URL oficial da instância, já registrada no master state: https://htykbebk3hceoen5bvopax.streamlit.app/ .
- CI #1085, #1086 e #1087 dos três commits documentais concluiu com sucesso.
- A raiz do app e `/_stcore/health` não puderam ser acessadas pelas ferramentas disponíveis; falha de acesso/DNS no ambiente não comprova que o serviço esteja fora do ar.
- O botão Brain 4 consta no código da main, mas a publicação da versão e sua visibilidade ainda não foram confirmadas. Próxima etapa: confirmar o último deploy no Streamlit Cloud ou obter acesso observável à UI; depois aguardar clique explícito do usuário para Gemini.


## REGRA CRÍTICA — RELATÓRIO DE RETOMADA E CONFIRMAÇÃO OBRIGATÓRIA

Antes de qualquer alteração em todo chat novo:
1. Ler os três documentos canônicos diretamente da `main`: master state, handoff mais recente e este bootstrap.
2. Verificar HEAD, commits recentes, arquivos alterados e GitHub Actions/checks. Investigar logs de falhas e estados pendentes.
3. Não confiar em anexos antigos, memória ou resumos como fonte principal. Não misturar datas; em conflito, prevalece a evidência atual da `main` e do Actions.
4. Exibir relatório de retomada contendo: horário atual da consulta ao GitHub em America/Sao_Paulo; horário do último checkpoint documental; HEAD/commit; último trabalho concluído; testes e resultados; estados separados (implementado, commitado, CI, deploy, render, validação); pendências; bloqueios; ponto exato e próxima ação.
5. Perguntar literalmente se o estado e o ponto de continuação estão corretos e se pode prosseguir. **Esperar confirmação explícita.** Até lá, não fazer alterações, commits, dispatches, chamadas externas, deploy ou render. Apenas leitura/auditoria para montar o relatório.
6. Se houver divergência, CI pendente/falho ou ponto de retomada incerto, declarar isso e não inventar resposta.

## REGISTRO DE CADA ETAPA
- Após cada etapa significativa, criar checkpoint com data/hora completa e fuso America/Sao_Paulo, ação, arquivos, commit, testes, evidências, limitações, estado real e próxima ação.
- Sincronizar master state, handoff e bootstrap; conferir os três arquivos na main e registrar SHAs. Se qualquer atualização falhar, declarar sincronização parcial.
- No encerramento, registrar exatamente onde parou, inclusive quando bloqueado.
- Diferenciar horário da consulta atual e horário da última atualização documental. Nunca inventar timestamps.
- Este mecanismo é continuidade versionada por GitHub, não promessa de memória automática entre chats.

O protocolo detalhado e prevalente está no fim do `NEXUS_MASTER_STATE.md`. O handoff deve conter sempre o checkpoint mais recente.


## REGRA PERMANENTE — CHECKPOINT APÓS TODO PROCESSO — 17/11/2026, 14:08:19 (America/Sao_Paulo)

**SEMPRE ATUALIZAR A CADA PROCESSO. SEMPRE REGISTRAR DATA E HORÁRIO. SEM EXCEÇÃO.**

Cada unidade de trabalho — consulta, leitura, pesquisa, análise, decisão, alteração, teste, workflow, revisão, correção, atualização documental ou bloqueio — exige checkpoint imediato, antes da próxima unidade. Registrar timestamp completo em `America/Sao_Paulo`, ação, resultado/evidência, arquivos/commits/IDs, estado real, limitações, pendências e próxima ação. Atualizar imediatamente master state e handoff; manter este bootstrap sincronizado quando mudar procedimento ou ponto de continuidade. Relêr na main. Se não for possível gravar, declarar o bloqueio e deixar o checkpoint explícito na resposta; nunca fingir que foi salvo. É proibido adiar os registros para o fim ou limitar a regra a etapas grandes. Ver regra prevalente no fim de `NEXUS_MASTER_STATE.md`.

Timestamp da atualização: 2026-11-17T14:08:19-03:00 (UTC−03:00).


## Checkpoint da regra absoluta — 17/11/2026, 14:08:47 (America/Sao_Paulo)
- Regra permanente: checkpoint após toda unidade de trabalho, sem exceção, com data/hora/fuso, ação, evidência, estado e próxima ação. Inclui etapas pequenas e bloqueios.
- Master state atualizado no commit `cab669983d7a6897d9e85e79095d96d18bc10349`; handoff atualizado no commit `6e56171a1305083df21a64188e7731f460347885`.
- Esta atualização sincroniza o bootstrap após o master/handoff. Timestamp: 2026-11-17T14:08:47-03:00 (UTC−03:00).


## Ponto operacional vigente — 2026-11-17T14:13:50-03:00 (America/Sao_Paulo)
- HEAD consultado: `8a4ab1c198caf7cc60c6c1f3648cf4fa3f32a403`; CI #1097–#1100 aprovado (unit-tests, Remotion typecheck, Commons smoke; render sintético skipped).
- Brain 4 smoke está no código main, mas deploy Streamlit não confirmado; Gemini real não executado e produção não iniciada.
- Próxima ação: usuário verificar o botão na URL Streamlit registrada; clique realiza uma geração Gemini e pode consumir cota/crédito. Ver checkpoint completo no fim de `NEXUS_MASTER_STATE.md` e do handoff.


## Resultado CI e próxima ação — 2026-11-17T14:15:22-03:00 (America/Sao_Paulo)
- CI #1101 / run `44134707594` passou: unit-tests, Commons live smoke e Remotion typecheck; render sintético skipped.
- Deploy Streamlit continua não confirmado. A próxima ação é verificar o botão Brain 4 na URL registrada; clique executa uma geração Gemini e pode consumir cota/crédito.
- O registro completo está no fim do master state e do handoff.


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
