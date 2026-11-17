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
