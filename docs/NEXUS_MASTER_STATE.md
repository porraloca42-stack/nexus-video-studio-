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
- A resposta JSON do Gemini deve ser extraída de todas as partes textuais, tolerar cercas Markdown/preambulo e reportar motivo real de bloqueio/truncamento em vez de erro genérico.
- O usuário escolhe a linguagem visual; cada cena devolve visual_style e style_search_terms, e os termos de estilo acompanham as buscas nas bibliotecas.
- Cada cena deve representar a fala correspondente com ação concreta; evitar stock genérico, slideshows, colagens e repetição de zoom.
- O usuário escolhe um estilo visual entre múltiplos presets; o estilo escolhido é enviado ao Gemini, aplicado por cena e incorporado às buscas de stock.
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
- O usuário identificou corretamente falha arquitetural: buscas não podem ser guiadas por dicionário fixo; quantidade e conteúdo das cenas devem ser decididos pelo Gemini a partir do roteiro. A expansão anterior com aliases fixos foi removida.
- Nova arquitetura publicada: Gemini recebe regras de segmentação por duração e densidade do roteiro. Para 40–60s, mínimo ceil(duração/5), meta ceil(duração/4) ou mais; em 50s, mínimo 10 e meta 12–15. Cenas normalmente 3–4s, com buscas próprias, distintas e específicas por cena.
- validate_storyboard agora recebe a duração solicitada e rejeita contagem inferior ao mínimo, soma de durações divergente em mais de 0,75s e cenas acima de 5s.
- nexus/assets.py deriva variações apenas dos termos da busca específica criada pelo diretor; não existe mais mapa fixo de temas ou sinônimos.
- nexus/render.py usa stream_loop para preencher o segmento quando o clipe-fonte for mais curto, evitando quadros vazios. Isso é uma proteção técnica, não substitui a seleção de clipes longos e variados.
- Corrigido tratamento de resposta do Gemini em nexus/director.py: agrega todos os blocos de texto, remove cercas de código, tenta decodificação JSON direta e extração do primeiro objeto; informa bloqueio, resposta vazia ou MAX_TOKENS com diagnóstico específico. Limite de saída elevado para 8192 tokens.
- app.py oferece 24 estilos visuais selecionáveis (cinematográfico, documentário, noir, publicidade premium, lifestyle, natureza, minimalista, vintage, VHS, cyberpunk, sci-fi, fantasia, surrealismo, anime 2D/3D, ilustração, aquarela, graphic novel, 3D, stop motion, macro e drone). O estilo é passado ao diretor, exibido no storyboard e anexado às buscas por cena. Em 2026-11-16, após usuário reportar que o seletor não estava visível no celular, foi movido da sidebar para a área principal, acima do roteiro.
- Redesign mobile-first publicado em app.py: hierarquia em etapas (conteúdo, direção visual, configurações), painel principal com controles de voz/duração, cartão compacto de prévia visual ilustrativa SVG para cada um dos 24 estilos e CSS de acabamento. O teste Coverr foi removido da tela inicial e movido para expander de ferramentas avançadas; não é necessário para uso normal. Commit 308504c; interface ainda aguarda confirmação visual do usuário. As prévias são ilustrações vetoriais de referência, não frames reais de stock.
- Refinamento solicitado após captura (commit `a5c302ee`): miniaturas da galeria ampliadas de 75 para 85 px; botões reduzidos para 78% da célula com máximo de 155 px, altura mínima 1,8 rem, padding menor; fonte forçada a 0,62 rem também nos elementos internos do botão (o tamanho anterior não prevalecia no texto renderizado). Mantidos alinhamento central, quebra de linha e duas colunas. Publicado no GitHub; aguarda reboot e validação no aparelho.
- Refinamento visual da galeria (commit `3ed841be`): miniaturas alinhadas horizontalmente ao centro de cada cartão; botões reduzidos para 88% da célula com máximo de 185 px, fonte menor (0,68 rem), padding e altura reduzidos; texto permanece centralizado e com quebra de linha, abaixo da imagem. Mantidas duas colunas e miniaturas de 75 px. Publicado no GitHub; aguarda reboot e confirmação visual mobile.
- Ajuste dos rótulos dos estilos após captura mobile (commit `749cd716`): botões da galeria agora usam altura automática, `max-width:100%`, texto com quebra de linha e sem ellipsis/overflow oculto; regras também aplicadas aos elementos internos do botão do Streamlit, que estavam mantendo o truncamento. Mantidas duas colunas e miniaturas de 75 px. Publicado; aguarda reboot e confirmação visual.
- Correção específica dos botões da galeria após nova captura (commit `0fd022c5`): a regra flex ainda permitia que a coluna esquerda ocupasse quase toda a largura e empurrasse a direita para fora da viewport. Substituída a linha flex por CSS Grid real `repeat(2,minmax(0,1fr))`; colunas limitadas a 100% da célula e botões limitados a 210 px, com texto quebrável. Miniaturas continuam 75 px. Publicado no GitHub; aguarda reboot e validação no telefone.
- Correção de overflow horizontal mobile (commit `010d6591`): nova captura após `a01838d` mostrou toda a página deslocada/cortada lateralmente. Causa provável: os blocos de colunas e seus filhos mantinham largura mínima/intrínseca maior que a viewport. CSS da galeria agora limita contêiner, linhas, colunas, imagens e botões a 100%/50%, aplica `min-width:0`, `box-sizing:border-box` e clipping horizontal local; miniaturas mantidas em 75 px. Publicado no GitHub; aguardando reboot e captura para validação. Não alterar outras seções até confirmar que o viewport voltou ao normal.
- Ajuste mobile seguinte (commit `a01838d4`): captura mostrou overflow horizontal após CSS global forçar `nowrap` em todos os blocos de colunas do Streamlit. CSS agora é escopado somente ao container `nexus-style-gallery`, preservando o restante do layout responsivo; miniaturas da galeria reduzidas de 150 px para 75 px (metade), botões compactados. Rótulo deixa explícito que são exemplos ilustrativos. As miniaturas continuam sendo SVGs vetoriais placeholders, não imagens fotográficas/frames reais; substituição por referências visuais fotográficas é trabalho separado ainda não implementado. Publicado no GitHub, aguarda reboot e confirmação visual no Streamlit.
- Nova validação visual em mobile (capturas recebidas após commit fd69708): apesar da miniatura fixa de 220 px, a galeria continuou em coluna única porque o Streamlit empilha `st.columns(2)` em telas estreitas. Correção publicada no commit `1f8e846`: forçar duas colunas lado a lado na galeria com CSS responsivo controlado, reduzir miniaturas para 150 px e compactar botões. Isso deve reduzir a rolagem de 24 itens para 12 linhas em celular. Como o CSS também atinge blocos horizontais da página, verificar configurações e demais seções após reboot. Estado: implementado/publicado, aguardando confirmação visual do deployment.
- Reteste visual em 16/11/2026: capturas mobile confirmaram seleção funcional e 24 ilustrações distintas, mas Streamlit colapsa as duas colunas em uma coluna no celular e `use_container_width=True` ampliava cada miniatura para quase toda a tela, alongando excessivamente a galeria. Correção incremental publicada: miniaturas da galeria agora usam largura fixa de 220 px, preservando botões de seleção e preview do estilo atual; texto de orientação atualizado. Commit `fd69708`. Implementado/publicado no GitHub; aguarda reboot e nova captura para validar a aparência no deployment.
- Redesign da interface em 16/11/2026: marca NEXUS VIDEO STUDIO em destaque discreto, tagline menor logo abaixo, hero com profundidade/glassmorphism e sombras sutis, mantendo hierarquia compacta para mobile.
- Direção visual atualizada: 24 prévias SVG ilustrativas distintas por linguagem visual (não mais uma paisagem genérica repetida), com cenas/objetos diferentes por estilo; seleção por cartões clicáveis em galeria expansível de duas colunas, cartão da escolha atual sempre visível e estado selecionado destacado. Estilo selecionado continua sendo enviado ao Gemini e anexado às buscas de cada cena.
- Ferramentas técnicas Coverr permanecem fora do fluxo principal, dentro de Ferramentas avançadas.
- Commit de interface: 87faa2a; publicado na branch main. Sintaxe e renderização em Streamlit ainda precisam de validação no deployment; usuário deve atualizar/reiniciar o app e confirmar visualmente.
- validate_storyboard exige visual_style e style_search_terms em cada cena. Código publicado; ainda aguarda novo teste no Streamlit.
- Usuário reportou erro em runtime: `validate_storyboard() takes 1 positional argument but 2 were given`, indicando divergência entre versões de app.py e módulo director.py carregadas no deployment/cache. app.py foi atualizado com fallback compatível: tenta assinatura com duração e, se detectar módulo antigo, usa assinatura de um argumento e aplica verificações locais de quantidade/duração/estilo. O seletor visual foi movido para o corpo principal para ficar visível em mobile, em vez da sidebar recolhida. Commit 2fcd82e; exige reboot/refresh do app para carregar versão nova. Não testado ainda pelo usuário.
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
5. PRÓXIMO: testar a correção do JSON do Gemini no Streamlit; verificar se o storyboard gera 10+ cenas, soma correta e se cada cena contém visual_style/style_search_terms.
6. Confirmar que o estilo selecionado aparece nas consultas de busca de cada cena.
7. Retestar a busca por cena e validar relevância, variedade e duração dos clipes antes de renderizar.
9. Implementar ranking semântico e avaliação multimodal dos candidatos.

10. Renderizar o primeiro MP4 real de 40–50s, inspecionar qualidade e validar entrega do arquivo final.
9. Considerar Pixabay como fallback quando a chave estiver disponível; Pexels permanece fora do escopo enquanto a emissão de chaves estiver indisponível.
10. Avaliar MCP oficial do Coverr somente se trouxer vantagem após validar a integração REST.

- Ajuste de espaçamento da galeria (commit `f8afaad4`): grid responsivo mantém duas colunas, com `column-gap` de 0,55 rem, `row-gap` de 0,7 rem e margem inferior de 0,7 rem em cada linha de cartões para separar visualmente imagem/botão do próximo estilo. Publicado no GitHub; aguarda reboot e conferência visual em dispositivo móvel.

- Alinhamento das miniaturas (commit `7c9e4583`): o contêiner de cada imagem agora usa a mesma largura relativa/máxima do botão (78%, máx. 155 px), com flex centralizado também no contêiner interno e na própria imagem. Objetivo: centralizar cada prévia exatamente sobre seu botão correspondente nas duas colunas. Publicado no GitHub; aguarda reboot e validação visual móvel.

- Correção da galeria após validação visual (commit `99449eaa`): restaurada a miniatura em 85 px reais (largura/min/max fixados em 85 px no CSS e `st.image(..., width=85)` preservado). O contêiner da imagem volta a ocupar 100% da coluna; a própria imagem usa `left:50%` + `translateX(-50%)` para centralização inequívoca sobre o botão, sem reduzir a miniatura para a largura do botão. Publicado no GitHub; aguarda reboot e validação visual.


## Continuidade técnica — 2026-11-16
- Próxima frente retomada após pausar ajustes visuais: confiabilidade da seleção de mídia e produção end-to-end.
- Commit `0ffb8464` em `nexus/assets.py`: adicionada pontuação lexical dos candidatos com base nos termos do roteiro/cena (título e descrição), priorizando relevância textual antes de orientação e resolução. Mantido o comportamento de fallback progressivo entre variantes de busca; resultados sem URL e URLs já usadas são descartados.
- Commit `df5d9970` em `app.py`: o pipeline mantém um conjunto de URLs já utilizadas e passa a excluir esses clipes nas buscas seguintes, reduzindo repetição entre cenas do mesmo vídeo.
- Commit `8aa5c5bc`: adicionados testes unitários em `tests/test_assets.py` para garantir que relevância da cena vença resolução quando os metadados sustentam isso e que clipes já usados sejam excluídos.
- Verificação realizada nesta sessão: inspeção dos arquivos atuais no GitHub; teste isolado da lógica de ranking/exclusão passou. Os testes do repositório e a execução no Streamlit ainda não foram executados; não considerar pipeline validado.
- Próxima sequência: (1) executar testes automatizados/compilação no repositório; (2) testar storyboard real de 50s com 10–15 cenas e estilo escolhido; (3) testar busca Coverr por cena e revisar títulos/consultas escolhidos, sem repetir clipes; (4) ajustar a busca se houver falsos positivos ou ausência de resultados; (5) gerar o primeiro MP4 completo, validar FFprobe, duração, áudio, legendas e qualidade visual. Pixabay permanece pendente de chave; Pexels permanece fora do escopo até a emissão de chave estar disponível.

- Commit `1d390e2c`: criado workflow GitHub Actions `.github/workflows/tests.yml`, executando compilação sintática (`compileall`) e `unittest discover` em pushes/PRs para `main`. O arquivo foi confirmado no GitHub; o endpoint de status ainda não retornou checks, portanto CI permanece pendente e não deve ser descrita como aprovada.

## Regras para o assistente em novos chats
- Começar lendo este arquivo e o código relevante no GitHub antes de propor mudanças.
- Tratar este documento como registro de continuidade, mas conferir o estado atual do repositório e deployment; pode ficar desatualizado.
- Fazer alterações diretamente no repositório usando a integração GitHub disponível.
- Fazer uma mudança coerente por vez; não instruir o usuário a editar código.
- Dar instruções curtas, uma ação de cada vez.
- Distinguir claramente: implementado no código, implantado, testado, validado com MP4.
- Não pedir para o usuário repetir contexto que esteja documentado aqui.
- Não afirmar conexão em tempo real com Streamlit, logs ou execução do app se isso não estiver disponível.
