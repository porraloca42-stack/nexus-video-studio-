# NEXUS VIDEO STUDIO — CONTEXTO OPERACIONAL

Última atualização: 16/11/2026

## Objetivo
Aplicativo pessoal em nuvem para transformar tema ou roteiro em vídeo vertical 9:16 de aproximadamente 40–60 segundos, com direção contextual por IA, narração, legendas, clipes coerentes, edição e exportação MP4.

## Repositório e publicação
- GitHub: https://github.com/porraloca42-stack/nexus-video-studio-
- Branch: main
- Streamlit: https://htykbebk3hceoen5bvopax.streamlit.app/
- App principal: app.py
- Pacote Python: nexus/

## Preferências de produto
- Prioridade: qualidade audiovisual e coerência semântica.
- O diretor deve compreender o roteiro inteiro antes de criar cenas.
- Cada cena deve representar a fala correspondente com ação concreta; evitar stock genérico, slideshows, colagens e repetição de zoom.
- Um único estilo visual bloqueado por vídeo.
- Preferir clipes reais em movimento; geração de vídeo por IA é futura e não deve consumir créditos sem autorização.
- Pesquisar em várias bibliotecas, comparar candidatos e futuramente avaliar visualmente os clipes.
- Alvo inicial: uso pessoal, cerca de 2 vídeos/dia, 50 segundos, 720p, 9:16.

## Arquitetura atual
- Interface: Streamlit (app.py).
- Diretor: Gemini API (nexus/director.py), lista modelos disponíveis para a chave e seleciona automaticamente; prioriza gemini-3.5-flash-lite quando disponível.
- Voz/legendas: Edge TTS (nexus/audio.py).
- Renderização: FFmpeg (nexus/render.py).
- Busca/baixar mídia: nexus/assets.py.
- Fontes planejadas: Coverr principal, Pixabay reserva. Pexels fora do fluxo atual por falta de chave.
- Análise multimodal de candidatos e geração de cenas originais ainda NÃO implementadas.

## Segredos
Nunca armazenar valores de chaves neste arquivo, no GitHub ou em instruções do projeto.
No Streamlit → Manage app → Settings → Secrets:
- GEMINI_API_KEY — configurada pelo usuário; não solicitar novamente sem necessidade.
- GEMINI_MODEL = "auto" — configurado pelo usuário.
- COVERR_API_KEY — precisa ser validada com teste real de autenticação, busca e download.
- PIXABAY_API_KEY — ainda não configurada.
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
