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
