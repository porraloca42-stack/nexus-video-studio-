# NEXUS VIDEO STUDIO — CONTEXTO OPERACIONAL

Última atualização: 2026-11-16

## Objetivo
Aplicativo pessoal em nuvem para transformar tema ou roteiro em vídeo vertical 9:16 de aproximadamente 40–60 segundos, com direção contextual por IA, narração, legendas, clipes coerentes, edição e exportação MP4. O usuário não programa; o assistente deve executar as alterações técnicas e orientar apenas ações simples no painel quando indispensáveis.

## Repositório e publicação
- GitHub: https://github.com/porraloca42-stack/nexus-video-studio-
- Branch: main
- Streamlit: https://htykbebk3hceoen5bvopax.streamlit.app/
- App principal: app.py
- Pacote Python: nexus/

## Preferências de produto
- Prioridade: qualidade audiovisual e coerência semântica, não funcionalidades periféricas.
- O diretor deve compreender o roteiro inteiro antes de criar cenas.
- Cada cena deve representar a fala correspondente com ação concreta; evitar stock genérico, slideshows, colagens e repetição de zoom.
- Um único estilo visual bloqueado por vídeo.
- Preferir clipes reais em movimento; geração de vídeo por IA é uma etapa futura e não deve consumir créditos sem autorização.
- Pesquisar em várias bibliotecas, comparar candidatos e futuramente avaliar visualmente os clipes antes de selecioná-los.
- Alvo inicial: uso pessoal, cerca de 2 vídeos/dia, 50 segundos, 720p, 9:16.
- Não afirmar que MP4 está pronto sem render real validado.

## Arquitetura atual
- Interface: Streamlit (app.py).
- Diretor: Gemini API (nexus/director.py), lista modelos disponíveis para a chave e seleciona automaticamente; prioriza gemini-3.5-flash-lite quando disponível.
- Voz/legendas: Edge TTS (nexus/audio.py).
- Renderização: FFmpeg (nexus/render.py).
- Busca/baixar mídia: nexus/assets.py.
- Fontes planejadas: Coverr principal, Pixabay reserva. Pexels fora do fluxo atual por falta de chave.
- Análise multimodal de candidatos e geração de cenas originais ainda NÃO implementadas.

## Segredos (nunca armazenar valores de chaves neste arquivo ou no GitHub)
No Streamlit → Manage app → Settings → Secrets:
- GEMINI_API_KEY — configurada pelo usuário; não solicitar novamente sem necessidade.
- GEMINI_MODEL = "auto" — configurado pelo usuário.
- COVERR_API_KEY — usuário informou chave e foi orientado a adicioná-la aos Secrets. Não afirmar que está validada até testar.
- PIXABAY_API_KEY — ainda não configurada.
Nunca copiar chaves para arquivos do repositório, logs ou mensagens públicas.

## Estado verificado em 2026-11-16
- Streamlit abriu a interface.
- Planejamento de storyboard com Gemini funcionou ao usar Gemini 3.5 Flash-Lite; usuário confirmou com captura mostrando cenas geradas.
- Render MP4 ainda não foi validado.
- A tela apresentou ImportError após mudanças em nexus/assets.py/app.py. Foi criado nexus/__init__.py, mas a correção ainda precisa ser confirmada no deploy.
- O último print mostrava traceback truncado na importação de nexus.assets; logs do Streamlit são necessários se reboot não resolver.
- app.py importa search_video_sources e download_file de nexus.assets.
- nexus/assets.py contém search_coverr_videos, search_pixabay_videos, search_video_sources e download_file.
- Implementação Coverr/Pixabay é preliminar e precisa ser confrontada com documentação/API real antes de considerar funcional.
- MCP oficial do Coverr ainda NÃO está integrado ao NEXUS.

## Próximas etapas obrigatórias
1. Estabilizar importação e inicialização do Streamlit; se falhar, ler Logs e corrigir a causa exata.
2. Testar autenticação e busca Coverr com COVERR_API_KEY; confirmar endpoint, autenticação, resposta e URLs reais.
3. Fazer download de um clipe de teste e validar formato, codec e duração.
4. Integrar Pixabay como fallback e respeitar termos, atribuição, cache e limites da API.
5. Criar busca multi-fonte por cena com ranking de candidatos.
6. Implementar avaliação multimodal dos clipes para verificar correspondência com a narração.
7. Renderizar primeiro MP4 real de 40–50s, inspecionar qualidade e só então declarar o pipeline validado.
8. Considerar MCP oficial do Coverr apenas após verificar endpoint, autenticação e ferramentas disponíveis; não confundir MCP no ChatGPT com MCP dentro do app.

## Regras para o assistente em novos chats
- Começar lendo este arquivo e o código relevante no GitHub antes de propor mudanças.
- Tratar este documento como registro de continuidade, mas conferir o estado atual do repositório e deployment; pode ficar desatualizado.
- Fazer alterações diretamente no repositório usando a integração GitHub disponível.
- Fazer uma mudança coerente por vez; não instruir o usuário a editar código.
- Dar instruções curtas, uma ação de cada vez.
- Distinguir claramente: implementado no código, implantado, testado, validado com MP4.
- Não pedir para o usuário repetir contexto que esteja documentado aqui.
- Não afirmar conexão em tempo real com Streamlit, logs ou execução do app se isso não estiver disponível.
