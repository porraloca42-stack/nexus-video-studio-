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
