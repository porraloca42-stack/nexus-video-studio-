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
- O usuário mostrou um storyboard cuja soma era 43s para 50s; o planejamento foi sinalizado para revisão e a produção foi bloqueada. A causa específica de o modelo não completar os 50s ainda precisa ser investigada.
- Render MP4 final ainda NÃO está validado de ponta a ponta.
- Coverr/Pixabay são implementações preliminares; confirmar documentação/API, autenticação, URLs e licenças antes de considerar fontes validadas.
- MCP oficial do Coverr ainda NÃO está integrado ao NEXUS.

## Alterações recentes
- Commit f617fb3: em app.py, o bloco "Direção audiovisual" passou a ser um expander recolhido por padrão, evitando ocupar a tela com a interpretação e tese do diretor. A lista de cenas também passou a iniciar recolhida; o usuário pode abrir cada seção quando quiser.
- Essa alteração foi gravada na branch main do GitHub. Ainda precisa ser confirmada no deploy do Streamlit e testada no celular.

## Próximas etapas obrigatórias
1. Confirmar que a alteração de interface foi implantada no Streamlit e que os expanders abrem/fecham corretamente em tela móvel.
2. Investigar por que o Gemini retornou cenas somando 43s para uma solicitação de 50s; implementar correção/segunda tentativa de planejamento sem aceitar storyboard incompleto.
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
