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
