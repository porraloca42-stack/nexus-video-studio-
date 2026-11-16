# NEXUS VIDEO STUDIO

Aplicação pessoal para transformar um assunto ou roteiro em vídeo vertical com direção contextual por IA, narração, legendas e exportação MP4.

## Publicação
Aplicação Streamlit. Arquivo principal: `app.py`.

## Segredos da aplicação
Configure nas definições privadas do serviço:
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (opcional; padrão `auto`)
- `COVERR_API_KEY` (Coverr; configurada pelo usuário, ainda pendente de teste real)
- `PIXABAY_API_KEY` (opcional; integração preliminar, ainda não configurada)

As chaves são lidas do gerenciador de segredos e não devem ser inseridas no repositório.

## Estado desta versão
O diretor gera storyboard com Gemini; Edge TTS gera a narração e as legendas; FFmpeg monta o vídeo vertical. A aplicação abre normalmente no Streamlit, conforme confirmação do usuário em 2026-11-16.

A busca Coverr está implementada e foi testada no ambiente publicado: a API autenticou e retornou cinco clipes. O download interno no servidor e a integridade do MP4 foram testados com sucesso: H.264, 606×1080, 8 segundos. Esse diagnóstico usa armazenamento temporário no servidor, não no celular. O fluxo de produção foi atualizado para validar clipes, gerar narração e legendas, renderizar com FFmpeg, verificar áudio/vídeo e manter o MP4 disponível para prévia e download. O primeiro teste end-to-end encontrou storyboard válido, mas zero resultados nas buscas de seis cenas; FFmpeg não foi iniciado. A quantidade de cenas e as buscas visuais são decididas pelo Gemini com base no roteiro, sem dicionário fixo de temas. Para 50s, mínimo 10 cenas e meta 12–15, normalmente 3–4s cada. A resposta JSON do Gemini agora é tratada de forma robusta, com extração de múltiplos blocos, remoção de cercas Markdown, detecção de bloqueio/truncamento e limite de saída de 8192 tokens. O app oferece 24 estilos visuais selecionáveis; o estilo é enviado ao Gemini, mostrado por cena e anexado às consultas de stock. Cada cena precisa retornar visual_style e style_search_terms. Aguardando novo storyboard e teste real.

Coverr, Pixabay e Pexels possuem adaptadores no motor de busca. O motor consulta todas as fontes com chave configurada, agrega os candidatos, remove URLs duplicadas e compara a relevância antes de escolher. Coverr está configurado; Pixabay ainda depende de PIXABAY_API_KEY; Pexels depende de PEXELS_API_KEY, e a emissão pública de novas chaves está pausada. A presença do adaptador não significa que a fonte esteja autenticada ou operacional.

A seleção visual multimodal dos clipes ainda não foi implementada. Não considerar o pipeline MP4 validado até renderizar e inspecionar um vídeo real.


A seleção multi-fonte preserva os metadados de origem dos clipes e apresenta créditos na interface de prévia quando a produção termina. A seleção visual por modelo multimodal continua sendo uma etapa futura; o ranking atual usa metadados textuais e qualidade técnica.
