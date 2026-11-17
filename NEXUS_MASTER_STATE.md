# NEXUS VIDEO STUDIO — CONTEXTO OPERACIONAL

Última atualização: 16/11/2026

## Objetivo
Aplicativo pessoal em nuvem para transformar tema ou roteiro em vídeo vertical 9:16 de aproximadamente 40–60 segundos, com direção contextual por IA, narração, clipes coerentes, edição e exportação MP4. O NEXUS não gera legendas; o usuário as adiciona no editor final.

## Repositório e publicação
- GitHub: https://github.com/porraloca42-stack/nexus-video-studio-
- Branch: main
- Streamlit: https://htykbebk3hceoen5bvopax.streamlit.app/
- App principal: app.py
- Pacote Python: nexus/

## Preferências de produto
- Prioridade absoluta: qualidade audiovisual, narração natural e coerência semântica.
- O diretor deve compreender o roteiro inteiro antes de criar cenas.
- Cada cena deve representar a fala correspondente com ação concreta; evitar stock genérico, slideshows, colagens e repetição de zoom digital.
- Manter um estilo visual coerente por vídeo, mas variar sujeitos, ambientes, enquadramentos, ações e bibliotecas de mídia para evitar monotonia.
- Preferir clipes reais em movimento; preservar o movimento original do vídeo. Geração de vídeo por IA é futura e não deve consumir créditos sem autorização.
- Pesquisar em várias bibliotecas, comparar candidatos por cena e avaliar quadros reais antes de selecionar.
- Alvo inicial: uso pessoal, cerca de 2 vídeos/dia, 40–50 segundos, 720p, 9:16.

## Arquitetura atual — estado do repositório em 16/11/2026
- Interface: Streamlit (app.py).
- Diretor: Gemini API (nexus/director.py), com failover entre modelos textuais compatíveis; produz roteiro, storyboard semântico e contrato `scene_direction` por cena.
- Narração: Fish Audio S2.1 Pro Free como provedor obrigatório (nexus/audio.py); Edge TTS foi removido do pipeline e das dependências. A interface apresenta uma curadoria de até 25 vozes masculinas e 25 femininas de narração em português, com amostras e seleção. Não há busca nem criação/gravação de voz na UI. Não há trilha de legendas no pipeline.
- Motor padrão selecionado na interface: Cloudflare Workers AI FLUX.2 Klein gera keyframes por cena; Modal/LTX-Video I2V anima cada keyframe em clipe MP4; o worker GitHub Actions usa Remotion (`nexus/remote_render_job.py`, `nexus/modal_i2v.py`, `nexus/remotion_renderer.py`, `remotion/`) para compor o MP4 vertical. O pipeline integrado foi validado em smoke test de 2s em 16/11/2026; ainda falta validar produção de 40–50s com Fish Audio.
- Modo alternativo: bibliotecas de vídeo com busca multi-fonte e renderização FFmpeg (`nexus/assets.py`, `nexus/render.py`); preservar o movimento nativo dos clipes.
- O worker padrão depende dos secrets do Streamlit e do repositório GitHub; implantação do Streamlit e credenciais externas precisam ser verificadas separadamente.
- Busca de mídia: Wikimedia Commons sem chave; Pixabay e Pexels somente quando suas chaves estiverem configuradas. Coverr não é considerado fonte ativa/validada.
- Busca multi-fonte por cena, ranking semântico, exclusão de URLs já usadas e shortlist que favorece variedade de provedores já existem. A seleção final inspeciona dois quadros dos candidatos com Gemini.
- Auditoria do MP4 final agora extrai três quadros por cena (início, meio e fim) e os envia agrupados para revisão semântica/temporal. É consultiva; três quadros não equivalem a análise quadro a quadro nem medem optical flow ou lip-sync.
- O render de clipes de biblioteca preserva o movimento real da filmagem e não aplica zoompan artificial por padrão.
- Não presumir parallax real nem animação orgânica de objetos em imagem única.

## Segredos
Nunca armazenar valores de chaves neste arquivo, no GitHub ou em instruções do projeto.
No Streamlit → Manage app → Settings → Secrets, o modo padrão requer:
- `GITHUB_ACTIONS_TOKEN` — autoriza o dispatch e a leitura do workflow remoto.
- `CLOUDFLARE_API_TOKEN` — protege o manifesto/MP4 em trânsito e é encaminhado cifrado para o worker.
- `FISH_API_KEY` — obrigatório para Fish Audio S2.1 Pro Free; não há fallback para Edge TTS. Sem a chave, a produção é interrompida.
- `FISH_VOICE_ID` — opcional, se a conta exigir/usar uma voz específica.
- `GEMINI_API_KEY` e `GEMINI_MODEL = "auto"` — direção e storyboard.
No repositório GitHub → Settings → Secrets and variables → Actions:
- `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_API_TOKEN` — necessários ao Cloudflare Workers AI.
- `CLOUDFLARE_API_TOKEN` também é o segredo de transporte compartilhado com o Streamlit; não registrar seu valor.
- `COVERR_API_KEY` e `PIXABAY_API_KEY` pertencem ao modo alternativo de bibliotecas, quando habilitados; suas integrações ainda precisam de validação individual.
Nunca copiar chaves para arquivos do repositório, logs ou mensagens públicas.

## Estado técnico verificado
- Repositório principal e branch main identificados.
- app.py e nexus/director.py lidos diretamente do GitHub.
- A interface Streamlit e o planejamento de storyboard com Gemini já foram vistos funcionando em capturas do usuário.
- O diretor instrui o modelo a criar no mínimo ceil(duração/5) cenas e prefere ceil(duração/4) ou mais; para 50s, mínimo 10 e meta 12–15.
- O validador rejeita storyboard cuja soma das cenas difere da duração solicitada em mais de 0,75s, cenas acima de 5s ou campos obrigatórios ausentes.
- O usuário mostrou storyboards com soma abaixo do solicitado e uma cena sem voiceover. A geração agora aceita uma primeira soma entre duração escolhida ±5s, solicita uma segunda correção ao Gemini quando a soma sai da faixa ou há voiceover vazio, exige narração preenchida em todas as cenas e então redistribui as durações para fechar exatamente a duração escolhida.
- Render MP4 final ainda NÃO está validado de ponta a ponta.
- Coverr/Pixabay são implementações preliminares; confirmar documentação/API, autenticação, URLs e licenças antes de considerar fontes validadas.
- MCP oficial do Coverr ainda NÃO está integrado ao NEXUS.

## Alterações recentes
- Commit f617fb3: primeira compactação dos detalhes do planejamento.
- Commit f0e0ddf: primeira versão da redistribuição determinística do tempo.
- Commit b518894: tentativa intermediária de tolerância de ±5s; substituída pela regra de duração determinística.
- Commit bf3fe42: nexus/director.py passa a criar o roteiro narrado com extensão proporcional à duração escolhida; divide em cenas e atribui a duração final exata por peso de palavras da narração, ignorando a estimativa temporal do Gemini. Inclui até duas tentativas de correção de voiceover vazio.
- Commit 4caa185: app.py limpa storyboard antigo antes de uma nova tentativa, remove fallback de validação obsoleto e só exibe planejamento quando a soma bate exatamente com a duração escolhida.
- Commit 3b2cab7: app.py reúne interpretação, tese e detalhes de todas as cenas em um único expander recolhido: "Ver planejamento completo". Não há expanders individuais por cena.
- Commit 954c413: nexus/render.py ajusta também os tempos das legendas quando a narração é acelerada/desacelerada para caber na linha do tempo.
- Alterações gravadas na branch main. Ainda precisam ser confirmadas no deploy do Streamlit e testadas no celular.

## Próximas etapas obrigatórias

1. Confirmar que as alterações recentes foram implantadas no Streamlit e testar no celular: um único botão de planejamento, duração exata e abertura/fechamento.
2. Executar um MP4 real de 50s para validar a nova distribuição de duração, o ajuste de áudio e a sincronização de legendas.
3. Estabilizar importação e inicialização do Streamlit; se falhar, ler Logs e corrigir a causa exata.
4. Testar autenticação e busca Coverr com COVERR_API_KEY; confirmar endpoint, autenticação, resposta e URLs reais.
5. Fazer download de um clipe de teste e validar formato, codec e duração.
6. Integrar Pixabay como fallback e respeitar termos, atribuição, cache e limites da API.
7. Criar busca multi-fonte por cena com ranking de candidatos.
8. Implementar avaliação multimodal dos clipes para verificar correspondência com a narração.
9. Renderizar primeiro MP4 real de 40–50s, inspecionar qualidade e só então declarar o pipeline validado.
10. Considerar MCP oficial do Coverr apenas após verificar endpoint, autenticação e ferramentas disponíveis; não confundir MCP no ChatGPT com MCP dentro do app.


## Biblioteca de narração — expansão e organização
- Implementado no código: seletor de vozes dentro de gaveta recolhida por padrão; a tela principal mantém apenas o nome da voz ativa. A busca é enviada por formulário para evitar chamadas à API a cada tecla.
- A biblioteca consulta o endpoint oficial `GET /model` da Fish Audio, com busca por nome, paginação, filtro de idioma português e ordenação por uso.
- Catálogos separados: mais relevantes, mais usadas e vozes privadas da própria conta. A busca local percorre nome, descrição, autor, origem declarada, tags e idiomas dentro dos registros da página carregada.
- Os metadados `licensed`, `source`, autor, descrição, idiomas e tags retornados são preservados e exibidos. A UI alerta para conferir a licença antes de uso comercial. Não usa parâmetros de API de licenciamento que não foram confirmados na documentação pública.
- A gaveta oferece link oficial para Professional Voice Clone no web app Fish Audio; a documentação informa plano pago, ao menos 10 minutos de áudio limpo e verificação/consentimento do titular. Depois de liberada com disponibilidade Platform/API, a voz só aparece no catálogo do NEXUS se estiver disponível pela API e no idioma filtrado.
- Vozes sem amostra publicada agora oferecem geração de prévia sob demanda; o áudio gerado fica em session state durante a sessão e não é gerado automaticamente para todas as vozes.
- Commits: `d52db7d` (metadados/licença no catálogo), `2cabd4b` (gaveta e biblioteca), `fa27503` e `f5f9c73` (busca por formulário e rótulos remotos em texto simples), `3b1904c` (filtros por estilo vocal e timbre indicado).
- Revisão estática no GitHub confirmou os novos parâmetros, as três categorias e a gaveta recolhida. Teste automatizado Python, implantação no Streamlit e teste visual no celular: ainda pendentes.


## Biblioteca de narração — curadoria profissional (16/11/2026)
- Requisito do usuário: remover opção de gravar/criar voz paga da interface; não mostrar personagens, atores, anime, memes ou vozes de entretenimento; apresentar vozes humanizadas para narração em português brasileiro, separadas por sexo, sem busca.
- UI: duas listas masculinas e femininas, até 25 opções por grupo (alvo máximo de 50), com player apenas para amostras já publicadas e botão de seleção. Exibe a origem como "Professional Voice Clone" e/ou "Licenciada pela Fish Audio" quando aplicável. Sem busca, filtros manuais, paginação, catálogo privado, criação/clonagem de voz ou geração paga de prévias.
- Descoberta consulta Fish Audio com tags `male+narration` e `female+narration`, idioma `pt`, ordenação por uso e também consulta `licensed=true`. O OpenAPI oficial confirma esse filtro e os campos `source` e `licensed` em `ModelEntity`; a curadoria inclui somente modelos com `source=pvc` ou `licensed=true`.
- Pagina até cinco páginas de 100 registros por combinação de sexo/origem, interrompendo quando encontra 25 candidatos elegíveis ou termina o catálogo. Mescla PVC e licenciadas, remove duplicados e prioriza licenciadas, depois uso.
- O filtro local exige metadados que indiquem português brasileiro, gênero e narração; exclui metadados associados a personagens, anime, memes, celebridades, atores, filmes e jogos, além de excluir português europeu. Se a API não devolver candidatos suficientes, a lista terá menos de 25 em cada grupo. É curadoria baseada em metadados, não avaliação acústica automática.
- Alterações principais: `3b7cf85` curadoria inicial; `06e921d` UI simples; `746b644` correção do falso bloqueio da palavra narrator; `5d227a8` filtro PVC/licensed; `2c2c3c9` filtro pt-BR; `1a2dd99` remoção de prévias pagas sob demanda; `eed0c85` paginação; `5e1ef06` rótulos de origem; `26b285f` correção do teste de paginação.
- CI #574, #576, #577, #578, #579, #580, #581, #584, #585, #586 e #588 passaram integralmente (unit-tests, Remotion typecheck e Commons smoke). CI #588 executou 88 testes e passou. A tentativa intermediária #587 falhou por fixture de teste que simulava uma página vazia com total maior que 100; a fixture foi corrigida em #588, sem alteração no comportamento de produção.
- Implementação e CI estão validados no GitHub main. Ainda não foi possível consultar a biblioteca autenticada com o FISH_API_KEY dos Streamlit Secrets nem ouvir as amostras reais neste ambiente. Implantação visual na Streamlit Cloud, quantidade efetiva de 40–50 vozes e qualidade perceptiva continuam pendentes de validação na app publicada.

## Regras para o assistente em novos chats
- Começar lendo este arquivo e o código relevante no GitHub antes de propor mudanças.
- Tratar este documento como registro de continuidade, mas conferir o estado atual do repositório e deployment; pode ficar desatualizado.
- Fazer alterações diretamente no repositório usando a integração GitHub disponível.
- Fazer uma mudança coerente por vez; não instruir o usuário a editar código.
- Dar instruções curtas, uma ação de cada vez.
- Distinguir claramente: implementado, implantado, testado e validado com MP4.
- Não pedir para o usuário repetir contexto documentado.
- Não afirmar conexão em tempo real com Streamlit, logs ou execução do app se isso não estiver disponível.

 
## Correção de duração e interface — 16/11/2026
- Implementado no código: o tempo solicitado é distribuído entre as cenas existentes quando o total retornado pelo Gemini diverge. O algoritmo preserva pesos relativos das durações originais, limita cada cena a 2–5s e garante soma exata quando há cenas suficientes.
- Teste do algoritmo com o caso real de 43s/12 cenas → 50s: passou; resultado soma 50s e cada cena fica entre 4 e 5s.
- Testes adicionais passaram para 40s/12 cenas, 50s/10 cenas e 60s/12 ou 15 cenas.
- Interface alterada para um único expander recolhido contendo direção audiovisual e todas as informações das cenas.
- Legendas SRT são retimadas pelo mesmo fator aplicado ao áudio; teste com 43s de áudio ajustado para 50s passou.
- Não foi executado Streamlit, Gemini, Coverr ou FFmpeg neste ambiente. Portanto, as alterações estão implementadas e commits confirmados no GitHub, mas implantação, integração real e MP4 final ainda NÃO estão testados/validados.

 
## Tolerância do diretor e reparo de narração — 16/11/2026
- Commit b518894 implementa margem de ±5 segundos na soma inicial de duração retornada pelo Gemini.
- Se a soma inicial sair da faixa ou qualquer cena vier sem voiceover, o diretor faz uma segunda chamada de correção com o roteiro original, o storyboard e os problemas detectados.
- Se a segunda chamada continuar sem narração ou fora da margem, o planejamento é interrompido com erro claro; não permite seguir com cena sem fala.
- Se o storyboard corrigido estiver dentro da margem, o sistema ajusta proporcionalmente as durações para fechar exatamente a duração escolhida pelo usuário.
- Teste isolado da distribuição: 50s/12 cenas a partir de estimativa de 44s, 50s/10 cenas, 40s/12 cenas e 60s/15 cenas fecharam exatamente o alvo, com cenas entre 2 e 5 segundos.
- Não houve chamada real ao Gemini nem renderização de MP4 neste ambiente. Código implementado no GitHub; deploy e fluxo real ainda aguardam validação.

 
## Roteiro dirigido pela duração e eliminação de storyboard antigo — 16/11/2026
- Commit bf3fe42: o Gemini recebe a duração como requisito editorial, gera narração com aproximadamente 2,2–2,5 palavras por segundo (50s ≈ 110–125 palavras), e cria cenas em cima da progressão do roteiro.
- As durações retornadas pelo Gemini são apenas estimativas e não determinam a duração final. O código distribui o tempo solicitado usando a quantidade de palavras de cada fala, com clipes de 2–5s e soma exata.
- Para narrações vazias, o diretor tenta duas correções completas. Se ainda houver cenas sem fala, interrompe com erro explícito.
- Commit 4caa185: o app apaga resultados anteriores antes de começar um novo planejamento. Isso evita que um storyboard antigo de 44s permaneça visível caso uma nova tentativa falhe. Também valida a soma exata antes de mostrar o novo plano.
- Teste isolado do algoritmo de duração: 50s/12 cenas, 50s/10 cenas, 40s/10 cenas, 60s/15 cenas e 50s/15 cenas fecharam exatamente o alvo, com cada cena entre 2 e 5 segundos.
- Limitação: não houve chamada real ao Gemini nem deploy/execução Streamlit neste ambiente. O código está no GitHub; a geração real e o MP4 ainda precisam ser confirmados após a implantação.

 
## Resiliência do Gemini — 16/11/2026
- Evidência do usuário: a interface mostrou "Falha no Gemini (HTTP 503)" ao solicitar novo planejamento.
- Diagnóstico: a implementação anterior fazia uma única chamada ao modelo selecionado e tratava 503 como erro fatal. A duração do roteiro não causou esse erro.
- Commit 05e2311: nexus/director.py agora consulta modelos compatíveis, tenta cada modelo com até duas tentativas para erros transitórios (429, 500, 502, 503, 504 e falhas de conexão) e faz failover para até cinco modelos compatíveis.
- Erros de autenticação (401/403) e erros de requisição não transitórios continuam explícitos; se todos os modelos estiverem indisponíveis, a interface apresenta uma mensagem clara para tentar novamente.
- O failover preserva o mesmo prompt e a duração escolhida; não troca o pedido do usuário nem usa um storyboard antigo.
- Estado: código gravado no GitHub. Ainda não houve chamada real ao Gemini após o commit nem validação do deploy Streamlit. O erro 503 deve ser retestado no app publicado.

- Commit 944d99e: corrigidos escapes no parser da resposta JSON do Gemini, preservando a separação de blocos de texto e a limpeza de cercas Markdown após a chamada com failover.
- Revisão estática no GitHub confirmou os escapes corretos no trecho de parsing. Não há status de CI/checks reportado para o commit 05e2311; validação de execução Python e chamada real Gemini ainda pendentes.


## Correção de seleção de modelos Gemini — 16/11/2026
- Evidência do usuário: HTTP 400 no modelo `gemini-3.8-flash-lite-tts`, com mensagem `Developer instruction is not enabled for this model`.
- Causa confirmada no código: `discover_models()` ranqueava modelos apenas por `generateContent`; um modelo especializado em TTS podia vencer o ranking Flash Lite, embora o diretor envie `systemInstruction` e espere JSON textual.
- Commit 941e874: modelos TTS, áudio nativo, imagem e vídeo são excluídos da seleção do diretor. Se a API ainda devolver um erro 400 específico de incompatibilidade com developer/system instruction, o diretor registra o modelo como incompatível e tenta o próximo modelo textual compatível, em vez de abortar.
- Não foi possível fazer chamada real ao Gemini neste ambiente. Código atualizado no GitHub; implantação e validação ponta a ponta dependem do Streamlit carregar o commit e de uma chamada real.


## Investigação do erro persistente de modelo Gemini — 16/11/2026
- O usuário repetiu o erro HTTP 400 citando `gemini-3.8-flash-lite-tts` depois do commit 941e874. Isso demonstra que o runtime acessado ainda não refletia a correção anterior; não é prova de que o filtro atualizado tenha sido executado.
- Revisão da seleção encontrou outro defeito: quando `GEMINI_MODEL` apontava para um modelo filtrado/incompatível, o fallback preservava o primeiro item na ordem arbitrária retornada pela API, em vez de ranquear todos os modelos textuais compatíveis.
- Commit 2408b59: corrigido o fallback; quando o modelo configurado não existe entre os modelos textuais compatíveis, todos os candidatos são ordenados pela classificação de capacidade/estabilidade. A preferência configurada só é mantida se for compatível.
- Commit b1e6816: alterado também `app.py` para incluir no expander de diagnóstico a identificação `NEXUS-2026.11.16-model-guard-2`. Isso permite confirmar visualmente se o Streamlit carregou o novo commit e separa problema de implantação de problema de configuração.
- Commits confirmados no branch `main`. Ainda não houve acesso ao ambiente Streamlit publicado nem chamada real à API Gemini; portanto, deploy e execução permanecem pendentes de validação.


## Correção de validação semântica — 16/11/2026
- O usuário confirmou que o erro de modelo Gemini deixou de aparecer; o novo erro foi de validação: "Cena 10: justificativa semântica superficial". Isso indica que o diretor já respondeu e o storyboard chegou à validação.
- Causa encontrada em `nexus/director.py`: a validação rejeitava qualquer justificativa com menos de 35 caracteres, sem etapa de reparo semântico, embora o prompt não definisse extensão mínima nem houvesse recuperação específica.
- Commit 89c5cfe: adicionado reparo focado nas cenas com justificativa abaixo de 80 caracteres. O diretor recebe a fala e os elementos visuais daquela cena e tenta explicar a correspondência concreta; narração, ordem e duração não são alteradas. Se a explicação continuar curta ou a chamada de reparo falhar, é criada uma justificativa de apoio usando exclusivamente fala, ação, ambiente e sujeitos já presentes na própria cena, evitando abortar todo o planejamento por concisão textual.
- A validação agora exige justificativa de pelo menos 80 caracteres; o fluxo tenta corrigir antes de validar.
- Commit a0942be: identificador visual atualizado para `NEXUS-2026.11.16-semantic-repair-1`.
- Testes locais executados no trecho do reparador: sintaxe Python aprovada; teste de fallback confirmou justificativa acima de 80 caracteres e preservação de fala/ação da cena.
- Ainda pendente: confirmar o novo identificador no Streamlit publicado e testar uma solicitação real de planejamento. Deploy e validação end-to-end não estão confirmados.


## Correção do painel após planejamento — 16/11/2026
- Evidência do usuário: a interface confirmou "Roteiro criado: 11 cenas · 50s, conforme solicitado" e exibiu o planejamento, mas em seguida lançou `KeyError` ao renderizar a caixa informativa da estimativa.
- Causa confirmada: `nexus/director.py` grava `duration_adjustment.ai_estimated_seconds`, enquanto `app.py` tentava acessar a chave inexistente `adjustment['original_seconds']`. O storyboard e a soma de 50s já tinham sido produzidos corretamente; a falha era exclusivamente na apresentação do detalhe da estimativa.
- Commit 44f6918: corrigido o acesso para usar `ai_estimated_seconds`, mantendo fallback compatível com registros antigos que contenham `original_seconds`.
- Commit 5e545f9: build atualizado para `NEXUS-2026.11.16-plan-ui-keyerror-fix-1`, para facilitar a confirmação da versão no Streamlit.
- Validação estática: confirmado que o produtor e o consumidor usam agora a mesma chave; o acesso antigo direto foi removido. A mensagem de sucesso e o painel de cenas não foram alterados.
- Estado: correção gravada no branch main do GitHub. Deploy e reteste na interface Streamlit ainda pendentes; não declarar produção validada até o usuário confirmar a abertura do planejamento sem erro.


## Recuperação automática de JSON Gemini — 16/11/2026
- Evidência do usuário: nova tentativa falhou com `finishReason=STOP` e mensagem de JSON incompleto/inválido. O trecho exibido na tela era apenas uma prévia truncada pelo app; não prova por si só que o texto completo do Gemini terminou naquele ponto.
- Causa técnica no fluxo: `_request()` encerrava o planejamento imediatamente quando a resposta não podia ser decodificada como JSON, sem nova tentativa de geração e sem failover para outro modelo. O tratamento anterior só repetia falhas HTTP/conexão.
- Commit 8a09542: ao detectar JSON inválido, o diretor tenta uma segunda geração no mesmo modelo com instrução explícita para reconstruir o JSON completo e conciso; se falhar novamente, segue para os demais modelos compatíveis. Não aceita storyboard incompleto e não exibe conteúdo parcial do roteiro na mensagem de erro.
- Commit 34c5c2d: teste unitário com respostas simuladas verifica duas respostas JSON inválidas no primeiro modelo, retry com instrução corretiva e sucesso no segundo modelo, sem chamadas externas.
- Commit 225adce: identificador visual atualizado para `NEXUS-2026.11.16-json-recovery-1`.
- Pendente: execução do GitHub Actions após os commits, confirmação de implantação no Streamlit e nova geração real via Gemini. A API real não foi chamada neste ambiente; produção MP4 continua não validada.


### Resultado dos testes automatizados — 16/11/2026
- GitHub Actions executou `python -m compileall -q app.py nexus`: sucesso.
- O novo teste `test_retries_malformed_json_then_fails_over_to_next_model`: sucesso. Simula duas respostas inválidas no primeiro modelo, verifica a instrução de retry e confirma recuperação no segundo modelo.
- A suíte geral ainda termina com 1 erro preexistente/fora deste reparo em `tests/test_render.py::test_render_produces_vertical_mp4_with_audio_and_subtitles`: FFmpeg não consegue abrir `subtitles_retimed.srt`. Não atribuir essa falha ao reparo JSON; ela precisa ser investigada em uma etapa própria antes de declarar toda a suíte verde.
- O workflow não está verde; portanto, status técnico atual: compilação e teste unitário específico aprovados, suíte global reprovada por falha de renderização; chamada Gemini real e implantação Streamlit ainda pendentes.


## Correção de compatibilidade Edge TTS — 16/11/2026
- Evidência do usuário: planejamento concluído (10 cenas, 50s) e a produção avançou até "Gerando narração, legendas e montagem", mas interrompeu com `'SubMaker' object has no attribute 'generate_subs'`.
- Diagnóstico: `nexus/audio.py` usava a API antiga do `edge_tts.SubMaker` (`create_sub` + `generate_subs()`). A API atual utiliza `feed(chunk)` e `get_srt()`; a biblioteca não expõe mais o método antigo na versão instalada.
- Commit 18bbe69: atualizado o gerador para usar `feed()` com o evento completo e `get_srt()` quando disponíveis, mantendo fallback para `create_sub()`/`generate_subs()` em instalações antigas. Também aceita eventos WordBoundary e SentenceBoundary.
- Commit e7f9742: CI passa a instalar `edge-tts`, dependência real do módulo de áudio, para que os testes importem e exercitem o caminho de produção.
- Commit faf7461: identificador visual atualizado para `NEXUS-2026.11.16-edge-tts-compat-1`.
- Commit b7b7a19: testes unitários simulam as APIs moderna e legada e verificam gravação de áudio e arquivo SRT.
- Pendente: resultado do GitHub Actions, confirmação do novo build no Streamlit e produção real completa. Ainda não declarar MP4 validado até FFprobe confirmar áudio, vídeo, duração e dimensões.


## Recuperação de busca de clipes por correspondência semântica — 16/11/2026
- Evidência do usuário: storyboard de 12 cenas/50s foi mantido, mas a produção interrompeu informando ausência de clipes para as cenas 4–12.
- Diagnóstico no fluxo: a busca exigia no mínimo duas correspondências de termos da cena em título/descrição dos bancos de stock e encerrava sem recuperação quando o metadado usava sinônimos ou descrições mais curtas. O fluxo tentava consultas principais e alternativas, mas a validação semântica estrita descartava candidatos com apenas uma correspondência.
- Commit b7da40b: adicionada recuperação semântica em duas etapas. Primeiro, mantém a exigência estrita de duas correspondências; depois de esgotar fontes e variantes, aceita apenas candidatos com pelo menos uma correspondência real com termos da cena e relevância mínima. Conteúdo sem qualquer sobreposição continua rejeitado; URLs já utilizadas continuam excluídas.
- Commit e12d2a4: testes atualizados para cobrir recuperação por correspondência parcial e rejeição de stock sem relação semântica.
- Aumento das variantes de busca de quatro para oito, derivadas exclusivamente da consulta específica da cena; sem dicionário temático fixo.
- Pendente: GitHub Actions, implantação Streamlit e novo teste real. A API Coverr/Pixabay não foi chamada neste ambiente; não afirmar que as cenas 4–12 já encontraram clipes nem que o MP4 foi produzido.


## Correções adicionais encontradas na regressão — 16/11/2026
- A inspeção dos logs do GitHub Actions revelou dois defeitos adicionais que impediam a validação global:
  1. `tests/test_audio.py` tinha erro de sintaxe no uso de múltiplos context managers; commit 72a3212 corrigiu o teste.
  2. `nexus/render.py` tinha o padrão regex de timestamps SRT com escapes duplicados e escrevia separadores `\\n` literais, não quebras de linha; commit de correção de renderização antecedente ao teste removeu os escapes duplicados. A fixture do teste também escrevia `\\n` literal; commit 6e209d6 corrigiu a fixture.
- A falha FFmpeg ao abrir `subtitles_retimed.srt` era compatível com a geração de SRT inválido; agora o parser reconhece timestamps SRT e o arquivo retimado é gravado com linhas reais.
- A suíte ainda precisa concluir novamente após esses commits. Nenhuma renderização MP4 real do usuário foi validada.


## Motor multi-biblioteca de clipes — 16/11/2026
- Evidência do usuário: duas tentativas de produção interromperam com várias cenas sem clipes, apesar do storyboard válido. A captura mais recente mostra 10 cenas/50s e ausência de resultados em 8 cenas.
- Causa arquitetural confirmada no código: `search_video_sources()` retornava imediatamente ao encontrar resultados estritos na primeira fonte, sem comparar os candidatos das outras bibliotecas. A implementação tinha Coverr e Pixabay, mas Pixabay dependia de uma chave ainda não configurada. Não havia adaptador Pexels.
- Commit 9cfd951: busca multi-fonte agrega resultados de todas as bibliotecas habilitadas, deduplica URLs e só então classifica o conjunto completo. Uma falha isolada de uma API não impede o uso das demais. A busca foi limitada a duas consultas por fonte/cena para equilibrar cobertura e limites de requisição.
- Commit 9cfd951: criado adaptador Pexels usando o endpoint oficial atual `/v1/videos/search`, orientação portrait, locale pt-BR e seleção de arquivo MP4 com dimensões utilizáveis.
- Commit 88301a7: app lê opcionalmente `PEXELS_API_KEY`, encaminha a chave para as buscas principal e alternativa e aceita qualquer uma das três fontes configuradas. Novo identificador visual: `NEXUS-2026.11.16-multi-source-1`.
- Commit a454780: testes de agregação entre Coverr/Pixabay/Pexels e tolerância a falha isolada de fornecedor.
- Estado de credenciais confirmado no registro: Coverr configurado; Pixabay ainda sem chave; Pexels sem integração anterior e emissão pública de novas chaves pausada conforme página oficial consultada. O adaptador Pexels está pronto no código, mas não operacional até existir uma chave válida.
- Regras de licença: validar os termos do plano/API de cada fornecedor e mostrar créditos exigidos. Não tratar um clipe como liberado para uso comercial só por ser retornado pela API.
- Pendente: resultado do GitHub Actions para estes commits, implantação Streamlit, configurar/validar Pixabay ou Pexels quando possível e executar uma nova produção real. Não afirmar que a cobertura de todas as cenas ou MP4 está garantida.


### Extensão de testes e créditos de mídia — 16/11/2026
- Commit ebdd1e2: teste do adaptador Pexels valida endpoint atual, orientação portrait, escolha MP4 e metadados de autoria/URL da fonte.
- Commit ebdd1e2: teste garante que URLs repetidas entre fornecedores sejam deduplicadas antes do download.
- Commit fd797bc: produção passa a preservar provedor, página do clipe e autor quando fornecido; a interface exibe créditos das bibliotecas usadas após o vídeo ser produzido.
- A execução do CI para estes commits ainda está pendente no momento deste registro. Confirmar compilação, testes e deploy antes de declarar a mudança validada.


## Credenciais Pixabay e Pexels recebidas — 16/11/2026
- O usuário compartilhou chaves de API do Pixabay e Pexels na conversa. Por segurança, os valores não foram copiados para o GitHub, para este arquivo, para o código ou para logs.
- O código do app já lê `PIXABAY_API_KEY` e `PEXELS_API_KEY` via Streamlit Secrets e os adaptadores das duas bibliotecas já estão no repositório.
- Commit d2ac91c: o painel de diagnóstico foi ampliado para testar cada fonte configurada individualmente: autenticação/busca, download real de um MP4 e leitura técnica por FFprobe. Uma falha de uma fonte não interrompe os testes das outras. O painel não revela nem imprime chaves.
- Novo identificador de build: `NEXUS-2026.11.16-library-diagnostics-1`.
- Ação ainda necessária no ambiente Streamlit: cadastrar as chaves recebidas nos Secrets com os nomes `PIXABAY_API_KEY` e `PEXELS_API_KEY`. Não há ferramenta conectada nesta sessão para gravar diretamente os Secrets privados do Streamlit.
- Após salvar os Secrets, executar no app: Ferramentas avançadas → Testar todas as bibliotecas configuradas. Só marcar Pixabay/Pexels como operacionais depois de confirmar busca, download e leitura MP4.
- Recomenda-se revogar e gerar novas chaves depois de concluir a configuração, pois as credenciais foram compartilhadas em uma conversa. Nunca armazenar valores de chaves no repositório.


## Correção de ImportError no Streamlit — 16/11/2026
- Após publicar o diagnóstico multi-biblioteca, o app apresentou ImportError na linha de importação de `nexus.assets` (captura do usuário).
- A captura não mostra a mensagem-raiz completa; a hipótese mais provável é incompatibilidade temporária entre a revisão do app e a revisão do pacote durante a implantação, pois o app passou a importar diretamente três adaptadores específicos.
- Correção preventiva commit b97318e: removidos os imports diretos dos adaptadores Pixabay/Pexels no `app.py`. O diagnóstico agora chama o ponto de entrada já estabelecido `search_video_sources`, isolando uma fonte por chamada. A importação original e estável de `search_video_sources`, `search_coverr_videos` e `download_file` foi preservada.
- O workflow de CI deve concluir para b97318e antes de considerar a correção testada. A implantação Streamlit e o teste real no navegador ainda precisam de confirmação.


## Compatibilidade de assinatura na busca Pexels — 16/11/2026
- O teste real no Streamlit revelou `search_video_sources() got an unexpected keyword argument 'pexels_key'`, apesar de o arquivo atual `nexus/assets.py` já declarar esse parâmetro.
- Isso confirma divergência entre a versão da função carregada no worker e a chamada feita pelo app; não é evidência de chave API inválida.
- Commit 3133d3b: adicionado `_search_stock_compatible` no `app.py`. A função inspeciona a assinatura carregada: usa a integração central quando há suporte a `pexels_key`; em workers com assinatura antiga, busca Coverr/Pixabay pela interface legada e consulta Pexels diretamente via API, normalizando os resultados para o esquema interno. O diagnóstico e a produção usam o mesmo adaptador.
- CI e teste real no Streamlit ainda pendentes. Não declarar correção validada até produção confirmar busca, download e leitura de MP4.


## Correção definitiva da geração SRT — 16/11/2026
- Evidência do usuário: produção chegou à etapa “Gerando narração, legendas e montagem”, mas interrompeu com `'SubMaker' object has no attribute 'generate_subs'`.
- Causa: a camada de áudio dependia de uma API interna/variável de `edge_tts.SubMaker`; a versão instalada no worker não expunha `generate_subs()`. O código já tentava detectar APIs alternativas, mas o worker executou uma revisão antiga ou incompatível.
- Correção commit pendente: remover totalmente a dependência de `SubMaker`. `nexus/audio.py` passa a coletar eventos WordBoundary/SentenceBoundary do stream e gerar SRT diretamente, convertendo ticks de 100 ns para timestamps SRT, agrupando palavras em legendas curtas. Se o serviço não emitir eventos de tempo, gera legendas aproximadas para que a produção não pare apenas por falta de metadados de sincronização.
- Testes adicionados: geração de MP3/SRT sem SubMaker, fallback por SentenceBoundary e fallback sem eventos de tempo.
- Validação pendente: CI e produção real no Streamlit. A sincronização de fallback sem eventos é estimada, não word-level; a sincronização precisa usa eventos do Edge TTS.


### Ajuste de testes da correção SRT — 16/11/2026
- O primeiro CI da correção de legendas falhou porque o arquivo de testes antigo ainda esperava a implementação anterior baseada em `SubMaker`. A implementação já havia removido essa dependência, mas os testes não foram atualizados de forma consistente devido a commits concorrentes.
- Commit subsequente substitui os testes antigos por testes da implementação efetiva: eventos WordBoundary, fallback SentenceBoundary e fallback sem metadados temporais.
- Até novo CI verde, a correção permanece não validada e não deve ser considerada implantada.


### Revalidação dos testes SRT — 16/11/2026
- O CI do commit `386bc2e` executou 19 testes: 18 passaram e 1 falhou por uma expectativa excessivamente rígida no teste de fallback por sentença (o algoritmo pode dividir uma frase longa em mais de uma legenda para manter legibilidade).
- Ajustado o teste para validar o conteúdo integral, sem impor quantidade fixa de blocos.
- Aguardando nova execução CI. Ainda não há validação do pipeline real no Streamlit.



## Correção da estrutura SRT — 16/11/2026
- Evidência do usuário: a produção já havia gerado vídeo intermediário H.264 vertical de 50s e narração MP3 de 50,69s, mas FFmpeg falhou ao abrir `subtitles_retimed.srt` durante o filtro de legendas.
- Diagnóstico no código: `nexus/audio.py` escrevia separadores de linha como barras invertidas literais seguidas de `n`, em vez de quebras de linha reais. Isso produzia um arquivo que não obedecia à estrutura SRT esperada pelo FFmpeg.
- Commit `2b63e5b`: corrigidas as quebras de linha na escrita dos blocos SRT e nas legendas multilinha.
- Commit `7ee0182`: teste de áudio reforçado para exigir que o arquivo tenha quebras de linha reais e não contenha sequências literais `\\n`.
- Estado: correção e teste gravados na branch main. Ainda aguardam execução CI e nova produção real no Streamlit. O MP4 final ainda não está validado.

- Commit `edebc82`: identificador visual do app atualizado para `NEXUS-2026.11.16-srt-newline-1`, para confirmar que o worker Streamlit carregou a revisão com a correção.


### Validação CI da correção SRT — 16/11/2026
- GitHub Actions run #89 (43818662048) para o commit c16040b concluiu com sucesso.
- Job unit-tests: sucesso; compilação dos módulos da aplicação concluída.
- 19 testes executados em 2,659s: 19 passaram, 0 falharam.
- Incluído teste de integração de renderização FFmpeg que produz MP4 vertical com áudio e legendas em ambiente CI; isto valida a rotina sintética/isolada, não a produção real com mídia e chaves do Streamlit.
- A correção SRT e os testes estão validados no CI.
- Deploy/worker Streamlit ainda não verificado. Próxima confirmação simples na interface: build NEXUS-2026.11.16-srt-newline-1.
- Primeiro MP4 real do usuário ainda pendente; não declarar pipeline de produção concluído.

- Commit 221038e: identificador de build movido para logo abaixo do cabeçalho principal, visível sem abrir ferramentas avançadas. Isso simplifica a confirmação do deploy no celular.


### Ajuste de duração da narração — 16/11/2026
- Evidência do usuário: storyboard de 50s/12 cenas gerou MP3 com 36,1s; o renderizador bloqueou corretamente porque a diferença ultrapassava 15% (áudio 27,8% mais curto que a timeline).
- Causa operacional: a velocidade padrão do Edge TTS resultou em leitura rápida demais para a duração alocada pelo storyboard, apesar do prompt orientar 110–125 palavras para 50s.
- Commit 757025b: Edge TTS passa a sintetizar com rate=-25%, buscando aproximar a narração da duração planejada sem remover a proteção de sincronização do FFmpeg.
- Commit af3230f: teste unitário verifica que a taxa -25% é aplicada ao sintetizador.
- Commit a89c0cc: build identificada como NEXUS-2026.11.16-voice-paced-25, visível abaixo do cabeçalho.
- CI da nova alteração ainda em execução no momento do registro. A taxa precisa ser confirmada com uma nova produção real; não afirmar MP4 final concluído.


### Correção de arquitetura: roteiro calibrado pela voz real — 16/11/2026
- Feedback explícito do usuário: não desacelerar a voz para preencher duração. A IA deve construir e revisar o roteiro para a duração escolhida, usando ritmo natural.
- Revertida a alteração experimental de Edge TTS em -25%; o sintetizador voltou a rate=+0% (velocidade natural).
- Commit 3952b10: nova função `revise_narration_for_duration` no diretor. Usa duração real medida do primeiro áudio, contagem de palavras e velocidade efetiva da voz selecionada para pedir ao Gemini uma revisão editorial da narração, mantendo quantidade/ordem das cenas e coerência fala-imagem.
- Commit e911f9c: fluxo de produção mede o áudio com ffprobe e pode solicitar até duas revisões automáticas; sintetiza novamente em velocidade natural. Só segue quando a duração fica dentro de 10% da meta. Se não conseguir, interrompe com mensagem clara, sem forçar velocidade nem exportar narração inadequada.
- Commit 6deae2a: velocidade natural restaurada.
- Testes adicionados para calibragem da narração e preservação de cenas; CI aguardando conclusão.
- Build de teste: `NEXUS-2026.11.16-voice-script-calibration-1`.
- Estado: código enviado; ainda não validado pelo CI nem em produção real. Não considerar o MP4 concluído.


### Diretor profissional: retenção, CTA e SEO semântico — 16/11/2026
- Requisito do usuário: assunto/roteiro + estilo visual + duração do painel devem ser o briefing completo para a IA entregar conteúdo profissional, incluindo hook, retenção, CTA e SEO.
- Commit d00397b: ampliado o SYSTEM do diretor Gemini com regras editoriais para hook nos primeiros segundos, progressão de retenção, narrativa falada natural, estrutura com payoff e CTA contextual, sem empilhar pedidos.
- SEO semântico: palavra-chave principal/secundárias, integração natural no roteiro, título, descrição e hashtags fiéis ao conteúdo; proíbe keyword stuffing e clickbait enganoso.
- Contrato JSON ampliado com hook, retention_strategy, cta e seo (primary_keyword, secondary_keywords, title, description, hashtags).
- Commit 822c8c2: painel do storyboard exibe estratégia editorial e pacote SEO para revisão.
- Commit bffb6fb: corrigidos placeholders de duração e contagem de palavras no prompt do diretor.
- Teste específico criado em tests/test_professional_director_brief.py.
- Build indicado na interface: NEXUS-2026.11.16-professional-director-1.
- CI do novo diretor ainda em execução após os commits mais recentes. Implantação Streamlit e geração MP4 real ainda não confirmadas.


### Pontuação expressiva para interpretação vocal — 16/11/2026
- Requisito do usuário: a narração deve usar pontuação que oriente a entonação do sintetizador e produza cadência mais humana, sem reduzir artificialmente a velocidade da voz.
- Commit 56f444c: ampliado o SYSTEM do diretor com regras explícitas para vírgulas (continuidade/respiração curta), pontos (fechamento/queda), dois-pontos (preparação de revelação), travessões (aparte/contraste), interrogações e exclamações moderadas, reticências apenas quando semanticamente justificadas.
- Orientada a variação de frases curtas, médias e longas; leitura mental em voz alta; ênfase lexical sem excesso de caixa alta ou pontuação decorativa.
- Revisão de duração também recebeu instrução para preservar/refinar pontuação expressiva e nunca inserir pausas artificiais ou apagar sinais relevantes.
- Commit caea92d: testes cobrem as regras de pontuação e cadência vocal.
- Commit 5d5f5c0: build identificada como NEXUS-2026.11.16-human-voice-punctuation-1.
- CI dos commits de pontuação ainda em execução no momento do registro. Deploy Streamlit e qualidade perceptiva da voz ainda dependem de teste real; pontuação orienta a prosódia do TTS, mas não garante interpretação humana perfeita por si só.


### CI aprovado: pontuação expressiva e cadência vocal — 16/11/2026
- GitHub Actions run #113 (43821464546), commit 5d5f5c0: concluído com sucesso.
- Job unit-tests: sucesso; 23 testes executados em 2,582s, incluindo os testes de pontuação/entonação e requisitos editoriais.
- Run #112 (43821459374), commit caea92d: sucesso; 23 testes executados.
- Run #111 (43821455227), commit 56f444c: sucesso; 23 testes executados.
- Código e testes da orientação de pontuação expressiva validados pelo CI.
- Build esperado na interface: NEXUS-2026.11.16-human-voice-punctuation-1.
- Ainda não foi feita avaliação auditiva da voz TTS nem confirmado um MP4 real renderizado com a nova versão. CI verde não equivale a validação perceptiva ou validação de produção.


### Correção de inicialização Streamlit após ImportError — 16/11/2026
- Evidência do usuário: Streamlit não iniciou; traceback aponta para linha 5 de app.py ao importar `revise_narration_for_duration` de `nexus.director`.
- Verificação no GitHub: a função existe no módulo atual (definida em linha 567); app.py fazia import antecipado no topo. O cenário é compatível com worker Streamlit usando módulo desatualizado durante atualização/reinício.
- Commit b689070: removida a importação antecipada do calibrador; agora ele é importado no ponto de uso, com mensagem de erro operacional clara caso o worker esteja com módulo antigo. Build: `NEXUS-2026.11.16-import-guard-1`.
- Commit 1545831: criado teste para garantir que o calibrador não seja importado durante o startup e que a importação tardia esteja protegida.
- CI run #116 em execução no momento do registro; run #117 enfileirado. Ainda não confirmado deploy Streamlit nem startup real após reinício.


### Primeiro MP4 revisado: qualidade visual e legendas — 16/11/2026
- Primeiro vídeo real recebido: 50s, 720×1280, H.264 + AAC. Revisão visual por amostragem de frames em 0s, 5,4s, 10,9s, 16,3s, 21,8s, 27,2s, 32,7s, 38,1s, 43,6s e 49s.
- Problemas observados: clipes sem relação visual direta clara com a narração (incluindo água/copo, ambiente tecnológico e paisagens genéricas); seleção parecia depender demais dos metadados da biblioteca. Legendas excessivamente grandes e empilhadas no centro, prejudicando a imagem.
- Não é possível afirmar apenas pelo MP4 se só a chave Pixabay estava configurada. O pipeline pesquisa todas as bibliotecas que tenham chave nos Secrets; foi incluído aviso visível quando apenas uma fonte estiver configurada.
- Commit 5cebae6: shortlist de candidatos prioriza comparar pelo menos um resultado de cada biblioteca configurada antes de repetir um provedor.
- Commit e6e6570: adicionada avaliação visual multimodal Gemini por cena. O NEXUS baixa até 3 candidatos, extrai dois frames representativos de cada clipe e pede ao Gemini comparar imagem real com narração, ação, sujeitos e ambiente. Só aprova com confiança mínima; rejeita todos se nenhum representar a cena. Falha de revisão não cai silenciosamente para escolha aleatória.
- Commit 9ca4921: integração da revisão visual no pipeline de produção, com tratamento de falhas por candidato e progresso dedicado à avaliação.
- Commit 142d486: corrigida importação Path usada pela avaliação visual.
- Commit 98be254: legendas reduzidas de FontSize 17 para 12, contorno menor e posicionamento inferior com margem de segurança (170px).
- Commits f9488a6, c0752ba, 5762632, f4b9b1c, 449a19e e 864f0a4: agrupamento de legendas em frases curtas de até 4 palavras, máximo de duas linhas, sem empilhar cues; correções de newline real e intervalos de fim de cue.
- Commit 1777448: shortlist diversificada testada. Commit 8640d6e: testes da avaliação visual Gemini. Commit d7e3eb4: testes de legendas curtas.
- Commit 0579667: painel passa a mostrar confiança média e justificativa da revisão visual por cena; build `NEXUS-2026.11.16-visual-review-subtitles-4`.
- CI das alterações finais ainda em execução; primeiras execuções identificaram falhas nos testes de legenda e importação Path, que foram corrigidas nos commits seguintes. Não declarar a nova versão validada até CI verde e nova produção real.


### CI verde: revisão visual Gemini e novo layout de legendas — 16/11/2026
- GitHub Actions run #139 (43823404090), commit d7e3eb4: sucesso.
- Job unit-tests: 29 testes executados em 2,285s; resultado OK.
- Inclui teste de shortlist diversificada entre bibliotecas, teste de legendas curtas em até duas linhas e testes de seleção/rejeição de candidatos pela avaliação visual Gemini.
- Run #140 (842939c, atualização do estado mestre): também concluído com sucesso.
- Build atual indicado no app: `NEXUS-2026.11.16-visual-review-subtitles-4`.
- Código e testes validados pelo CI. Ainda falta deploy/refresh real do Streamlit e um segundo MP4 para validação audiovisual da nova seleção de clipes e do layout das legendas.


### Seleção de mídia orientada primeiro pela narração — 16/11/2026
- Requisito confirmado pelo usuário: escolher sempre o clipe com maior conexão real com o trecho narrado; estilo visual e qualidade técnica nunca podem superar a correspondência narrativa.
- Alteração implementada no código: consultas de conteúdo da cena e de estilo visual são separadas. Cada biblioteca habilitada recebe a busca semântica da cena e uma busca adicional pelo estilo; resultados que só correspondem ao estilo não passam pelo filtro semântico.
- Ranking textual passa a ordenar por relevância da narração/ação primeiro, aderência ao estilo como critério secundário e qualidade técnica como terceiro critério. A shortlist compara até seis candidatos, priorizando diversidade entre bibliotecas antes de repetir uma fonte.
- Avaliação Gemini recebe todos os candidatos da shortlist e os quadros reais; instrução explícita determina pontuação separada para conexão narrativa e aderência estética, escolhendo primeiro a maior conexão com a narração. Confiança mínima continua impedindo clipes sem relação direta.
- Interface de revisão registra e exibe conexão semântica e aderência ao estilo por cena. Build: `NEXUS-2026.11.16-narration-first-selection-1`.
- Testes adicionados: relevância semântica vence correspondência apenas estética; busca de estilo é independente e não aceita resultados sem conexão com a cena; avaliação visual expõe a prioridade semântica.
- Estado: alterações gravadas no GitHub; aguardando CI. Não confundir implementação com deploy no Streamlit nem validação audiovisual com MP4 real.


### Correção de recuperação de candidatos: busca semântica antes da revisão visual — 16/11/2026
- Evidência do usuário: produção percorreu 10/10 cenas e encerrou com "Não encontrei clipes para as cenas [1..10]". Isso indica conclusão do laço de busca, não conclusão da renderização. A tela não mostrava erro de API; a etapa não chegou à montagem/narração/MP4.
- Revisão do código identificou um gargalo arquitetural: os resultados retornados pela própria busca específica da cena eram descartados quando título/tags da biblioteca não repetiam palavras do briefing. Isso bloqueava candidatos antes da análise dos quadros reais pelo Gemini, especialmente quando metadados usam sinônimos ou outro idioma.
- Correção em `nexus/assets.py`: candidatos retornados por consultas de conteúdo da cena agora seguem para a avaliação visual; resultados obtidos somente pela consulta estética continuam bloqueados, salvo se metadados também indicarem conexão com a cena. O Gemini permanece responsável por aceitar/rejeitar os quadros reais, mantendo a confiança mínima.
- `app.py`: detalhes de falha agora mostram consulta de conteúdo, estilo solicitado e bibliotecas efetivamente configuradas; build atualizado para `NEXUS-2026.11.16-narration-first-selection-2`.
- Testes atualizados para garantir que candidatos da busca semântica cheguem ao revisor visual e que resultados somente estéticos não preencham a cena.
- Commits: `4172678` (recuperação de candidatos), `e95818f` (ordenação antes do filtro), `3422599` (testes), `ec9574c` (diagnóstico e build).
- Estado: código gravado no GitHub; CI desta correção aguardando. Não há evidência suficiente para afirmar qual biblioteca ou consulta específica falhou na execução do usuário, pois o painel de detalhes da captura não está expandido. Deploy/refresh Streamlit e MP4 de validação continuam pendentes.


### Ajuste dos testes da recuperação de candidatos — 16/11/2026
- A primeira execução CI da correção detectou dois testes antigos que ainda esperavam rejeição apenas por metadados; esses testes foram substituídos por cobertura do novo contrato: consulta de cena entrega candidatos à inspeção visual e consulta apenas estética não libera clipes sem evidência semântica.
- A execução seguinte detectou um fixture incompleto no teste de estilo: a função faz duas variantes de consulta de cena antes da consulta de estilo. Fixture corrigido no commit `c7ea142`, com três respostas simuladas na ordem real.
- CI run #155 (43825816807) estava em execução no momento deste registro; resultado ainda não confirmado.
- Correção de produção permanece no build `NEXUS-2026.11.16-narration-first-selection-2`. Não declarar validado até CI verde e teste real.


### CI verde: recuperação de candidatos e prioridade semântica — 16/11/2026
- GitHub Actions run #155 (43825816807), commit `c7ea142`: concluído com sucesso.
- Job `unit-tests`: 31 testes executados em 2,114s; resultado `OK`. Inclui testes de passagem de candidatos da consulta de cena para revisão por quadros e bloqueio de resultados exclusivamente estéticos sem evidência semântica.
- Código de recuperação de candidatos e testes está validado pelo CI.
- Build `NEXUS-2026.11.16-narration-first-selection-2`.
- A atualização documental mais recente (run #156) ainda estava na fila no momento deste registro.
- Estado operacional: código e testes validados; implantação Streamlit não confirmada; produção e validação de novo MP4 pendentes. O usuário deve atualizar/reabrir o app após o deploy automático do GitHub e confirmar o build visível antes da nova produção.


### Diagnóstico de falha real em produção e robustez de runtime — 16/11/2026
- Evidência do usuário: todas as cenas falharam na revisão visual com `name 'Path' is not defined`; Coverr retornou HTTP 403 Forbidden nas consultas. O painel também mostrava incorretamente “Bibliotecas consultadas: nenhuma”, porque alguns ramos de falha não preenchiam o campo `sources`.
- Revisão do repositório confirmou que `nexus/director.py` contém `from pathlib import Path`, mas o worker Streamlit em execução não tinha esse símbolo no módulo carregado. A hipótese operacional mais provável é módulo antigo retido em cache/hot reload parcial; a captura não permite provar a causa interna exata.
- Correção incremental: antes da produção, recarregar explicitamente `nexus.director` no worker e usar o módulo recarregado para a revisão visual; diagnóstico passa a mostrar as bibliotecas configuradas mesmo em falhas de download/revisão.
- Busca: erros HTTP 401/403 agora interrompem novas variantes na biblioteca afetada, preservam a tentativa nas demais fontes e exibem orientação para verificar chave/permissões, evitando chamadas repetidas inúteis.
- Build proposto: `NEXUS-2026.11.16-runtime-review-auth-diagnostics-1`.
- Estado: alterações preparadas para CI; ainda não implantadas nem validadas com nova produção. O HTTP 403 do Coverr permanece dependente de conferir a chave/permissão configurada; não foi possível validar segredo do Streamlit a partir do repositório.


### Substituição do Coverr por Wikimedia Commons — 16/11/2026
- Decisão: remover Coverr da produção (plano Demo retorna `Invalid API_KEY` para a chave atual; usuário não quer contratar plano pago) e adicionar Wikimedia Commons como fonte sem chave de API.
- Pesquisa técnica: MediaWiki Action API permite busca de arquivos de vídeo no namespace File; Commons publica vídeos WebM, Ogg Theora e MPEG, que o FFmpeg pode ler. Metadados de licença/autoria são acessíveis por `imageinfo/extmetadata`. Referências: MediaWiki API Search, Commons file types e machine-readable data.
- Adaptador `search_wikimedia_videos`: consulta `filetype:video`, normaliza URLs, dimensões, título, autor e licença; por segurança comercial, aceita somente CC0, domínio público e CC BY (exclui CC BY-SA, NC e ND). Atribuição é preservada nos metadados por clipe.
- App: Coverr removido das fontes ativas e do diagnóstico; Wikimedia Commons fica disponível sem chave; Pixabay e Pexels continuam usando as chaves já configuradas. O diagnóstico inclui busca, download e leitura do vídeo. Build: `NEXUS-2026.11.16-wikimedia-provider-1`.
- Limitação conhecida: Commons não é um stock cinematográfico tradicional; variedade/verticalidade pode ser menor. É fonte complementar e os candidatos continuam sujeitos à inspeção visual do Gemini. A validação de API real e compatibilidade de arquivos depende do deploy e teste de produção.
- Estado: código e testes gravados no GitHub; CI pendente; não afirmar implantação nem validação audiovisual.


### Ajustes de integração Wikimedia Commons — 16/11/2026
- Corrigido o fluxo de produção para ativar explicitamente a busca no Wikimedia Commons tanto na consulta principal quanto na consulta alternativa.
- Removida a condição que bloqueava a produção quando Pixabay e Pexels não tinham chave; Commons é fonte sem chave e deve poder ser testada isoladamente, com aviso de que seu catálogo é complementar.
- Créditos por clipe agora preservam licença, URL da licença, autor e indicação de atribuição; interface apresenta licença e link ao lado da fonte. Isso é necessário para arquivos CC BY e domínio público.
- Testes de diversidade atualizados para tratar Wikimedia Commons como biblioteca ativa.
- Build atualizado para `NEXUS-2026.11.16-wikimedia-provider-2`.
- Estado: CI pendente; ainda não implantado nem validado com chamadas reais ao Commons.


### Substituição do Coverr e endurecimento do provedor Wikimedia — 16/11/2026
- Coverr removido do fluxo ativo de produção; não exigir mais `COVERR_API_KEY`.
- Wikimedia Commons adicionado como provedor sem chave nas buscas principal e alternativa. O adaptador consulta `filetype:video`, lê `imageinfo/extmetadata`, preserva autor/fonte/licença e filtra para CC0, domínio público e CC BY; exclui licenças NC, ND e BY-SA para reduzir complexidade de redistribuição.
- Pixabay e Pexels permanecem integrados por chaves existentes. Commons é fonte complementar; não é catálogo de stock tradicional e a cobertura vertical/anime pode ser limitada.
- Diagnóstico avançado permite testar Commons sem chave, Pixabay e Pexels individualmente. Ajustado o helper para não misturar Commons nas chamadas de diagnóstico isoladas.
- Créditos finais agora incluem autor, URL da fonte e licença do Commons.
- README atualizado para refletir fontes e estado reais.
- Build: `NEXUS-2026.11.16-wikimedia-provider-2`.
- CI run #171 (43827784402) encontrou uma expectativa antiga duplicada no teste de shortlist; teste duplicado removido no commit `3c702e8`. Teste adicional garante que falha do Commons não bloqueie Pixabay.
- CI run #173 (43827844195), commit `d486f57`, ainda em execução no momento deste registro. Não marcar integração como validada até CI verde.
- Código gravado no GitHub; deploy Streamlit e teste real de busca/download/FFprobe ainda pendentes.



## Expansão de bibliotecas gratuitas e direção 9:16 — 16/11/2026
- Implementado em `nexus/assets.py`: o ranking preserva relevância semântica como critério principal e, em caso de equivalência, prioriza vídeo vertical e proporção mais próxima de 9:16 (0,5625), antes da resolução. A proporção e o índice de aderência são registrados no candidato.
- Implementado em `nexus/director.py`: Gemini Vision recebe dimensões/proporção dos candidatos e considera composição/corte vertical 9:16 como critério técnico terciário, sem sacrificar correspondência com a narração.
- Implementado em `tests/test_assets.py`: teste para desempate entre 4:5, 9:16 e paisagem, mantendo relevância semântica.
- Implementado em `app.py`: painel de fontes complementares gratuitas com links e avisos de licença para Mixkit, ISO Republic, Vecteezy, Vidsplay e National Park Service.
- Política de integração: automação apenas por APIs/documentação permitidas. Mixkit proíbe scraping e bots/download em massa; ISO Republic, Vidsplay e NPS não têm API pública de pesquisa de stock verificada; Vecteezy anuncia API gratuita com até 500 downloads/mês, mas a tabela oficial não inclui metadados de recursos no plano gratuito. Por isso, essas fontes ficam em curadoria manual e não são falsamente apresentadas como busca automática.
- Fontes automáticas gratuitas atuais: Wikimedia Commons sem chave (somente CC0, domínio público e CC BY), Pixabay (chave gratuita) e Pexels (chave gratuita, se configurada). Coverr permanece desativado no fluxo porque a credencial do plano Demo não autenticou; não exigir upgrade pago.
- Referências de licença consultadas: Mixkit Free vs Restricted e termos contra scraping; Vecteezy API/pricing e Free License; ISO Republic CC0; NASA excluída da seleção comercial automática por direitos de terceiros e restrições de uso promocional.
- Commits desta etapa: `0f67aed` (ranking 9:16), `a8259b3` (teste), `31b9b9e` (direção visual), `e5752fe` (painel de fontes), `db290c6` (README).
- Estado de validação no momento do registro: CI dos commits 175–179 em execução/fila. Ainda não há prova de deploy Streamlit nem de busca externa/download/render real com essas alterações. O MP4 final continua não validado.



## Teste de integração ao vivo — 16/11/2026
- Confirmado CI principal no commit `4c45884`: compilação dos módulos e 36 testes unitários passaram (`OK`), incluindo o teste de desempate 9:16 e teste de render MP4 vertical com áudio/legendas em ambiente de CI.
- Adicionado job separado `commons-live-smoke` para testar API pública real do Wikimedia Commons, baixar um arquivo com licença aceita e inspecioná-lo via FFprobe. O job usa `continue-on-error: true` para que indisponibilidade temporária externa não bloqueie regressões locais.
- Primeira execução do smoke test detectou erro de importação por execução direta do script dentro de `tests/`; corrigido `sys.path` no commit `3a0d728`.
- CI do commit `3a0d728` (run #183, ID `43828898694`) está em execução no momento deste registro; o job Commons ainda não terminou. Não declarar API/download reais aprovados até ler o log final.
- Limite: workflow atual não tem as chaves privadas do Streamlit Cloud para Pixabay/Pexels/Gemini. Portanto, APIs que exigem essas chaves, Gemini Vision ao vivo, deploy e geração MP4 ponta a ponta no app publicado ainda dependem do diagnóstico avançado no ambiente Streamlit.



### Resultado parcial do smoke test real do Commons — 16/11/2026
- Run #183: busca real na API do Commons funcionou e retornou 2 arquivos com licenças aceitas (CC BY 3.0 e CC0). A tentativa de download do primeiro candidato recebeu HTTP 403 do upload.wikimedia.org; portanto busca foi validada, download ainda não.
- Correção aplicada: `download_file` agora envia User-Agent descritivo do NEXUS; smoke test tenta candidatos alternativos quando um arquivo específico falha.
- Commits: `5bf3df5` (User-Agent em downloads), `ea08012` (fallback entre candidatos). Run #186 (commit `ea08012`) ainda está executando o smoke test real no momento deste registro.
- Os testes unitários/compilação do commit `3a0d728` passaram; não declarar download Commons validado até concluir run #186.
- Pixabay/Pexels/Gemini não puderam ser testados ao vivo pelo GitHub Actions porque as chaves estão guardadas no Streamlit Secrets e não foram disponibilizadas ao workflow. Deploy/diagnóstico do app publicado também não foram confirmados.


### Validação CI e Wikimedia Commons concluída — 16/11/2026
- Run #187 (43829105466), commit 8e6a65738fde9c076f261e0692f2c92a22965055: workflow concluído com sucesso; jobs unit-tests e commons-live-smoke concluídos com sucesso.
- Testes automatizados: 36 executados, todos aprovados (OK); compilação dos módulos também passou.
- Teste real do Wikimedia Commons: API retornou 2 candidatos com licenças aceitas (CC BY 3.0 e CC0); download real concluído com sucesso após envio de User-Agent; FFprobe identificou vídeo VP9 1920x1080, duração 261,16 s, arquivo 64.018.936 bytes, licença CC BY 3.0. O teste valida busca, download e leitura do arquivo, não a adequação editorial de todos os resultados.
- Render de MP4 vertical com áudio e legendas permanece coberto por teste automatizado de integração; não equivale a uma geração ponta a ponta no app publicado.
- Estado: código no GitHub e CI validados; integração real do Commons validada para o candidato testado. Deploy Streamlit, chaves/serviços Pixabay, Pexels e Gemini no ambiente publicado e geração audiovisual ponta a ponta ainda não foram confirmados. Não declarar o estúdio integralmente pronto/implantado.
- Run: https://github.com/porraloca42-stack/nexus-video-studio-/actions/runs/43829105466


### Continuidade de validação operacional — 16/11/2026
- README atualizado para refletir o estado comprovado: CI #187 aprovado, 36 testes, integração ao vivo Commons com download/FFprobe aprovados; deploy, APIs com Secrets e geração ponta a ponta continuam pendentes.
- URL de publicação registrada no histórico do projeto: https://htykbebk3hceoen5bvopax.streamlit.app/ . Não há confirmação independente nesta sessão de que o deploy esteja servindo o commit mais recente; tentativa de acesso externo não retornou conteúdo verificável.
- Commit documental do README: ffef2bd122a4b6457190ce056b9e04da5d103b17. CI #189 (43829849725) disparado por essa atualização está em execução; não marcar a revisão documental como CI validada até concluir.
- Próximo bloqueio real: executar no Streamlit publicado o painel Ferramentas avançadas → Testar todas as bibliotecas configuradas e depois uma produção curta/real; esse ambiente contém os Secrets Gemini/Pixabay/Pexels que não estão disponíveis ao GitHub Actions. Sem o resultado desse teste, não declarar deploy nem pipeline ponta a ponta validados.


### Correção após falha reportada no Streamlit — 16/11/2026
- Evidência do usuário: geração planejada com 10 cenas/50s interrompeu a produção porque não encontrou clipes nas cenas [1, 2, 5, 6, 8, 9]. A captura não inclui o conteúdo expandido de “Detalhes das buscas sem resultado”; portanto, não atribuir a falha a uma API/chave específica sem essa evidência.
- Removido do `app.py` o expander “Bancos gratuitos complementares · pesquisa manual”. Essas fontes não participam do render automático; não devem ocupar espaço na interface principal.
- Diagnóstico de código: `search_video_sources` estava limitando a consulta de cada cena a somente duas variantes (frase completa e combinação de palavras), apesar de `build_query_variants` suportar termos individuais. Isso tornava a recuperação excessivamente restrita em bibliotecas com indexação/tagging diferente.
- Correção incremental: ampliada a busca por cena para até cinco variantes de consulta, incluindo consultas mais curtas e termos-chave individuais. A seleção final continua condicionada à revisão visual semântica; não se relaxa o filtro de licença nem se permite clipe de estilo apenas.
- Adicionado teste de regressão para verificar expansão da busca a consultas curtas. Build UI: `NEXUS-2026.11.16-stock-search-recovery-1`.
- Commits: `9b44d28` remoção do painel manual e build; `a026923` expansão da busca; `6c5f403` teste de regressão.
- CI #191 (app), #192 (assets) e #193 (teste) estão em execução/fila. Não marcar a correção como testada até verificar CI; tampouco assumir deploy automático confirmado. Após CI, confirmar no Streamlit publicado e, se a busca ainda falhar, coletar o conteúdo expandido de “Detalhes das buscas sem resultado” para identificar erro de autenticação, rate limit, indisponibilidade ou ausência de resultados.


### Revisão da avaliação semântica visual — 16/11/2026
- Evidência adicional do usuário: em novo planejamento com 11 cenas, o app rejeitou clipes nas cenas [2, 3, 5, 7, 8, 9, 10, 11]. A repetição após ampliação de consultas indica que o gargalo não era apenas busca; a etapa de revisão semântica estava rejeitando candidatos demais.
- Diagnóstico do código: `review_visual_candidates` exigia confiança mínima 70 e instruía a IA a aceitar somente representação DIRETA, com regra explícita para selecionar nenhum candidato se não houvesse relação direta. Isso excluía metáforas visuais, B-roll contextual e equivalências narrativas razoáveis. O app revisava apenas os 6 primeiros candidatos.
- Alterações: confiança mínima padrão reduzida de 70 para 55; prompt passa a aceitar ação literal, consequência visual, metáfora reconhecível e situação cotidiana que comunique a ideia, sem aprovar clipes meramente estéticos/desconexos; shortlist aumentada de 6 para 12 candidatos por cena. Critérios de licença, inspeção dos quadros reais, prioridade semântica e composição vertical permanecem.
- Adicionado teste de aceitação de metáfora visual útil (61%) e atualizado teste de rejeição de candidato fraco (42%). Atualizados testes de contagem de consultas para a expansão a cinco variantes.
- Commits: `44f5352` prompt/limiar semântico; `059e170` shortlist 12; `9fcc7d3` expectativas de busca; `a6ec100` teste de metáfora visual.
- CI #195–#198 está em execução/fila no último check; run #198: https://github.com/porraloca42-stack/nexus-video-studio-/actions/runs/43831774818 . Não marcar alterações como testadas/implantadas até CI verde e confirmação do Streamlit.
- Limitação: a captura mostra apenas cenas rejeitadas, não os detalhes internos nem quadros candidatos; a hipótese do filtro excessivo é confirmada pelo código, mas ainda precisamos de uma produção real pós-deploy para medir a taxa de aceitação e a qualidade editorial.


### Correção do bloqueio de estilo global — 16/11/2026
- Nova evidência do usuário: no diagnóstico da Cena 2, “Estilo solicitado: não informado”, enquanto a consulta de conteúdo continha “anime”. Usuário observou corretamente que o estilo selecionado não parecia aplicado ao vídeo inteiro.
- Diagnóstico: `create_storyboard` gravava `plan['style_lock']`, mas confiava que o Gemini repetisse `visual_style` e `style_search_terms` em todas as cenas. O código de diagnóstico de falhas lia somente `scene['style_search_terms']`; quando ausente, mostrava “não informado” e a busca não tinha um termo de estilo separado.
- Correção determinística: novo helper `apply_visual_style_lock(plan, style)` aplica o estilo selecionado a TODAS as cenas e gera termos de busca de estilo por meio de um mapa estável para as 24 opções visuais. Aplicado após criação inicial, após reparo do storyboard e após reparo semântico; assim o estilo não depende de conformidade do modelo.
- Teste de regressão garante que todas as cenas recebam `visual_style` e `style_search_terms` idênticos ao estilo global selecionado. Commits: `8aaffba` (implementação) e `f4e751a` (teste).
- Correções adicionais em testes existentes após inspeção de falhas de CI: mocks/expectativas atualizados para o número real de consultas por provedor e nova redação do prompt de revisão. Commits `5a0291d` e `2bd05a5`.
- CI #202 (43832119971) e #203 (43832130656) em execução/fila; execução #199–#201 falhou por expectativas de teste desatualizadas, não por erro de compilação. Não declarar as alterações validadas até CI verde.
- Próxima validação: confirmar CI e, após atualização do Streamlit, gerar storyboard novo. Planos já salvos em `st.session_state` não são reescritos automaticamente; o usuário deve clicar “Planejar vídeo” novamente para que o estilo seja propagado a todas as cenas.

- Hardening adicional no render: `app.py` agora reaplica `plan['style_lock']` a cada cena no início da produção, com fallback para planos salvos antigos sem `style_search_terms`; a busca e o diagnóstico passam a usar o estilo global mesmo quando o storyboard anterior veio incompleto. Commit `7da9c87`. CI correspondente #205 disparado; aguardar resultado.


### Ajustes finais de regressão após revisão de CI — 16/11/2026
- CI #206 confirmou que o novo teste de estilo global passou (`test_selected_visual_style_is_locked_on_every_scene`) e que testes de render/avaliação visual passaram, mas 3 testes antigos de `tests/test_assets.py` ainda tinham assinaturas de mocks/contagens incompatíveis com as chamadas reais (Commons `requests.get`, adaptador Wikimedia e cinco variantes + uma busca de estilo). Não foi falha da função de bloqueio de estilo.
- Corrigidas as três expectativas restantes em `tests/test_assets.py` (commit `ed1958e`). CI #207 (`43832587620`) está na fila; aguardando conclusão antes de declarar suite verde.
- O teste ao vivo Commons continuou passando em #206; deploy Streamlit e geração end-to-end permanecem não verificados.


### Continuidade após CI #209 — 16/11/2026
- CI #209: `commons-live-smoke` passou (busca real, download e FFprobe), compilação passou e os testes de estilo global, render MP4, revisão visual e licenças Commons passaram. Suite total: 39 testes; apenas uma expectativa no teste de variantes de busca estava incorreta: código retorna `writing goals notebook`, `writing`, `goals`, `notebook`, e o teste esperava `goals notebook`.
- Corrigida a expectativa para o termo efetivamente produzido (`writing goals notebook`), commit `76c3ecb`. Nova execução #210 disparada; ainda pendente.
- Estado: integração Commons e compilação verificadas; suite regressiva quase verde, falta nova execução. Streamlit/deploy e produção end-to-end ainda não confirmados.


## Prova técnica Remotion — 16/11/2026
- Criado projeto isolado em `remotion/`, sem alterar o pipeline atual Streamlit/Python/FFmpeg.
- Pacotes Remotion/CLI fixados em 4.0.543 e React 18.3.1; composição `NexusDemo` configurada em 720×1280, 30 fps e 50 segundos.
- Primeira composição demonstrativa contém cinco sequências animadas, tipografia, elementos gráficos, movimento e barra de progresso. Ainda é uma composição de demonstração, sem narração real nem integração com storyboard.
- Criado workflow manual/por alterações em `remotion/**` para instalar dependências, renderizar MP4 e publicar artefato por 7 dias.
- Workflow: `.github/workflows/remotion-demo.yml`.
- Estado: scaffold e workflow gravados na branch main. A renderização no GitHub Actions ainda precisa concluir; não declarar MP4 validado até inspecionar o artefato e os logs.
- Próxima etapa: validar CI de Remotion; corrigir falhas de dependências/render; baixar/inspecionar MP4; depois definir contrato JSON para receber cenas do diretor Gemini. Não substituir FFmpeg nem alterar o app publicado antes dessa validação.
- Licença consultada em 16/11/2026: a Free License cobre indivíduos para uso pessoal ou comercial e permite automações sem pagar por renderizações; custos de infraestrutura de renderização permanecem separados. A elegibilidade muda se o uso passar a ser feito por organização/equipe fora dos critérios gratuitos. Fontes oficiais: https://www.remotion.dev/docs/license/faq e https://www.remotion.dev/docs/terms.


## Composição orientada por manifesto — 16/11/2026
- Criado `remotion/src/types.ts`: contrato TypeScript inicial de projeto, cenas, modos visuais (graphic/image/video), narração, trilha e legendas por frames.
- Criado `remotion/src/NexusVideo.tsx`: composição genérica com suporte a camadas gráficas, imagens, vídeos, áudio de narração/música e legendas temporizadas.
- Criado `remotion/src/ManifestRoot.tsx` e `remotion/public/sample-manifest.json`: composição parametrizada `NexusFromManifest` para receber propriedades JSON.
- `remotion/src/Root.tsx` registra tanto a demonstração quanto a composição baseada em manifesto.
- `remotion/README.md` documenta instalação, preview e render via CLI.
- Workflow atualizado para executar TypeScript typecheck, render de demonstração e render da composição por manifesto.
- Validação confirmada até aqui: instalação npm e typecheck passaram na execução #43840856848. O render completo da composição de demonstração está em andamento; a composição por manifesto e o upload dos dois MP4s ainda aguardam conclusão.
- Execução anterior #43840460460 concluiu com sucesso e publicou artefato MP4 de 2.541.139 bytes para a composição visual inicial. Esse arquivo ainda não foi inspecionado visualmente; portanto, não declarar qualidade audiovisual validada.
- Integração com Python/Gemini e Streamlit ainda NÃO implementada. O FFmpeg continua como renderizador ativo do aplicativo.
- Próximo marco: concluir ambos os renders, inspecionar os artefatos e então criar adaptador Python que converta storyboard para o manifesto JSON e invoque o renderer Node isoladamente.


## Adaptador Python para Remotion — 16/11/2026
- Criado `nexus/remotion_renderer.py`: converte storyboard Python, mídia aprovada, narração e SRT em manifesto JSON; copia os assets para `remotion/public/jobs/<job_id>/`; disponibiliza chamada CLI para renderização Remotion quando Node/npm e dependências estiverem instalados no worker.
- Criado `tests/test_remotion_renderer.py`: cobre cópia de mídia/áudio, cena gráfica sem stock, conversão de legendas SRT para frames e rejeição de duração inválida.
- Corrigido o componente Remotion para resolver arquivos locais usando `staticFile()`.
- CI Python no commit `2ef3b18`: compilação e suíte de regressão concluídas com sucesso; teste de integração Wikimedia também passou.
- CI Remotion anterior no commit `82c7535`: typecheck, render da composição de demonstração e render da composição por manifesto concluídos com sucesso; artefato `nexus-remotion-demos` publicado (4.643.759 bytes). MP4s ainda não foram inspecionados visualmente.
- CI Remotion mais recente no commit `2ef3b18`: typecheck passou; render da demo está em execução, depois seguirá para o render do manifesto e upload. Verificar conclusão antes de considerar a versão com `staticFile()` validada.
- O adaptador Python ainda NÃO foi ligado ao botão de renderização do Streamlit. O ambiente Streamlit Community Cloud precisa de uma estratégia Node/Chromium compatível; `packages.txt` instala dependências apt, mas não se deve presumir que o Node disponível tenha versão suficiente. Não alterar o renderer padrão antes de testar o ambiente de execução.


## Validação de mídia real via adaptador Remotion — 16/11/2026
- Os artefatos da execução #43841148965 foram baixados e inspecionados localmente com FFprobe e extração de quadro.
- `nexus-demo.mp4`: H.264, 720×1280, 30 fps, 50,0 s; render de composição gráfica concluído.
- `nexus-manifest.mp4`: H.264, 720×1280, 30 fps, 50,0 s; composição JSON concluída. Um quadro extraído confirmou render visual, mas esse exemplo usa gráficos e ainda não prova integração de clipes reais/áudio.
- Criado `scripts/build_remotion_ci_manifest.py` para gerar manifesto com o adaptador Python real a partir de mídia de teste.
- Workflow ampliado para gerar clipe sintético e áudio, converter SRT, chamar `nexus/remotion_renderer.py`, renderizar a composição resultante e verificar com FFprobe vídeo H.264 720×1280, faixa de áudio e duração de 4 s. O artefato agora também inclui esse MP4 de integração.
- Execução #43841744780 (commit 447ca5e) está em andamento; typecheck já passou, render gráfico de 50 s em execução, etapa de integração áudio/vídeo ainda pendente. A execução seguinte #43841779142 (commit dbbd961) também foi disparada pelo ajuste de workflow.
- O adaptador Python e o workflow estão implementados no GitHub. Não conectar ainda ao Streamlit: primeiro aguardar o teste ponta a ponta com áudio e vídeo e decidir a infraestrutura Node/Chromium para o app publicado.

## Integração inicial Cloudflare Workers AI — 16/11/2026
- Decisão de arquitetura: adicionar geração original de imagens por cena via Cloudflare Workers AI, com Remotion como compositor de vídeo. Objetivo: reduzir dependência de bibliotecas de stock genéricas e dar direção visual específica a cada cena.
- Pesquisa em documentação oficial Cloudflare (preços atualizados em 12/11/2026): Workers AI inclui 10.000 Neurons/dia no plano Free; acima disso exige Workers Paid e cobra US$ 0,011 por 1.000 Neurons. A franquia diária reinicia às 00:00 UTC. Limites e custo dependem do modelo e parâmetros.
- Modelo candidato inicial: `@cf/black-forest-labs/flux-1-schnell`. A tabela oficial indica 9,6 Neurons por step; com 6 steps, estimativa simples de 57,6 Neurons por imagem e cerca de 173 imagens/dia na franquia de 10.000 Neurons, antes de variações por tiles/resolução, falhas/retries e demais usos. A estimativa de 140–170 imagens/dia é plausível como margem operacional, mas não é uma cota fixa garantida. Modelos mais caros, como FLUX.2 [dev], reduzem substancialmente a quantidade.
- Implementado no GitHub: `nexus/cloudflare_images.py`, adaptador isolado para chamada REST autenticada, salvar PNG/JPEG/WebP, validar resposta, controlar steps e gerar imagem por cena a partir de `image_prompt`/descrição visual. Segredos esperados no Streamlit Secrets: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`; modelo opcional `CLOUDFLARE_IMAGE_MODEL`.
- Implementado: `tests/test_cloudflare_images.py` com testes de credenciais ausentes, prompt vazio, resposta inválida e persistência de PNG. Ainda aguarda CI.
- Segurança/escopo: nenhum token foi solicitado ou gravado no repositório. O adaptador não está ligado ao botão de produção nem ao app publicado; ainda não houve chamada real ao Workers AI porque as credenciais não estão disponíveis nesta sessão.
- Arquitetura de produção proposta: Gemini produz storyboard e prompt visual detalhado por cena; Workers AI gera imagens; revisão visual valida correspondência; Remotion recebe imagens aprovadas, narração e SRT para compor MP4. FFmpeg permanece como fallback até validação real.
- Não remover ainda Wikimedia/Pixabay/Pexels: fontes de mídia podem continuar como fallback para cenas em que movimento real seja essencial ou em que a imagem gerada não represente adequadamente a ação.

## Correção do CI Remotion e compatibilidade de áudio — 16/11/2026
- Execução Remotion #43841744780: typecheck e render gráfico de 50s passaram; teste de integração falhou antes do adaptador porque o runner Ubuntu não tinha FFmpeg instalado (`ffmpeg: command not found`). Portanto não houve render do manifesto com mídia/áudio nessa execução.
- Correção no GitHub: workflow agora instala FFmpeg via apt antes de criar os fixtures sintéticos. Commit `72ec0c6`.
- Correção no adaptador: preserva a extensão real da narração (por exemplo WAV continua WAV, MP3 continua MP3), evitando rotular conteúdo WAV como MP3. Commit `0306f17`.
- Adicionado teste de regressão para extensão WAV. Commit `d4e9a15`.
- Workflow inclui o teste Cloudflare no gatilho de testes. Commit `28976b8`.
- Estado: correções gravadas em main; novas execuções CI precisam concluir. Nenhuma destas alterações está validada por nova execução ainda.

- CI adicional: workflow Remotion agora instala dependências de teste Python e executa `pytest` nos adaptadores Cloudflare e Remotion antes dos renders. Últimos commits do workflow: `ffde1e6` e `04617fa`. Aguardar execução e logs antes de marcar testes aprovados.

## Modo Cloudflare Workers AI + Remotion — atualização 16/11/2026
- Revisão de modelo: FLUX.1 schnell não aceita resolução/aspect ratio como parâmetros; para evitar crop de imagem quadrada no vídeo vertical, selecionado FLUX.2 Klein 4B, que aceita width/height por multipart/form-data e possui inferência fixa de 4 passos.
- Configuração inicial: 512×910 pixels (proporção praticamente 9:16). Pricing oficial: 26,05 Neurons por tile de saída 512×512; estimativa aproximada de dois tiles por imagem (52,1 Neurons), cerca de 191 imagens/dia dentro dos 10.000 Neurons gratuitos. Teto teórico, não garantia. FLUX.2 Klein 4B é Apache 2.0 e permite uso comercial; Klein 9B e FLUX.2 dev não devem ser confundidos com essa licença.
- Criado `nexus/cloudflare_images.py`: autenticação REST, multipart para FLUX.2 Klein, validação de imagem, assinatura real PNG/JPEG/WebP, extensão coerente com o conteúdo e geração por cena.
- Diretor: prompt de storyboard agora inclui `image_prompt` em inglês, com enquadramento 9:16 e sem texto embutido. Validador exige esse campo.
- Remotion: manifesto carrega `imagePrompt` e `cameraMotion`; camadas de imagem recebem movimentos individuais (push-in, pull-out e pans).
- Worker remoto: `.github/workflows/nexus-render-worker.yml` e `nexus/remote_render_job.py` geram imagens, narração Edge TTS, SRT e MP4 no GitHub Actions, validando 720×1280, áudio e duração.
- App: seletor opcional "Imagens originais · Cloudflare AI + Remotion" chama o worker e recupera o MP4; pipeline FFmpeg atual permanece intacto como padrão/fallback.
- Privacidade: o repositório é público. Para não expor roteiros/MP4, `nexus/render_crypto.py` usa Fernet com chave derivada do token Cloudflare; manifesto enviado ao workflow_dispatch e MP4/relatório do artefato são criptografados. O artefato não inclui imagens nem MP4 em texto claro.
- Credenciais necessárias para teste real:
  - GitHub Actions Secrets: `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` (Workers AI Read).
  - Streamlit Secrets: `GITHUB_ACTIONS_TOKEN` (fine-grained token, Actions Read/Write + Contents Read) e o mesmo `CLOUDFLARE_API_TOKEN` (chave de criptografia local).
- CI run #271 (commit `ae27ac6`): compilação e 53 testes passaram, incluindo adaptador Cloudflare, adaptador Remotion, criptografia, GitHub dispatch/artifact mock e render FFmpeg vertical com áudio/legendas. Remotion TypeScript typecheck passou.
- CI Remotion run #43843799113: typecheck e testes de adaptadores passaram; render gráfico 50s em andamento; integração de áudio/vídeo ainda pendente.
- Nenhuma chamada real ao Cloudflare Workers AI foi feita, pois credenciais ainda não foram fornecidas/configuradas. O worker remoto está implementado, mas não testado com credenciais nem artefato de produção. Deploy Streamlit não confirmado.
- Não declarar novo modo concluído/validado até gerar imagens reais, executar worker e inspecionar MP4 final no app publicado.

- Correção do smoke test Remotion: execução #25 falhou no script `scripts/build_remotion_ci_manifest.py` por `ModuleNotFoundError: nexus` ao ser chamado como script dentro de `scripts/`. Adicionado o diretório raiz do repositório a `sys.path` (commit `a54e14c`). Execução #26 está em andamento para validar novamente o build do manifesto, o render com áudio/vídeo e FFprobe.
- CI #277 (commit `39bbaf4`): suíte principal passou com 53 testes; Commons smoke também passou. Isso inclui o modo opcional de render remoto, seletor da interface e a recuperação do artefato criptografado em teste simulado.
- CI #271 (commit `ae27ac6`): 53 testes passaram, incluindo geração Cloudflare simulada, criptografia e regressões de render FFmpeg. Typecheck Remotion passou.
- CI #25 Remotion: render gráfico de 50s e FFmpeg fixture passaram; build do manifesto falhou apenas pela importação Python acima. Não houve render real de manifesto com mídia/áudio nessa execução.
- Estado atual: código do modo Cloudflare + Remotion no GitHub; testes unitários aprovados. O worker de produção ainda não foi executado porque faltam Secrets do usuário. Deploy Streamlit e render de integração com áudio/vídeo continuam pendentes.

- **Validação Remotion ponta a ponta concluída em CI:** run #26 (`43844202166`), commit `a54e14c`, sucesso. Typecheck, testes de adaptadores, demo 50s, instalação FFmpeg, criação de clipe sintético + WAV + SRT, build do manifesto via adaptador Python, render Remotion, validação FFprobe e upload de artefatos passaram.
- Artefato `nexus-remotion-demos` baixado e inspecionado: `nexus-adapter-integration.mp4` é H.264 720×1280, AAC, 4,011s; `nexus-demo.mp4` é H.264 720×1280, 50,0s. O teste prova integração de vídeo/áudio/legendas via adaptador em runner GitHub, não Cloudflare real.
- Inspeção visual detectou fonte serifada por fallback no manifesto. Corrigido em `remotion/src/NexusVideo.tsx` com família sans-serif explícita (commit `3583c6d`); aguardar nova CI para confirmar.
- CI #277 e #280–#281: suíte principal passou; run #277 confirmou 53 testes e Commons smoke. Run #282 está testando a validação de duração da narração no worker.
- CI agora mantém o render gráfico de demonstração de 50s apenas para acionamento manual; pushes automáticos priorizam o teste de integração de mídia de 4s. Isso reduz o tempo de feedback.

- **Remotion fonte corrigida e validada:** run #29 (`43844697510`), commit `3583c6d`, typecheck e render de integração passaram. Artefato baixado; quadro extraído confirmou fonte sans-serif na composição por manifesto. MP4 permaneceu H.264 720×1280 com áudio AAC e duração 4,011s.
- Criado `docs/WORKERS_AI_SETUP.md` com instruções de criação e armazenamento seguro dos Secrets. O modo remoto não será ativado até o usuário configurar os Secrets em GitHub e Streamlit.
- Adicionada validação de tamanho e resolução 512×910 para cada imagem gerada e bloqueio quando a duração de áudio Edge TTS divergir mais de 10% da meta; essas alterações aguardam a CI dos commits mais recentes.
- O teste de resposta JSON Base64/JPEG foi adicionado para confirmar extensão de arquivo correta; aguardar execução #290/#291 antes de declarar o teste aprovado.

- **CI Remotion #31** (`43844936917`, commit `352236cb`): sucesso. Typecheck, testes Cloudflare/Remotion, fixture sintética, build do manifesto, render via Remotion, validação H.264/AAC 720×1280 e upload do artefato passaram.
- CI #291 (`43844936875`): suíte principal passou após corrigir o fixture JPEG para usar bytes reais da assinatura JPEG. A falha anterior no Remotion #30 era somente o fixture de teste com assinatura escapada incorretamente; corrigido no commit `352236c`.
- Testes de render com manifesto agora passaram em duas execuções consecutivas (#27 e #31); fonte sans-serif validada visualmente no artefato do #29.
- Estado técnico: Remotion + adaptador Python + render de vídeo/áudio/legendas validados em GitHub Actions com fixtures. Cloudflare Workers AI real, worker de produção com credenciais, deploy Streamlit e MP4 final gerado com imagens Cloudflare ainda aguardam Secrets e validação ao vivo.


## Ativação de credenciais Cloudflare — 16/11/2026
- Usuário concluiu a criação de um token pelo fluxo oficial **Workers AI → API REST → Crie um token de API Workers AI**. A interface exibiu acesso de leitura e edição; a configuração foi conferida visualmente como **Workers AI: Lido + Editar**, restrita à conta NEXUS.
- O valor do token não deve ser registrado neste arquivo, em commits, issues ou mensagens. O token foi compartilhado na conversa; por prudência, recomenda-se substituí-lo por um novo token antes de uso prolongado, mas a ativação depende do cadastro de Secrets.
- Próxima etapa: cadastrar `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_API_TOKEN` em GitHub → Settings → Secrets and variables → Actions. Cadastrar também `CLOUDFLARE_API_TOKEN` em Streamlit Secrets. Ainda não confirmado: nenhum Secret foi gravado por esta sessão e nenhum render real Cloudflare foi executado.
- A integração do GitHub disponível nesta sessão não expõe operações de escrita/leitura de Actions Secrets; o cadastro precisa ser feito pela interface do GitHub.


## GitHub Actions Secrets cadastrados pelo usuário — 16/11/2026
- Usuário informou que cadastrou no repositório os dois Repository Secrets: `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_API_TOKEN`.
- Registro baseado na confirmação do usuário; os valores não foram lidos nem expostos. A existência/validade dos Secrets e a autenticação Cloudflare ainda não foram verificadas por execução do worker.
- Próxima etapa: cadastrar `CLOUDFLARE_API_TOKEN` em Streamlit Cloud → Manage app → Settings → Secrets, junto de `GITHUB_ACTIONS_TOKEN` (GitHub fine-grained PAT com Actions Read/Write e Contents Read). Depois executar um render real curto e inspecionar o MP4.


## Secrets Streamlit cadastrados pelo usuário — 16/11/2026
- Usuário confirmou que inseriu e salvou no Streamlit Secrets as entradas `GITHUB_ACTIONS_TOKEN` e `CLOUDFLARE_API_TOKEN`.
- Registro baseado na confirmação do usuário; os valores não foram lidos. Não armazenar credenciais no repositório.
- Próxima validação: executar o modo opcional “Imagens originais · Cloudflare AI + Remotion” com um roteiro curto e confirmar dispatch do workflow, autenticação Workers AI, geração das imagens, render e recuperação do MP4.
- Até a execução real, integração Cloudflare em produção permanece configurada segundo relato do usuário, mas não testada nem validada de ponta a ponta.


## Primeiro teste real do worker Cloudflare — 16/11/2026
- Execução manual #2 do workflow `nexus-render-worker.yml`, run ID `43854339955`, foi iniciada pelo Streamlit e terminou em failure.
- Logs confirmam que checkout, Python, Node, FFmpeg, dependências Remotion e typecheck passaram. O passo de produção recebeu os dois Secrets Cloudflare (valores mascarados nos logs) e avançou até a geração da primeira imagem.
- A primeira imagem retornou em 512×896; o worker exigia exatamente 512×910 e interrompeu antes da narração/render. Isso confirma resposta de geração do Workers AI, mas ainda não comprova todas as cenas nem MP4.
- Correção commit `102c5f9`: o worker agora aceita dimensões positivas retornadas pelo modelo e normaliza imagens fora de 512×910 via FFmpeg para o canvas vertical esperado antes de entregar ao Remotion.
- Estado da correção: commit gravado em main; CI disparado automaticamente, ainda aguardando resultado. Novo teste real do worker e MP4 final ainda pendentes.


## Tratamento de bloqueio de moderação Workers AI — 16/11/2026
- Execução real #43855056751 confirmou que o erro anterior de resolução foi ultrapassado; a geração chegou à primeira cena e o modelo retornou HTTP 400, código 3030 ("output has been flagged").
- Commit `a3a81a8`: em `nexus/cloudflare_images.py`, a geração de cada cena agora reconhece exclusivamente o código 3030 e faz uma única nova tentativa com enquadramento editorial conservador (não gráfico, não sexual, personagens fictícios, sem nudez/ferimentos explícitos/logos/texto), preservando cenário, sujeito e ação benigna da descrição original. Outros erros HTTP não são repetidos.
- Se a segunda tentativa também for bloqueada, o erro informa o número da cena e orienta revisar o prompt visual; não tenta contornar bloqueios repetidamente.
- Commit `f673d92`: adicionados testes unitários para a nova tentativa moderada e para garantir que erros não relacionados a moderação não sejam repetidos.
- CI dos commits `a3a81a8` e `f673d92` está em execução (runs #43855578370, #43855578442, #43855616814 e #43855616779); ainda sem resultado final nesta atualização.
- Não houve nova execução real do worker após esta correção. MP4 final e fluxo de ponta a ponta continuam não validados.


### Validação automatizada do retry de moderação — 16/11/2026
- Run #43855616814 (commit `f673d92`): regressão concluída com sucesso; jobs `unit-tests` e `commons-live-smoke` aprovados. Isso valida os testes simulados do retry 3030 e a compilação/suíte de regressão no commit com a implementação.
- Run #43855578442 (commit `a3a81a8`): demo Remotion concluída; steps de type-check, testes dos adaptadores, render via adaptador Python/Remotion e validação do MP4 sintético 720×1280 com áudio/duração passaram. A etapa de demo manual de 50s foi explicitamente skipped; não confundir com render Cloudflare real.
- Run #43855679107 (commit de documentação `9b747ad`): nova regressão disparada pela atualização deste arquivo; ainda em andamento na última consulta.
- Estado atualizado: correção de moderação implementada e coberta por testes automatizados aprovados; Remotion demo e integração sintética aprovadas. Falta implantação efetiva no Streamlit e novo render real via Cloudflare para validar se o modelo aceita as imagens e se o MP4 final é produzido.


### Confirmação de recarga do aplicativo e CI — 16/11/2026
- Run #43855829296 (commit `d4dc4bf`) concluiu com sucesso a suíte de regressão.
- Run #43855679107 (commit `9b747ad`) também concluiu com sucesso; os jobs unit-tests e commons-live-smoke passaram.
- O usuário enviou captura após recarregar o Streamlit: interface inicial do NEXUS abriu normalmente e mostra rótulo de versão `NEXUS-2026.11.16-stock-search-recovery-1`. Esse rótulo é o identificador exibido pela aplicação; não é, isoladamente, prova do SHA exato implantado.
- Próximo passo operacional: usuário deve preencher um roteiro de teste benigno, gerar o planejamento e acionar “Produzir vídeo completo” com “Imagens originais · Cloudflare AI + Remotion”. A execução real pós-correção de moderação ainda não foi disparada nem validada.


## Correção de storyboard com quantidade insuficiente de cenas — 16/11/2026
- Captura do usuário mostrou falha intermitente no planejamento: Gemini retornou 8 cenas para vídeo de 50s; a validação exige pelo menos 10 cenas (segmentos de até 5s). O mesmo limite se aplica proporcionalmente a 40s e 60s.
- Diagnóstico no código: `create_storyboard()` solicitava a quantidade adequada, mas aceitava a primeira resposta com cenas não vazias e não tinha etapa automática de reparo quando o modelo subsegmentava a narrativa. O botão “Planejar vídeo” dependia de nova tentativa manual.
- Commit `936a4ab`: se a primeira resposta vier abaixo do mínimo, o diretor agora faz uma chamada de reparo específica, preservando narração, ordem e sentido, solicitando divisão em unidades visuais menores e completas. Se a segunda resposta continuar abaixo do mínimo, apresenta erro claro sem avançar com storyboard incompleto.
- Commit `96a765d`: testes adicionados para (a) reparo automático de 8 para 10 cenas em 50s e (b) não fazer chamada extra quando o storyboard já atende ao mínimo.
- CI disparado pelos commits acima; aprovação automatizada ainda pendente. A captura não foi gerada por falha do motor Cloudflare; é um problema anterior, no planejamento Gemini.


## Correção da falha de duração da narração no worker — 16/11/2026
- Run real #43858265947, usando commit `49703fb`, passou pela geração de imagens Cloudflare e falhou depois da geração TTS: áudio medido em 35,4s para timeline de 40,0s (desvio de 11,5%, acima do limite rígido de 10%).
- As 8 cenas do planejamento de 40s estavam corretas (mínimo de 8); não era falha de contagem de cenas. A causa da interrupção foi o desvio entre a duração do TTS regenerado no worker e a duração total planejada.
- Commit `fbe5d8a`: o worker agora faz ajuste de tempo moderado por FFmpeg quando o TTS diverge até 15% da timeline, e aplica o mesmo fator aos timestamps SRT para manter legendas sincronizadas. Diferenças superiores a 15% continuam sendo bloqueadas para evitar áudio muito acelerado/lento.
- Commit `cde5384`: adicionados testes para reescalonamento dos timestamps das legendas.
- CI iniciado; ainda pendente. Novo render Cloudflare e MP4 final ainda não validados.


### Correção final dos testes de sincronização SRT — 16/11/2026
- A execução #43860063761 ainda falhou nos dois testes novos de SRT. Diagnóstico: expressão regular em `_retime_srt` continha barras invertidas duplicadas e não reconhecia timestamps SRT reais.
- Commit `3e8f726`: corrigida a regex para reconhecer `HH:MM:SS,mmm` e aplicar o fator de sincronização às legendas.
- Novas execuções de regressão #43861160198 e demo Remotion #43861160323 disparadas; aguardando conclusão.
- O ajuste TTS/legendas está implementado, mas só será considerado aprovado após os testes verdes. Render Cloudflare real pós-correção permanece pendente.


### Aprovação da correção TTS/SRT e demo Remotion — 16/11/2026
- Run #43861160198 (commit `3e8f726`): regressão completa aprovada; jobs `unit-tests` e `commons-live-smoke` concluídos com sucesso. Os testes de timestamps SRT passaram após correção da regex.
- Run #43861160323 (commit `3e8f726`): demo Remotion aprovada. Type-check, adaptadores Python/Remotion, render via manifesto real, validação dos streams MP4 e duração e upload de artefatos concluídos com sucesso.
- O passo de demo manual de 50 segundos foi skipped pelo workflow; não confundir com render real Cloudflare.
- Estado: correção de sincronização TTS/SRT implementada e regressão aprovada; pipeline sintético Python + Remotion gera MP4 validado. Ainda falta executar novamente o workflow real Cloudflare a partir do Streamlit com o código atualizado, validar geração de imagens, áudio, render e recuperação do MP4.


## Protocolo rígido de no mínimo 10 cenas — 16/11/2026
- Nova captura do usuário confirmou que o planejamento de 40s ainda aceitava 6 cenas; mensagem de validação indicava mínimo 8. Causa exata: `create_storyboard()` e `validate_storyboard()` calculavam o mínimo apenas como duração/5, portanto 40s permitiam 8 cenas. O reparo anterior só tentava alcançar esse mínimo incorreto.
- Commit `284f56a`: mínimo rígido agora é `max(10, ceil(duração/5))` tanto na geração quanto na validação. Para 40s exige 10; 50s exige 10; 60s exige 12. Prompt inicial e correções instruem explicitamente que 6–9 cenas são proibidas. O diretor tem até 3 tentativas automáticas de reparo e só aceita resposta que alcance o mínimo.
- Commit `a7de9de`: testes adicionados para reparar 7→10 cenas em 40s e para rejeitar 7 cenas no validador.
- CI dos commits em execução; ainda não aprovado. Após CI verde, precisa recarregar o Streamlit e confirmar o comportamento real.


### Ajuste de teste do protocolo mínimo de cenas — 16/11/2026
- A implementação `284f56a` já aplicava o mínimo rígido `max(10, ceil(duração/5))` na geração e validação, com até 3 reparos automáticos.
- A primeira regressão do commit `a7de9de` identificou apenas uma expectativa antiga no teste de 50s: ele ainda procurava o texto anterior do prompt ("NO MÍNIMO 10 cenas"), enquanto a nova instrução usa "NO MÍNIMO ABSOLUTO 10 CENAS". Não foi falha da regra de produção.
- Commit `6bc0963`: expectativa do teste atualizada para o protocolo novo.
- Run #43862094799 está na fila para validar o commit com a correção do teste; aprovação ainda pendente. Não pedir ao usuário para retestar antes de CI verde.


### Acompanhamento CI do mínimo de cenas — 16/11/2026
- Run #43870626598 (commit `b67371e`) falhou somente ao importar o teste novo: indentação incorreta no bloco de contexto `with`; a suíte restante passou (59 testes executados).
- Commit `f4a78b1`: corrigida a indentação do caso de teste de 40s.
- Aguardar nova regressão; até aprovação, não liberar teste do Streamlit.


### Aprovação final do protocolo mínimo de cenas — 16/11/2026
- Run #43871112101, commit `f4a78b1`: concluída com sucesso. Jobs `unit-tests` e `commons-live-smoke` aprovados.
- A regra rígida de mínimo `max(10, ceil(duração/5))` está no código e a regressão correspondente passou: 40s = mínimo 10; 50s = mínimo 10; 60s = mínimo 12.
- O teste inclui cenário de resposta inicial com 7 cenas para 40s, reparo automático para 10, e validação que rejeita 7 cenas.
- Aprovado em CI; falta confirmação funcional pelo Streamlit publicado. O usuário pode atualizar a página e executar o planejamento de 40s. Ainda não é necessário iniciar render Cloudflare até confirmar que o planejamento entrega pelo menos 10 cenas.


## Auditoria do MP4 real enviado pelo usuário — 16/11/2026
- Arquivo recebido: MP4 de 40s, 720×1280, H.264/AAC, 30fps; metadado do container identifica Remotion 4.0.543.
- Inspeção visual de quadros: imagens fotográficas distintas aparecem ao longo das cenas; não é correto afirmar que o vídeo foi composto exclusivamente por stock. O worker chama `generate_scene_images()` com `image_prompt` de cada cena, usa o modelo Cloudflare FLUX.2 Klein e passa os arquivos como mídia para o adaptador Remotion. A execução reporta uso de imagens geradas, mas o MP4 isolado não contém proveniência criptográfica por quadro; a participação do worker é sustentada pelo código e metadados, não pela imagem isolada.
- Defeitos confirmados no MP4/código:
  1. `NexusVideo.tsx` exibia `visualDescription` em inglês, headline, marca e rodapé técnico sobre cada imagem, poluindo o vídeo com texto de direção que deveria ser apenas metadado.
  2. Movimento aplicado a imagens era mínimo (zoom aproximado de 6–8%, deslocamento de até 34px); `motion_events` não eram propagados no manifesto. Isso não produz movimento perceptível para o padrão pretendido.
  3. Fade in/out simultâneo por cena zerava a opacidade no primeiro frame da nova cena e no último frame da anterior, gerando quadros pretos nas transições.
  4. Legendas preferiam WordBoundary, gerando flashes de palavras isoladas em vez de frases naturais quando SentenceBoundary estava disponível.
- Commits de correção:
  - `d330197`: removidos overlays editoriais/descrições/headlines e rodapé; removido fade que causava frames pretos; reforçado movimento de câmera Ken Burns (push/pull 16%, pan até 76px e drift discreto).
  - `3ba6da1`: manifesto não expõe visualDescription/headline como texto e transporta motion_events como metadado.
  - `20aa757`: tipos Remotion alinhados ao manifesto e eventos de movimento.
  - `f829a7f`: legendas priorizam SentenceBoundary e agrupam WordBoundary em frases maiores.
  - `f287146`: testes para priorização de frase e agrupamento de palavras.
  - `7763634`: teste para impedir texto editorial no manifesto e garantir propagação de motionEvents.
- Limitação explícita: o pipeline atual gera imagens estáticas via Cloudflare FLUX e anima movimento de câmera via Remotion; ainda não integra um modelo de geração de vídeo com movimento orgânico de pessoas/objetos. motion_events agora seguem no manifesto, mas não são ainda animação semântica de personagens.
- CI para esses commits iniciado; MP4 de usuário permanece reprovado. Não marcar produção audiovisual como validada até novo render real e revisão quadro a quadro.


### Continuação da correção audiovisual — 16/11/2026
- Commit `f829a7f`: legendas agora priorizam eventos SentenceBoundary do Edge TTS; na ausência, agrupam WordBoundary em frases maiores (até 7 palavras/52 caracteres e até 3,2s) para evitar flashes de palavras isoladas.
- Commit `f287146`: teste para priorização de frases.
- Commit `7763634`: teste para garantir que o manifesto transporte motion_events, sem expor headline/visualDescription como texto.
- Commit `09712bf`: removidos campos de headline do manifesto de demonstração para compatibilidade com os novos tipos.
- Commit `90e39c2`: teste de legendas ajustado ao novo limite de agrupamento.
- Commit `4077bfd`: removidas as headlines remanescentes do manifesto de demonstração após o typecheck identificar incompatibilidade.
- CI ainda em andamento para commits `90e39c2` e `4077bfd`; aguardar aprovação.
- Auditoria visual detalhada do MP4: imagens estáticas distintas, mas zoom anterior era discreto; texto inglês de visualDescription era impresso; transições tinham opacidade zero no primeiro/último frame de cada cena. Correções aplicadas em `d330197` e `3ba6da1`.


## Contrato de direção cinematográfica — 16/11/2026
- Commit `47b2b51`: ampliado o prompt do Gemini com um contrato estruturado `scene_direction` por cena: câmera parametrizada, camadas de profundidade, iluminação, atmosfera, transições e beats visuais.
- O contrato limita intensidade e parallax a valores normalizados, escala de câmera a 1.0–1.15, no máximo três beats por cena e enumera opções de fallback seguras. Também instrui o diretor a não prometer animação orgânica de pessoas/objetos quando a fonte for uma imagem única sem camadas.
- Commit `d6d2942`: testes de contrato verificam que o prompt exige direção estruturada, camadas e beats.
- Commit `094dfce`: corrigido o teste de legendas para comparar texto normalizado sem confundir quebra de linha real com os dois caracteres `\\n`. A falha anterior era do teste, não de geração de legenda.
- Run #43874109675 foi iniciado para validar os três commits; no momento deste registro ainda estava em execução. Não declarar CI aprovado até consultar o resultado final.
- Escopo desta etapa: contrato e instruções do diretor Gemini. O motor de render ainda não consome todos esses parâmetros; efeitos de profundidade, luz, atmosfera, transições e beats permanecem pendentes de implementação e teste no renderizador.
- Estado de produto: contrato implementado no prompt; validação automatizada pendente; deploy Streamlit e MP4 real não validados.


## Primeiro motor de direção cinematográfica no Remotion — 16/11/2026
- CI anterior confirmado: runs #43874200887 e #43874127964 concluídas com sucesso após correção do teste de legendas; regressão Python aprovada.
- Commits desta etapa:
  - `763e31a`: tipos TypeScript estritos para `sceneDirection`.
  - `6d60c3f`: sanitização/whitelist no adaptador Python e transporte do plano estruturado ao manifesto.
  - `cd639c9`: teste de limites, enumerações permitidas, truncamento de beats e fallback seguro.
  - `4a6c940`: Remotion consome direção de câmera, intensidade, escala, foco, beats de ênfase, efeitos de atmosfera (chuva/poeira/brasas/névoa), efeitos de iluminação (light sweep/flicker/exposure ramp) e crossfade de entrada com sobreposição de sequências.
- Segurança: strings arbitrárias do Gemini não viram código ou CSS; enums são whitelisted, valores numéricos limitados, texto de metadados truncado e máximo de três beats por cena.
- Limites conhecidos: camadas de profundidade são transportadas, mas parallax verdadeiro ainda não é executado porque as imagens não vêm segmentadas em planos; não há animação orgânica de pessoas/objetos. Beats atualmente produzem uma ênfase sutil de câmera, não animação semântica do alvo descrito.
- Run de regressão #43875070412 e demo Remotion #43875070449 iniciados após os commits; status pendente no momento do registro. Não marcar a etapa como aprovada até conclusão de ambos.
- Estado: código implementado no GitHub; typecheck/render de demonstração e testes Python pendentes; Streamlit deploy e MP4 real ainda não validados.


## Auditoria visual final por cena — 16/11/2026
- Commit `840f515`: criado `nexus/visual_review.py` para normalizar a avaliação visual por cena.
- Commit `92ef47f`: corrigido o formato multimodal Gemini e adicionada seleção dinâmica de modelos compatíveis via `discover_models`.
- Commit `fd3a1d1`: extração de um quadro JPEG central por cena do MP4, com verificação de duração da timeline.
- Commit `1e05f31`: integração no fluxo Streamlit Cloudflare + Remotion; a revisão é executada após recuperar o MP4, armazenada no diagnóstico do vídeo e exibida por cena. Falha de auditoria não apaga nem invalida o MP4 tecnicamente renderizado.
- Commit `7e614c6`: testes unittest para normalização, pontuação limitada, cenas ausentes e payload multimodal.
- Commit `7a3909c`: corrigido erro de sintaxe no prompt da auditoria.
- Run #43875995037 (commit `7a3909c`): jobs `unit-tests` e `commons-live-smoke` concluídos com sucesso; compilação Python e regressão aprovadas.
- Limites: a auditoria vê um quadro por cena, não verifica movimento temporal, lip-sync ou continuidade entre todos os frames. Não executa regeneração automática de cenas reprovadas. A chamada Gemini usa a chave já configurada no Streamlit e pode consumir cota da API.
- Estado: código integrado e CI aprovado. Ainda falta validar no Streamlit publicado com uma geração real Cloudflare/Remotion e inspecionar o MP4 final; não declarar produto ponta a ponta validado.


## Auditoria multimodal no MP4 final — atualização 16/11/2026
- Commit `2b8e2c8`: integrada a auditoria final também ao pipeline de bibliotecas de vídeo, além do pipeline Cloudflare/Remotion.
- Commit `ebfbe5c`: corrigida a apresentação da auditoria Cloudflare para usar o mesmo campo `final_visual_audit` da interface comum, preservando a estrutura antiga `visual_reviews` usada para avaliações de clipes stock.
- A interface agora exibe os resultados da auditoria final em uma tabela por cena para os dois motores. A avaliação de candidatos stock permanece separada da avaliação do MP4 final.
- Run #43876220228 (commit `fc4e3a8`): testes da auditoria visual, compilação Python e smoke test Commons aprovados.
- Run #43876350775 (commit `2b8e2c8`) e run #43876416211 (commit `ebfbe5c`): regressão completa concluída com sucesso; compilação Python, testes unitários e smoke test Commons aprovados.
- Estado: implementação no GitHub e CI da integração final aprovados. O workflow #43876529440, disparado apenas pela atualização documental, ainda estava em execução. Deploy Streamlit e render real com credenciais ainda não confirmados.


## Pesquisa comparativa Revid AI / AutoShorts.ai e upgrade de narração — 16/11/2026
### Pesquisa pública (não representa acesso ao código interno dos concorrentes)
- Revid declara pipeline integrado: descoberta de formatos virais por biblioteca de vídeos reais e engajamento, geração de roteiro, mídia por cena (stock, imagem, vídeo IA ou motion graphics), voz, legendas, música, editor de timeline, publicação e analytics. A empresa informa suporte a múltiplos modelos externos; não há evidência pública de um "Gemini secreto" proprietário.
- AutoShorts.ai declara fluxo de séries recorrentes: tema/prompt, configurações de voz/estilo/duração/música, prévia e edição de roteiro/título/imagens/música, agendamento e publicação. A página pública apresenta créditos de movimento separados, sinal de que geração de movimento é um recurso/custo distinto de imagens estáticas.
- Conclusão de arquitetura: a vantagem aparente dos SaaS não é um único prompt secreto, mas orquestração de modelos especializados, biblioteca/benchmark de formatos, templates, geração por cena, edição granular, publicação, automação e feedback de desempenho.
### Verificação de stack
- Gemini: o diretor atual usa REST generateContent, systemInstruction, JSON MIME e validação/retry manual. Ainda não usa responseSchema formal do Structured Outputs; fica registrada como melhoria futura.
- Cloudflare: NEXUS usa atualmente `@cf/black-forest-labs/flux-2-klein-4b`, não FLUX.1 schnell. O adaptador envia prompt e dimensões via multipart; a documentação do FLUX.1 schnell não deve ser aplicada automaticamente ao Klein.
- Remotion: o motor aplica transformações reais de câmera em imagens estáticas, atmosferas e transições. Isso não é geração de movimento orgânico. Revid diferencia explicitamente imagens animadas por pan/zoom de AI video com movimento real.
- faster-whisper: suporta `word_timestamps=True`, mas exige runtime/dependências de inferência e CPU/RAM; não foi adicionado ainda. Fish oferece endpoint de TTS com alinhamento por palavra, preferível para a narração que ele próprio gera.
- GitHub Actions: 2.000 minutos mensais no GitHub Free são para repositórios privados elegíveis; runners padrão em repositórios públicos são gratuitos. Não assumir 2.000 minutos como benefício universal.
### Fish Audio
- Documentação oficial: `POST /v1/tts/stream/with-timestamp`, header `model: s2.1-pro-free`, fornece blocos de áudio e alinhamento por palavra com offsets; permite evitar Whisper para esse caminho.
- A oferta grátis S2.1 Pro Free é anunciada como temporária até 30/11/2026 e sem SLA. A documentação também sinaliza política Fair Use e possíveis restrições para alguns usos comerciais; revisar termos antes de usar em escala/monetização.
- Commit `49bd18a`: integração Fish Audio S2.1 Pro Free com fallback Edge TTS e geração de SRT.
- Commit `6f6f519`: correção para somar offsets entre chunks no alinhamento de palavras.
- Commit `2160e02`: app passa FISH_API_KEY e FISH_VOICE_ID via Secrets para o narrador primário.
- Commit `d8fcd18`: interface identifica a voz Edge como fallback.
- Commit `c22eb61`: testes de Fish Audio e fallback Edge adicionados.
- A chave Fish publicada pelo usuário não foi inserida no repositório. Configurar uma chave nova em Streamlit Secrets como `FISH_API_KEY`; opcionalmente `FISH_VOICE_ID` para uma voz de referência. Revogar a chave exposta.
- Pendente: validar a integração com chave real, conferir se o áudio MP3 concatenado é aceito pelo FFprobe, confirmar identidade de voz de referência e aprovar condições comerciais. Até lá, Fish está implementado no código, mas não validado em produção.


## Teste de alinhamento Fish Audio em múltiplos blocos — 16/11/2026
- Commit `b068cea`: adicionado teste unitário que simula dois blocos SSE de áudio e verifica que `chunk_audio_offset_sec` é somado aos timestamps locais do segundo bloco, preservando a linha do tempo global das legendas.
- A alteração é somente de teste; não altera a integração de produção nem contém credenciais.
- CI disparado pela atualização do repositório; aprovação ainda pendente.
- A integração Fish permanece implementada, mas sem validação real de provedor/MP3 até haver credencial configurada no ambiente seguro. Não usar a chave que foi exposta na conversa.


## Observabilidade do provedor TTS — 16/11/2026
- Commit `044c4eb`: `make_voice` ganhou opção retrocompatível `return_provider=True`, que informa se o áudio veio do Fish Audio ou do Edge TTS e, em caso de fallback, registra o motivo resumido.
- Commit `a6241d4`: a interface Streamlit passa a exibir o provedor efetivamente usado, em vez de inferir Fish apenas pela existência da chave.
- Commit `0c30ffa`: teste para confirmar que a rota Fish reporta Fish Audio.
- Commit `f71e29d`: teste para confirmar que falha do Fish reporta Edge TTS como fallback.
- As chamadas antigas de `make_voice` continuam recebendo o par `(audio, subtitles)`; a nova tripla é ativada apenas pelo app com `return_provider=True`.
- CI e validação com provedor real ainda pendentes. A integração lê `FISH_API_KEY` e `FISH_VOICE_ID` de Streamlit Secrets/ambiente; este registro não contém valores de credenciais.

## Remoção de legendas e foco em vídeo + narração — 16/11/2026
- Decisão de produto confirmada pelo usuário: o NEXUS deve entregar o vídeo visual com narração; legendas serão adicionadas manualmente na edição de publicação. Não gerar SRT nem inserir texto de legenda no MP4.
- Commits 1e55059 e f4ec05a: nexus/audio.py gera somente o arquivo de áudio; Fish Audio continua com fallback Edge TTS e informação do provedor. A interface não anuncia mais etapa de legendas.
- Commit f6d6a02: render FFmpeg recebe apenas mídia, áudio e saída; removida a aplicação de filtro SRT e o retiming de legendas.
- Commits 7949ed0, 83f387a, c049a3b, c48ebc8: removidas legendas do manifesto, tipos e composição Remotion.
- Testes reorientados para garantir saída de áudio sem SRT, MP4 com vídeo/áudio sem overlay e manifesto Remotion sem campo de captions. Commits de testes: 3eb03e4, e64e2bd, adf962a, b103df9, e7b882d e ajuste final da chamada do manifesto.
- Estado: alterações gravadas em main; CI após a sequência de commits está em execução/aguarda confirmação. Deploy Streamlit e MP4 real continuam sem validação ponta a ponta.
- Próxima prioridade: obter suíte verde e, em seguida, produzir e inspecionar um MP4 real com foco em qualidade visual, coerência das cenas e narração. Não reintroduzir legendas no pipeline sem nova solicitação explícita.
- Commit 9acc215: identificador da interface atualizado para NEXUS-2026.11.16-audio-only-1, permitindo confirmar visualmente que o Streamlit carregou a versão sem legendas.
- GitHub Actions no commit 48144ae: regressão unitária e smoke test Wikimedia Commons concluídos com sucesso. Render demo separado ainda estava em execução na última consulta; implantação Streamlit e MP4 real seguem pendentes.

 
## Preservação do movimento real dos clipes de biblioteca — 16/11/2026
- Revisão do pipeline ativo confirmou que a produção principal do Streamlit usa FFmpeg e clipes de bibliotecas; o adaptador Remotion é um fluxo alternativo, não o render padrão dessa opção.
- Problema identificado: `normalize_clip()` aplicava `zoompan` sintético em todos os clipes, mesmo quando o vídeo de origem já tinha movimento de câmera ou de objetos. Isso podia deixar a montagem artificial e repetitiva.
- Alteração incremental: o pipeline de bibliotecas agora usa o modo `preserve` por padrão e mantém o movimento fotografado no clipe original. O enquadramento continua sendo adaptado para 9:16, 720×1280, 30 fps, sem impor zoom/pan artificial.
- O app define explicitamente `camera_motion="preserve"` para mídia de bancos de vídeo. A direção cinematográfica do storyboard continua registrada, mas não força movimentos artificiais sobre filmagens reais.
- Teste de regressão adicionado para confirmar que o caminho padrão preserva o clipe sem filtro `zoompan`.
- Estado: código alterado no repositório; aguarda CI e render MP4 real para validar resultado audiovisual. Não afirmar implantação no Streamlit nem qualidade final validada antes dessas verificações.

 
## Auditoria temporal do MP4 — 16/11/2026
- A revisão final anterior analisava apenas um quadro central por cena; isso permitia avaliar semântica e aparência, mas não observar a progressão visual dentro do clipe.
- `extract_scene_frames()` agora extrai três quadros ordenados por cena (20%, 50% e 80% da duração). A revisão multimodal recebe cada trio agrupado e pode apontar repetição, ausência de ação/movimento significativo, problemas de continuidade e aderência à fala.
- A função mantém compatibilidade com chamadas que forneçam um único quadro por cena, mas a extração padrão do MP4 passa a fornecer três.
- Testes adicionados para trio temporal válido e grupos incompletos.
- Limite: três amostras não equivalem a análise quadro a quadro nem medem optical flow/lip-sync. A revisão segue consultiva e depende da disponibilidade do Gemini.
- Estado: alteração gravada no GitHub; CI e render real ainda precisam confirmar comportamento e custo/latência da auditoria.


## Continuidade para novo chat — estado consolidado em 16/11/2026
Este bloco é a referência mais recente para continuar o trabalho. Em caso de conflito com trechos históricos abaixo, priorizar as decisões e o estado descritos aqui e conferir o código atual na branch `main`.

### Decisões de produto confirmadas pelo usuário
- Prioridade absoluta: resultado audiovisual para TikTok, com vídeo forte e narração natural.
- Não gerar legendas, SRT ou texto de legenda no MP4. O usuário adiciona legendas manualmente no editor final.
- Manter um estilo visual consistente dentro de cada vídeo, mas variar cenas, pessoas, ambientes, ações, enquadramentos e fontes de mídia. Consistência estética não deve virar repetição de imagens.
- Preferir vídeos reais de bibliotecas quando fizerem sentido; avaliar a qualidade e adequação para o resultado do TikTok, não apenas a facilidade técnica.
- Não ativar geração de vídeo IA paga nem consumir créditos sem autorização explícita.
- NEXUS deve ser genérico; não presumir que todo vídeo usa Gabriel/personagem fixo.
- O assistente é responsável por pesquisa, estratégia, engenharia, direção e validação. O usuário não deve ser instruído a programar.

### Pesquisa e direção audiovisual acordadas
- Benchmark público de Revid AI, AutoShorts e Pictory sugere valor em pipeline integrado: roteiro, cenas específicas, fontes visuais variadas, seleção por cena, edição, som e análise. Materiais dos fornecedores são marketing público, não prova de algoritmo proprietário nem garantia de visualizações.
- Estratégia aprovada: narração guia a história; cada cena deve corresponder à fala; identidade estética consistente com variedade real de conteúdo; cortes e duração definidos pela progressão narrativa; evitar slideshows, colagens, stock genérico e zoom repetitivo.
- Roadmap: melhorar direção por cena; elevar qualidade e diversidade de busca/seleção de mídia; evoluir montagem e ritmo; acrescentar sound design após validar fontes/licenças; fortalecer auditoria audiovisual.

### Alterações técnicas mais recentes gravadas em main
- `a87495a`: `nexus/render.py` passa a preservar movimento nativo dos clipes de biblioteca por padrão (`camera_motion="preserve"`), sem aplicar `zoompan` artificial a cada cena.
- `b478217`: `app.py` envia explicitamente `camera_motion="preserve"` para clipes de bancos de vídeo.
- `cdfa798`: teste de regressão confirma que o modo padrão não inclui `zoompan` e mantém o recorte vertical.
- `a44c0d8`: `nexus/visual_review.py` extrai três quadros por cena (20%, 50%, 80%) para a auditoria do MP4 e os agrupa em sequência temporal para Gemini. Mantém compatibilidade com um quadro por cena.
- `0525fa6`: testes para grupo temporal válido e grupo incompleto.
- `9469818` e `ffd67f3`: atualização deste registro e correção do resumo arquitetural para refletir o pipeline real.
- A revisão temporal pode apontar progressão/repetição e aderência semântica, mas três quadros não são análise quadro a quadro, não calculam optical flow e não validam lip-sync. A auditoria continua consultiva; não regenera automaticamente cenas ruins.

### Arquitetura ativa verificada
- Opção de produção por bibliotecas no Streamlit: `app.py` + `nexus/assets.py` + `nexus/render.py` (FFmpeg).
- Remotion/Cloudflare é um caminho alternativo via worker, não confundir com o render FFmpeg principal da opção de bibliotecas.
- Gemini dirige roteiro/storyboard e faz revisão visual; Fish Audio S2.1 Pro Free é o TTS primário quando configurado, Edge TTS é fallback.
- A seleção de candidatos já faz busca multi-fonte, shortlist diversa e revisão visual com dois quadros por candidato; verificar a implementação atual antes de expandir, para não duplicar mecanismos existentes.
- Fontes: Wikimedia Commons sem chave; Pixabay/Pexels dependem de configuração e validação de credenciais/licenças. Não declarar Coverr ativo/validado.
- O render preserva movimento de filmagem; ainda é necessário avaliar variedade real das cenas, ritmo, enquadramento, continuidade, qualidade de áudio e adequação ao formato TikTok.

### Estado de validação — não confundir etapas
- Código: alterações acima gravadas na branch `main`; commits confirmados por leitura no GitHub.
- Testes: foram adicionados testes de regressão. A consulta de status/checks para os commits recentes retornou lista vazia; portanto, não há confirmação disponível nessa consulta de que CI executou ou passou. Executar/consultar CI antes de declarar testes aprovados.
- Deploy: atualização do Streamlit publicado não confirmada.
- Integração real: ainda não confirmadas nesta sequência uma chamada Gemini de auditoria temporal em MP4 publicado, nem produção Fish real.
- Validação audiovisual: ainda falta produzir e inspecionar um MP4 real de 40–50s, ouvir a narração e assistir às cenas em sequência. Não declarar NEXUS ponta a ponta concluído antes disso.

### Próximos passos prioritários
1. Consultar workflow/CI e executar a suíte de testes; corrigir falhas antes de avançar.
2. Verificar se o Streamlit publicado carregou os commits (usar marcador de build se necessário).
3. Produzir um MP4 real de 40–50s no fluxo de bibliotecas, sem legendas, e inspecionar vídeo e áudio.
4. Avaliar criticamente variedade de bibliotecas, correspondência fala-imagem, movimento, enquadramento vertical, cortes e repetição. Se a seleção de mídia não for boa, melhorar ranking/shortlist e cobertura das fontes sem inventar provedores nem pressupor credenciais.
5. Validar a auditoria de três quadros no MP4 real e seu custo/latência.
6. Só depois avançar para ritmo editorial variável e sound design (música, ambientes, efeitos e ducking), respeitando licenças e sem prejudicar a voz.
7. Atualizar este arquivo após cada etapa com commit, testes executados, resultado, limitações e o que falta.

### Instrução para iniciar no próximo chat
Começar lendo a versão atual de `NEXUS_MASTER_STATE.md` no GitHub e conferindo os arquivos/commits mais recentes de `main`. Não pedir ao usuário para repetir o contexto. Informar que o registro preserva decisões e estado técnico, mas não prometer memória literal de todas as mensagens do chat anterior. Continuar do próximo passo prioritário, sem reabrir decisões já aprovadas.


## Correção da retomada — integração Remotion + Fish Audio + Cloudflare — 16/11/2026
- Correção editorial: a resposta anterior priorizou indevidamente o fluxo FFmpeg/bibliotecas e não respeitou o caminho de produção que o usuário indicou. A arquitetura do produto contém duas opções distintas; a validação solicitada nesta continuidade deve usar a opção `Imagens originais · Cloudflare AI + Remotion`.
- Revisão dos arquivos atuais encontrou incompatibilidades concretas no worker Remotion: `nexus/audio.py::make_voice` retorna um único caminho por padrão (ou par caminho/provedor com `return_provider=True`) e não gera SRT; porém `nexus/remote_render_job.py` tentava desempacotar dois valores, sincronizar legendas e passar `subtitles_path` para `render_video_remotion`, cuja assinatura não aceita esse argumento. Esse caminho falharia antes de entregar o MP4.
- Fish Audio estava implementado no módulo de áudio e usado pelo fluxo FFmpeg do Streamlit, mas as credenciais Fish não eram encaminhadas ao worker remoto. O worker chamava `make_voice` sem `FISH_API_KEY`/voice ID, portanto não usava Fish; caía no Edge TTS.
- Correção em andamento: encaminhar credenciais Fish de forma criptografada no dispatch GitHub Actions, descriptografá-las apenas no worker, chamar `make_voice(..., return_provider=True)`, remover dependências SRT do worker e chamar Remotion conforme a assinatura real. Cloudflare Workers AI FLUX.2 Klein permanece responsável por gerar uma imagem por cena; Remotion compõe o MP4 vertical.
- A chave Fish não deve ser gravada em arquivos, logs ou Secrets do repositório. O transporte entre Streamlit e worker usa o payload já criptografado com o segredo de transporte existente.
- Estado: diagnóstico confirmado por leitura do código; correção e testes desta integração precisam passar no CI antes de declarar o worker reparado. Deploy, execução real do Cloudflare/Fish e MP4 final continuam pendentes.


## Correção e validação do worker Cloudflare + Fish + Remotion — 16/11/2026
- O caminho Cloudflare + Remotion passou a ser a opção padrão no seletor do Streamlit; bibliotecas de vídeo permanecem como alternativa. O aviso do modo alternativo foi alinhado ao novo rótulo.
- Commits `ae67a1c`, `22ba20e`, `01cf09e`, `83c5f16`: app encaminha Fish API key e voice ID ao worker; o dispatch criptografa as credenciais usando o mecanismo de transporte existente; o workflow recebe apenas o payload cifrado; o worker descriptografa em memória e chama `make_voice(..., return_provider=True)`. A chave Fish não é gravada no repositório nem impressa em logs.
- O worker Remotion foi corrigido para a API real de `nexus/audio.py`: removeu desempacotamento de SRT inexistente, retiming de legendas e argumento `subtitles_path` que não existe em `render_video_remotion`. Agora sincroniza somente o áudio, sem gerar legendas, e registra o provedor de narração no relatório final.
- O Streamlit exibe o provedor efetivamente usado no render (Fish Audio ou Edge TTS fallback), sem inferir pelo segredo configurado.
- Commits de regressão: `ed723ae`, `d9c3509`, `ac44f95`, `7add395`, `b4a61fc`. Testes cobrem cifragem/decifragem de credenciais, chamada Fish no worker, fallback Edge, sincronização de áudio sem SRT e orquestração completa simulada Cloudflare → Fish → Remotion → MP4 cifrado.
- GitHub Actions run #412 (`43883603781`), commit `b4a61fc`: compilação e **72 testes unitários passaram**; smoke test real do Wikimedia Commons também concluiu com sucesso. A orquestração completa do worker passou com serviços externos simulados; isso não equivale a um render real com créditos Cloudflare/Fish.
- Commit `95b37c6`: adicionado job `remotion-typecheck` ao workflow de regressão para validar o projeto TypeScript do Remotion. Run #413 (`43883657226`) ainda estava em execução no momento desta atualização.
- Commits de interface: `bb46bdfe` (Remotion/Cloudflare como padrão), `856a733a` (rótulo de biblioteca alternativa).
- Estado: correção do código e integração simulada validadas pelo CI Python; typecheck Remotion ainda aguardando conclusão; deploy Streamlit não confirmado; nenhuma execução real do worker com Cloudflare/Fish nem MP4 real de 40–50s foi produzida nesta retomada.
- Próxima etapa: confirmar typecheck e deploy; executar pelo Streamlit a opção padrão Cloudflare + Remotion com as credenciais já configuradas; inspecionar o MP4 real, incluindo imagens, progressão de cena, movimentos Remotion, transições, sincronização e provedor real de narração.


### Atualização de validação do worker — 16/11/2026
- GitHub Actions run #413 (`43883657226`): job `remotion-typecheck` executou `npm install` e `npm run typecheck`; ambos concluíram com sucesso. O job Python também passou; o smoke test Commons estava em execução separada, sem bloquear a validação Remotion.
- A correção e a orquestração simulada do worker foram validadas em run #412: 72/72 testes passaram, incluindo o teste integrado que descriptografa as credenciais Fish, confirma que são entregues ao gerador de narração, simula imagem Cloudflare, composição Remotion e valida MP4 vertical de 50s com áudio. MP4 e relatório são gravados cifrados no teste.
- O app agora inicia com `Imagens originais · Cloudflare AI + Remotion` selecionado; bibliotecas são alternativa. O painel mostra o provedor de narração lido do relatório real do worker.
- Não houve chamada real ao Cloudflare Workers AI nem Fish Audio nesta validação automatizada; as integrações foram simuladas. Deploy Streamlit não foi confirmado pelo acesso externo nesta sessão. A validação audiovisual final ainda depende de um render real no worker e inspeção do arquivo MP4 produzido.


## Correção do teste de integração Remotion e estado atual — 16/11/2026
- A investigação do workflow Remotion demo #59 (commit antigo `7add395`) encontrou falha real em `scripts/build_remotion_ci_manifest.py`: o script passava seis argumentos posicionais e um caminho SRT para `build_remotion_manifest`, embora a assinatura atual aceite `plan, media, audio_path, public_dir, job_id` e não possua trilha de legendas.
- Commit `746c86b`: corrigido o script para usar a assinatura atual, produzir manifesto com mídia e narração e não criar/esperar SRT.
- Commit `0c0436b`: workflow `.github/workflows/remotion-demo.yml` atualizado para remover a criação de legendas do teste sintético e refletir o pipeline sem SRT.
- GitHub Actions run #60 (`43884194378`), commit `746c86b`: sucesso. O adaptador Python real criou o manifesto; Remotion renderizou o MP4; FFprobe validou H.264 720×1280, áudio AAC presente e duração de 4,011s. O artefato `nexus-remotion-demos` foi publicado. É uma integração sintética curta, não um render Cloudflare/Fish nem um vídeo editorial real.
- GitHub Actions run #417 (`43884210872`), commit `0c0436b`: os três jobs de regressão concluíram com sucesso: testes Python, typecheck Remotion e smoke test Commons.
- GitHub Actions run #61 (`43884210769`), commit `0c0436b`: sucesso. Repetiu a integração atualizada sem geração de SRT; o manifesto Python, render Remotion, validação FFprobe e upload do artefato passaram.
- A interface do app confirma no código que o modo padrão é `Imagens originais · Cloudflare AI + Remotion`; bibliotecas/FFmpeg ficam como alternativa. Streamlit requer `GITHUB_ACTIONS_TOKEN`, `CLOUDFLARE_API_TOKEN`, `FISH_API_KEY` (opcional `FISH_VOICE_ID`); o repositório requer `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_API_TOKEN`.
- Não foi possível confirmar a implantação pública do Streamlit nesta sessão: a URL não ficou acessível pela verificação externa disponível. Não houve execução real do worker com Cloudflare Workers AI ou Fish Audio, nem MP4 de 40–50 segundos do usuário. A validação audiovisual final permanece pendente.
- GitHub Actions run #418 (`43884423159`), disparado pelo commit de atualização deste registro, estava em execução no momento desta anotação; consultar resultado final.
- Próximo passo: confirmar no Streamlit o marcador/versão carregada e executar o botão de produção no modo padrão; depois inspecionar o MP4 real e confirmar no relatório se a narração veio de Fish Audio ou Edge TTS.


## Revisão do MP4 de teste, animação e biblioteca Fish Audio — 16/11/2026

### Revisão audiovisual do arquivo enviado pelo usuário
- Arquivo recebido: MP4 de 40,0s, 720×1280 (9:16), 30fps, H.264 + AAC estéreo 48kHz, aproximadamente 8,53MB. Integridade técnica básica aprovada.
- Inspeção visual por quadros em vários tempos: cenas em anime usam imagens estáticas como fonte; há algum movimento de câmera, mas os sujeitos/objetos não executam movimento orgânico. Algumas imagens permanecem visualmente iguais por vários segundos.
- Causa identificada no código: o Remotion limitava a câmera a escala máxima 1.15; `motion_events` eram enviados no manifesto, mas não eram consumidos na composição; metadados `depthLayers` ainda não geram camadas reais de parallax.

### Estratégia editorial pesquisada
- Referências oficiais do TikTok: hook nos primeiros segundos, estrutura hook/desenvolvimento/fechamento, movimento, cortes/transições, som e mudanças visuais para estimular atenção; manter vertical 9:16 e respeitar áreas da interface.
- Referências práticas de produção faceless: aprovar keyframes primeiro, animar somente imagens aprovadas com image-to-video, editar em ritmo variável e usar zoom/reframe, sound design e pattern interrupts. O intervalo de 1,5–2,5s é uma referência de edição, não regra universal nem garantia de retenção.
- O diretor foi atualizado para shots de 2–3,5s, mudança visual a cada 2–3s, pattern interrupt a cada 7–9s, hook imediato, progressão narrativa e final que pode conectar ao hook. A meta de cenas para 50s passa a 15–18 (40s: 12–15; 60s: 18–22).

### Melhorias Remotion implementadas
- `remotion/src/NexusVideo.tsx`: agora executa beats do Gemini e, quando não existem, deriva beats dos `motion_events`; cada beat aciona punch-in, micro-shake e acento gráfico. Movimento de câmera mais forte e variado, light sweep/atmosfera e transições crossfade/fade respeitando entrada/saída.
- `nexus/remotion_renderer.py`: escala de câmera validada ampliada para 1.02–1.28, com defaults 1.04→1.22.
- `nexus/director.py`: direção de câmera mais intensa, movimentos variados entre cenas e microeventos observáveis. A partir do commit `874ef82`, cada cena também recebe `video_motion_prompt` em inglês com ação física específica, duração de 2–5s e instruções para preservar a imagem-base.
- GitHub Actions Remotion demo run #67 (`43888656099`), commit `a66be40`: sucesso. O manifesto foi criado pelo adaptador Python com uma imagem estática PNG e dois microeventos; Remotion renderizou 120 frames e FFprobe validou MP4 H.264 720×1280 + áudio AAC, 4,011s. Artefato `nexus-remotion-demos` publicado. Isso valida o novo caminho de movimento de câmera/beat na imagem estática, mas não movimento orgânico de personagens.
- Importante: `motion_events` agora acionam câmera/acentos gráficos; isso não é parallax real nem image-to-video. Não afirmar que braços, rosto ou objetos se movem naturalmente sem gerar vídeo a partir da imagem.

### Fish Audio — mudanças implementadas
- `nexus/audio.py`: Fish Audio S2.1 Pro Free tornou-se obrigatório; se faltar chave, voz ou a API falhar, a produção interrompe com erro claro. Não há fallback silencioso para voz robótica.
- Biblioteca: endpoint `GET https://api.fish.audio/model` com paginação, busca por nome, filtro de idioma, modelos públicos e modelos próprios; amostras publicadas são exibidas e, quando ausentes, a interface permite gerar uma prévia curta usando `POST /v1/tts` com `reference_id`.
- `app.py`: navegador de vozes Fish Audio, seis vozes por página, áudio de amostra antes do nome, seleção persistente na sessão, fonte pública ou Minhas vozes, idioma Português ou Todos. A voz selecionada é encaminhada ao worker e ao modo alternativo.
- `requirements.txt` e workflow `.github/workflows/nexus-render-worker.yml`: dependência `edge-tts` removida. O worker também não usa mais identificador de voz Edge como default; sem voz Fish selecionada, interrompe a geração.
- Não é possível ler o valor de `FISH_API_KEY` do Secret pelo assistente. O usuário confirmou que adicionou a chave; validação real da consulta de vozes e TTS depende da aplicação publicada. Vozes públicas de terceiros podem ter restrições de direitos; verificar licença antes de uso comercial.

### Image-to-video: pesquisa e decisão pendente
- O catálogo oficial Cloudflare AI lista modelos image-to-video, incluindo `alibaba/wan-2.7-i2v` (720p: US$0,10 por segundo) e `alibaba/hh1-i2v` (720p: US$0,14 por segundo), com entrada de imagem por URI e prompt de movimento.
- Exemplo estimado para 40s de vídeo gerado: aproximadamente US$4,00 usando Wan 2.7 I2V a 720p, antes de eventuais custos adicionais, caso todo o tempo seja gerado por esse modelo. A estimativa não inclui geração de imagens, áudio, retries ou outras tarifas.
- Não foi integrado nem acionado: o modelo exige uma URI acessível da imagem de referência e o projeto ainda não tem um fluxo R2/URL temporária validado; além disso, gera custo por segundo. A ativação deve aguardar autorização explícita do usuário para o gasto e decisão de armazenamento/entrega de imagens.

### Estado e próximos passos
- Implementado no GitHub: Fish-only, seletor de vozes com prévias, Remotion executando motion beats e câmera mais expressiva, direção de retenção atualizada.
- Testado: integração Remotion com imagem estática e dois beats aprovada no run #67. Typecheck Remotion e regressão Python já passaram em commits intermediários; regressão completa do commit mais recente ainda em execução no momento deste registro.
- Não validado: consulta real à biblioteca Fish, prévias reais, TTS real Fish, deploy Streamlit, produção editorial real com o novo motion pipeline.
- Limitação conhecida: movimento de câmera e beats gráficos melhoram a percepção de dinamismo, mas para personagens/objetos com movimento natural será necessário image-to-video por cena. O usuário ainda precisa autorizar o custo e a infraestrutura temporária.
- Próximo passo: aguardar CI mais recente; confirmar que o Streamlit carregou a nova versão; testar a biblioteca Fish e selecionar uma voz; executar um MP4 real; inspecionar qualidade. Depois, decidir se habilita Wan 2.7 I2V (ou outro modelo) com custo explícito.

- Commit `01471d2`: removido também o último identificador legado `pt-BR-AntonioNeural` do default do worker. Busca no repositório não encontrou mais referências a `edge-tts`, `Edge TTS` ou esse ID de voz.
- GitHub Actions run #439 (`43888932375`): unit-tests e Remotion typecheck concluíram com sucesso após remoção da dependência Edge; o smoke test Commons ainda estava em execução no momento da atualização.

- GitHub Actions run #441 (`43889005293`), commit `01471d2`: workflow completo `success`. Unit tests: 75/75 aprovados; Remotion typecheck: aprovado; smoke test Wikimedia Commons: aprovado. O worker não instala mais `edge-tts`.

- Commit `2c5d06c` e `b278559`: a tela de vozes agora informa que gerar prévia consome uso da API, mostra o ID da voz escolhida e explica como persistir a voz padrão em `FISH_VOICE_ID`. Rótulo de versão da interface atualizado para `NEXUS-2026.11.16-fish-voice-library-2`.

- Commit `5a45495`: cards de voz Fish ajustados para mobile: player de áudio em largura maior antes do nome/descrição, escolha abaixo do preview; evita player estreito em três colunas. O CI correspondente (#447) estava em execução no momento desta anotação.

- GitHub Actions run #447 (`43889447149`), commit `5a45495`: workflow completo `success` após o ajuste mobile da biblioteca Fish. Compilação Python, 75 testes, typecheck Remotion e smoke test Commons aprovados.

## Integração Modal + LTX image-to-video — 16/11/2026

### Decisão aprovada pelo usuário
- Modal aprovado para executar geração image-to-video por GPU serverless.
- Objetivo de produção: até aproximadamente 2 vídeos/dia, cada um com 40–50 segundos; a arquitetura deve suportar esse volume e medir o custo real antes de ampliar.
- Estratégia editorial: cada cena do storyboard recebe um keyframe original Cloudflare e, no caminho principal, é animada como clipe MP4 por LTX-Video no Modal. Remotion compõe os clipes, áudio e movimentos de câmera na timeline final.
- A intenção é movimento orgânico em todas as cenas, não apenas zoom/pan em imagens. Se Modal falhar, o worker interrompe a produção em vez de entregar silenciosamente um slideshow estático.

### Código implementado no GitHub main
- `modal_worker.py`: aplicação Modal `nexus-video-i2v`, classe `Inference`, pipeline `Lightricks/LTX-Video` na revisão fixada `a6d59ee37c13c58261aa79027d3e41cd41960925`; GPU H100; cache de pesos em Volume persistente; escala a zero após 60s sem uso; entrada de imagens e prompts em lote; exporta clipes MP4.
- Resolução inicial de geração: 512×896, 24 fps. Duração por cena limitada a 2–5s; contagem de frames ajustada ao requisito LTX de 8n+1. A resolução final do MP4 composto continua 720×1280.
- `nexus/modal_i2v.py`: adaptador do worker GitHub para chamar a classe Modal uma vez por lote, validar quantidade/tamanho dos clipes e gravar MP4s por cena. Usa prompt explícito de movimento quando presente e fallback derivado da ação, imagem e direção de câmera.
- `nexus/remote_render_job.py`: após gerar e validar as imagens Cloudflare, chama Modal para animar todas as cenas; valida cada MP4 com FFprobe; Remotion recebe os MP4s em vez das imagens. Relatório inclui fonte visual, quantidade de clipes e tempo de inferência.
- `.github/workflows/nexus-render-worker.yml`: instala o cliente Modal e encaminha `MODAL_TOKEN_ID` e `MODAL_TOKEN_SECRET` a partir dos GitHub Actions Secrets.
- `.github/workflows/modal-deploy.yml`: workflow manual para implantar `modal_worker.py` depois que os dois secrets estiverem configurados.
- `app.py`: rótulo e orientação do motor principal atualizados para Cloudflare + Modal I2V + Remotion; a interface lê a fonte visual real do relatório do worker e exibe quantidade de cenas animadas, segundos de vídeo gerado e segundos de inferência GPU (não confundir inferência com tempo total faturado).
- `tests/test_modal_i2v.py`: testes simulados para prompts, lote, gravação de MP4 e rejeição de durações inválidas.
- `docs/MODAL_SETUP.md`: passo a passo para criar tokens, guardá-los nos GitHub Actions Secrets, limitar gastos e implantar o worker. O primeiro teste recomendado é um único vídeo completo de 40–50s.
- `tests/test_remote_render_job.py`: cenário de integração simulado atualizado para 10 cenas animadas antes do Remotion.
- `.github/workflows/tests.yml`: compilação de sintaxe inclui `modal_worker.py`.

### Custos e limites — não confundir hipótese com medição
- Modal Starter: US$0/mês com US$30/mês em créditos de computação; não é receita nem pagamento ao usuário. É crédito de uso sujeito às regras do plano. GPU exige método de pagamento válido na conta.
- O worker usa H100 e escala a zero com janela de 60 segundos. Isso reduz tempo ocioso, mas não elimina custos de cold start, carga do modelo, processamento, CPU/memória, armazenamento, retries ou tráfego.
- A referência oficial do exemplo Modal/LTX estima cerca de 15s de inferência warm para um clipe de 5s, mas esse número ainda não foi reproduzido neste projeto. O exemplo oficial usa 25 frames por padrão (~1s a 24fps), embora seu comentário descreva 5s; portanto, qualquer projeção de custo baseada nessa referência é apenas cenário, não orçamento validado.
- Não prometer que 2 vídeos/dia com todas as cenas animadas caberão nos créditos até medir tempo real por cena, cold start, tempo de carga do modelo e consumo total faturado. O piloto deve começar com um vídeo e revisão da fatura/uso antes de ampliar.
- O checkpoint LTX-Video selecionado tem licença própria para os pesos, separada da licença do código. A licença pública menciona exigência de acordo comercial pago para entidades com receita anual igual ou superior a US$10 milhões; verificar o texto completo e as restrições aplicáveis ao uso monetizado antes de escalar comercialmente.

### Estado de implementação, implantação e validação
- Implementado no GitHub main: integração Modal/LTX e fluxo worker → Modal → Remotion; workflows e testes simulados adicionados.
- Implantado no Modal: NÃO. Ainda depende de configurar secrets e executar o workflow manual de deploy.
- Credenciais: `MODAL_TOKEN_ID` e `MODAL_TOKEN_SECRET` ainda NÃO foram fornecidos/configurados no GitHub Actions. Não solicitar que sejam enviados no chat.
- Teste automatizado: aprovado nos GitHub Actions runs #459, #460, #461, #462, #463, #464, #465 e #466. Os runs #464 (commit `874ef82`) e #466 (commit `a7825dd`) passaram em compilação Python, suíte de regressão, typecheck Remotion e smoke test Commons. Isso valida sintaxe, adaptador simulado e compatibilidade da composição, mas não comprova chamada real ao Modal.
- Teste real de GPU, qualidade image-to-video, duração vertical, custo e MP4 editorial: NÃO executado.
- Nenhuma execução Modal/GPU foi disparada por esta integração durante a implementação; não houve consumo de créditos Modal nesta etapa.
- Lacuna de consistência de personagem: as imagens-base Cloudflare continuam sendo geradas independentemente por texto; o NEXUS ainda não encaminha uma imagem de referência persistente do personagem entre keyframes. LTX pode preservar a identidade dentro de cada clipe a partir da imagem-base, mas não garante continuidade de Gabriel entre cenas com imagens-base diferentes. Validar e planejar referência persistente antes de afirmar consistência global do personagem.

### Próximas etapas obrigatórias
1. CI Python, testes de regressão, typecheck Remotion e smoke test Commons aprovados até o run #464; continuar observando novos commits.
2. Usuário cria token de acesso Modal e configura os dois valores como GitHub Actions Secrets `MODAL_TOKEN_ID` e `MODAL_TOKEN_SECRET`; nunca colar tokens no chat.
3. Executar manualmente o workflow `Deploy NEXUS Modal video worker`; confirmar deploy e app `nexus-video-i2v`.
4. Fazer um piloto controlado com uma única cena representativa (imagem/personagem e ação), verificar identidade, anatomia, movimento, saída 9:16 e latência/custo real.
5. Após aprovação visual do piloto, produzir um MP4 editorial de 40–50s com todas as cenas animadas; inspecionar continuidade, movimento, sincronização, codecs e custo total.
6. Atualizar este registro com números observados e só então definir limite operacional de cenas e orçamento mensal.

## Registro de continuidade — deploy Modal em andamento (16/11/2026)

- O usuário confirmou que criou token Modal e cadastrou os GitHub Actions Secrets `MODAL_TOKEN_ID` e `MODAL_TOKEN_SECRET`. Não registrar valores.
- O workflow manual `Deploy NEXUS Modal video worker` foi executado como run #1 no commit `82ab49d`, branch `main`.
- Última evidência enviada pelo usuário: captura do GitHub Actions mostra job `deploy` como `In progress`, com duração `30m 39s`.
- O YAML contém `timeout-minutes: 30`, mas a execução permanecia ativa após 30m39s na captura. Portanto, não afirmar que o GitHub cancela necessariamente exatamente aos 30 minutos; observar o status real.
- Orientação vigente: não cancelar, não reiniciar e não disparar outro deploy enquanto o run #1 estiver ativo. Aguardar o resultado e então verificar logs/status.
- O `timeout=45 * MINUTES` em `modal_worker.py` controla a classe de inferência Modal e é distinto do timeout do job GitHub Actions.
- Deploy Modal, download do modelo, geração GPU, custo e qualidade ainda não estão confirmados.
- Ver também `docs/CHAT_HANDOFF.md` para instruções completas e ponto exato de retomada em novo chat.

## Regra permanente — atualização de continuidade entre chats
**Obrigatória em toda sessão e após cada etapa concluída:**
1. Sempre que uma atualização, correção, teste, decisão, configuração ou etapa de trabalho for concluída nesta conversa, atualizar imediatamente `docs/CHAT_HANDOFF.md` com o que foi feito, evidências, arquivos/commits envolvidos, resultado e próximo passo exato.
2. Atualizar também `NEXUS_MASTER_STATE.md` quando a mudança alterar arquitetura, decisões, estado técnico, segurança, custos, implantação, validação ou prioridades do projeto. O master state continua sendo a fonte principal do estado do projeto; o handoff registra a linha do tempo e o ponto exato para retomada.
3. Registrar data e horário local de Brasília (America/Sao_Paulo, UTC−03:00) sempre que disponíveis. Se o horário não puder ser confirmado, registrar somente a data e não inventar horário.
4. Separar explicitamente fatos confirmados, evidências observadas, hipóteses e itens pendentes. Nunca transformar uma intenção, instrução ou execução em andamento em tarefa concluída.
5. Depois de gravar, reler os arquivos no GitHub para confirmar que a atualização realmente ficou na branch `main`. Só então informar ao usuário que foi salva.
6. Em novo chat, ler integralmente o master state e o handoff, conferir o estado vivo do GitHub e continuar do último ponto registrado sem repetir etapas concluídas.
7. Não armazenar segredos, tokens, senhas ou valores de credenciais nos documentos; registrar apenas os nomes dos secrets e seu estado de configuração.


## Registro de continuidade — regra permanente e confirmação do handoff (16/11/2026 14:12 BRT)

- O usuário solicitou que o documento de continuidade permaneça sempre atualizado para que novos chats recuperem o histórico e o ponto exato da sessão.
- Regra permanente adicionada: após cada etapa/atualização concluída, atualizar `docs/CHAT_HANDOFF.md`; atualizar também este master state quando houver impacto no estado técnico, arquitetura, decisões, segurança, custos, implantação ou validação.
- Registrar data e horário de Brasília quando confirmáveis; não inventar horários.
- Distinguir fatos confirmados, evidências, hipóteses e pendências; nunca registrar tarefa em andamento como concluída.
- Após cada gravação, reler os documentos na branch main para verificar persistência antes de confirmar ao usuário.
- Nunca incluir valores de tokens, senhas ou credenciais.
- Horário desta atualização confirmado: 16/11/2026 14:12:52 UTC−03:00.

## Pesquisa do tamanho do modelo LTX na revisão pinada — 16/11/2026
- O código `modal_worker.py` fixa o repositório Hugging Face `Lightricks/LTX-Video` na revisão `a6d59ee37c13c58261aa79027d3e41cd41960925`.
- A página do Hugging Face para essa revisão informa tamanho total do snapshot de aproximadamente **43,8 GB**. A pasta `transformer` sozinha aparece com **7,69 GB** (dois shards de 4,94 GB e 2,75 GB). Isso confirma que o conjunto de arquivos da revisão é grande; não confundir com o tamanho de 254 GB mostrado na branch atual do repositório, que contém várias versões/checkpoints.
- O pipeline pode precisar baixar componentes distribuídos em várias pastas, além de instalar dependências Python/PyTorch na imagem Modal. O tempo real depende de cache, rede, construção da imagem e arquivos que Diffusers efetivamente solicita.
- A duração de 37 minutos relatada pelo usuário é longa, mas compatível com uma preparação que envolva dezenas de GB; **não prova** que o download esteja ativo nem que o deploy esteja saudável. Só os logs/etapa atual confirmam.
- Evidência externa consultada: página do Hugging Face para a revisão exata e listagem da pasta transformer. Links: https://huggingface.co/Lightricks/LTX-Video/tree/a6d59ee37c13c58261aa79027d3e41cd41960925 e https://huggingface.co/Lightricks/LTX-Video/tree/a6d59ee37c13c58261aa79027d3e41cd41960925/transformer
- Próximo passo permanece: não cancelar/reiniciar enquanto o job estiver ativo; se continuar muito tempo, abrir os logs da etapa `deploy` e identificar a última operação. Não assumir que basta esperar indefinidamente.

## Simplificação da seleção de voz Fish Audio — 16/11/2026 16:14 BRT
- Evidência do usuário: Streamlit exibiu `list_fish_voices() got an unexpected keyword argument 'self_only'`; a tela também mostrava filtros de busca, idioma, origem, paginação, descrições e botões separados, que o usuário considerou poluição visual.
- Diagnóstico seguro: o runtime que exibiu a tela chamou `list_fish_voices` com `self_only`, mas a função carregada nesse runtime não aceitava esse argumento. Isso é compatível com versões de `app.py` e `nexus/audio.py` carregadas em momentos diferentes. Não afirmar qual mecanismo de cache/deploy causou a divergência sem logs.
- Commits aplicados em main: `b44cf80` e `c0430e9` simplificam a interface para um único selectbox de vozes públicas em português e um player/ação de prévia ao lado da seleção. Removidos busca por nome, filtros de idioma/origem, biblioteca pessoal, paginação, descrições e metadados da tela.
- O app deixou de passar o argumento `self_only`, tornando a chamada compatível com o módulo antigo que gerou o erro.
- A lista solicita modelos em português (`language=pt`) e apenas vozes públicas; o TTS e a prévia agora enviam `language=pt-BR` para normalização brasileira do texto. Isso não altera por si só o sotaque intrínseco da voz escolhida; o sotaque depende do modelo de voz publicado na Fish Audio.
- Prévia: usa o áudio de amostra publicado pela Fish Audio quando disponível; se não houver amostra, exibe `▶ Ouvir` para gerar uma prévia curta sob demanda. A geração sob demanda consome uso da API. O player fica ao lado do seletor, sem expandir metadados.
- Testes atualizados em `tests/test_audio.py` para verificar `pt-BR` nos payloads de prévia e narração.
- Estado: alterações gravadas no GitHub main; leitura posterior confirmou os blocos alterados e o teste. CI automático por push e deploy do Streamlit ainda precisam ser observados; não declarar correção implantada/validada na interface até o usuário confirmar que o app recarregou sem erro.

- Revisão final de leitura em `main` às 16:15 BRT confirmou: UI sem busca/filtros/paginação; chamada da lista sem `self_only`; player de prévia ao lado do selectbox; payloads TTS com `pt-BR`; asserts correspondentes nos testes. Último commit de UI: `567ba08`.
- A verificação foi estática por leitura dos arquivos no GitHub. A suíte automatizada ainda depende do GitHub Actions; o comportamento visual e a integração real com Fish Audio ainda dependem do Streamlit publicado.

## Curadoria de vozes naturais brasileiras — 16/11/2026 16:24 BRT
- Pedido do usuário: ampliar o seletor com vozes normais/humanizadas, evitando memes, imitações de figuras públicas e personagens.
- Pesquisa na biblioteca oficial Fish Audio identificou filtros/categorias úteis: Narração, Conversacional, Documentário, Profissional, Neutro, além de tags e amostras de áudio. A documentação do SDK oficial confirma suporte a filtros `tag`, `language`, `sort_by` e paginação em `GET /model`.
- A biblioteca oficial descreve Letícia como voz feminina com sotaque brasileiro, suave e acolhedora; Ricardo como voz masculina com sotaque brasileiro, clara e profissional. Outras vozes padrão como Tomás/Rafael não foram incluídas automaticamente porque a descrição consultada não confirma sotaque brasileiro.
- Alterações em `nexus/audio.py` (commit `5105372`): adicionados filtros por tags, ordenação por score e função `list_fish_natural_brazilian_voices`, que consulta tags de narração/conversação/documentário/profissional/neutro, inclui buscas por Letícia e Ricardo, mescla por ID e filtra metadados para priorizar português brasileiro e estilos humanos, excluindo termos de memes/personagens/figuras públicas.
- Alterações em `app.py` (commit `322d299`): seletor compacto passa a usar a lista curada, mantendo player de amostra ao lado.
- Testes em `tests/test_audio.py` (commit `efc5b09`): cobrem parâmetros de tags/score e regras de inclusão/exclusão.
- Limitação conhecida: API da Fish Audio não oferece um atributo objetivo de “humanizada”; a curadoria depende de tags, descrição e idioma declarados pelo criador. A amostra de áudio ainda precisa ser ouvida para validar naturalidade, sotaque e adequação. Vozes comunitárias podem ter direitos/licenças distintos; verificar termos comerciais da Fish e da voz antes de monetizar.
- Estado: commits gravados na branch main e arquivos relidos. Testes automatizados e comportamento ao vivo no Streamlit ainda precisam de confirmação pelo GitHub Actions e pela interface publicada.
- Fontes consultadas: biblioteca oficial https://fish.audio/pt/app/voice-library/ ; categoria de narração https://fish.audio/pt/voice-library/narration/ ; categoria conversacional https://fish.audio/pt/voice-library/conversational/ ; SDK oficial https://github.com/fishaudio/fish-audio-go/blob/main/voices.go

## Incidente Streamlit — ImportError ao carregar app após curadoria de vozes (16/11/2026)
- Usuário enviou captura do Streamlit com erro `ImportError: This app has encountered an error`. A parte visível do traceback aponta para a instrução `from nexus.audio import generate...` em `app.py`, mas o restante da linha e o nome exato que falhou estão cortados/redigidos.
- Verificação ao vivo na branch `main`: `app.py` importa `generate_fish_preview`, `list_fish_natural_brazilian_voices` e `make_voice`; `nexus/audio.py` define as três funções. Portanto, o código atual do GitHub contém os símbolos importados.
- Isso não prova que o Streamlit Cloud já esteja executando o mesmo commit/árvore de arquivos. Hipótese principal a verificar: deploy/checkout em versão inconsistente ou erro de importação distinto no ambiente publicado. Não aplicar patch especulativo sem a mensagem completa.
- Estado: app publicado apresenta erro segundo captura do usuário; código no GitHub main contém os nomes importados. Ainda não há logs completos do Streamlit nem confirmação do commit ativo no deploy.
- Próximo passo obrigatório: obter o erro completo em Manage app → Logs (ou detalhes da exceção) e identificar o nome exato que o import não encontrou; comparar com o commit implantado. Não reiniciar nem alterar dependências às cegas.

## Correção imediata do ImportError Streamlit — 16/11/2026 — 16:31 BRT
- Usuário enviou erro de inicialização que apontava para a linha de importação de `nexus.audio` no `app.py`. O traceback visual não mostrava o símbolo exato.
- Causa mais provável isolada: foi introduzida uma dependência de inicialização nova (`list_fish_natural_brazilian_voices`) no import de `app.py`. Se o Streamlit Cloud atualizasse `app.py` antes de sincronizar a versão correspondente de `nexus/audio.py`, ocorreria `ImportError`. Isso é uma hipótese forte, não uma confirmação do log oculto.
- Correção aplicada no commit `ac84bad`: removido o import do helper novo; `app.py` voltou a importar apenas as três funções já usadas anteriormente (`generate_fish_preview`, `list_fish_voices`, `make_voice`). A curadoria foi movida para o próprio bloco de interface, usando a função de listagem compatível e metadados disponíveis. Assim a inicialização não depende da existência do helper novo no pacote de áudio publicado.
- A interface segue compacta; filtros locais excluem palavras ligadas a memes/personagens/figuras públicas e priorizam metadados de narração natural/brasileira. Como a biblioteca pode variar nos metadados, a lista real precisa ser validada após o app subir.
- Arquivo relido após commit: `app.py` em main. CI e deploy Streamlit ainda precisam confirmar execução. Não declarar incidente resolvido até o app abrir sem ImportError.

## Correção do IndentationError na curadoria de vozes — 16/11/2026 16:30 BRT
- Nova captura do usuário revelou erro concreto: `IndentationError: unexpected indent` na linha `excluded_voice_terms` em `app.py`.
- Causa confirmada pela leitura do arquivo: o bloco de curadoria dentro do `try:` tinha indentação excessiva em relação ao restante do bloco.
- Correção aplicada no commit `60693ba`: reindentado integralmente o bloco desde `voice_page_data = list_fish_voices(...)` até `voice_page_data["items"] = curated_voices`, mantendo todos os comandos no mesmo nível dentro do `try:`.
- Verificação pós-commit: `app.py` foi relido da branch main; o bloco agora apresenta indentação coerente com o `try:` e com a sequência `voices = [...]`.
- Estado: patch gravado e leitura estática confirmada. Ainda não executei compilação Python nem CI nesta etapa, e o Streamlit Cloud ainda precisa recarregar para confirmar que o app inicia. Não declarar resolvido até abrir sem erro.
- Erro anterior de ImportError foi substituído por um erro de sintaxe causado pelo patch de curadoria; assumir responsabilidade por ter enviado código com indentação incorreta.

## Curadoria de vozes humanas — atualização conservadora (16/11/2026 16:45:45 BRT)
- Usuário confirmou que o app voltou a abrir e pediu substituir vozes de personagens por vozes de pessoas comuns/naturais, mantendo o seletor compacto.
- Alterado somente `app.py`; não foi alterada a geração de áudio, o módulo `nexus/audio.py`, o player de prévia nem o layout do seletor.
- Busca agora percorre até 3 páginas de 100 modelos cada na biblioteca Fish Audio (`language="pt"`), deduplica pelo ID e filtra modelos públicos.
- Exclui metadados que indiquem memes, anime, personagens, imitações, celebridades, figuras políticas, desenhos, paródias e personagens de jogos.
- Exige que os metadados públicos identifiquem português brasileiro (termos Brazilian/Brasileiro/pt-BR/Brasil) e rejeita descrições explicitamente de Portugal/pt-PT. Isso evita listar vozes cujo sotaque brasileiro não esteja declarado.
- Entre as vozes brasileiras aprovadas pelo filtro, prioriza termos de narração, conversa, documentário, profissional, neutro, natural, podcast e entrevista; popularidade fica como critério secundário.
- Commits da alteração: `5b9cbc2` (busca ampliada e exclusões) e `900f7d3` (exigência de metadados BR e priorização de narração natural).
- Estado: arquivo atualizado e relido no GitHub main. Não houve alteração em outros módulos. CI ainda precisa validar compilação e testes; app Streamlit precisa recarregar e confirmar lista real. Não declarar validado até esses checks.
- Limitação: a Fish Audio não fornece um campo objetivo de naturalidade; a curadoria usa metadados publicados. A audição das prévias continua necessária para aprovação humana.

## Pesquisa e correção definitiva do seletor de vozes — 16/11/2026 16:45 BRT
- Nova captura do usuário mostrou que o seletor ainda listava "NARRADOR DO TODO MUNDO ODEIA O CHRIS", Neymar, Isabela, Waldo e outras vozes/personagens. O campo inferior abria teclado e permitia editar/buscar texto.
- Diagnóstico: o filtro por palavras-chave em metadados não identificava nomes de celebridades/personagens desconhecidos (ex.: Neymar); além disso, `st.selectbox` é um combobox pesquisável e abre campo de digitação no mobile. Isso contrariava o pedido de seleção simples.
- Pesquisa na biblioteca oficial Fish Audio identificou quatro modelos oficiais explicitamente brasileiros e não clonados de pessoas reais:
  - Ricardo — ID `add7bcb8d3c8423bbfa152ca232aad6e`, voz masculina de meia-idade, clara/profissional.
  - Rafael (Brasil) — ID `0ffee1af32254090b3630823baade12b`, voz masculina jovem, conversacional/profissional, pt-BR.
  - Letícia — ID `b3c060cc41544a7da94a2c487647c902`, voz feminina jovem, suave/acolhedora, pt-BR.
  - Beatriz (Brasil) — ID `0e26d2df0d0848e3b34099bfb55fd6ea`, voz feminina jovem, clara/profissional, pt-BR.
- Referências oficiais consultadas: https://beta.fish.audio/m/add7bcb8d3c8423bbfa152ca232aad6e/ ; https://beta.fish.audio/m/0ffee1af32254090b3630823baade12b/ ; https://beta.fish.audio/m/b3c060cc41544a7da94a2c487647c902/ ; https://beta.fish.audio/m/0e26d2df0d0848e3b34099bfb55fd6ea/ ; documentação SDK list/get models https://github.com/fishaudio/fish-audio-go/blob/main/voices.go
- Alterações em `nexus/audio.py` commit `c2c3e7f`: função `get_fish_voice` busca cada modelo pelo ID fixo em `GET /model/{id}`, normaliza amostra e rejeita modelo privado/não treinado/não TTS.
- Alterações em `app.py` commit `30f2eab`: removido totalmente o `st.selectbox` e a busca dinâmica da comunidade. O seletor agora mostra quatro botões de escolha fixos (Ricardo, Rafael (Brasil), Letícia, Beatriz (Brasil)); cada linha tem o player da amostra oficial ao lado. Isso elimina o campo digitável/teclado e impede modelos de personagens/famosos de entrar no catálogo.
- Alterações em `tests/test_audio.py` commit `362a771`: testes para buscar voz pelo ID e rejeitar modelos privados.
- Estado: arquivos gravados e relidos na branch main. Testes automáticos e validação real do Streamlit ainda pendentes; não declarar publicado/validado até CI e confirmação da interface.
- Decisão: começar com 4 vozes oficiais seguras, com sotaque pt-BR declarado, em vez de expor a biblioteca comunitária inteira. Ampliar somente após curadoria individual e audição de amostras.

## Correção de ImportError após troca do seletor — 16/11/2026 17:00 BRT
- Usuário enviou captura de ImportError durante inicialização após commits de troca do seletor.
- Revisão do main confirmou que `nexus/audio.py` exporta `generate_fish_preview`, `get_fish_voice` e `make_voice`, mas `app.py` já não usa `generate_fish_preview` após substituir o antigo player de geração sob demanda pelo sample oficial.
- Correção aplicada no commit `bd54f26`: removido do import de `app.py` o símbolo obsoleto e não utilizado `generate_fish_preview`. Mantidos somente `get_fish_voice` e `make_voice`.
- Hipótese técnica: o ambiente Streamlit estava carregando uma versão de `nexus.audio` sem o símbolo obsoleto (cache/atualização parcial) ou houve incompatibilidade transitória de checkout. O traceback da captura está truncado e não permite confirmar o nome exato após `generate_fish...`; portanto, não afirmar causa raiz com certeza.
- Verificação após commit: relido `app.py` e `nexus/audio.py` no main; import agora contém apenas símbolos efetivamente usados e exportados.
- Validação pendente: CI disparado por push e reinício do Streamlit. Não declarar resolvido até abrir o app.

## Segundo ajuste de compatibilidade do import Fish Audio — 16/11/2026 17:05 BRT
- Nova captura do usuário ainda mostrava ImportError na linha do import de `nexus.audio`, mesmo após remoção do símbolo obsoleto. A captura não revela a mensagem completa nem qual nome falhou.
- Revisão confirmou que ambos os símbolos (`get_fish_voice`, `make_voice`) existem em `nexus/audio.py` no main. Isso reforça hipótese de cache/checkout parcial entre arquivos no Streamlit Cloud, mas não confirma causa.
- Alteração em `app.py`, commit `a8b5ac9`: substituído import nomeado `from nexus.audio import ...` por import de módulo `import nexus.audio as fish_audio`; chamadas passaram a usar `fish_audio.get_fish_voice(...)` e `fish_audio.make_voice(...)`. Isso elimina falha de import por símbolo ausente em versões antigas do módulo e deixa eventual incompatibilidade localizada na chamada.
- Pós-commit, leitura do main confirmou: nenhum import nomeado de nexus.audio; import de módulo presente; referências às duas funções qualificadas no módulo.
- Validação pendente: CI e reload/restart Streamlit. Se continuar falhando, precisamos obter logs completos porque o traceback curto não identifica a exceção raiz; não fazer nova alteração às cegas.

## Fish Audio — correção de carregamento de vozes oficiais — 16/11/2026
- Usuário confirmou que o Streamlit abre, mas a área de vozes mostra "Não foi possível carregar as vozes oficiais brasileiras da Fish Audio."
- Causa provável encontrada no código: `get_fish_voice()` rejeitava qualquer modelo cujo campo `visibility` não fosse exatamente `public`. A documentação de modelo Fish Audio distingue `public`, `unlist` e `private`; vozes oficiais podem estar acessíveis por URL direta sem aparecer em busca pública. O código anterior rejeitava `unlist` como se fosse privado. Fonte de contexto: docs oficiais Fish Audio para GET /model/{id}; página oficial de voz Ricardo confirma modelo/descrição pt-BR.
- Alterações em `nexus/audio.py`, commit `9bb4bf0`: agora aceita `public` e `unlist`, mas continua bloqueando `private`.
- Alterações em `app.py`, commit `ab4e097`: se a lista em session_state estiver vazia, tenta novamente em vez de guardar o erro indefinidamente; registra falha individual por nome de voz e mostra diagnóstico curto em caption, em vez de engolir todos os erros.
- Teste em `tests/test_audio.py`, commit `6dd71be`: novo teste garante aceitação de modelo `unlist`; teste existente continua rejeitando `private`.
- Verificação pós-commit por leitura do main: condição de visibilidade permite public/unlist; private continua rejeitado; UI refaz tentativa se catálogo vazio e mostra diagnóstico; teste novo presente.
- Estado: commits gravados e leitura estática conferida. Testes CI e carregamento real no Streamlit ainda pendentes. Não declarar resolvido até os quatro modelos aparecerem e amostras funcionarem.

## Diagnóstico definitivo do catálogo vazio — módulo Fish Audio obsoleto no Streamlit — 16/11/2026
- Captura do usuário mostrou diagnóstico explícito repetido: `module 'nexus.audio' has no attribute 'get_fish_voice'` para os quatro modelos.
- Isso prova que o objeto de módulo carregado no processo Streamlit não contém a função, embora o arquivo `nexus/audio.py` atual em main contenha `def get_fish_voice(...)`. A causa é módulo antigo retido no processo/cache do Python/Streamlit, ou caminho carregado diferente; a captura sozinha não identifica qual.
- Correção em `app.py`, commit `ea7fa5a`: imediatamente após `import nexus.audio as fish_audio`, executar `importlib.reload(fish_audio)` (importlib já era importado no topo). Adicionado guard que verifica `hasattr(fish_audio, "get_fish_voice")` e, se ausente, gera erro explícito com o caminho de `fish_audio.__file__`. Isso impede o app de continuar silenciosamente com módulo sem o helper.
- Pós-commit: app.py relido de main; reload, guard e chamada qualificada confirmados. GitHub connector não retornou workflow runs associados ao commit (consulta wrapper lista apenas PR-triggered runs); CI completo não foi verificado nesta etapa.
- Estado: patch gravado e leitura estática confirmada. Aguardando reinício/redeploy do Streamlit Cloud; não afirmar resolvido até o catálogo carregar.
- Próximo passo se ainda falhar: usar o caminho de módulo mostrado no erro e corrigir colisão/checkout/import path com base nessa evidência; não trocar IDs nem API da Fish sem motivo.

## Deploy Modal/LTX confirmado — 16/11/2026 17:15 BRT
- Usuário informou que o processo LTX finalizou e pediu verificação.
- Consulta direta à GitHub Actions confirmou workflow `Deploy NEXUS Modal video worker` run #1, ID `43909635680`, evento `workflow_dispatch`, commit `82ab49d7fe50c8e16d78c4a3e3b08c40ae8a1a5b`, status `completed`, conclusão `success`.
- Job `deploy` ID `133447708054` e todos os steps concluídos com sucesso: checkout, setup Python, instalar Modal CLI e `modal deploy modal_worker.py`.
- Logs finais confirmam:
  - imagens Modal construídas, incluindo a imagem com PyTorch 2.6.0, torchvision 0.21.0, diffusers 0.32.2, transformers 4.49.0 e dependências CUDA;
  - `Created Function Inference.*`;
  - `App deployed in 95.955s`;
  - URL do deploy: https://modal.com/apps/porraloca42-stack/main/deployed/nexus-video-i2v
- Isso valida que o worker foi implantado no Modal e as imagens do container foram construídas. NÃO valida inferência real LTX, download dos pesos LTX-Video, inicialização da GPU H100, geração de clipe nem qualidade audiovisual. Deploy não acionou execução da função de inferência.
- Foram encontrados render workflows #6 e #7 concluídos com sucesso e artifacts MP4/report, mas ambos foram executados antes do deploy Modal (14:28–14:34 UTC; deploy às 16:37 UTC), portanto não servem como prova de LTX I2V após deploy.
- Próximo passo para validação real: executar um render de teste pequeno/curto com uma cena ou job mínimo, monitorar custo e logs; só então realizar o primeiro vídeo completo. Respeitar gasto Modal, confirmar spend limit/créditos antes de executar GPU.

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

## Primeiro smoke test real do LTX aprovado — 16/11/2026 17:27 BRT
- GitHub Actions Modal Deploy #2, run ID `43949077365`, commit `0436eae841e406dbe6d0180ec1f1216c64e8b063`: completed/success em 2m53s.
- Todos os passos passaram: instalação de dependências, deploy do worker, inferência real de uma cena na H100, validação FFprobe e upload do artefato.
- Log do smoke test confirma:
  - status success;
  - modelo `Lightricks/LTX-Video`, revision `a6d59ee37c13c58261aa79027d3e41cd41960925`;
  - duração 2.041667 s; 49 frames; 24 fps;
  - inferência informada pelo worker: 7.863 s;
  - resolução 512×896; codec H.264;
  - MP4 28,376 bytes.
- Artefato GitHub Actions `nexus-ltx-smoke-test`, ID `14267146078`, size 28,076 bytes, criado 16/11/2026 20:25:10Z, expira 19/11/2026 20:25:09Z. Inclui MP4 e report JSON. Link: https://github.com/porraloca42-stack/nexus-video-studio-/actions/runs/43949077365/artifacts/14267146078
- Estado: worker implantado e inferência H100 validada; MP4 exportado e validado tecnicamente. Qualidade editorial/movimento ainda precisa inspeção visual do MP4. Smoke test usou paisagem sintética, não imagem real do NEXUS.
- Próximo passo: baixar artefato e assistir ao MP4; depois executar render de uma cena real via pipeline NEXUS (Cloudflare base image -> Modal I2V -> Remotion) e validar compatibilidade/duração/qualidade; somente então render de 40–50s.
- Tempo de inferência 7.863s refere-se ao campo retornado pelo worker para 2s de vídeo; não equivale ao tempo total do job nem a custo faturado. Verificar Modal usage/billing para custo real.

## Preparação do teste integrado Cloudflare → LTX → Remotion — 16/11/2026 17:40 BRT
- Usuário autorizou prosseguir até concluir a validação do pipeline.
- Adicionado `scripts/live_pipeline_smoke_test.py` (commit `c7b6224`): gera uma imagem editorial real no Cloudflare FLUX.2 Klein, anima com o worker Modal LTX, cria faixa de áudio sintética de validação, compõe o clipe no Remotion e valida MP4 vertical 720×1280 com H.264/AAC, duração e tamanho.
- Adicionado workflow manual `.github/workflows/nexus-live-pipeline-smoke.yml` (commit `75417b1`): instala FFmpeg/Python/Node/Remotion, usa secrets Cloudflare + Modal, executa a integração real e publica MP4, imagem-base e relatório como artifact por 3 dias.
- O teste usa áudio sintético de 440Hz somente para validar muxagem do Remotion; NÃO é narração de produção e NÃO testa Fish Audio. Não exige credenciais Fish.
- CI regression #534, run ID `43952157568`, commit `c7b6224`: todos os jobs concluídos com sucesso; compilação Python (inclui scripts), testes unitários, typecheck Remotion e smoke Commons.
- CI #535, run ID `43952202569`, commit `75417b1`, foi disparado após adicionar workflow; estava em andamento na última consulta.
- Remotion demo render #75, run ID `43952157522`, commit `c7b6224`: typecheck e testes de adapters passaram; job ainda executava etapas de integração de mídia/Remotion.
- Limitação operacional: conector GitHub disponível não expõe ação para disparar workflow_dispatch. O workflow integrado precisa de um clique manual do usuário. Link: https://github.com/porraloca42-stack/nexus-video-studio-/actions/workflows/nexus-live-pipeline-smoke.yml
- Após workflow #535 aprovar, usuário precisa executar o workflow acima uma vez. A execução chama Cloudflare Workers AI e Modal H100 e pode gerar custos; confirmar spend limit/créditos antes. O output artifact contém MP4 final e report.
- Critério de conclusão desta fase: workflow integrado success, MP4 720×1280 H.264 + AAC validado, duração ~2s, e inspeção visual do movimento. Em seguida, rodar vídeo completo de 40–50s somente após verificar custos e qualidade; produção integral requer Fish Audio credentials e manifesto editorial real.

## CI e integração Remotion aprovados — 16/11/2026 17:42 BRT
- CI regression #535, run ID `43952202569`, commit `75417b1`: completed/success; unit-tests, Remotion typecheck e Commons live smoke aprovados.
- Remotion demo render #75, run ID `43952157522`, commit `c7b6224`: completed/success. Testes de adapters, criação de mídia sintética, manifesto via adapter Python, render de integração Remotion, validação dos streams/duração e upload de demos passaram.
- Esses resultados validam o Remotion e o adapter de mídia, mas o demo #75 não chama Cloudflare nem Modal LTX; a integração real completa está no workflow novo `nexus-live-pipeline-smoke.yml`.
- Estado: código e CI do teste integrado aprovados. A execução Cloudflare→LTX→Remotion ainda aguarda disparo manual.


## Primeira execução do pipeline integrado e correção de ambiente — 16/11/2026
- O workflow manual `NEXUS live visual pipeline smoke test` foi iniciado pelo usuário; run #1, ID `43953906585`, commit `245b6c039deb4ed592f58b60d9d65d591987b91f`, conclusão `failure`.
- Steps de checkout, setup Python 3.11, Node 22, FFmpeg, dependências Python, dependências Remotion e typecheck Remotion passaram.
- O step de integração falhou antes de chamar qualquer provedor, com `ModuleNotFoundError: No module named 'nexus'` ao importar `nexus.cloudflare_images`. Portanto, nesta execução NÃO houve geração Cloudflare, inferência Modal/LTX, render Remotion, nem artifact. Não houve evidência de falha dos motores.
- Correção aplicada em `.github/workflows/nexus-live-pipeline-smoke.yml`, commit `e77458e650868bb367d47b0ba5bbaa68550d0dad`: definido `PYTHONPATH: ${{ github.workspace }}` no ambiente do step de integração, para disponibilizar a raiz do checkout ao importador Python.
- Estado da correção: commit gravado no `main`; aguardando CI pós-commit e nova execução manual do workflow integrado. Não considerar integração validada.


## Retomada da finalização e orçamento — 16/11/2026
- O usuário definiu orçamento operacional de até US$ 30/mês para uma meta de 22 vídeos mensais de 40–50s. Tratar como teto de projeto, não como custo validado; acompanhar custo real por execução antes de estimar custo unitário.
- Branch main confirmada no commit d18635ad27dfa93ace2c06770f10a6010e892ede.
- CI regression #540 (run ID 43955175273), commit e77458e650868bb367d47b0ba5bbaa68550d0dad: completed/success. CI regression #541 (run ID 43955194251), commit d18635ad27dfa93ace2c06770f10a6010e892ede: completed/success.
- A correção PYTHONPATH do workflow integrado está no main e as regressões pós-correção passaram. A execução integrada Cloudflare → Modal/LTX → Remotion ainda NÃO foi repetida após a correção; requer disparo manual de workflow_dispatch e pode consumir créditos Cloudflare/Modal.
- O fluxo principal selecionado no app é Cloudflare FLUX.2 Klein → Modal LTX I2V → Remotion, com narração Fish Audio. O worker remoto atualmente anima cada cena do storyboard com LTX; não há seleção automática de cenas com/sem I2V implementada. Não alterar essa decisão silenciosamente; qualquer otimização editorial do uso de LTX precisa ser validada contra qualidade e orçamento.
- Próximo marco: repetir o workflow manual nexus-live-pipeline-smoke.yml após a correção de PYTHONPATH, inspecionar o MP4/artifact e, se aprovado, validar um manifesto de produção com Fish Audio e duração real de 40–50s. Não executar geração paga completa antes de revisar o resultado e o custo do smoke test.
- Estado: CI automatizado #540/#541 aprovado; worker LTX já implantado e smoke técnico isolado H100 aprovado anteriormente; integração Cloudflare→LTX→Remotion ainda pendente; produção MP4 de 40–50s ainda NÃO validada.


## Pipeline integrado aprovado — 16/11/2026
- O usuário confirmou que o custo acumulado de 5 testes foi US$ 0,40 (média aritmética observada: US$ 0,08/teste). Este valor é o gasto informado pelo usuário, não uma estimativa de custo unitário de produção; registrar consumo real por execução.
- Workflow manual `NEXUS live visual pipeline smoke test` #2, run ID `43956968062`, commit `5a1d59fb8dfe36335f60b4e3138971e7e21c4533`: completed/success. Job `live-pipeline` e todos os 10 steps concluídos com sucesso, incluindo o step Cloudflare→LTX→Remotion e upload do artifact.
- Artifact `nexus-live-pipeline-validation`, ID `14273235414`, 747,658 bytes, válido até 19/11/2026. ZIP baixado e inspecionado; contém `nexus-live-pipeline.mp4` (810,674 bytes) e `pipeline-report.json`.
- Relatório: Cloudflare Workers AI FLUX.2 Klein 4B gerou imagem 512×910 (351,386 bytes); Modal LTX-Video em H100 gerou clipe H.264 512×896, 49 frames, 24fps, 2.041667s, inferência 7.131s; Remotion gerou MP4 H.264 720×1280, 30fps, AAC, 2.005s, 810,674 bytes. FFprobe validou os streams e a duração; frame extraído foi inspecionado visualmente e a composição corresponde ao prompt de silhueta em montanha sob céu estrelado.
- Limitação explícita: smoke test usa áudio sintético de 440Hz e apenas uma cena/2s. Não valida Fish Audio, narrativa completa, storyboard multi-cena, sincronização de voz, legendas (não fazem parte do fluxo atual), nem MP4 de produção de 40–50s. Não declarar o produto finalizado ainda.
- Estado atualizado: Cloudflare→Modal/LTX→Remotion está implementado, executado e validado em smoke test de 2s. Worker Modal H100 isolado também validado. Produção real de 40–50s com Fish Audio permanece pendente.
- Próximo passo de finalização: executar validação de produção controlada com roteiro real de 40–50s e Fish Audio, revisar storyboard e cenas, medir duração/custo total, inspecionar o MP4 final. Preservar H100 até comparar custos e qualidade; não trocar GPU sem benchmark.


## Correção de referência operacional — 16/11/2026
- As descrições antigas que diziam que o motor padrão produzia apenas imagens estáticas e que Edge TTS seria fallback foram substituídas. A referência atual é Cloudflare FLUX.2 Klein → Modal/LTX-Video I2V → Remotion, com Fish Audio obrigatório e sem fallback robótico.
- Smoke test integrado #2 validou a cadeia visual e muxagem de áudio sintético em 2s. Não confundir esse teste com a validação de uma produção editorial de 40–50s com narração Fish Audio.
- O app aceita cenas de 2–5s; o adaptador Modal rejeita durações fora dessa faixa e processa todas as cenas num único batch. O worker de produção gera imagens, anima todas as cenas, sintetiza Fish Audio, ajusta áudio dentro de tolerância máxima de 15% e valida o MP4 final via FFprobe.
- Próximo critério de liberação: um vídeo real de 40–50s, com voz Fish Audio selecionada, todas as cenas animadas e coerência audiovisual revisada. Registrar duração, custo, codecs, resolução e inspeção visual antes de declarar finalizado.


## Catálogo manual de narrações — 16/11/2026
- Usuário forneceu 40 IDs de modelos e definiu três grupos, preservados sem alteração: CapCut (14), ElevenLabs (4) e Licenciadas Fish (22).
- Criado `nexus/voice_catalog.py` com os 40 IDs exatos na ordem recebida e classificação conservadora de gênero por metadados explícitos. Metadados ambíguos ou sem marcador ficam em `unknown`; não inferir gênero pelo nome de forma especulativa.
- `nexus/audio.py` agora enriquece cada ID consultando `GET /model/{id}` na Fish Audio, em até 8 chamadas concorrentes. Falha/indisponibilidade de metadados não remove o ID do catálogo; a interface mantém o ID selecionável e sinaliza que os metadados não foram carregados. A validação de acesso/compatibilidade real de cada ID ainda depende da API autenticada.
- `app.py` substitui a descoberta automática anterior por três grupos manuais, cada um subdividido em vozes masculinas, femininas e gênero não identificado. A seleção grava o ID original em `nexus_fish_voice_id`, que continua sendo passado ao pipeline Fish Audio como `reference_id`.
- Testes adicionados para total/categorias/ordem dos IDs, classificação conservadora de gênero e preservação dos IDs após consulta de metadados.
- Commits relacionados: `ff5f8da` (catálogo), `aca443f` (consulta de metadados), `6dc8f5d` (UI), `ebafc5d` (estrutura UI), `3b4d858` (testes), `11c60ee` e `26bc349` (fixtures/testes), `c33a3e2` (indentação), `239f2d1` (metadados), `6c9c0da` (versão UI), `1c79796` (registro mestre).
- Estado: código gravado no GitHub main. CI/checks, deploy Streamlit, resposta autenticada dos 40 IDs, audição das amostras e teste de síntese real com IDs selecionados ainda não foram confirmados. Não declarar catálogo validado até esses testes.


## Ajuste de interface mobile — remoção do rodapé Streamlit (16/11/2026)
- Solicitação do usuário: remover a faixa inferior branca do app móvel que exibe “Built with Streamlit” e o atalho “Fullscreen”.
- Commit `4a80ee8` em `app.py`: ampliados os seletores CSS para ocultar o footer/status inferior do Streamlit e o viewer badge, incluindo variantes de classes dinâmicas usadas pelo badge. A alteração é somente visual; não modifica o pipeline de produção.
- Estado: alteração gravada em `main`. Ainda não foi confirmada no deploy Streamlit nem visualmente no celular. O CSS atua dentro da aplicação; se a faixa for renderizada pelo contêiner externo da Streamlit Cloud fora do DOM do app, ela poderá permanecer e exigirá outra abordagem suportada pela plataforma.


## Contorno externo para ocultar a barra do Streamlit Cloud — 16/11/2026
- Nova evidência do usuário: abrir a URL com `?embed=true` removeu o cabeçalho/toolbar do viewer, mas a faixa fixa inferior “Built with Streamlit / Fullscreen” permaneceu. A captura confirma que o elemento é renderizado pelo shell externo de embed, fora do DOM controlado pelo CSS em `app.py`; portanto os seletores CSS internos não podem removê-lo.
- Pesquisa na documentação oficial Streamlit confirma que `?embed=true` remove toolbar/padding/footer documentados, mas a barra promocional de embed com link Fullscreen é um componente separado do viewer. Discussões da comunidade registram que CSS interno não a oculta e usam uma máscara no documento pai.
- Criado `mobile/index.html` (commit `833ed41`) como shell independente: carrega o app via iframe com `?embed=true` e sobrepõe uma máscara escura fixa no rodapé do viewport, cobrindo a faixa do viewer sem alterar o conteúdo interno. A máscara tem safe-area para dispositivos móveis.
- Criado `.github/workflows/deploy-mobile-shell.yml` (commit `7bbee1b`) para publicar o shell em GitHub Pages; deploy requer Pages habilitado com GitHub Actions nas configurações do repositório. Atualizado o padding inferior mobile em `app.py` (commit `2f2c4f5`) para preservar espaço de rolagem atrás da máscara.
- Estado: arquivos gravados em `main`; workflow ainda não foi confirmado como executado, GitHub Pages ainda não foi confirmado como habilitado e a máscara ainda não foi validada no celular. Não declarar missão concluída até abrir a URL Pages e conferir visualmente.
- URL esperada após habilitar Pages: `https://porraloca42-stack.github.io/nexus-video-studio-/`.


## Identidade visual — cabeçalho com logo NEXUS (16/11/2026)
- Solicitação aprovada: cabeçalho centralizado em composição horizontal, com a logo original completa à esquerda e o nome à direita em duas linhas: “NEXUS” e “VIDEO STUDIO”. O nome deve permanecer inteiro em uma linha por título, inclusive em telas móveis.
- `app.py` atualizado no commit `e024807`: substituído o cabeçalho anterior por um lockup horizontal; logo original incorporada em PNG otimizado (256×256, fundo preto), exibida com `object-fit: contain`, dimensões responsivas e sem recorte; tipografia com `white-space: nowrap` para impedir quebra do nome; conjunto centralizado e adaptado para mobile.
- Versão visual identificadora: `NEXUS-2026.11.16-brand-header-1`.
- Escopo: somente cabeçalho/CSS e identificação visual; não altera o pipeline de roteiro, narração, geração, animação ou montagem.
- Estado: commit gravado em `main`; confirmação por leitura posterior do arquivo é necessária. Deploy e validação visual em celular ainda pendentes.


## Biblioteca de estilos visuais e direção de arte — 16/11/2026
- Curadoria aprovada para o catálogo: 18 estilos (7 novos propostos pelo usuário, 8 preservados e 3 complementares): Quântico & Cósmico; Sonho Lúcido; Dark Psychology; Épico Espiritual; Aura Neon; Hermetismo Clássico; Visual ASMR / Hipnótico; Cinematográfico; Dark Cinematográfico; Ilustração Editorial; Filme Noir; Aquarela Artística; Fantasia Cinematográfica; Graphic Novel; Minimalista Clean; Realismo Humano Emocional; Reconstituição Histórica; Natureza Contemplativa.
- Nova biblioteca interna `nexus/visual_styles.py`: cada estilo recebe identidade/intenção, paleta, iluminação, fotografia/composição, texturas/atmosfera, termos para busca, restrições e metadados mínimos de interface. As descrições técnicas são exclusivamente para o diretor; a UI mostra apenas nome, pequena referência visual e descrição curta.
- `nexus/director.py` incorpora a direção detalhada ao prompt do Gemini e fixa o perfil no storyboard; a busca recebe termos específicos por estilo. O estilo é critério de identidade artística, nunca substitui a correspondência semântica da cena com a narração.
- `app.py` consome o catálogo centralizado, remove as seis opções antigas não aprovadas, atualiza o contador para 18 e usa Cinematográfico como padrão. A galeria permanece compacta e não expõe os prompts internos.
- Decisão de produto: na interface redesenhada, haverá uma aba independente “Estilos” para explorar referências e exemplos. A tela “Criar” continuará enxuta, com seleção em carrossel. A aba de consulta ainda não foi implementada neste conjunto de commits.
- Commits: `ec80c66` (catálogo na UI), `3e5217c` (perfis internos), `74e5be9` (integração com Gemini), `031ab44` (testes), `54f1f77` (correção de separadores de linha), `c76aead` (ajuste do teste), `084d6b6` (perfil completo também na revisão visual).
- Revisão estática pós-commit: os 18 nomes estão presentes, app importa o catálogo centralizado, o padrão antigo foi removido, e o diretor injeta a direção completa tanto no planejamento quanto na avaliação dos candidatos. O endpoint de status do commit não retornou checks; CI/testes Python ainda não estão confirmados. Deploy Streamlit e geração real com estilos distintos continuam pendentes. A existência dos perfis e a revisão estática do código não comprovam ainda a qualidade visual da geração.


## Gramática visual e biblioteca de estilos — revisão anti-template (17/11/2026)
- Requisito central reforçado pelo usuário: a IA não pode associar estilos a cenas fixas (ex.: Dark Psychology não significa homem diante do espelho). Estilo deve ensinar linguagem visual, não fornecer receita de conteúdo.
- `nexus/visual_styles.py` revisado: os 18 perfis agora descrevem princípios de identidade, meio, fotografia, luz, paleta, textura e atmosfera sem prescrever cenas-modelo. Termos de busca foram limpos para conter apenas linguagem formal, sem sujeitos/objetos/cenários como padrão.
- `build_visual_style_directive()` agora injeta regra anti-template explícita: derivar sujeito/ação/ambiente da fala, tratar referências como possibilidades e nunca receitas, variar motivos ao longo do vídeo e escolher a solução visual pela semântica antes da estética.
- `nexus/director.py` atualizado no prompt principal e na revisão visual multimodal: estilo é gramática visual secundária à intenção narrativa; cada cena nasce do seu trecho; evitar repetição de protagonistas, gestos, objetos simbólicos, ambientes e composições. Termos específicos de estilo gerados por cena são preservados e recebem somente os modificadores formais do perfil.
- Versão do contrato de perfil elevada para `2.0` para sinalizar a mudança de semântica.
- `app.py` agora separa a experiência em abas “Criar” e “Estilos”. A aba Criar preserva o fluxo atual de produção; a aba Estilos oferece galeria compacta com referências simplificadas, descrição curta e ação “Usar este estilo”. Nenhuma instrução técnica detalhada da IA é exibida.
- Testes adicionados para garantir ausência de motivos fixos nos perfis, preservação de termos específicos da cena e presença da regra anti-template.
- Estado: alterações gravadas em `main`. Revisão estática confirmou abas, 18 estilos, perfis anti-template e integração do diretor. CI acionado pelo GitHub Actions; aguardar conclusão. Deploy Streamlit e teste real de storyboard/render ainda pendentes.


## Integração final da gramática visual ao worker — 17/11/2026
- Verificado o caminho real de produção: `nexus/cloudflare_images.py` consome diretamente `scene.image_prompt` para gerar os keyframes; `nexus/modal_i2v.py` usa `video_motion_prompt` ou deriva movimento da imagem-base. Por isso, apenas guardar o perfil em `plan.style_directive` não era suficiente para garantir que o gerador de imagem recebesse a direção.
- `apply_visual_style_lock()` agora anexa a direção de arte interna completa ao `image_prompt` de cada cena, com marcador idempotente para evitar duplicação em reprocessamentos. O worker Cloudflare recebe, portanto, as regras anti-template, a gramática formal e as restrições do estilo no prompt efetivamente usado.
- A animação LTX preserva a imagem-base e seu estilo; a instrução de movimento permanece subordinada à ação da cena e à identidade visual do keyframe.
- Teste específico adicionado para verificar a presença do perfil completo no prompt real do worker e impedir duplicação.
- Commits desta revisão: `d12ac01` (perfis sem motivos fixos), `2e184d3` (diretor anti-template), `56b7d1e` (abas Criar/Estilos), `5429e4a` (testes anti-template), `06356a7` (contrato 2.0), `0ebd0de` (perfil no image_prompt), `4649652` (teste de integração), `cbf7f56` (quebras de parágrafo no prompt), `372eb3f` (remoção de motivos concretos também das restrições negativas), `2131a3f` (teste contra vazamento de motivos específicos).
- Revisão estática confirmou que a aba Estilos existe, as 18 opções são carregadas do catálogo centralizado, os prompts completos permanecem internos e o worker de imagens recebe o perfil. GitHub Actions run `43988702350` (commit `2131a3f`) está em execução no momento do registro; não marcar testes como aprovados até conclusão.
- Deploy Streamlit e validação visual da nova navegação, além de storyboard e MP4 reais com estilos diferentes, permanecem pendentes.


## Idempotência e último ciclo de regressão — 17/11/2026
- `apply_visual_style_lock()` também evita duplicar os modificadores formais em `style_search_terms` quando o storyboard é reprocessado; o teste agora verifica idempotência tanto da direção anexada ao `image_prompt` quanto dos termos de busca.
- Limpeza das instruções negativas: removidas referências a objetos/cenas concretos dos campos `avoid` para reduzir ativação involuntária de clichês mesmo quando mencionados como algo a evitar.
- Commits adicionais: `372eb3f` (restrições sem exemplos de cena), `2131a3f` (teste de não vazamento), `e6be587` (idempotência do lock), `789d294` (teste de idempotência).
- Workflow atual: GitHub Actions run `43988866199` associado ao commit `6776d2f`; estado `in_progress` no último polling. O run anterior `43988771498` concluiu com sucesso o smoke de Wikimedia Commons e o typecheck Remotion; compilação Python também concluiu, enquanto a suíte unitária ainda estava em execução. Aguardar o run mais recente para conclusão integral.


## Versão e responsividade da biblioteca de estilos — 17/11/2026
- A galeria da aba “Estilos” foi ajustada para duas colunas, preservando legibilidade em telas móveis.
- Versão identificadora do app: `NEXUS-2026.11.17-style-grammar-and-library-2`.
- Commits finais de código: `9f6dd9d` (galeria em duas colunas), `6776d2f` (versão atualizada).
- GitHub Actions foi acionado novamente pelo commit `6776d2f`; aguardar todos os jobs. Acessibilidade pública do Streamlit não pôde ser consultada pelo navegador disponível; implantação visual continua sem confirmação.


## Correção de compatibilidade após CI — 17/11/2026
- O run `43988866199` identificou falhas de regressão, não falhas de compilação: testes antigos ainda chamam os estilos `Cinematográfico realista` e `Anime 2D`, removidos da seleção visível. Também detectaram que dois perfis ainda citavam motivos concretos nas instruções (paleta ASMR e negação de clichê noir).
- Correção aplicada: adicionados perfis de compatibilidade ocultos para os dois nomes antigos. Eles permanecem utilizáveis em storyboards salvos e testes, mas não entram em `STYLE_OPTIONS` e não aparecem na UI. Termos concretos foram removidos dos dois perfis que acionaram o teste.
- Novo teste garante que aliases antigos continuam funcionando sem reaparecer na galeria. Commit de compatibilidade `e99df1d`; teste `075739b`.
- Novo GitHub Actions run `43988997953` está em execução; aguardar o resultado antes de declarar a suíte aprovada.


## Remoção de exemplos visuais fixos — 17/11/2026
- Revisão pós-CI identificou que o prompt anti-template ainda carregava exemplos indiretos nos campos de paleta, luz, composição, textura e até nas frases negativas dos perfis. Esses elementos podiam continuar condicionando a geração mesmo quando descritos como algo a evitar.
- Os 18 perfis foram reescritos para descrever apenas gramática formal: tratamento de cor, iluminação, fotografia, enquadramento, textura, meio artístico e atmosfera. Nenhum perfil prescreve personagens, objetos, locais ou ações.
- A galeria “Estilos” deixou de exibir mini-cenas ilustrativas (pessoa, veículo, relógio, paisagem etc.). Agora mostra amostras abstratas de cor, luz, textura e composição — a prévia comunica a estética sem sugerir o conteúdo de um vídeo.
- Compatibilidade com os nomes antigos “Cinematográfico realista” e “Anime 2D” permanece oculta na seleção, apenas para storyboards existentes.
- Commits: `672277f` (perfis sem motivos narrativos), `e24c786` (amostras abstratas na galeria).
- Revisão estática confirmou ausência dos termos de exemplo conhecidos nos perfis e remoção do catálogo de mini-cenas do app. GitHub Actions run `43989176956` acionado; aguardando testes.


## Ajuste final do teste de gramática cósmica — 17/11/2026
- A primeira execução após remover exemplos aprovou 98 de 99 testes; a única falha era uma expectativa antiga que exigia a palavra “geometric”, removida intencionalmente para não transformar um motivo visual em parte obrigatória do estilo. O teste agora verifica “luminous contrast”, característica formal preservada no perfil.
- Commit do ajuste: `3cfbaeb`. Novo ciclo de CI acionado; resultado pendente.


## Validação CI concluída — 17/11/2026
- GitHub Actions run `43989261776` (commit `3cfbaeb`) concluiu com sucesso: `unit-tests`, `remotion-typecheck` e `commons-live-smoke` todos em `success`.
- A suíte Python executou 99 testes e terminou `OK`; inclui os testes de gramática sem motivos fixos, compatibilidade legada oculta, direção completa anexada ao prompt efetivamente consumido pelo worker e idempotência.
- O typecheck da composição Remotion passou. O smoke de Wikimedia Commons concluiu busca, download e inspeção de um vídeo licenciado.
- Estado: implementação e CI validados no GitHub. Ainda não declarar deploy Streamlit visualmente validado nem pipeline de vídeo integral validado por este ciclo; a saída MP4 de teste registrada pelo job remoto confirma artefato de teste, não uma sessão real do usuário com os novos estilos.

## Redesign da interface mobile — 17/11/2026
- Evidência visual do usuário: a versão publicada ainda apresentava o formulário longo com abas superiores e o logotipo quebrado; a referência desejada é uma experiência mobile de estúdio, com navegação inferior, campo de roteiro compacto, seletor horizontal de estilos, prévia vertical e identidade visual roxa.
- Commit `8d66cbc`: `app.py` substitui as abas Criar/Estilos por navegação inferior com quatro áreas: Criar, Biblioteca, Modelos e Perfil.
- Cabeçalho deixa de depender do PNG inline que aparecia quebrado; usa marca vetorial SVG embutida, sem requisição externa nem arquivo de imagem.
- Tela Criar passa a usar área de roteiro menor, duração compacta, estilos selecionáveis em chips horizontais e prévia vazia 9:16. Configurações de motor e diagnóstico ficam recolhidas em configurações avançadas.
- Biblioteca apresenta o último vídeo/planejamento da sessão atual; persistência entre sessões ainda não está implementada. Modelos apresenta os 18 estilos; Perfil mostra somente estado de configuração dos serviços, nunca valores de segredos.
- O pipeline de storyboard e renderização existente foi preservado. O botão principal agora é rotulado "Gerar vídeo".
- Estado: alteração gravada no GitHub main. GitHub Actions do commit `8d66cbc493536970661b3a29691351d25c4f7d20` iniciou os três checks (unit-tests, Remotion typecheck e Commons smoke), mas ainda não havia resultado final no momento desta atualização. Implantação automática e aparência real no Streamlit mobile ainda precisam ser confirmadas.
- Limitação conhecida: a prévia vazia é apenas um placeholder visual; não representa uma prévia renderizada. A biblioteca ainda é limitada à sessão ativa e não é uma biblioteca persistente.

- Validação posterior do commit `8d66cbc`: GitHub Actions run `43989995593` concluiu com sucesso nos três jobs. `unit-tests` compilou os módulos da aplicação e passou em 99 testes; `remotion-typecheck` e `commons-live-smoke` também passaram.
- A compilação do CI confirma sintaxe Python dos módulos, mas não comprova a renderização visual do Streamlit. O novo layout ainda aguarda inspeção no app publicado em celular; não afirmar implantação visual validada.

## Correção do seletor mobile após evidência do usuário — 17/11/2026
- Novas capturas do app publicado mostraram que o seletor `st.radio(horizontal=True)` não respeitava a apresentação horizontal em telas estreitas: os rótulos eram quebrados verticalmente. Também havia um cartão-resumo duplicando o estilo selecionado e a navegação inferior ficava parcialmente encoberta pela sobreposição "Manage app" do Streamlit.
- Commit `d441a75`: substituído o seletor de estilo por `st.pills(selection_mode="single")`, com chips de largura intrínseca, texto sem quebra e rolagem horizontal. Removido o cartão de resumo redundante; a escolha permanece visível no próprio seletor.
- Commit `2879abe`: barra de navegação também migrou para `st.pills`, foi elevada acima da sobreposição inferior do Streamlit e recebeu espaço de rolagem horizontal; área de prévia reduzida de 290px para 220px; espaço inferior da página ampliado para evitar conteúdo encoberto.
- Requisito mínimo do Streamlit elevado para `>=1.40`, versão que inclui `st.pills`.
- Revisão estática dos arquivos no GitHub confirmou: ambos os seletores usam `st.pills`; o antigo `st.radio` do estilo foi removido; o cartão-resumo foi removido; o placeholder ficou limitado a 220px.
- Estado: commits gravados em `main`. GitHub Actions run `43990510784` está em execução; ainda não declarar CI aprovado. A aparência final no Streamlit mobile precisa ser confirmada por nova captura após o deploy.

## Composição da tela Criar conforme referência mobile — 17/11/2026
- Referência visual recebida novamente: marca e botão de configurações no cabeçalho; campo de tema/roteiro com ação principal dentro do mesmo cartão; estilos em chips horizontais logo abaixo; narração e duração lado a lado; palco de prévia de vídeo abaixo; navegação inferior com quatro destinos.
- Commits incrementais: `03ecf31` (estrutura de cabeçalho, prompt, estilos, voz/duração e prévia); `4742897` (remoção de fragmentos duplicados do layout anterior); `1b4da95` (mover configurações avançadas para Perfil e mostrar o MP4 no palco de prévia); `69ccb98` e `542616e` (correções de indentação do bloco de configurações); `80e9647` e `42a2eea` (polimento de marca, botão de configurações e navegação com ícones).
- O fluxo funcional foi preservado: o botão superior solicita o storyboard; após o planejamento, o fluxo existente ainda oferece a etapa separada de produção/renderização do MP4. A prévia passa a hospedar o MP4 quando ele existe; sem vídeo, exibe placeholder vertical 9:16. A biblioteca e as opções avançadas continuam disponíveis nas áreas inferiores.
- Motor de produção e diagnósticos foram movidos para Perfil > Configurações avançadas; a seleção fica guardada em `nexus_render_mode` e é recuperada na tela Criar.
- Estado: código atualizado no GitHub `main`. Run `43991099437` do commit de aplicação `42a2eea` concluiu com sucesso nos três jobs. O deploy Streamlit e a confirmação visual no dispositivo continuam pendentes.

- Validação do código de interface: GitHub Actions run `43991099437`, commit de aplicação `42a2eea`, concluiu com sucesso nos três jobs (`unit-tests`, `remotion-typecheck`, `commons-live-smoke`). A suíte unitária passou; typecheck e smoke também passaram.
- O run `43991135448`, disparado pelo commit de documentação `53a4a5c`, também concluiu com sucesso os três jobs: unit-tests, Remotion typecheck e Commons smoke. O código de aplicação validado é o mesmo commit `42a2eea`.
- Limite de validação: CI confirma regressões automatizadas e sintaxe exercitada pela suíte, não confirma a aparência publicada nem o comportamento real dos widgets no navegador móvel. Aguardando confirmação visual no Streamlit após sincronização.

## Refinamento mobile: carrossel e controles compactos — 17/11/2026
- Evidência recebida em novas capturas: os estilos apareciam em várias linhas e os controles de narração/duração eram cartões altos empilhados, apesar da intenção anterior de duas colunas. Isso criava rolagem excessiva e afastava as ações principais do alcance do polegar.
- Commit `988ab9a`: seletor de estilos encapsulado em `nexus-style-carousel`, com CSS direcionado para uma única faixa flexível, sem quebra de linha e com rolagem horizontal; o objetivo é manter todos os estilos acessíveis por gesto lateral.
- Narração e duração substituem os cartões por dois gatilhos compactos de `st.popover` em uma linha de colunas forçada a não quebrar no mobile. A escolha da voz e o catálogo curado continuam disponíveis dentro do popover; a duração oferece 40, 45, 50 e 60 segundos, com 45s como padrão novo, preservando valores de sessão válidos.
- O restante do fluxo de storyboard, seleção de estilo, voz Fish Audio, renderização e prévia não foi substituído.
- Estado: implementação gravada em `main`. GitHub Actions run `43991873374` está em execução; ainda não declarar CI aprovado. A eficácia visual do CSS do carrossel e a interação dos popovers precisam de confirmação em captura real do Streamlit mobile após o deploy.

- Validação CI: GitHub Actions run `43991873374` do commit `988ab9a` concluiu com sucesso nos três jobs. `unit-tests` passou em 99 testes (`Ran 99 tests ... OK`), `remotion-typecheck` e `commons-live-smoke` também passaram.
- Isso valida regressões automatizadas e a compilação/testes do repositório; não comprova que os seletores CSS renderizem como carrossel no navegador móvel nem que os popovers tenham a ergonomia visual desejada. A confirmação visual permanece pendente.

## Correção real do overflow mobile — 17/11/2026
- As novas capturas do usuário demonstraram que o CSS adicionado no commit `988ab9a` não criou o carrossel: os chips ainda quebravam em linhas e as regras `width:max-content` em descendentes genéricos faziam o documento inteiro transbordar horizontalmente, cortando os controles de voz/duração e a prévia.
- Correção incremental: removidas as regras CSS que manipulavam a estrutura interna de `st.pills` e de `st.columns/st.popover`. O seletor agora usa o comportamento nativo oficial `st.pills(..., width="stretch", wrap=False)`, que mantém as opções numa linha e fornece rolagem horizontal dentro do próprio widget.
- Dependência mínima atualizada de `streamlit>=1.40` para `streamlit>=1.64.0`, versão cuja API documenta o parâmetro `wrap` de `st.pills`. Referência: documentação oficial do widget `st.pills`.
- Narração e duração mantêm os dois popovers em colunas; ao remover o CSS que ampliava os ancestrais, os controles deixam de herdar largura artificial. Não foi introduzida rolagem horizontal global nem largura fixa na página.
- Commits: `75870c1` (remoção do CSS invasivo e uso de wrap=False) e `dbd2738` (mínimo Streamlit 1.64.0).
- Estado: código e dependência gravados em `main`. GitHub Actions run `43992412802` do commit `75870c1` e run `43992420470` do commit de dependência `dbd2738` foram acionados; confirmar os resultados. A validação visual no Streamlit mobile permanece pendente até nova captura do usuário.

- Resultado parcial confirmado: run `43992412802` do commit de aplicação `75870c1` concluiu os três jobs com sucesso; `unit-tests` passou em 99 testes, além de `remotion-typecheck` e `commons-live-smoke`. O run `43992420470` referente ao commit de dependência `dbd2738` ainda tinha o job `commons-live-smoke` em execução no último polling; não registrar o ciclo da dependência como totalmente concluído até encerrar.

## Refinamento final da tela Criar: marca, seletores modais e palco 9:16 — 17/11/2026
- Novas capturas do usuário mostraram três pontos restantes: marca do cabeçalho desalinhada e sem o símbolo N enviado; controles de voz/duração exibidos como painéis inline grandes e com fluxo de seleção redundante; prévia ainda quadrada em vez de vertical 9:16.
- Cabeçalho: substituído o ícone geométrico anterior por um traçado vetorial do símbolo N fornecido pelo usuário. A marca N + wordmark NEXUS fica centralizada com colunas laterais equilibradas; o botão de configurações permanece à direita.
- Narração: removidos os popovers e a lista longa de expansores por categoria. Um botão abre diálogo modal central; dentro dele há um seletor pesquisável único que reúne as 40 vozes com o provedor no rótulo, amostra de áudio quando disponível e uma única ação “Usar esta voz”. IDs e catálogo existente são preservados.
- Duração: um botão irmão abre diálogo modal compacto com quatro escolhas (40s, 45s, 50s, 60s) em pills e uma única confirmação. O valor escolhido permanece em session_state e continua sendo passado ao diretor/storyboard.
- Os dois botões ficam em colunas iguais, lado a lado, com altura e estilo uniformes. A tela principal não exibe selects duplicados nem listas abertas.
- Prévia vazia: CSS atualizado para largura limitada e proporção exata 9:16; o MP4 real continua sendo exibido no mesmo palco quando disponível.
- Commits de aplicação: `063d837` (primeira versão de modais/layout e testes), `2c61ce0` (ordem segura de declaração dos diálogos após set_page_config), `5fe0df7` (path vetorial do símbolo N conectado ao cabeçalho); teste `1d5cc14` cobre marca centralizada, diálogos e proporção do palco.
- CI run `43993586380` foi acionado para o commit final `5fe0df7`; resultado ainda pendente no último polling. A validação visual publicada no Streamlit mobile ainda depende de nova captura após deploy. Não declarar aparência validada antes disso.

## Ajuste final solicitado após nova captura mobile — 17/11/2026
- Evidência: usuário confirmou que o topo ainda não usava o símbolo de marca enviado e que o seletor de duração exigia interação redundante. O fluxo de voz precisava abrir um painel mais enxuto.
- Marca: o arquivo de referência fornecido pelo usuário (N branco em fundo preto) foi vetorizado por contorno preservando a silhueta irregular/brushstroke e recortes internos. Asset versionado em `assets/nexus-mark.svg`; `app.py` o carrega diretamente do repositório. Cabeçalho deixou de usar colunas Streamlit (que colapsavam/alteravam a centralização no mobile): agora é um contêiner de largura total, lockup N + NEXUS centralizado e engrenagem posicionada de forma absoluta no canto direito, sem deslocar o centro.
- Voz: diálogo reduzido de largura large para medium, com um único seletor pesquisável por nome/provedor, amostra/descrição quando disponível e confirmação explícita da voz escolhida. Mantém IDs e catálogo existente.
- Duração: diálogo pequeno com quatro opções em grade 2×2; tocar em 40s/45s/50s/60s aplica imediatamente e fecha o diálogo via rerun. Removidos o seletor duplicado e o botão de confirmação.
- Prévia: mantida no palco vertical CSS 9:16 já existente, com MP4 real no mesmo espaço quando renderizado.
- Commits: `2d32c09` (estrutura de cabeçalho e seleção de duração), `06f67fd` (asset SVG vetorizado da marca), `dc884b7` (testes de contrato), `cba7adf` (diálogo de voz compacto/pesquisável).
- Validação intermediária: o run `43993995236` do commit `2d32c09` falhou apenas porque o teste antigo ainda esperava as colunas removidas; o teste foi atualizado no commit `dc884b7`. Runs `43994072632` e `43994103531` acionados para os commits de teste e app final; consultar resultado antes de declarar CI aprovado.
- Limite: alterações estão em `main`; aparência publicada no Streamlit mobile ainda não foi confirmada. A validação automatizada não comprova alinhamento/renderização do SVG nem comportamento real do modal no dispositivo.

- Validação confirmada: run `43994072632` do commit `dc884b7` passou nos três jobs; suíte unitária executou 102 testes e terminou em `OK`, além de Remotion typecheck e Commons live smoke aprovados.
- Run `43994103531` do commit final de aplicação `cba7adf`: Remotion typecheck já aprovado; unit-tests e Commons smoke ainda estavam em execução no último polling. Não declarar o código final totalmente validado até a conclusão desses dois jobs.

- Run `43994160209` do commit `56f7c8d` concluiu com sucesso nos três jobs: unit-tests, Remotion typecheck e Commons live smoke. O run anterior `43994072632` também passou com 102 testes.
- Ajuste final de robustez do cabeçalho: removido `display:flex` do contêiner Streamlit externo para não interferir no DOM interno; o lockup centraliza por largura total própria e o botão de configurações fica em posicionamento absoluto. Commit `a53364c`.
- Run `43994261797` foi acionado para esse último ajuste; estava em fila no último polling. A validação do layout publicado segue pendente.

## Correção do tamanho dos controles de voz e duração — 17/11/2026
- Evidência: nova captura mobile mostrou que os dois botões estavam extrapolando a largura disponível; a segunda coluna ficava parcialmente fora da tela e o primeiro botão ocupava mais que metade da linha.
- Correção em `app.py`: o bloco dos controles agora usa CSS Grid explícito com duas colunas iguais `minmax(0,1fr)`, gap fixo, largura/máximo de 100%, `min-width:0` e `box-sizing:border-box` em todos os níveis. As colunas Streamlit deixam de impor largura flex percentual e os botões ficam contidos em cada metade. Altura e aparência foram preservadas.
- Teste de regressão adicionado em `tests/test_app_import_resilience.py` para verificar a grade 50/50 e as restrições contra overflow.
- Commits: `e4bcbbc` (CSS de layout) e `bafb49f` (teste de regressão).
- Estado: alteração enviada à branch `main`; CI do commit final ainda precisa ser consultado. A captura do usuário confirma o problema original; a aparência após deploy ainda depende de nova captura.

## Correção do seletor de narração: catálogo completo e escolha em um toque — 17/11/2026
- Evidência: captura mobile mostrou que o seletor nativo abria uma lista suspensa interna, exibindo inicialmente apenas as primeiras vozes CapCut e exigindo um toque adicional para abrir a lista. Isso ocultava visualmente os demais provedores.
- Catálogo verificado em `nexus/voice_catalog.py`: 40 IDs preservados e agrupados em CapCut (14), ElevenLabs (4) e Licenciadas Fish (22). `nexus/audio.py:list_curated_voice_catalog` enriquece os IDs com metadados sem descartar opções quando uma consulta individual falha.
- Alteração em `app.py`: removido o `st.selectbox` nativo do diálogo. O painel agora mostra os três provedores com contagem, seções abertas por padrão e opções em duas colunas. Cada voz é um botão direto; um toque grava o ID e o nome exatos no estado da sessão e fecha o diálogo por rerun. As 40 entradas permanecem selecionáveis mesmo quando os metadados não estão disponíveis.
- Transparência: o painel informa o total carregado e alerta se o serviço devolver menos de 40 entradas; não mascara falhas parciais como catálogo completo.
- Teste de regressão em `tests/test_app_import_resilience.py` cobre as três categorias, exibição das contagens, opções em duas colunas e seleção sem seletor/confirmador extra. O teste existente em `tests/test_audio.py` já valida os 40 IDs e as quantidades por categoria.
- Commits: `f9d0e3a` (interface de seleção direta) e `89c5b24` (teste de regressão).
- Estado: código e teste enviados à branch `main`. CI do commit final ainda precisa ser consultado; não declarar validado até todos os jobs concluírem. A atualização visual no Streamlit mobile ainda depende de nova captura após deploy.

## Prévia de áudio individual para cada voz — 17/11/2026
- Solicitação/capturas: usuário aprovou a lista por provedor e pediu um botão pequeno ao lado de cada nome para ouvir a voz antes de selecioná-la.
- Em `app.py`: cada opção agora é renderizada em linha com botão de seleção e controle circular compacto ▶ ao lado. Ouvir não altera a voz selecionada; tocar no nome continua sendo a única ação de seleção.
- Vozes com `sample_audio` usam a amostra publicada diretamente. Se não houver amostra, ▶ chama `fish_audio.generate_fish_preview` sob demanda; o MP3 resultante fica em `st.session_state` e aparece no mesmo controle compacto para reprodução. Não são geradas amostras para as 40 vozes automaticamente.
- Segurança/robustez: URL de áudio escapada para HTML; somente fontes http/https/data são aceitas no player. Falhas de geração são mostradas sem impedir seleção da voz.
- Teste de regressão adicionado em `tests/test_app_import_resilience.py` para presença do botão junto ao nome, player compacto, uso da amostra publicada e geração sob demanda.
- Commits: `627d2cf` (player e prévia sob demanda), `aea5de0` (teste de regressão).
- Estado: enviado à branch `main`; CI do commit final ainda pendente. O funcionamento de reprodução no navegador móvel depende de confirmação visual/funcional após o deploy; os testes estáticos não substituem essa verificação.

## Refinamento do player de prévia das vozes — 17/11/2026
- Evidência da nova captura mobile: o iframe de áudio era renderizado abaixo do nome, aumentando a altura da lista; players independentes também permitiam reprodução simultânea e não ofereciam um controle de pausa integrado ao botão compacto.
- Em `app.py`: removido o iframe HTML por voz. Nome e botão de prévia agora são dois botões Streamlit nativos em colunas 86/14 na mesma linha. O botão alterna entre ▶ e ⏸ para a voz ativa.
- Todos os previews usam um único `st.audio` compartilhado. Ao tocar outra voz, a fonte do player é substituída; ao tocar novamente na voz ativa, a fonte é removida e a prévia é interrompida. Isso elimina players simultâneos e disponibiliza os controles nativos de reprodução/pausa.
- As amostras publicadas (URL ou data URI) continuam suportadas; vozes sem amostra geram MP3 sob demanda e armazenam o áudio em sessão.
- Teste de regressão substitui o teste anterior do iframe e verifica botões alinhados em colunas, toggle ▶/⏸, player compartilhado único e remoção do iframe/player individual.
- Commits: `d08a57e` (interface e player único), `968fd6f` (teste de regressão).
- Estado: enviado à branch `main`; CI do commit final pendente. A captura do usuário confirma a falha anterior; a nova disposição e autoplay/pausa ainda dependem de confirmação no navegador móvel após deploy.

## Fluxo de narração: ouvir primeiro e confirmar a escolha — 17/11/2026
- Evidência da captura mobile: controles de prévia e seleção em colunas empilharam; tocar no nome alterava imediatamente a voz e fechava o diálogo, enquanto o player compartilhado ficava separado da lista.
- Mudança em `app.py`: cada voz agora é um único botão de largura total. Tocar no nome prepara/reproduz a amostra e mantém o diálogo aberto. A escolha fica em estado pendente (`nexus_pending_voice_*`), sem alterar a voz usada na produção.
- Quando há voz pendente, o diálogo mostra um único player nativo e um botão explícito **Confirmar voz [nome]**. Só esse botão grava `nexus_fish_voice_id/name` e encerra o diálogo via rerun. Tocar em outro nome troca a prévia pendente; a seleção confirmada anterior é preservada até nova confirmação.
- Removidos os botões ▶/⏸ individuais e o layout de duas colunas que o Streamlit empilhava em telas estreitas. O player nativo fornece pausa/reprodução.
- Teste de regressão verifica prévia ao tocar no nome, estado pendente, player único e confirmação explícita antes de atualizar a voz final.
- Estado: implementação e teste enviados à branch `main`; CI e comportamento mobile após deploy ainda pendentes. Autoplay pode ser restringido pelo navegador; o player nativo permanece disponível para iniciar/pausar manualmente.

## Correção do fechamento indevido do seletor ao ouvir prévia — 17/11/2026
- Evidência da captura mobile: tocar na voz fechava o diálogo; ao reabri-lo, a prévia pendente aparecia e começava a tocar.
- Causa identificada em `app.py`: o clique na voz atualizava o estado pendente e chamava `st.rerun()` no escopo global, descartando o diálogo antes de renderizar a prévia.
- Correção: o clique de prévia e a ação de tentar novamente o catálogo usam `st.rerun(scope="fragment")`, atualizando somente o fragmento do diálogo. A confirmação final continua usando `st.rerun()` global intencionalmente para fechar o seletor e retornar à criação.
- Teste de regressão adicionado para distinguir o rerun local de prévia do rerun global de confirmação.
- Commits: `b1753c4` (correção) e `1db54dd` (teste).
- Estado: enviado à branch `main`; CI ainda precisa concluir. A validação final de manter o diálogo aberto e tocar a amostra depende de teste no navegador móvel após deploy.

## Galeria de estilos com prévias visuais distintas — 17/11/2026
- Solicitação/captura mobile: a aba Modelos já apresentava imagens SVG abstratas, mas todas repetiam a mesma composição orbital; o usuário pediu uma imagem que mostre melhor a identidade de cada estilo.
- Em `app.py`: `style_preview_svg()` agora cria 18 amostras SVG distintas, uma por estilo, variando composição, contraste, luz, textura e tratamento gráfico. As amostras demonstram gramática visual e não prescrevem personagens, objetos ou cenários para os vídeos.
- Teste de regressão verifica cobertura dos 18 estilos e a manutenção da galeria com imagens por cartão.
- Também foi corrigido um teste legado do seletor de narração que ainda esperava seleção imediata; agora ele valida prévia pendente e confirmação explícita.
- Commits: `33e5af2` (pré-visualizações distintas), `8e14ffa` (teste da galeria) e commit subsequente de ajuste do teste do fluxo de voz.
- Estado: código enviado à branch `main`; CI ainda precisa concluir. A aparência final no navegador mobile depende de nova captura após deploy.

## Correção do limite de payload no envio do storyboard ao GitHub Actions — 17/11/2026
- Evidência do teste real no Streamlit: planejamento de 10 cenas/45s foi gerado, mas a etapa de produção parou com "O storyboard excede o limite seguro de envio ao GitHub Actions".
- Causa confirmada em `nexus/github_renderer.py`: o manifesto JSON era enviado integralmente (após criptografia Fernet) como input de `workflow_dispatch`, com bloqueio preventivo de 42.000 caracteres antes mesmo da tentativa de envio.
- Solução incremental: novo par `encrypt_compressed_text/decrypt_compressed_text` em `nexus/render_crypto.py` aplica zlib nível 9 antes da criptografia Fernet. O app envia o manifesto comprimido e criptografado; `nexus/remote_render_job.py` descriptografa/descomprime antes de reconstruir o mesmo JSON completo. Nenhuma cena ou campo é removido.
- O limite preventivo agora mede o objeto completo de inputs do workflow após compressão, com teto de 60.000 caracteres para manter margem em relação ao limite do evento GitHub. Se ainda exceder, informa que o manifesto permanece grande mesmo após compressão e não reduz o conteúdo.
- Testes adicionados/ajustados: round-trip da compressão; storyboard maior que 42 KB aceito e recuperado sem perda; worker usa manifesto comprimido.
- Commits: `7fb8eff` (crypto comprimida), `bbf1bd1` (dispatch comprimido), `f716616` (worker descomprime), `e9b6c37` (teste crypto), `8968995` (teste de manifesto grande), `6cd43ce` (teste do worker).
- Estado: implementação enviada à branch `main`; CI do commit mais recente ainda precisa concluir. Não declarar render validado até nova tentativa no app gerar e recuperar MP4 real.

- Validação CI concluída: execução GitHub Actions `43999265137`, commit `82a05b2f4f1b613da989f82d8b2923faff91b0f5`, resultado `success`; jobs `unit-tests`, `remotion-typecheck` e `commons-live-smoke` concluídos com sucesso. Isso valida os testes automatizados e o contrato de transporte comprimido; não equivale a render MP4 real.

## Incidente de produção — recarga de módulo criptográfico (17/11/2026)
- Após os testes automatizados anteriores passarem, a tentativa real no Streamlit falhou com ImportError: `cannot import name 'decrypt_compressed_text' from 'nexus.render_crypto'`.
- A inspeção do código no GitHub confirmou que `nexus/render_crypto.py` define a função e `nexus/github_renderer.py` a importa. O bloco de produção em `app.py` recarregava apenas `nexus.github_renderer`, sem recarregar primeiro sua dependência criptográfica; isso pode deixar a referência antiga em memória no processo Streamlit.
- Commit `401ccb83343f90222678b64d475f6aade5a4c13d`: `app.py` agora recarrega `nexus.render_crypto` primeiro, verifica a presença de `decrypt_compressed_text` e só então recarrega `nexus.github_renderer`.
- Verificação pós-commit: o bloco atualizado foi relido do GitHub e confirmado na branch `main`. A implantação no Streamlit e a produção MP4 ainda NÃO foram validadas. Não declarar resolvido até nova tentativa real.


## Incidente de render — calibração de narração antes da geração visual (17/11/2026)
- Evidência da execução real GitHub Actions `44055004220`: imagens e animações foram geradas; o worker falhou ao sincronizar áudio de 37,6s com a linha do tempo de 45,0s. A faixa segura de ajuste de 15% rejeitou a proporção 0,8356. Não foi falha de Cloudflare, Modal ou Remotion.
- Causa arquitetural: `nexus/remote_render_job.py` gerava imagens e clipes I2V antes de sintetizar/medir a narração. O erro de duração só era descoberto depois de aproximadamente 10 minutos de processamento visual.
- Correção enviada à branch `main`: a narração Fish Audio agora é gerada e medida antes de qualquer geração de imagem. Quando a duração real diverge mais de 10% da meta, o worker usa `revise_narration_for_duration` com Gemini para reescrever somente as falas, preservando a ordem e as cenas; sintetiza novamente e mede outra vez. São permitidas até duas calibrações. Se a narração permanecer fora da faixa segura de 15%, o trabalho falha antes de iniciar a geração visual.
- O worker recalcula as durações das cenas após a revisão. A credencial Gemini, o tema e o estilo são enviados dentro do bloco de credenciais já criptografado; nenhuma chave é enviada em texto simples.
- `app.py` agora encaminha `GEMINI_API_KEY`, tema e estilo ao dispatcher; `nexus/github_renderer.py` os inclui no pacote criptografado.
- Testes atualizados para cobrir envio criptografado dos dados de calibração e o cenário de narração inicialmente curta (37,6s) revisada para a meta antes de iniciar imagens.
- Commits: `871c542` (worker/preflight e calibração), `24f7f47` (dispatcher criptografado), `2d8dab8` (app), `48488bc` (teste do dispatcher), `8e25496` (teste de calibração), `81cec91` (fixture alinhada).
- Estado: código e testes enviados à branch `main`. CI `44057057040` concluído com sucesso: `unit-tests`, `remotion-typecheck` e `commons-live-smoke` aprovados. Isso valida regressões e integração automatizada, mas não substitui render real. A nova execução real no Streamlit ainda NÃO foi validada; não declarar MP4 concluído até o vídeo ser produzido, recuperado e inspecionado.


## Incidente de instalação Remotion — 17/11/2026
- Execução real `44058484835` falhou no passo `Install Remotion dependencies`, antes de typecheck, geração de imagens, Fish Audio, Modal LTX ou render MP4. Os passos seguintes foram explicitamente ignorados.
- Erro: npm HTTP 404 ao baixar `csstype-3.2.4.tgz`. Pesquisa do registro npm mostra `csstype` publicado atualmente em `3.2.3`; `3.2.4` não está publicado.
- Correção aplicada em `remotion/package.json`: override exato `"csstype": "3.2.3"` para forçar a resolução da versão publicada e evitar a dependência transitiva inexistente.
- Commit: `8a59784e163b6e02774d5da97c49ca7cbd6cb6e6`.
- Impacto de custo: a etapa de render foi ignorada antes do passo que chama `nexus.remote_render_job`; portanto esta execução não iniciou Modal LTX nem geração de mídia.
- Estado: aguardando CI da correção e depois nova tentativa real. MP4 não validado.


## Melhoria de UX — acompanhamento da produção e organização do Criar (17/11/2026)
- Solicitação: remover parte do espaço vertical abaixo da marca NEXUS, manter o logotipo no mesmo tamanho e aproximar o formulário/controles; mostrar o estado do planejamento e da renderização logo abaixo dos controles de voz e duração, em vez de deixar erros e resultados distantes no fim da tela.
- CSS do cabeçalho ajustado para reduzir altura/margens sem alterar dimensões da marca SVG e do nome NEXUS.
- Criado slot de status no fluxo principal, logo após os controles de voz/duração. Quando o storyboard existe, mostra quantidade de cenas e duração e orienta o próximo passo. Durante render, o mesmo slot recebe barra, etapa atual, tempo decorrido e restante estimado; erros também são apresentados nesse espaço.
- `nexus/github_renderer.py` agora envia ao callback uma fração de progresso, tempo decorrido e restante estimado. Como o workflow agrupa a geração de mídia numa etapa longa e não expõe progresso por frame, a barra entre o início e conclusão é explicitamente uma estimativa temporal (base inicial de 10 min), não telemetria exata da Modal. O estado final só chega a 100% depois que o MP4 é recuperado e as verificações/auditoria do app terminam.
- Teste de regressão do callback de progresso adicionado em `tests/test_github_renderer.py`.
- Commits: `bd9bdd5` (telemetria estimada), `91f9227` (layout/status no app), `6cd8712` (correção de sintaxe no cálculo percentual), `1b81542` (teste do callback).
- CI do commit `1b815421bca7c1b5f75ebdf49f54af98fa71d755`: `unit-tests`, `remotion-typecheck` e `commons-live-smoke` aprovados na execução `44062631463`. A execução de render de integração `44062631615` concluiu com sucesso: dependências Remotion instaladas, adaptador Python executado, manifesto de movimento renderizado, streams MP4 e duração validados, artefatos enviados. O passo de demonstração manual de 50s ficou explicitamente skipped; o teste de integração do adaptador e MP4 foi aprovado.
- Deploy Streamlit e validação visual em dispositivo móvel ainda pendentes.

- Atualização de validação: o job `render-demo` da execução `44062631615` terminou `success`; o teste de integração gerou e validou MP4 sintético via adaptador Python + Remotion. Isso não é ainda uma produção real usando Cloudflare + Modal LTX/Fish Audio no app.


## Incidente de calibração Gemini e reorganização do fluxo Criar — 17/11/2026
- Render real `44063454151` falhou durante a calibração de narração, antes da geração de imagens e Modal I2V. A Fish Audio produziu 49,6s para uma meta de 45,0s; o worker chamou `revise_narration_for_duration`, mas o callback de leitura de secrets aceitava só um argumento e `director._request` solicitou `secret_reader("GEMINI_MODEL", "auto")`. Erro exato: `TypeError: lambda() takes 1 positional argument but 2 were given`.
- Correção: `nexus/remote_render_job.py` agora usa callback compatível com argumento opcional `default`, preservando o default de `GEMINI_MODEL`. Commit `d339186`.
- Teste de regressão: `tests/test_remote_render_job.py` simula a calibração e verifica tanto `secret_reader("GEMINI_API_KEY")` quanto `secret_reader("GEMINI_MODEL", "auto")`. Commit `13afbbc`.
- UX: o bloco de prévia do vídeo estava antes do storyboard e do botão de produção, empurrando o planejamento para muito abaixo da tela no celular. O bloco de prévia foi movido para depois do planejamento/produção; assim o roteiro, expander e botão ficam logo depois dos controles de voz/duração, antes da prévia vertical. Erros de render agora substituem a barra de progresso no próprio painel superior em vez de surgir como alerta separado; commit `f9e992f`.
- Barra: ao terminar o worker, o texto passa a indicar recuperação/validação do MP4 e o restante estimado zera; não exibe mais minutos restantes estimados após o worker concluir. Commit `812b763`.
- CI das correções está em execução: runs `44064355595`, `44064383883`, `44064401470`, `44064418134`. Aguardando todos os checks antes de nova tentativa real.
- Ainda não há vídeo MP4 real validado. Não iniciar nova produção até CI aprovado e sincronização Streamlit.

- Atualização CI: execução `44064383883` (inclui teste da função de leitura com 2 argumentos) concluiu `unit-tests`, `remotion-typecheck` e `commons-live-smoke` com sucesso. Execução `44064401470` para o rearranjo visual concluiu `unit-tests` e `remotion-typecheck` com sucesso; `commons-live-smoke` ainda estava em andamento no último acompanhamento. Execuções de render de integração `44064355595` e `44064418134` ainda em andamento no último acompanhamento.
- O deploy/sincronização do Streamlit e a validação visual no celular ainda dependem do CI terminar e da atualização do app. Não pedir nova produção real enquanto isso não for confirmado.


## Mudança de política de duração — janela editorial +10s (17/11/2026)
- Solicitação: abandonar a duração exata como obrigação do Gemini. A duração escolhida passa a ser referência editorial, com teto de +10s (30→40s; 40→50s; 60→70s), priorizando qualidade, clareza, progressão, narração natural e coerência entre voz e cenas.
- `nexus/director.py`: SYSTEM e prompt do storyboard agora orientam mirar a duração escolhida e usar a margem apenas quando o raciocínio precisar; proibido encher texto, repetir ou cortar ideias essenciais para bater segundo exato. A quantidade mínima de cenas é calculada pelo teto, mantendo clipes de até 5s. Planejamento mostra estimativa preliminar por contagem de palavras.
- `validate_storyboard` valida teto requested+10s em vez de soma exata com a duração escolhida.
- `_fit_scene_durations` agora distribui uma duração medida/estimada proporcionalmente às palavras de cada cena, com clipes entre 1,5 e 5s, sem forçar a duração solicitada.
- `nexus/remote_render_job.py`: Fish Audio é fonte de verdade. Mede o áudio natural; se estiver dentro do teto, usa exatamente essa duração. Não estica nem comprime a voz. Só chama revisão editorial se exceder o teto, permitindo uma única edição para remover redundâncias sem acrescentar conteúdo; se ainda exceder, interrompe antes de gerar imagens. Recalcula os tempos de cena com a duração real medida e valida o MP4 contra essa duração.
- `app.py`: planejamento informa estimativa, referência e limite máximo; deixa claro que a duração final acompanhará a voz real.
- Testes alterados para verificar alocação proporcional ao áudio medido, margem de +10s e ausência de time-stretch no worker.
- Commits principais: `41b5a3e` (diretor/janela), `fc038c9` (worker), `ccc77f9` (UI), `09c8bab` e `cb6f8e3` (cobertura de cenas), `1480cc7` (revisão somente para teto), `c0289fb` e `3a742e4` (teste worker), `f2c7ca9` (timeline medida), `dfb48d2` (instruções SYSTEM), `87a4877` (fixture de teste).
- CI consolidado do commit `87a4877`: execução `44066397504` concluiu com sucesso (`unit-tests`, `remotion-typecheck` e `commons-live-smoke`). Execuções intermediárias falharam por fixture de teste com newline escapado duas vezes; corrigido no commit `87a4877`.
- Não há render real validado com esta política ainda. Não consumir créditos da Modal até CI passar; depois realizar teste controlado e conferir duração real do MP4.

- Validação confirmada: todos os checks da execução `44066397504` passaram no commit `87a4877`. O commit posterior de documentação `f5ad5b7` também iniciou CI separado; sem alterações adicionais de código após o commit testado.


## Correção do polling do GitHub Actions — 17/11/2026
- Evidência real do usuário: ao iniciar a produção, a interface exibiu `cannot access local variable 'status' where it is not associated with a value`.
- Causa confirmada em `nexus/github_renderer.py`: durante a janela entre o dispatch e a primeira aparição da execução na API do GitHub Actions, o callback de progresso lia `status` antes de sua primeira atribuição. O mesmo ramo também dependia de `remaining_seconds` antes de qualquer atribuição.
- Correção: o callback da fase de espera usa apenas o tempo decorrido e a estimativa restante; não consulta estado de execução que ainda não existe. O polling do status real continua no segundo loop, após a execução ser localizada.
- Teste de regressão adicionado em `tests/test_github_renderer.py`: simula uma primeira consulta sem execução visível, aciona o callback de progresso e depois devolve a execução; valida recuperação do MP4 simulado.
- Estado: correção gravada no GitHub; CI e sincronização do Streamlit aguardam validação. Não iniciar novo render pago até o CI passar e o app publicado carregar a correção.


## Auditoria da primeira produção real LTX e plano de qualidade/custo — 17/11/2026
- MP4 fornecido pelo usuário: 45,568s, 720×1280, H.264, 30 fps. Inspeção visual em amostras temporais confirmou cenas quase estáticas, com movimentos físicos discretos e zooms/deslocamentos repetidos. O usuário avaliou a entrega como inaceitável; essa avaliação reprova a qualidade audiovisual mesmo com MP4 tecnicamente válido.
- Execução real associada: GitHub Actions run `44068327952`, job `133987750172`, sucesso técnico. O log registra 10 clipes LTX, total de 45,417s, 151,337s somados de inferência, resolução 512×896 e 50 passos por cena. Portanto, o worker LTX foi de fato chamado e retornou 10 MP4s; o problema é a qualidade/magnitude do movimento, não ausência de chamada.
- Custo informado pelo usuário: US$ 0,61 para LTX/Modal; teto desejado: US$ 0,50 por vídeo. O log de inferência não contém o tempo de carregamento do modelo nem o tempo total faturável da Modal, então não permite reconciliar o valor. A US$ 0,001097/s de H100, 151,337s de inferência equivalem a aproximadamente US$ 0,166 apenas de GPU de inferência; a diferença sugere overhead de inicialização/carregamento/tempo faturável adicional, mas precisa ser medida, não presumida.
- Causa técnica identificada: `modal_worker.py` usa `Lightricks/LTX-Video` (família 0.9.x, legado) via `diffusers==0.32.2` e chamada direta de `LTXImageToVideoPipeline`, single-stage, sem o workflow multi-scale/upscaler recomendado pelo repositório oficial. A Lightricks indica o ComfyUI como workflow recomendado para melhor fidelidade; a documentação atual recomenda LTX-2.5 para novos projetos. Fontes: README oficial LTX-Video e docs LTX-2.5.
- Causa de montagem: `remotion/src/NexusVideo.tsx` aplicava zoom, pan, drift, rotação e pulsos de beats também sobre clipes MP4 gerados pelo LTX. Isso sobrepunha movimento digital repetitivo ao movimento gerado.
- Causa de prompt/falha silenciosa: `video_motion_prompt` era solicitado ao Gemini, mas não era obrigatório no validador; o fallback de `nexus/modal_i2v.py` misturava `image_prompt` (descrição estática) e `visual_action` (português) no prompt do LTX. A documentação oficial I2V diz para descrever o movimento após a imagem de referência, não repetir o que já está visível.
- Plano de engenharia: (1) obrigar prompt I2V dedicado, em inglês, cronológico e com ação física observável; (2) tornar a imagem FLUX um quadro inicial pronto para a ação; (3) remover transformações digitais do Remotion sobre vídeo gerado; (4) registrar tempo de carregamento, tempo total da chamada Modal, GPU, passos e prompts; (5) implementar avaliação de movimento/continuidade antes de aprovar clipes; (6) comparar o caminho oficial ComfyUI LTX-Video 0.9.8 multi-scale e LTX-2.5 I2V two-stage/distilled em testes controlados antes de substituir o worker.
- Referência de preço Modal publicada: H100 US$0,001097/s; A100 80GB US$0,000694/s; L40S US$0,000542/s. Não mudar GPU apenas com base em preço nominal: medir tempo real, memória, inicialização e custo total. Fonte: Modal pricing.
- Regra financeira: nenhum teste de render completo ou retry automático deve ser iniciado sem estimativa de custo compatível com teto de US$0,50; não gerar novamente os 10 clipes para testar pequenas alterações. Preferir testes unitários/estáticos e um teste controlado aprovado pelo usuário.
- Estado inicial desta auditoria: hipóteses e causas de código documentadas; alterações corretivas de prompt, montagem e telemetria em andamento. Ainda não há novo MP4 de qualidade validado nem custo real reconciliado.


## Continuidade de personagem via FLUX.2 Klein — 17/11/2026
- Pesquisa oficial Cloudflare confirmou que FLUX.2 Klein 4B aceita até quatro imagens de referência via multipart `input_image_0` ... `input_image_3`, cada uma menor que 512×512. Isso permite ancorar identidade do protagonista em vez de pedir consistência apenas por texto.
- Implementação: o diretor define `visual_continuity.visual_arc`, `lead_character` e `character_reference_prompt`. Quando há protagonista recorrente, o worker gera uma referência 448×448 e a envia para cada imagem de cena; o prompt instrui o FLUX a preservar identidade, mas variar pose, ação, enquadramento e ambiente.
- O diretor agora privilegia continuidade de protagonista quando o roteiro segue uma jornada individual; variedade deve vir da fotografia e dos inserts, não da troca arbitrária de pessoas.
- Arquivos: `nexus/director.py`, `nexus/cloudflare_images.py`, `nexus/remote_render_job.py`; testes em `tests/test_cloudflare_images.py` e `tests/test_director_scene_count_repair.py`.
- Custo adicional estimado da imagem de referência: uma geração 448×448; o custo exato depende da unidade faturada do Workers AI e será medido no relatório/conta Cloudflare. Não envolve Modal/LTX.
- Estado: implementação enviada à branch main; CI pendente. Ainda não validada em MP4 real.

- Ajuste de custo adicional: o worker Modal tinha `scaledown_window=60` apesar de cada render fazer uma única chamada em lote. Reduzido para 5s, preservando o tempo de execução do lote e evitando manter H100 ociosa por um minuto após o trabalho. O teto de economia por execução é 55s de GPU (aprox. US$0,060 em H100; US$0,038 em A100 80GB), antes de CPU/memória. Commit Modal: 5cb0ed112b00338ba8d56dd4d5d6f99821171adb.
- Segurança da referência FLUX: valida MIME real PNG/JPEG/WebP e impede enviar referências para modelo diferente de FLUX.2 Klein 4B. Commit: a439eb3e8337c715a174d404e111dbb5af37a5c5.

- Correção de configuração LTX confirmada na documentação Diffusers: a revisão fixa `a6d59ee37c13c58261aa79027d3e41cd41960925` do repositório `Lightricks/LTX-Video` contém os pesos `ltx-video-2b-v0.9.1.safetensors` e `ltx-video-2b-v0.9.safetensors`; portanto o worker atual usa a família 2B v0.9.1, não LTX 13B nem LTX-2.5. O `model_index.json` dessa revisão registra Diffusers 0.32.0.dev0. Fonte: snapshot Hugging Face a6d59ee.
- Para LTX 0.9.1+, a documentação Diffusers recomenda `decode_timestep=0.05` e `image_cond_noise_scale=0.025`; para modelo não destilado recomenda guidance mais alto, por exemplo 5.0. O worker estava usando guidance 3.0 e omitindo os dois parâmetros. Ajustado para 50 passos, guidance 5.0 e parâmetros de condicionamento 0.05/0.025. Commit: e907c22acb9030c0d96bd6cfe1d724eff1224d7a.
- Próxima decisão de modelo ainda aberta: comparar LTX-Video 0.9.8 13B distilled (com workflow multi-scale/upscaler recomendado) e LTX-2.5 22B distilled (recomendado atualmente para projetos novos). Não trocar às cegas: ambas as opções precisam de estimativa e benchmark dentro do limite financeiro. O LTX 0.9.8 oficial recomenda ComfyUI para maior fidelidade e apresenta fluxo de geração em baixa resolução, upscaler latente 2× e refinamento.

## Substituição do pipeline LTX legado por 0.9.8 distilled multi-scale — 17/11/2026
- Identificação anterior: revisão HF `a6d59ee...` carregava pesos LTX 2B v0.9.1, 50 passos, guidance 3 e geração direta de uma etapa sem upscaler.
- Implementação nova em `modal_worker.py`: usa o pacote oficial `ltx_video` da revisão GitHub `50f0aef1297574a4b29acbdb874e3a363a6d5f2e`, checkpoint `ltxv-2b-0.9.8-distilled.safetensors`, spatial upscaler 0.9.8 e `LTXMultiScalePipeline`.
- Perfil: primeira passagem 7 timesteps em baixa resolução; upscaling latente 2×; segunda passagem 3 timesteps de refinamento; guidance 1.0; decode timestep 0.05; decode noise scale 0.025; image conditioning noise 0.025. Prompt enhancement LTX desligado para não carregar Florence/Llama adicionais, pois Gemini já fornece o prompt dirigido.
- GPU Modal alterada de H100 para L40S (preço publicado US$0,000542/s contra H100 US$0,001097/s) e scaledown mantido em 5s. A redução de custo total é hipótese até medir o primeiro render; tempo de inferência pode variar por GPU e o pipeline agora inclui upscaler.
- Adicionado `nexus/ltx_config.py` e `tests/test_ltx_config.py` para proteger modelo, schedule, upscaler, GPU e cópia independente da configuração.
- Estado: implementação no GitHub; CI pendente. Ainda não implantada na Modal e não testada em GPU real. Não declarar qualidade ou custo final validados até render controlado e leitura do custo efetivo.

## Atualização de implementação LTX e orçamento — 17/11/2026
- Pipeline substituído: LTX 2B v0.9.1 single-pass foi trocado pelo perfil oficial LTX-Video 2B v0.9.8 distilled multi-scale, com 7 timesteps na primeira passagem, upscaler latente 2× e 3 timesteps de refinamento. Código LTX oficial pinado em `50f0aef1297574a4b29acbdb874e3a363a6d5f2e`; pesos e upscaler são obtidos pelos nomes de arquivo 0.9.8 do repositório oficial.
- Modal GPU: alterada de H100 para L40S (US$0,000542/s, aproximadamente 50,6% menos por segundo que H100). `scaledown_window` de 60s para 5s.
- Proteção de custo: orçamento interno de GPU limitado a US$0,42, reservando US$0,08 para CPU/memória e variação de cobrança. O worker mede o tempo de carregamento e o tempo do lote e interrompe a geração antes de iniciar cenas adicionais quando a estimativa atinge o limite. Isso é uma estimativa operacional, não garantia de fatura; o primeiro smoke test vai registrar tempo total e custo estimado de GPU.
- Telemetria: cada clipe e o relatório do MP4 registram modelo/revisão, GPU, tempo de carregamento, tempo de inferência, tempo de lote, tempo total da chamada Modal, schedule 7+3, guidance, parâmetros de condicionamento e estimativa de custo GPU.
- Smoke test Modal atualizado: gera apenas um clipe de 2s, mede a chamada completa, extrai quadros inicial/meio/final e reporta estimativa de custo GPU. A observação no relatório deixa explícito que CPU/memória são adicionais e que o teste técnico ainda requer revisão visual humana.
- Continuidade: o diretor define arco visual e protagonista; FLUX.2 Klein gera uma referência 448×448 e a reutiliza nas imagens de cena. O prompt LTX é obrigatório, em inglês, focado apenas na ação após a imagem inicial. Remotion não aplica mais zoom/pan/shake sobre clipes LTX.
- CI: execução `44074680173` no commit `78dd8e570bf62a61d5476f1d40538fb249ec1981` passou nos testes unitários e compilação. Execução `44074672124` passou também em `remotion-typecheck` e `commons-live-smoke` no commit imediatamente anterior; o commit seguinte alterou apenas o relatório de custo. Demo Remotion do commit atual ainda em execução no último acompanhamento.
- Não implementado/validado ainda: deploy do novo worker na Modal e render real de smoke test. O workflow `Deploy NEXUS Modal video worker` continua manual. Nenhum novo render pago de vídeo completo foi iniciado. A qualidade e o custo final do novo pipeline permanecem pendentes de validação em GPU real.

## Correção após tentativa de deploy Modal — 17/11/2026
- Execução iniciada pelo usuário: workflow `44075161120` falhou no passo `Deploy serverless LTX worker`; o smoke test foi pulado e nenhuma inferência foi iniciada.
- Log exato: Modal rejeitou `image.add_local_python_source("nexus")` porque havia passos de build depois dele. A exigência é que `add_local_*` seja o último passo da cadeia de imagem ou use `copy=True`.
- Correção aplicada no commit `7f7626e758231c4b4f89e4ee9cf3a08fdbe15351`: movido `add_local_python_source("nexus")` para depois do último `.env(...)`, tornando-o o passo final do build.
- Estado: correção enviada para main; novo CI e novo deploy ainda precisam ser executados. O pipeline LTX 0.9.8 multi-scale não foi carregado em GPU real; qualidade e custo permanecem não validados.


## Diagnóstico gratuito de movimento por clipe — 17/11/2026
- Implementado em `nexus/video_quality.py`: usa o filtro nativo FFmpeg `freezedetect` para medir intervalos de congelamento visual por clipe, duração congelada, proporção do clipe e maior intervalo congelado.
- O worker `nexus/remote_render_job.py` executa a análise depois de receber cada MP4 LTX e inclui `motion_quality` e `low_motion_scene_count` no relatório de produção/logs.
- Limite do diagnóstico: mede congelamento de pixels, não reconhece a ação, não confirma aderência à narração, não avalia estética, continuidade facial ou qualidade de movimento semântico. É um alarme técnico, não uma nota de qualidade.
- O limiar inicial de aviso é 40% do clipe em congelamento. Não há retry automático nem nova chamada paga; a análise usa FFmpeg já presente no worker.
- Testes adicionados em `tests/test_video_quality.py` para intervalos fechados, congelamento até EOF, proporção limitada e execução sem serviço externo.
- Pesquisa oficial: LTX 0.9.8 recomenda ComfyUI para maior fidelidade; o modelo 2B distilled não tem workflow oficial ComfyUI listado. O perfil atual do NEXUS usa o YAML oficial 2B multi-scale, mas não equivale ao workflow recomendado para maior fidelidade. Fonte: README e config oficiais da Lightricks.
- Estado: código e testes gravados na branch main; CI ainda precisa concluir. Não houve deploy Modal, inferência GPU, cobrança adicional ou validação visual de MP4 nesta etapa.

## Validação do diagnóstico de movimento e exposição na interface — 17/11/2026
- O diagnóstico FFmpeg por clipe foi integrado ao relatório do worker e agora também é exibido no Streamlit, com aviso quando há congelamento prolongado e tabela por cena.
- A interface deixa explícito que ausência de congelamento não significa que a ação corresponde à narração; o diagnóstico não é uma nota estética nem semântica.
- Teste de integração do worker atualizado para simular o analisador sem alterar a sequência de chamadas FFprobe/FFmpeg do teste. A tentativa inicial revelou essa interferência no mock; corrigida sem mudar o pipeline de produção.
- CI da revisão final `32dceb2ee206fd054dd2e2c7538a4064223ed286`, execução `44078360380`: 120 testes Python aprovados, Remotion typecheck aprovado e Commons live smoke aprovado.
- Código gravado na branch main. Não houve deploy no Streamlit/Modal, chamada Gemini adicional, inferência GPU ou produção de MP4 nesta etapa. Portanto, implementação e CI estão validados; deploy e comportamento visual na app publicada ainda não.
## Direção de movimento sem ações concorrentes — 17/11/2026
- Ajustado o SYSTEM do diretor: cada clipe de 2–5s deve ter uma única ação física principal com progressão observável (início → execução → resultado). Um microevento ambiental secundário é permitido, mas não deve competir com o gesto principal.
- A regra substitui a exigência anterior de dois microeventos visuais independentes, que podia incentivar excesso de ações numa tomada curta.
- Teste de contrato adicionado em `tests/test_director_scene_count_repair.py` para proteger a instrução.
- CI da revisão `00b8ed31ccd4d6e5daedce2ff1237767b10f75c6`, execução `44078552758`: testes Python, Remotion typecheck e Commons live smoke aprovados.
- Alteração implementada e CI validado. Não houve geração de imagem/vídeo, chamada Gemini real, deploy ou custo de inferência.
## Auditoria editorial multimétrica — 17/11/2026
- Evoluída a revisão visual final existente: Gemini recebe três quadros temporais por cena (início, meio e fim) e agora avalia separadamente aderência semântica, progressão de movimento, execução observável da ação e continuidade visual.
- O contrato de resposta inclui `semantic_score`, `matches_narration`, `motion_progression_score`, `action_observed`, `continuity_score`, `temporal_progression`, `issues` e `critical_issues`.
- A interface calcula um índice editorial composto (40% aderência, 35% movimento, 25% continuidade) e sinaliza cenas abaixo de 7/10, ação não observável, fala não correspondida ou falha crítica. O índice é ferramenta de triagem, não uma certificação objetiva de qualidade.
- Revisão ausente agora falha de forma conservadora: campos críticos ficam zerados e `review_missing` é registrado, em vez de a cena parecer aprovada.
- Não foi adicionada chamada Gemini: a alteração amplia a análise multimodal já realizada após o render, usando os mesmos três quadros por cena.
- CI da alteração está em execução; não declarar validado até concluir. Não houve deploy, render real, nova inferência LTX ou cobrança de GPU.
## Pesquisa de migração LTX-2.5 e ComfyUI — 17/11/2026
- LTX-2.5 é a geração mais recente indicada pela Lightricks; substitui LTX-Video 0.9.x e LTX-2. O modelo open-weight 22B distilled usa 8 passos fixos e possui geração multi-shot nativa, melhor aderência a prompts, decoder de vídeo de maior fidelidade e encoder Gemma 4 12B.
- Licença LTX-2.x Community: uso comercial/produção sem taxa de licença para entidades abaixo de US$10M de receita anual, sujeito ao texto integral da licença; acima desse limite exige acordo comercial pago. Pesos abertos não tornam GPU gratuita.
- Requisitos publicados para LTX-2.5: GPU NVIDIA com pelo menos 32 GB VRAM; recomendado A100 80 GB ou H100, RAM 32 GB mínimo/64 GB recomendado, 100 GB de armazenamento livre, CUDA 12.7+, Python 3.12+.
- Workflows oficiais ComfyUI 2.5 incluem I2V/T2V distilled em dois estágios (recomendado para detalhe espacial) e single-stage (mais leve/rápido, menos detalhe), além de IC-LoRAs para controle de movimento/pose. A implementação atual NEXUS usa LTX-Video 0.9.8 2B e não pode ser tratada como equivalente.
- ComfyUI é open-source/gratuito quando auto-hospedado. Comfy Cloud é opcional e pago (a página oficial indica planos a partir de US$20/mês); não é necessário para integrar workflow no Modal.
- Modal tarifa GPU por segundo (consulta 17/11/2026): L40S US$0.000542/s, A100 80GB US$0.000694/s, H100 US$0.001097/s, além de CPU/memória e tempo de carregamento. Não há base para afirmar que LTX-2.5 custará igual/menos: 22B vs 2B e necessidade de VRAM maior podem aumentar tempo/custo; deve ser benchmarkado com um único clipe e custo efetivo.
- Plano de migração: preservar LTX 0.9.8 como fallback; prototipar ComfyUI + LTX-2.5 distilled I2V two-stage num worker isolado; testar primeiro numa GPU de 48GB com pesos quantizados oficiais compatíveis, sem presumir que caiba; se necessário testar A100 80GB/H100 apenas após estimativa; medir cold start, carregamento, inferência, qualidade temporal e custo total; comparar em cenas idênticas antes de trocar produção.
- Orçamento de US$0.50 por vídeo permanece requisito, mas não está demonstrado para LTX-2.5. Não realizar render de benchmark pago sem aprovação do usuário.

## Pré-validação gratuita de variedade do storyboard — 17/11/2026
- Adicionado `build_storyboard_preflight(plan)` em `nexus/director.py`. O relatório mede proporção de ações e buscas principais únicas, variedade de tipos de plano e ambientes; sinaliza repetições literais e baixa diversidade.
- O relatório é anexado ao plano como `preflight_report` após a criação do storyboard. É uma verificação determinística de texto/metadados, não uma avaliação semântica visual nem substitui a auditoria multimodal.
- Não faz chamadas adicionais ao Gemini, não usa GPU e não altera cenas automaticamente. Os avisos são diagnósticos para orientar revisão posterior, sem reprovar storyboards por heurísticas frágeis.
- Testes adicionados para repetição literal e diversidade de ações/buscas. Commits: `4d81513` (implementação) e `94b7980` (testes).
- Estado no momento do registro: alterações gravadas na branch main; status de CI ainda não retornado pela integração GitHub. Não houve deploy, inferência GPU, chamada paga ou geração de MP4.

## Exposição da pré-validação do storyboard na interface — 17/11/2026 09:56 BRT
- Retomada feita a partir da leitura integral de `NEXUS_HANDOFF_2026-11-17.md` e `NEXUS_MASTER_STATE.md` diretamente da branch `main`.
- HEAD observado antes desta alteração: `50a0a70c51de9c40648218772f672a362f1cecc9`. A branch `main` foi confirmada.
- Inspeção do código confirmou que `build_storyboard_preflight(plan)` já calcula repetição literal de ações/buscas, variedade de tipos de plano e variedade de ambientes, e anexa `preflight_report` ao plano. A interface não exibia esse relatório.
- Alteração em `app.py`: dentro do expander existente de planejamento, adicionada a seção compacta **Pré-validação audiovisual**, com percentuais de variedade textual de ações e buscas, quantidade de tipos de plano e ambientes distintos, além dos avisos encontrados.
- Transparência na UI: a seção informa que é uma checagem heurística de texto/metadados, não analisa quadros e não substitui a revisão visual. A ausência de alertas é descrita somente como ausência de repetição literal/alertas detectados pelas regras automáticas.
- Teste de contrato adicionado em `tests/test_app_import_resilience.py` para verificar exibição dos indicadores, avisos e limitações.
- Commits: `355d493ba1047e34a9df9d0a8fb8f7aec852f4fa` (interface) e `9b4326ced1eb14f34fb055512aec8aab4f82a839` (teste).
- Verificação pós-commit: `app.py` e `tests/test_app_import_resilience.py` foram relidos diretamente de `main`; a seção e o teste estão presentes. A consulta de status combinado para `9b4326c` retornou zero statuses. O wrapper de workflow runs disponível informa que filtra apenas execuções disparadas por pull request e também retornou lista vazia; portanto, o estado do CI de push não pôde ser confirmado por esta integração. O workflow `.github/workflows/tests.yml` declara gatilho `push` em `main`, mas isso não comprova que a execução terminou ou passou.
- Estado: implementação gravada no GitHub e confirmada por releitura; teste adicionado, ainda sem execução confirmada; CI de push não verificável nesta sessão; deploy Streamlit e visualização no celular pendentes.
- Custos: nenhuma chamada Gemini, Cloudflare, Fish Audio, Modal/GPU ou renderização paga foi iniciada nesta etapa. Custo variável adicional: US$0.
- Próximo passo: obter o resultado do CI de push do commit `9b4326c` por uma consulta de Actions que inclua eventos push; se verde, continuar com a próxima melhoria de direção semântica em código/testes locais, sem inferência paga. A validação visual publicada permanece separada.



## Pré-validação textual ampliada do storyboard — 17/11/2026
- Evolução de `build_storyboard_preflight(plan)` em `nexus/director.py`: além de repetição literal, compara sobreposição de termos informativos entre pares de ações e buscas. O critério é conservador (mínimo de quatro termos compartilhados e 80% de sobreposição sobre o menor conjunto); pares literalmente idênticos continuam reportados apenas pela regra de repetição exata.
- O relatório agora inclui `action_coverage_ratio`, `motion_prompt_coverage_ratio`, `near_duplicate_action_pairs` e `near_duplicate_search_pairs`, além dos indicadores existentes. A análise é lexical/determinística: NÃO compreende sinônimos, intenção ou semântica real e pode produzir falsos positivos/negativos.
- A interface Streamlit exibe cobertura de descrição da ação/movimento e quantidade de pares com possível semelhança, mantendo o aviso de que não analisa quadros e não substitui revisão visual.
- Testes adicionados/ajustados em `tests/test_director_scene_count_repair.py` e `tests/test_app_import_resilience.py`: repetição aproximada com palavras reordenadas, cobertura dos campos, ações concretas distintas e contrato da UI.
- Commits na branch main: `87380c4` (heurística), `f096421` (testes), `6c2f931` (métricas na UI), `7b50d6d` (teste de contrato UI), `464ca0f` (evitar alerta duplicado quando os conjuntos de termos são idênticos).
- Validação desta etapa: alterações gravadas no GitHub e precisam de releitura pós-commit. Os testes automatizados ainda NÃO foram executados/confirmados por CI. A integração GitHub disponível não expõe listagem de Actions para eventos push; o status combinado consultado anteriormente veio vazio. Tentativa de clone para execução local falhou por indisponibilidade de DNS no ambiente. Não declarar CI aprovado.
- Deploy Streamlit, validação mobile, produção MP4, inferência Gemini/Cloudflare/Fish/Modal e qualidade audiovisual real não foram executados nesta etapa. Custo variável adicional: US$0.
- Próximo passo: verificar HEAD e releitura dos arquivos; tentar confirmar CI com os recursos GitHub disponíveis. Se não houver evidência, manter CI como desconhecido. Depois, evoluir validação semântica do diretor sem chamadas externas pagas, com testes determinísticos e contratos claros.


### Complemento — verificação de ação física explícita (17/11/2026)
- A pré-validação também identifica prompts `video_motion_prompt` sem nenhum verbo de movimento físico reconhecido por uma lista lexical controlada. Retorna `motion_action_coverage_ratio` e `motion_scenes_without_recognized_action`, além de aviso com os números das cenas.
- A interface mostra a proporção de prompts com verbo físico reconhecido. Isso é apenas uma triagem lexical: não prova que o sujeito se move, que a ação é coerente com a fala, nem que o vídeo gerado executa o movimento. Um verbo pode se referir à câmera ou ao ambiente; sinônimos não listados podem ser falsos negativos.
- A normalização foi ajustada para preservar letras acentuadas do português. Teste adicionado para pares semelhantes com termos como “portão metálico” e para prompt sem verbo físico reconhecido.
- Commits adicionais: `6769d06` (normalização Unicode), `f8af365` (teste de português acentuado), `8161dd2` (detecção lexical de ação física), `875ea44` (teste do prompt estático), `3bf05cd` (métrica na UI), `6b8accc` (contrato UI).
- Código e testes foram gravados na branch main. Ainda não há execução de testes/CI confirmada, deploy ou validação visual. Nenhuma API paga, GPU ou renderização foi chamada; custo variável adicional: US$0.


## Protótipo ComfyUI/LTX-2.5 — pesquisa e cliente HTTP mockável (17/11/2026)
- Pesquisa do workflow oficial `LTX-2.5_T2V_I2V_Two_Stage_Distilled.json`: transformer distilled 22B BF16, I2V opcional com imagem inicial, upscale espacial latente 2× e refinamento de 3 passos; workflow gera áudio e vídeo conjuntamente e exige frame count 1+8n. O grafo consultado usa 24 fps e defaults paisagem 960×544/121 frames; NEXUS exigirá grafo vertical e duração 2–5s.
- Requisitos oficiais publicados: GPU NVIDIA 32 GB VRAM mínimo; A100 80 GB ou H100 recomendados; 32 GB RAM e 100 GB livres mínimos. L40S 48 GB supera o mínimo, mas fica abaixo da configuração recomendada. Não há evidência de que o grafo 22B BF16 caiba com margem ou respeite o custo de US$0,50/vídeo.
- Plano detalhado salvo em `NEXUS_LTX25_COMFYUI_PLAN.md`. A arquitetura proposta mantém worker independente, ComfyUI local dentro de Modal, API privada, pesos em volume persistente, grafo API versionado e fallback LTX 0.9.8.
- Implementado sem GPU: `nexus/comfyui_client.py`, cliente HTTP mockável para upload, submissão, histórico, espera, detecção de erro e download. Testes mockados adicionados em `tests/test_comfyui_client.py`.
- Ainda não implementado: workflow API exportado/patcher, worker Modal ComfyUI, custom nodes/versões pinadas, feature flag, integração ao render principal ou benchmark. Nenhuma inferência, download de pesos ou deploy.
- CI/testes ainda não confirmados; custo variável adicional US$0. Próximo passo: confirmar CI e construir contrato do workflow API exportado com testes de nós/inputs, sem iniciar ComfyUI ou baixar modelos.


### Complemento — patch seguro de workflow API (17/11/2026)
- `nexus/comfyui_client.py` agora inclui `patch_api_workflow(workflow, bindings)`: cria cópia profunda do grafo e altera somente inputs explicitamente mapeados. Rejeita nós/inputs inexistentes, bindings incompletos e inputs que já estejam conectados por links, evitando quebrar silenciosamente a topologia.
- Testes adicionais verificam isolamento do grafo original, alteração de widgets, rejeição de links e referências desconhecidas.
- Commits: `273c047` (patcher), `9cb0830` (testes).
- O arquivo `.github/workflows/tests.yml` foi inspecionado: a job de regressão compila `nexus` e executa `python -m unittest discover -s tests -v`, portanto o novo arquivo de teste entra na descoberta padrão. Isso confirma a configuração do workflow, não o resultado de uma execução.


## Decisão arquitetural definitiva — integração LTX-2.5 no NEXUS oficial (17/11/2026)
- Esta decisão substitui a proposta anterior de manter um protótipo/projeto paralelo com posterior portabilidade. Não haverá segundo repositório, produto duplicado nem migração posterior de código: implementação, workflow, worker, testes e operação pertencem ao repositório oficial `porraloca42-stack/nexus-video-studio-`, branch `main`.
- LTX-2.5 + ComfyUI é o motor-alvo definitivo da evolução audiovisual. O LTX-0.9.8 permanece temporariamente como motor de produção/fallback até que o novo motor passe pelos portões de compatibilidade, qualidade, estabilidade e custo. Não são dois produtos em paralelo.
- Um worker pode continuar isolado como processo/runtime por segurança e dependências, mas será um componente versionado e operado pelo próprio NEXUS; isolamento operacional não significa projeto paralelo.
- Implementado: contrato comum de animação em `nexus/video_engine.py` e adaptador `LTX098VideoEngine`. `nexus/remote_render_job.py` passa a chamar o contrato, preservando a função de entrada usada pelos testes e o comportamento atual. O contrato exige uma saída por cena com caminho MP4 e telemetria.
- A resolução de `ltx25_comfyui` falha explicitamente enquanto o workflow API versionado e o adaptador não estiverem prontos; não existe fallback silencioso que esconda configuração incompleta.
- Testes determinísticos adicionados em `tests/test_video_engine.py` para motor padrão, delegação, bloqueio explícito do LTX-2.5 incompleto e nome desconhecido. Ainda não há execução local/CI confirmada nesta atualização.
- A base HTTP ComfyUI e o patcher seguro existentes serão reutilizados. Próxima implementação: obter e versionar um workflow realmente exportado em formato API, validar IDs/classes/inputs e então implementar o adaptador ComfyUI no mesmo contrato. O JSON visual do workflow não pode ser tratado como API prompt.
- Não houve deploy, download de pesos, boot ComfyUI, chamada API paga, inferência GPU ou benchmark. Custo variável adicional: US$0. Nenhuma alteração do motor padrão de produção foi feita.
- Estado desta etapa: código gravado em `main`; teste adicionado; validação pós-commit, execução dos testes e CI pendentes; deploy e MP4 real não realizados.


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


## CI e compatibilidade de exportação API ComfyUI — 17/11/2026
- CI GitHub Actions #885, run 44092064304, commit e5eadb605609cacd5c0d8544f267029e0e073204: 153 testes Python passaram; Remotion typecheck e Commons live smoke passaram.
- CI GitHub Actions #887, run 44092812673, commit 2d0a8068c72430cc4dd6cded0f5d49a981968ccd: 154 testes Python passaram; Remotion typecheck e Commons live smoke passaram. Jobs concluídos com sucesso.
- Pesquisa do exportador oficial ComfyUI frontend, revisão 196dd85cde3314dffdc33b41caa3e5d9be432ffb, em src/utils/executionUtil.ts: graphToPrompt percorre a ordem de execução, expande nós internos via ExecutableNodeDTO.getInnerNodes(), resolve conexões e widgets e emite class_type + inputs. Widgets cujo valor é array são encapsulados como objeto com __value__ para não serem confundidos com links.
- Correção em nexus/comfyui_client.py: patch_api_workflow agora aplica o mesmo encapsulamento ao alterar widgets cujo valor é array. Teste de regressão em tests/test_comfyui_client.py confirma preservação do grafo original e compatibilidade com o validador. Commits: e5b3246 e 2d0a806.
- Inspeção do workflow upstream confirmou seis subgrafos reais e que o subgrafo Input Parameters contém nós GemmaAPITextEncode. O caminho de API externa é condicionado à presença de chave LTX; não adicionar nem configurar essa chave no NEXUS sem decisão de custo/segurança. O caminho local também carrega encoder/enhancer Gemma; a remoção/desativação do enhancer precisa ser feita no grafo API real e testada, não presumida.
- Estado: CI validado até 2d0a806; workflow API exportado ainda não existe; worker, binding IDs e integração produtiva continuam pendentes. Sem download de pesos, boot ComfyUI, GPU, API paga, deploy ou render. Custo variável adicional: US$0.



## Correção da referência de frontend ComfyUI — 17/11/2026
- O workflow visual original registra frontendVersion 1.48.7. A primeira investigação consultou uma revisão posterior (1.61.2), útil apenas como comparação, e não como referência de compatibilidade do workflow.
- Referência correta confirmada: tag oficial ComfyUI_frontend v1.48.7, commit 6d6af63c00f132cd25dc29307fc56bd2c094fa22. A função graphToPrompt e a classe ExecutableNodeDTO foram relidas nessa revisão. O manifesto workflows/ltx25/source_manifest.json foi corrigido para essa versão.
- O teste do manifesto agora verifica tag e versão. CI #895 (run 44094091786) e #896 (run 44094125992) passaram com 154 testes Python, Remotion typecheck e Commons live smoke. O run #894 falhou transitoriamente porque o manifesto foi atualizado antes do teste; a execução seguinte após atualizar o teste passou.
- O código do cliente NEXUS continua compatível com o encapsulamento de widgets array como __value__. O API prompt real ainda não foi exportado; a integração segue bloqueada até exportação oficial/runtime e validação dos bindings. Sem GPU, download de pesos, deploy, API paga ou render. Custo variável adicional US$0.


## Revisão de arquitetura econômica faceless — 17/11/2026
- O usuário questionou a necessidade de usar vídeo generativo em todas as cenas e trouxe uma hipótese baseada em Revid/Crayo: imagens IA + movimento de câmera/Remotion + overlays e vídeo IA só em cenas hero. Foi realizada pesquisa pública de Revid, Crayo, Pictory, InVideo, Fliki, VEED, Cloudflare e Modal.
- Relatório completo versionado em `NEXUS_FACELESS_VIDEO_ARCHITECTURE_RESEARCH_2026-11-17.md` (commit inicial 567dda6).
- Padrão confirmado nas documentações comerciais: seleção de mídia por cena entre stock, imagens IA animadas, motion graphics, mídia do usuário/gameplay e AI video. Revid recomenda reservar modelos premium para uma ou duas cenas hero; o produto também expõe densidade visual e vários modos de animação de imagem. Pictory/InVideo enfatizam matching de stock; Fliki expõe seleção entre stock, imagem IA e cobertura opcional de vídeo IA; Crayo combina gameplay/stock/story formats e timeline multifaixa.
- Auditoria do código atual: `nexus.remote_render_job.main` gera keyframes FLUX.2 Klein e encaminha **todas as cenas** para `animate_scene_images`; `nexus.modal_i2v.animate_scene_images` envia um único lote para `run_batch`. Modal atual usa L40S, não T4; LTX-0.9.8 multi-scale 10 passos; função timeout 45 min; scaledown 5 s; guard GPU US$0.42. Não há roteamento 0–2 cenas IA no worker.
- Cloudflare: o código gera 512×910 e Remotion finaliza em 720×1280/30fps; não é 4K. Com preço publicado de US$0.000287 por tile 512×512, 14 imagens de 512×910 custariam aproximadamente US$0.00804 se faturadas em dois tiles por imagem. 15 imagens: aproximadamente US$0.00861. Estimativa sujeita a confirmar o tile metering real e consumo de Neurons; a alocação diária gratuita é 10.000 Neurons, compartilhada com o restante do uso da conta.
- Modal: T4 custa US$0.000164/GPU-s; US$0.005 cobre cerca de 30.5 segundos faturáveis de GPU antes de CPU/memória. Isso não foi medido e não prova que o modelo NEXUS caiba/rode bem em T4. O timeout de 60s seria para a invocação/lote, não por cena, e inclui startup sem startup_timeout separado. A janela atual de 5s já é curta. Spend limit US$30 não é proteção “sem cobrança”: a documentação separa Workspace budget (limite rígido de uso antes dos créditos) e Spend limit (limite rígido líquido após créditos). Avaliar spend limit US$0 + workspace budget explícito.
- A afirmação de custo total inferior a US$0.02 não foi comprovada para nenhum concorrente; os fornecedores publicam créditos de cliente e features, não custo marginal interno. O número pode ser uma meta experimental para NEXUS, não um fato de mercado.
- Gap Remotion: já há zoom/pan/tilt 2D, transições e efeitos atmosféricos CSS. `depthLayers` ainda é metadado; não há depth-map parallax implementado nem overlays de vídeo transparentes. Os beats atuais vêm do storyboard, não de análise da batida da faixa. O componente examinado não inclui trilhas de SFX nem legendas word-level.
- **Decisão de governança:** pausar novas decisões de adoção/implementação do LTX-2.5 até comparar a rota híbrida e validar custo/qualidade. Não remover nem alterar o worker LTX-0.9.8 existente. Nenhuma GPU, API paga, deploy, download de pesos ou render foi executado nesta pesquisa. Custo variável adicional US$0.
- Próximo passo permitido sem custo: desenhar e testar por mocks o roteador por cena, a composição Remotion com camadas/overlays e o relatório de custo. Benchmark real de Cloudflare/Fish/Modal e comparação visual com GPU exigem autorização de custo separada.


## Retomada — pipeline editorial em quatro cérebros aprovado (17/11/2026)
- O usuário aprovou acrescentar à arquitetura híbrida uma cadeia editorial de quatro estágios especializados, inspirada na forma como apps faceless estruturam seus fluxos. Isso é uma arquitetura-alvo proposta para o NEXUS, não uma alegação verificada sobre os backends privados dos concorrentes.
- Cérebro 1 — Estrategista de retenção: cria três hooks distintos (curiosidade, perda/oportunidade relevante e quebra de padrão), seleciona o melhor com justificativa, define arco de tensão crescente, payoff e possível ligação final-início em loop.
- Cérebro 2 — Roteirista de micro-ritmo: converte o arco em blocos curtos; 2,5–3,5s por unidade é heurística inicial, não limite rígido. Remove enchimentos, marca ênfases/pausas e preserva naturalidade e duração total.
- Cérebro 3 — Diretor de fotografia: traduz intenção/emoção em metáforas visuais filmáveis, não ilustração literal; cria bíblia visual consistente (paleta, luz, lentes/enquadramentos, textura, composição e continuidade) sem repetir cenas. Cada beat também recomenda a rota de mídia do motor híbrido.
- Cérebro 4 — Editor de ritmo: após a voz final, alinha palavras ao áudio, seleciona âncoras de ênfase, sincroniza cortes, movimentos, SFX, legendas e música; loop final/inicial é validado quando intencional.
- Precisão: OpenAI Whisper tem opção word_timestamps, documentada como experimental; timestamp de palavra não identifica por si só sílaba tônica nem garante alinhamento fonético exato. Antes de prometer cortes na sílaba, avaliar forced alignment/nível fonético e análise de prosódia. Fontes registradas no relatório de pesquisa.
- Relatório atualizado: NEXUS_FACELESS_VIDEO_ARCHITECTURE_RESEARCH_2026-11-17.md, commit 92204b323c7ab8764cbe448a1ade731c1960db82.
- Estado: decisão de produto aprovada e documentação atualizada; pipeline de quatro cérebros ainda NÃO implementado, testado com áudio real ou validado por retenção/A-B. Nenhuma mudança de código de produção, API paga, GPU, deploy ou render foi executada. Custo variável adicional US$0.
- Próxima etapa sem custo: schemas/contratos JSON e testes determinísticos dos quatro estágios; integrar incrementalmente ao diretor atual somente depois de validar cada contrato. Preservar o roteador híbrido por cena e a pausa de novas decisões de motor LTX-2.5.



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
