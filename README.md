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

A busca Coverr está implementada e foi testada no ambiente publicado: a API autenticou e retornou cinco clipes. O download interno no servidor e a integridade do MP4 foram testados com sucesso: H.264, 606×1080, 8 segundos. Esse diagnóstico usa armazenamento temporário no servidor, não no celular. O fluxo de produção foi atualizado para validar clipes, gerar narração e legendas, renderizar com FFmpeg, verificar áudio/vídeo e manter o MP4 disponível para prévia e download. O primeiro teste end-to-end encontrou storyboard válido, mas zero resultados nas buscas de seis cenas; FFmpeg não foi iniciado. O usuário corrigiu a arquitetura: a quantidade de cenas e as buscas visuais devem ser decididas pelo Gemini com base no roteiro, sem dicionário fixo de temas. Atualizado: para 50s, mínimo 10 cenas e meta 12–15, normalmente 3–4s cada; validação rejeita storyboard insuficiente ou com duração divergente. Consultas de busca derivam apenas da intenção específica escrita pelo diretor. FFmpeg repete uma fonte curta para preencher a duração do segmento, como proteção contra lacunas; o sistema ainda deve priorizar variedade e clipes suficientes. Aguardando novo storyboard e teste real.

Pixabay possui implementação preliminar como alternativa, mas ainda não está operacional sem sua chave. Pexels não está integrado; a emissão de novas chaves API está temporariamente indisponível.

A seleção visual multimodal dos clipes ainda não foi implementada. Não considerar o pipeline MP4 validado até renderizar e inspecionar um vídeo real.
