# NEXUS VIDEO STUDIO — CONTEXTO OPERACIONAL

Última atualização: 2026-11-16 (revisado após confirmação do usuário)

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
- Fonte principal: Coverr; COVERR_API_KEY configurada e autenticação/busca genérica testadas pelo usuário. Busca semântica específica por cena falhou no primeiro teste end-to-end e recebeu fallback progressivo de consultas curtas; ainda aguarda reteste.
- Pixabay: há integração preliminar no código, mas PIXABAY_API_KEY não está configurada; não considerar operacional.
- Pexels: NÃO integrado. O usuário informou que a emissão de novas chaves API está temporariamente indisponível; não bloquear o desenvolvimento por isso.
- Análise multimodal de candidatos e geração de cenas originais ainda NÃO implementadas.

## Segredos (nunca armazenar valores de chaves neste arquivo ou no GitHub)
No Streamlit → Manage app → Settings → Secrets:
- GEMINI_API_KEY — configurada pelo usuário; não solicitar novamente sem necessidade.
- GEMINI_MODEL = "auto" — configurado pelo usuário.
- COVERR_API_KEY — configurada nos Secrets, conforme confirmação do usuário; ainda não validada por uma chamada real.
- PIXABAY_API_KEY — ainda não configurada.
Nunca copiar chaves para arquivos do repositório, logs ou mensagens públicas.

## Estado verificado em 2026-11-16
- Streamlit abriu a interface.
- Planejamento de storyboard com Gemini funcionou ao usar Gemini 3.5 Flash-Lite; usuário confirmou com captura mostrando cenas geradas.
- Render MP4 ainda não foi validado.
- Após a criação de nexus/__init__.py, o usuário confirmou em 2026-11-16 que a aplicação abre normalmente no Streamlit.
- Captura dos logs mostra atualização do app concluída (Updated app!). A inicialização está confirmada visualmente pelo usuário; não há confirmação independente de execução do pipeline.
- app.py importa search_video_sources, search_coverr_videos e download_file de nexus.assets.
- O usuário executou o diagnóstico Coverr e confirmou em captura que a API respondeu com sucesso e retornou cinco clipes, incluindo um vertical. Autenticação e busca genérica estão TESTADAS no ambiente publicado.
- Primeiro teste do botão “Produzir vídeo completo” gerou storyboard de seis cenas, mas não encontrou clipes para nenhuma cena. FFmpeg não foi iniciado; pipeline completo permanece NÃO VALIDADO.
- Primeira correção de busca progressiva foi insuficiente: captura do usuário mostra zero resultados em todas as sete cenas, mesmo após consultas originais e alternativas. As consultas estavam excessivamente específicas para o mecanismo de stock.
- Nova correção publicada em nexus/assets.py: expande a busca por cena para termos de assunto/ação individuais e aliases específicos (ex.: alarm→alarm clock/waking up; barbell→gym/weightlifting; book→reading; typing→computer/keyboard; city→city lights), além da consulta original e compacta. Limite de oito consultas por fonte/cena. Mantém a busca sem aceitar mídia sem URL MP4. Aguarda novo teste; não afirmar que corrigiu a disponibilidade sem resultado real.
- O usuário executou o download interno e confirmou em captura que o servidor recebeu e validou um MP4: H.264, 606×1080, 8 segundos, 4,65 MB. Download servidor→arquivo e leitura FFprobe estão TESTADOS. O arquivo ficou em diretório temporário do servidor e foi descartado ao fim do teste; não houve download para o celular, nem isso era o objetivo do diagnóstico.
- A interface explica que o diagnóstico Coverr baixa o clipe temporariamente no servidor; o usuário não deve receber arquivos-fonte individuais.
- Em 2026-11-16 foi publicado um fluxo de produção atualizado: botão “Produzir vídeo completo”; validação FFprobe de cada clipe baixado; geração de narração/legendas; render FFmpeg; validação do MP4 final com faixas de vídeo e áudio; armazenamento dos bytes do MP4 em session_state para manter prévia e botão de download após reruns. O código foi publicado, mas ainda NÃO foi executado pelo usuário nem validado com um MP4 real.
- A busca de diagnóstico usou “nature landscape”, mas um título retornado (“Astonished Crowd Beneath a Giant Hand”) parece pouco relacionado; relevância semântica da busca ainda precisa ser melhorada.
- A primeira implementação do botão de download ficou inacessível porque os resultados não eram persistidos em session_state após o rerun do Streamlit; o usuário reportou corretamente que não havia botão. Corrigido em 2026-11-16: um único botão “Testar Coverr: buscar e baixar clipe” agora executa busca, escolhe primeiro candidato vertical, baixa internamente em diretório temporário e valida faixa de vídeo, resolução, codec, duração e tamanho via FFprobe. Não solicita download manual ao usuário. Código publicado; aguarda teste real.
- nexus/assets.py contém search_coverr_videos, search_pixabay_videos, search_video_sources e download_file.
- Implementação Coverr/Pixabay é preliminar. A documentação oficial Coverr confirma GET https://api.coverr.co/videos, autenticação x-api-key, parâmetros query/page/page_size/urls e retorno de hits[].urls.mp4_download; o código atual usa esses campos. A chave e o download ainda precisam de teste real no app.
- MCP oficial do Coverr ainda NÃO está integrado ao NEXUS.

## Próximas etapas obrigatórias
1. CONCLUÍDO: usuário confirmou que a interface Streamlit abre normalmente após o commit que adicionou nexus/__init__.py.
2. CONCLUÍDO: autenticação e busca Coverr testadas com sucesso pelo usuário; cinco resultados retornados.
3. CONCLUÍDO: download interno Coverr e validação FFprobe confirmados pelo usuário (H.264, 606×1080, 8 s, 4,65 MB).
4. IMPLEMENTADO, AGUARDANDO RETESTE: fluxo de produção e entrega MP4 final. Primeiro teste parou antes do FFmpeg porque não houve resultados para as seis buscas específicas.
5. PRÓXIMO: retestar a busca com termos individuais e aliases semânticos; verificar resultados por cena e conferir a correspondência antes de renderizar.
6. Melhorar ranking semântico por cena; não selecionar automaticamente o primeiro resultado sem avaliar correspondência.
7. Implementar avaliação multimodal dos candidatos para verificar correspondência com a narração.
8. Renderizar o primeiro MP4 real de 40–50s, inspecionar qualidade e validar entrega do arquivo final.
9. Considerar Pixabay como fallback quando a chave estiver disponível; Pexels permanece fora do escopo enquanto a emissão de chaves estiver indisponível.
10. Avaliar MCP oficial do Coverr somente se trouxer vantagem após validar a integração REST.

## Regras para o assistente em novos chats
- Começar lendo este arquivo e o código relevante no GitHub antes de propor mudanças.
- Tratar este documento como registro de continuidade, mas conferir o estado atual do repositório e deployment; pode ficar desatualizado.
- Fazer alterações diretamente no repositório usando a integração GitHub disponível.
- Fazer uma mudança coerente por vez; não instruir o usuário a editar código.
- Dar instruções curtas, uma ação de cada vez.
- Distinguir claramente: implementado no código, implantado, testado, validado com MP4.
- Não pedir para o usuário repetir contexto que esteja documentado aqui.
- Não afirmar conexão em tempo real com Streamlit, logs ou execução do app se isso não estiver disponível.
