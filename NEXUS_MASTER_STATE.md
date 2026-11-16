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
- O usuário mostrou um storyboard de 12 cenas somando 43s para 50s. A geração agora redistribui deterministicamente a duração solicitada entre as cenas existentes, preservando o ritmo relativo e limitando cada clipe a 2–5s. Se a quantidade de cenas não comportar a duração, a geração falha explicitamente em vez de aceitar uma linha do tempo impossível.
- Render MP4 final ainda NÃO está validado de ponta a ponta.
- Coverr/Pixabay são implementações preliminares; confirmar documentação/API, autenticação, URLs e licenças antes de considerar fontes validadas.
- MCP oficial do Coverr ainda NÃO está integrado ao NEXUS.

## Alterações recentes
- Commit f617fb3: primeira compactação dos detalhes do planejamento.
- Commit f0e0ddf: nexus/director.py redistribui o tempo solicitado entre as cenas quando o Gemini retorna soma diferente; mantém cada clipe entre 2 e 5 segundos e registra a correção no plano.
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
