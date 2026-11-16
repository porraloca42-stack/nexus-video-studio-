# NEXUS VIDEO STUDIO

Aplicação pessoal para transformar um assunto ou roteiro em um vídeo vertical com direção contextual por IA, narração, legendas e exportação MP4.

## Publicação
Aplicação Streamlit. Arquivo principal: `app.py`.

## Segredos da aplicação
Configure nas definições privadas do serviço:
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (opcional; padrão `gemini-2.5-flash`)
- `PEXELS_API_KEY`

As chaves são lidas do gerenciador de segredos e não devem ser inseridas no repositório.

## Estado desta versão
Esta é uma primeira versão funcional em desenvolvimento. O diretor gera storyboard com Gemini; os clipes são encontrados por consultas textuais no Pexels; Edge TTS gera a voz e as legendas; FFmpeg monta o MP4 vertical. A seleção visual ainda precisa de avaliação multimodal por cena e a renderização ainda não equivale a um gerador de vídeo IA de ponta.
