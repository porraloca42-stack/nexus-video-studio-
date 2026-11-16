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
