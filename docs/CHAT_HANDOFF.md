# NEXUS VIDEO STUDIO — HANDOFF PARA NOVO CHAT

Atualizado em: 16/11/2026
Repositório: https://github.com/porraloca42-stack/nexus-video-studio-
Branch: main
App: https://htykbebk3hceoen5bvopax.streamlit.app/

## REGRA OBRIGATÓRIA PARA RETOMADA
Antes de qualquer ação técnica:
1. Ler integralmente `NEXUS_MASTER_STATE.md` na branch `main`.
2. Ler este arquivo de handoff.
3. Conferir no GitHub o estado atual do workflow e os arquivos relevantes; este handoff é um registro, não substitui a verificação ao vivo.
4. Não repetir passos já feitos, não disparar novo deploy e não alterar código enquanto o deploy atual estiver em andamento.
5. Dar ao usuário instruções curtas, uma ação por vez. Nunca pedir tokens no chat.
6. Não declarar Modal implantado até haver confirmação explícita de sucesso no GitHub/Modal.

## PONTO EXATO ONDE A CONVERSA PAROU
O usuário executou manualmente o workflow GitHub Actions:
- Workflow: `Deploy NEXUS Modal video worker`
- Arquivo: `.github/workflows/modal-deploy.yml`
- Execução: run #1
- Commit exibido: `82ab49d` (branch `main`)
- Job: `deploy`
- Última captura enviada pelo usuário: status **In progress**, duração do job **30m 39s** e execução iniciada manualmente há 30 minutos.
- A captura mostra que o job continuava em andamento depois de 30 minutos, apesar de o YAML conter `timeout-minutes: 30`.
- Portanto, a afirmação anterior de que o GitHub cancelaria necessariamente a execução exatamente aos 30 minutos estava incorreta. A observação da tela é a evidência mais recente; não presumir cancelamento.
- Instrução dada ao usuário: não cancelar nem reiniciar; deixar a execução atual terminar e enviar o resultado.
- Próxima ação: aguardar. Se ainda estiver em andamento, pedir apenas a tela dos logs finais/etapa atual; se terminar, inspecionar o resultado e logs antes de qualquer mudança.
- Não iniciar outra execução até entender o resultado da primeira.

## CONFIGURAÇÃO JÁ FEITA PELO USUÁRIO
O usuário confirmou que:
- Criou uma API token no Modal.
- Cadastrou no GitHub Actions Secrets os dois nomes `MODAL_TOKEN_ID` e `MODAL_TOKEN_SECRET`.
- Não se deve solicitar nem reproduzir valores desses secrets.
- Em momento anterior, o usuário colou um comando contendo token ID e secret no chat. Não está confirmado se esse token exposto foi revogado ou se foi o mesmo usado nos secrets. Tratar como potencialmente comprometido; quando oportuno, orientar uma única vez a revogar o token exposto e substituir os secrets por um token novo. Nunca pedir que compartilhe o valor.

## CONFIGURAÇÃO DO WORKFLOW
O arquivo atual `.github/workflows/modal-deploy.yml` foi relido diretamente da branch main nesta conversa. Contém:
- `timeout-minutes: 30`
- Python 3.12
- instalação do CLI Modal com `python -m pip install --upgrade modal`
- validação de presença dos secrets
- comando `modal deploy modal_worker.py`

O arquivo `modal_worker.py` também foi relido. Define:
- app Modal `nexus-video-i2v`
- classe `Inference`
- GPU H100
- modelo `Lightricks/LTX-Video`, revisão fixada
- volume persistente `nexus-ltx-model-cache`
- timeout do container de inferência de 45 minutos
- escala a zero após 60 segundos sem uso
- geração de clipes em lote, 512×896, 24 fps, 2–5 segundos por cena.

Importante: o `timeout=45 * MINUTES` no worker Modal é diferente do `timeout-minutes: 30` do job GitHub Actions. Não confundir os dois limites.

## ESTADO CONFIRMADO VS. NÃO CONFIRMADO
Confirmado:
- Integração Modal/LTX está implementada na branch main.
- Workflow manual existe.
- Usuário criou token Modal e informou que cadastrou os dois GitHub Secrets.
- Run #1 foi disparado e apareceu como In progress com 30m39s na última captura.

Ainda NÃO confirmado:
- Se run #1 terminou com sucesso ou falha.
- Se o app `nexus-video-i2v` foi realmente implantado no Modal.
- Se o modelo foi baixado/carregado.
- Se houve consumo de GPU/créditos.
- Qualquer teste real de geração image-to-video.
- Qualidade, latência e custo real por clipe ou vídeo.

Não dizer que o deploy está concluído até verificar a execução final.

## DECISÕES DE SEGURANÇA E CUSTO
- Não disparar geração GPU de teste sem autorização explícita.
- O usuário queria manter gastos adicionais em zero; a tela de billing anteriormente mostrava Credits $0, Debits $0 e Usage $0 of $42.50. O valor US$42.50 era limite de utilização, não crédito grátis. Confirmar saldo e limites diretamente no painel antes de qualquer teste pago.
- O usuário adicionou cartão virtual Nubank com limite configurado de R$1; não assumir que isso garante ausência absoluta de cobrança.
- Não afirmar que créditos mensais cobrem dois vídeos/dia sem benchmark real.
- O primeiro teste de GPU, quando autorizado, deve ser pequeno e controlado; o plano anterior recomendava começar por uma cena representativa antes do vídeo completo.

## PRÓXIMOS PASSOS — ORDEM EXATA
1. Aguardar o run #1 atual, sem cancelar ou reiniciar.
2. Quando terminar, verificar status e logs completos.
3. Se sucesso: confirmar no painel Modal que `nexus-video-i2v` foi implantado; não executar geração GPU sem autorização.
4. Se falha: diagnosticar a mensagem concreta. Só então corrigir o workflow/código. Não presumir que aumentar timeout resolverá; identificar a etapa lenta.
5. Se for necessário alterar o timeout, primeiro atualizar este handoff/master state e explicar que um novo workflow run precisará ser disparado manualmente pelo usuário. Não fazer novo deploy sem combinar.
6. Depois de deploy confirmado e autorização explícita para custo, executar piloto controlado e medir tempo/custo/qualidade antes de produzir vídeo de 40–50s.

## DIREÇÃO CRIATIVA — NÃO ESQUECER NO FECHAMENTO
O usuário decidiu que o NEXUS será usado principalmente para vídeos faceless cinematográficos. Não colocar Gabriel nas cenas: não há lip-sync no NEXUS e ele ficaria artificial/robótico. Vídeos anteriores com Gabriel tiveram baixo engajamento e davam muito trabalho; isso não prova que o personagem era a causa, mas reforça a mudança de abordagem.
Estilos a desenvolver depois da estabilização:
- Cosmic Cinematic: universo, espaço, luz e escalas monumentais.
- Hypnotic Surrealism: fenômenos visuais fascinantes, fluidos e movimentos orgânicos.
- Mystical Realism: mistério, espiritualidade e simbolismo.
- Quantum Visuals: visualizações conceituais, sem apresentar metáforas como fatos científicos.
- Emotional Cinematic: histórias humanas e transformação.
- Philosophical Documentary: conhecimento, livros e reflexão.
Três funções editoriais: Atrair (impacto visual e hook), Conectar (narrativa e identificação), Converter (livros como aprofundamento, sem propaganda artificial).
Prioridade: cenas hipnotizantes, movimentos orgânicos em todas as cenas, narração de impacto, hooks fortes e retenção. Após estabilizar o NEXUS, estudar retenção e vendas e então revisar as opções de estilos.
Essa pauta deve ser retomada antes de considerar o projeto encerrado.

## ORIENTAÇÃO DE COMUNICAÇÃO
O usuário ficou frustrado com orientações longas/repetitivas e com uma previsão errada sobre o timeout. Ser direto, assumir erros com clareza, não discutir, não mandar reiniciar sem evidência. O usuário não é programador; executar mudanças diretamente no GitHub.


## Regra permanente — atualização de continuidade entre chats
**Obrigatória em toda sessão e após cada etapa concluída:**
1. Sempre que uma atualização, correção, teste, decisão, configuração ou etapa de trabalho for concluída nesta conversa, atualizar imediatamente `docs/CHAT_HANDOFF.md` com o que foi feito, evidências, arquivos/commits envolvidos, resultado e próximo passo exato.
2. Atualizar também `NEXUS_MASTER_STATE.md` quando a mudança alterar arquitetura, decisões, estado técnico, segurança, custos, implantação, validação ou prioridades do projeto. O master state continua sendo a fonte principal do estado do projeto; o handoff registra a linha do tempo e o ponto exato para retomada.
3. Registrar data e horário local de Brasília (America/Sao_Paulo, UTC−03:00) sempre que disponíveis. Se o horário não puder ser confirmado, registrar somente a data e não inventar horário.
4. Separar explicitamente fatos confirmados, evidências observadas, hipóteses e itens pendentes. Nunca transformar uma intenção, instrução ou execução em andamento em tarefa concluída.
5. Depois de gravar, reler os arquivos no GitHub para confirmar que a atualização realmente ficou na branch `main`. Só então informar ao usuário que foi salva.
6. Em novo chat, ler integralmente o master state e o handoff, conferir o estado vivo do GitHub e continuar do último ponto registrado sem repetir etapas concluídas.
7. Não armazenar segredos, tokens, senhas ou valores de credenciais nos documentos; registrar apenas os nomes dos secrets e seu estado de configuração.

## Registro cronológico mais recente
### 16/11/2026 — 14:12:52 (Brasília, UTC−03:00)
- O usuário solicitou que este handoff seja mantido atualizado após cada etapa concluída, com histórico, data/horário e ponto exato para novos chats.
- A regra permanente acima foi adicionada também ao `NEXUS_MASTER_STATE.md`.
- Estado da execução Modal permanece conforme última evidência: run #1, job `deploy`, em andamento aos 30m39s na captura enviada. Não há evidência nova de conclusão nesta atualização.
- Nenhum deploy foi reiniciado, cancelado ou alterado nesta etapa; apenas documentação foi atualizada.

## Pesquisa técnica adicionada — tamanho da revisão LTX pinada (16/11/2026)
- Usuário relatou que o deploy chegou a aproximadamente 37 minutos.
- Consulta à revisão exata fixada em `modal_worker.py` (`a6d59ee37c13c58261aa79027d3e41cd41960925`) no Hugging Face: snapshot listado com aproximadamente **43,8 GB**; diretório `transformer` listado com **7,69 GB**.
- Não confundir com 254 GB da branch atual do repositório, que inclui diversos checkpoints/versões.
- Isso explica por que uma primeira preparação pode demorar bastante, mas não comprova que o job esteja baixando os pesos neste momento. Precisamos dos logs para saber a etapa atual.
- Fontes: https://huggingface.co/Lightricks/LTX-Video/tree/a6d59ee37c13c58261aa79027d3e41cd41960925 e https://huggingface.co/Lightricks/LTX-Video/tree/a6d59ee37c13c58261aa79027d3e41cd41960925/transformer
- Nenhum deploy foi cancelado, reiniciado ou alterado nesta pesquisa.

## Retomada mais recente — correção da seleção de voz (16/11/2026 16:14 BRT)
- O usuário enviou captura do Streamlit com erro vermelho: `list_fish_voices() got an unexpected keyword argument 'self_only'`.
- Também pediu interface mínima: apenas seleção de voz e áudio curto de prévia ao lado; sem busca, filtros, origem, paginação ou metadados.
- Mudanças já gravadas em `main`:
  - `app.py`: removido o argumento `self_only` da chamada para compatibilidade com o módulo antigo carregado no runtime; simplificada a interface para um único selectbox e player de amostra ao lado; removeu filtros e controles adicionais.
  - `nexus/audio.py`: prévia e narração enviam `language=pt-BR`.
  - `tests/test_audio.py`: asserts para idioma `pt-BR` na prévia e na narração.
- Commits mais recentes: `b44cf80`, `cda2a4a`, `c0430e9`, `13d7379`, `fd3a1c0`, `55adafc` (consultar GitHub main para cadeia completa).
- A lista consulta vozes públicas com filtro de idioma `pt`. A normalização TTS usa `pt-BR`; isso não garante sotaque brasileiro em cada modelo, pois o sotaque depende da voz cadastrada.
- Prévia usa sample publicado, se existir; sem sample, aparece botão `▶ Ouvir` que gera áudio curto sob demanda e consome uso da Fish API.
- Estado: código e testes gravados, blocos conferidos por leitura no GitHub. CI e atualização do Streamlit ainda pendentes de confirmação. Não declarar correção implantada até o usuário atualizar/abrir a aplicação e confirmar a tela.
- Próximo passo: observar GitHub Actions automático dos commits e aguardar o Streamlit atualizar; depois pedir ao usuário uma única confirmação visual da seleção compacta e do preview, sem erro vermelho.

- Revisão final de leitura em `main` às 16:15 BRT confirmou: UI sem busca/filtros/paginação; chamada da lista sem `self_only`; player de prévia ao lado do selectbox; payloads TTS com `pt-BR`; asserts correspondentes nos testes. Último commit de UI: `567ba08`.
- A verificação foi estática por leitura dos arquivos no GitHub. A suíte automatizada ainda depende do GitHub Actions; o comportamento visual e a integração real com Fish Audio ainda dependem do Streamlit publicado.

## Retomada — curadoria de vozes naturais brasileiras (16/11/2026 16:24 BRT)
- Usuário pediu adicionar ao app as vozes normais/humanizadas da Fish Audio, sem memes, imitações ou personagens.
- Código gravado na branch main:
  - `nexus/audio.py` commit `5105372`: pesquisa vozes por tags narration, conversational, documentary, professional e neutral; inclui buscas por Letícia e Ricardo; mescla IDs; filtra português brasileiro e estilo natural/profissional; exclui metadados com memes/personagens/figuras públicas.
  - `app.py` commit `322d299`: seletor compacto usa lista curada; player de prévia permanece ao lado.
  - `tests/test_audio.py` commit `efc5b09`: testes de tags, ordenação e filtros positivos/negativos.
- Letícia e Ricardo são as duas vozes Fish Official encontradas com sotaque brasileiro explicitamente descrito na página oficial. Tomás/Rafael e outras vozes padrão não foram incluídas por não haver confirmação de sotaque brasileiro nas descrições consultadas.
- A classificação “natural” depende dos metadados do criador e não substitui ouvir a amostra. Vozes públicas comunitárias podem ter termos/licenças diferentes; verificar direitos comerciais antes de monetizar.
- Próximo passo: observar CI no GitHub e validar lista real e amostras na interface Streamlit. Não afirmar que todas as vozes passaram em audição; não validar sotaque sem ouvir.
- Fontes: https://fish.audio/pt/app/voice-library/ ; https://fish.audio/pt/voice-library/narration/ ; https://fish.audio/pt/voice-library/conversational/ ; https://github.com/fishaudio/fish-audio-go/blob/main/voices.go

## Ponto atual — Streamlit falha com ImportError (16/11/2026)
- Captura mais recente do usuário mostra erro de importação na inicialização do app, na linha `from nexus.audio import generate...` em `app.py`; traceback está cortado e não revela qual nome exato falhou.
- Conferi os arquivos atuais na branch main: app importa `generate_fish_preview`, `list_fish_natural_brazilian_voices`, `make_voice`; os três símbolos existem em `nexus/audio.py`.
- Hipótese a testar: Streamlit Cloud está com commit/árvore de arquivos diferente do main atual ou outra falha de import no ambiente. Ainda sem prova.
- Não fiz alteração de código para este incidente; documentação atualizada para preservar diagnóstico. Não dizer que foi corrigido.
- Próxima ação: pedir ao usuário abrir Manage app → Logs e enviar a mensagem completa da exceção/linha do import. Depois comparar commit implantado e corrigir causa real.

## Correção imediata do ImportError Streamlit — 16/11/2026 — 16:31 BRT
- Captura do usuário mostrava erro de inicialização com traceback apontando para `from nexus.audio import ...` em `app.py`, mas sem revelar o símbolo exato.
- Patch gravado em main: commit `ac84bad`.
- Alteração: removida dependência de import do helper novo `list_fish_natural_brazilian_voices`; app volta a importar somente funções preexistentes `generate_fish_preview`, `list_fish_voices`, `make_voice`. Curadoria passa a ocorrer localmente no bloco UI com a função de listagem existente.
- Hipótese principal: incompatibilidade momentânea entre versão do app.py e do módulo nexus/audio.py durante sincronização/deploy do Streamlit. Não foi possível confirmar a causa exata porque o traceback foi redigido/cortado.
- Próximo passo: aguardar Streamlit sincronizar main e confirmar que a aplicação abre. Se ainda falhar, obter o erro exato dos logs e corrigir com base nele.
- Não declarar validado ainda: somente commit confirmado, sem teste de execução do Streamlit Cloud.

## Ponto mais recente — IndentationError corrigido (16/11/2026 16:30 BRT)
- Usuário enviou captura com `IndentationError: unexpected indent` na variável `excluded_voice_terms` dentro do bloco de curadoria de vozes em `app.py`.
- Causa confirmada: indentação excessiva no bloco dentro de `try:`.
- Correção em main: commit `60693ba`, reindentado bloco de curadoria desde a chamada `list_fish_voices` até a atribuição `voice_page_data["items"]`.
- Pós-commit: arquivo `app.py` relido do GitHub main e bloco visualmente conferido.
- Validação ainda pendente: compilação Python/CI e reinício/reload do Streamlit Cloud. Não declarar app funcionando até confirmação visual.
- Próximo passo: aguardar Streamlit atualizar e testar carregamento; se persistir erro, capturar traceback novo e corrigir causa exata.
- Assumir claramente que o erro de indentação foi introduzido pela alteração anterior; não pedir ao usuário para fazer debugging.

## Retomada — seleção de vozes humanas brasileiras atualizada (16/11/2026 16:45:45 BRT)
- Usuário confirmou que o app voltou a abrir e pediu remover vozes de personagens e priorizar vozes comuns/naturais brasileiras.
- Alterado somente `app.py`, commits `5b9cbc2` e `900f7d3`. Módulo de áudio, geração TTS, prévia e layout compacto não foram alterados.
- O app agora consulta até 3 páginas de 100 vozes em português na Fish Audio, mescla duplicadas e aplica filtro:
  - exclui memes, anime, personagens, imitações, celebridades/figuras políticas, cartoon, paródias e personagens de jogos;
  - exige metadados que identifiquem explicitamente português brasileiro (Brazilian/Brasileiro/pt-BR/Brasil);
  - exclui referências explícitas a Portugal/pt-PT;
  - prioriza metadados de narração/conversa/documentário/profissional/neutro/natural/podcast/entrevista; popularidade é critério secundário.
- Estado: código gravado e relido no main; CI e validação da lista real no Streamlit ainda pendentes. Não afirmar que a lista está visualmente validada até o usuário conferir.
- Próximo passo: aguardar Actions e reload do Streamlit; confirmar se aparecem vozes brasileiras normais com amostras audíveis. Se a lista ficar vazia ou curta, investigar metadados/API Fish Audio antes de relaxar filtro.
- Limitação: “natural” é inferido de descrição/tags; audição das amostras é necessária para validar.

## Retomada mais recente — seletor fixo de vozes brasileiras (16/11/2026 16:45 BRT)
- Usuário mostrou captura com vozes como "NARRADOR DO TODO MUNDO ODEIA O CHRIS", Neymar, Isabela e Waldo, além de campo editável/teclado do celular. A filtragem por palavras era insuficiente e `st.selectbox` abria busca textual.
- Pesquisa da biblioteca Fish Audio confirmou quatro vozes oficiais, desenhadas pela Fish (não clones de pessoas reais) e com metadados pt-BR:
  - Ricardo — `add7bcb8d3c8423bbfa152ca232aad6e`
  - Rafael (Brasil) — `0ffee1af32254090b3630823baade12b`
  - Letícia — `b3c060cc41544a7da94a2c487647c902`
  - Beatriz (Brasil) — `0e26d2df0d0848e3b34099bfb55fd6ea`
- Mudanças gravadas em main:
  - `nexus/audio.py` commit `c2c3e7f`: busca uma voz por ID via `GET /model/{id}`, normaliza sample e valida público/TTS/treinado.
  - `app.py` commit `30f2eab`: substitui selectbox pesquisável por quatro botões de seleção fixos; cada linha tem player de sample ao lado. O teclado/campo digitável foi removido. Não busca vozes da comunidade dinamicamente.
  - `tests/test_audio.py` commit `362a771`: testes de lookup e rejeição de modelo privado.
- Próximo passo: verificar GitHub Actions; aguardar Streamlit atualizar; confirmar que só aparecem quatro vozes e os samples tocam. Não declarar validação visual até confirmação do usuário.
- Fontes oficiais: https://beta.fish.audio/m/add7bcb8d3c8423bbfa152ca232aad6e/ ; https://beta.fish.audio/m/0ffee1af32254090b3630823baade12b/ ; https://beta.fish.audio/m/b3c060cc41544a7da94a2c487647c902/ ; https://beta.fish.audio/m/0e26d2df0d0848e3b34099bfb55fd6ea/ ; https://github.com/fishaudio/fish-audio-go/blob/main/voices.go

## Último erro e correção — ImportError (16/11/2026 17:00 BRT)
- Após substituir seletor, usuário recebeu ImportError na inicialização; captura mostra linha `from nexus.audio import generate_fish...`, mas traceback está cortado e não expõe símbolo completo.
- `app.py` ainda importava `generate_fish_preview`, embora a nova UI use amostras oficiais e não chame essa função. O módulo `nexus/audio.py` no main exporta `get_fish_voice` e `make_voice`.
- Commit `bd54f26`: removido import obsoleto `generate_fish_preview`; ficaram somente `get_fish_voice, make_voice`.
- Hipótese de causa: cache/checkout parcial do Streamlit ou símbolo obsoleto indisponível no runtime; não conclusivo devido ao traceback truncado.
- Pós-commit: arquivos relidos do main e import conferido. CI e reload Streamlit pendentes.
- Próximo passo: aguardar CI e reload. Se houver novo erro, pedir captura completa/abrir logs Streamlit; não fazer alterações adicionais sem traceback.

## Retomada — segundo ajuste ImportError (16/11/2026 17:05 BRT)
- Usuário enviou nova captura que ainda mostra ImportError na linha `from nexus.audio import get_fish_voice, make...`, após o commit `bd54f26`. A mensagem original está redigida/truncada.
- No main, `nexus/audio.py` contém `def get_fish_voice` e `def make_voice`; portanto não foi possível confirmar qual símbolo ou dependência causou o erro. Cache/checkout parcial do Streamlit é hipótese, não fato.
- Commit `a8b5ac9` altera `app.py`: troca import nomeado por `import nexus.audio as fish_audio`; chamadas passam a `fish_audio.get_fish_voice` e `fish_audio.make_voice`. Evita ImportError apenas por símbolo nomeado ausente em módulo antigo.
- Pós-commit, leitura confirmou nenhum `from nexus.audio import ...`, módulo importado e chamadas qualificadas.
- CI/Streamlit ainda pendentes. Se falhar novamente, capturar logs completos do Streamlit Cloud e identificar exceção raiz antes de alterar mais código.

## Retomada — Fish Audio voice catalog não carregava (16/11/2026)
- Captura do usuário: app abre, mas mostra "Não foi possível carregar as vozes oficiais brasileiras da Fish Audio."
- Diagnóstico de código: helper `get_fish_voice()` aceitava apenas `visibility="public"`; documentação Fish Audio reconhece `public`, `unlist`, `private`. Modelos oficiais podem ser unlisted e acessíveis pelo ID direto; código anterior rejeitava-os.
- Correções em main:
  - `nexus/audio.py` commit `9bb4bf0`: aceita public/unlist, rejeita private.
  - `app.py` commit `ab4e097`: se catálogo vazio, tenta de novo a cada rerun; guarda erro por nome da voz e mostra diagnóstico resumido, em vez de ocultar todas as exceções.
  - `tests/test_audio.py` commit `6dd71be`: teste novo de aceitação unlist, mantendo teste de rejeição private.
- Leitura pós-commit confirmou os três comportamentos no main. CI e validação real do Streamlit ainda pendentes.
- Próximo passo: aguardar deploy, conferir se as vozes carregam; se falhar, o caption de diagnóstico agora deve indicar exatamente quais IDs/erros retornaram. Não voltar a alterar código sem essa evidência.
- Referências: https://github.com/fishaudio/docs/blob/main/api-reference/endpoint/model/get-model.mdx ; https://beta.fish.audio/m/add7bcb8d3c8423bbfa152ca232aad6e/

## Ponto mais recente — catálogo Fish Audio sem get_fish_voice (16/11/2026)
- Captura do usuário trouxe diagnóstico exato: `module 'nexus.audio' has no attribute 'get_fish_voice'` para Ricardo, Rafael, Letícia e Beatriz.
- O arquivo atual `nexus/audio.py` em main contém a função, mas o módulo em memória do Streamlit não. Evidência aponta para módulo Python obsoleto retido no processo/cache ou caminho diferente; causa exata entre essas possibilidades ainda não determinada.
- Commit `ea7fa5a` em `app.py`: recarrega explicitamente o módulo com `importlib.reload(fish_audio)` após import; verifica a existência de `get_fish_voice`; se faltar, mostra caminho real do módulo em erro explícito.
- Verificação pós-commit: app.py relido de main; reload, guard e chamada confirmados. A consulta de workflow runs não retornou runs porque o wrapper só lista runs disparadas por pull request; CI geral não validado.
- Próximo passo: aguardar Streamlit sincronizar e verificar se as quatro vozes carregam. Se não, usar o caminho do módulo exposto no erro para identificar import path/checkout divergente; não alterar mais a API Fish ou IDs sem evidência.

## Última atualização — Modal LTX worker deploy confirmado (16/11/2026 17:15 BRT)
- Usuário informou que deploy LTX terminou. Conferido via GitHub Actions.
- Modal deploy workflow #1 ID `43909635680`, commit `82ab49d7fe50c8e16d78c4a3e3b08c40ae8a1a5b`: completed/success. Job #133447708054, todos steps success.
- Logs finais confirmam container images construídas, função `Inference.*` criada e `App deployed in 95.955s`. Modal app: https://modal.com/apps/porraloca42-stack/main/deployed/nexus-video-i2v
- Implementado e implantado: worker LTX em Modal.
- Ainda não testado: inferência GPU H100, download dos pesos LTX, primeira geração I2V e qualidade do clipe. Deploy sozinho não dispara inferência.
- Renders #6 e #7 passaram e produziram artifacts, mas são anteriores ao deploy Modal, então não provam LTX I2V.
- Próximo passo: teste controlado de uma cena/curta duração, checando custo e logs, após confirmar créditos/spend limit; depois vídeo integral.

## Preparação do primeiro teste real LTX — 16/11/2026 17:25 BRT
- Usuário autorizou prosseguir com a validação do LTX até concluir.
- Revisão técnica do worker identificou necessidade de persistir os pesos baixados no Modal Volume. Em `modal_worker.py`, commit `25f5616`, adicionado `model_cache.commit()` após carregar o pipeline. Também foi alinhado `frame_rate=24` e `guidance_scale=3.0` na chamada de inferência.
- Criado `scripts/modal_smoke_test.py` (commit `830b602`): gera imagem sintética de referência, chama o worker remoto para um único clipe de 2s, valida payload, resolução, duração e MP4 via FFprobe, grava MP4 e relatório JSON.
- Atualizado `.github/workflows/modal-deploy.yml` (commit `d627bd1`): timeout 60 min; instala Modal/Pillow/FFmpeg; após deploy executa smoke test GPU; publica MP4 e relatório como artifact de 3 dias.
- Atualizado `.github/workflows/tests.yml` (commit `8b5f1fa`) para compilar scripts junto com app/nexus/worker.
- CI encontrou falha preexistente em teste de voz: expectativa textual desatualizada ("não está publicada") vs mensagem atual ("é privada e não está disponível"). Corrigido teste em `tests/test_audio.py`, commit `5b8e650`. CI run #527 ainda em andamento no momento deste registro; runs #521–#526 falharam antes da correção ou estão em progresso com versões anteriores. Aguardar run #527.
- O smoke test ainda NÃO foi executado; requer disparar manualmente o workflow Modal Deploy (Run workflow) no GitHub. O conector GitHub disponível permite leitura/edição e logs, mas não oferece ação de workflow_dispatch. Não afirmar inferência validada até o workflow rodar e o artifact ser inspecionado.
- O smoke test usa imagem sintética: prova pipeline/inferência/export MP4, mas não comprova qualidade editorial com imagens reais do NEXUS. Depois dele, ainda será necessário renderizar um job real curto com Cloudflare e narração e avaliar o clipe visualmente.
- Atenção licença: a revisão do modelo pinada `a6d59ee...` contém pesos LTX-Video 0.9.1 2B e aponta para licença própria LTX Open Weights 0.x, não simplesmente Apache-2.0. A licença inclui condição para entidades com receita anual >= US$10 milhões obterem licença comercial paga e restrições de uso. Antes de monetização em escala/uso comercial por entidade desse porte, validar o enquadramento jurídico. Fontes consultadas: https://huggingface.co/Lightricks/LTX-Video/commit/a6d59ee37c13c58261aa79027d3e41cd41960925 ; https://static.lightricks.com/legal/LTX-Video-Open-Weights-License-0.X.pdf
- Próximo passo imediato: confirmar CI #527; então usuário deve iniciar uma única execução do workflow atualizado em https://github.com/porraloca42-stack/nexus-video-studio-/actions/workflows/modal-deploy.yml. Isso acionará a GPU e poderá consumir créditos Modal; spend limit/créditos devem estar disponíveis. Após sucesso, baixar/inspecionar artifact MP4 + report, então teste real de render completo.

## CI da preparação LTX aprovado — 16/11/2026 17:27 BRT
- GitHub Actions NEXUS regression tests #527, run ID `43948672400`, commit `5b8e650d1e4b234495ea406b9cc1fa8d198ec60a`: `completed/success`.
- Jobs aprovados: unit-tests, remotion-typecheck e commons-live-smoke. O teste unitário anterior falhava apenas por mensagem esperada desatualizada no teste Fish; expectativa corrigida e suite aprovada.
- Isso valida sintaxe/compilação e testes automatizados, não executa o workflow Modal Deploy nem GPU.
- Workflow atualizado de deploy+smoke test está pronto em `.github/workflows/modal-deploy.yml`; aguarda disparo manual pelo usuário. Depois validar artifact e inferência real.
