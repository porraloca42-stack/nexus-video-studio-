# NEXUS VIDEO STUDIO

Aplicação Streamlit para transformar roteiros em vídeos verticais com storyboard dirigido por IA, busca de mídia, revisão visual multimodal, narração, legendas e exportação MP4.

## Publicação
- Aplicação Streamlit.
- Arquivo principal: `app.py`.

## Segredos
Configure apenas no gerenciador privado de segredos do Streamlit:
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (opcional; padrão `auto`)
- `PIXABAY_API_KEY` (chave gratuita da API de vídeo do Pixabay)
- `PEXELS_API_KEY` (chave da API de vídeo do Pexels, se já disponível)

O Wikimedia Commons não exige chave de API. O Coverr foi removido das fontes ativas porque a chave disponível na conta do projeto retorna `Invalid API_KEY` e a conta está no plano Demo; não será exigido upgrade pago.

Nunca coloque chaves no repositório nem as envie pelo chat.

## Bibliotecas de vídeo ativas
1. **Wikimedia Commons** — API pública sem chave. O adaptador pesquisa arquivos de vídeo e só aceita arquivos com licença CC0, domínio público ou CC BY. Arquivos CC BY carregam autor, fonte e link de licença para atribuição.
2. **Pixabay** — requer `PIXABAY_API_KEY`. A API limita chamadas e exige cache dos resultados por 24 horas; o app deve respeitar os termos de uso.
3. **Pexels** — requer `PEXELS_API_KEY`. A API usa o endpoint `/v1/videos/search`; respeitar limites e requisitos de atribuição da plataforma.

O Commons é uma fonte complementar e não um catálogo de stock cinematográfico tradicional. Seus vídeos podem ser WebM, Ogg ou MPEG; o pipeline usa FFmpeg para leitura e conversão durante a montagem. A disponibilidade, qualidade, orientação e variedade são verificadas por clipe.

## Pipeline e critérios de seleção
- Gemini planeja cenas e cria consultas específicas para ação/conteúdo e estilo.
- O motor consulta as bibliotecas ativas e agrega candidatos, removendo URLs duplicadas.
- A conexão semântica com a narração é prioridade; estilo visual é secundário; qualidade técnica desempata.
- Gemini Vision avalia quadros reais dos candidatos antes da seleção.
- A produção é interrompida se alguma cena não tiver clipe aprovado; não gera MP4 incompleto.
- Edge TTS gera narração e legendas; FFmpeg monta e valida MP4 vertical, áudio, duração e integridade.

## Diagnóstico
O painel avançado testa busca, download e leitura do vídeo. O resultado precisa ser validado no Streamlit publicado e com uma geração real; testes unitários simulados não comprovam a disponibilidade externa das bibliotecas.

## Estado
Build atual em desenvolvimento: `NEXUS-2026.11.16-wikimedia-provider-2` (a integração Commons e os ajustes de fluxo foram gravados no GitHub; CI e implantação ainda precisam ser confirmados). A seleção multimodal e o pipeline final devem ser considerados validados apenas após inspecionar um MP4 real produzido nesta versão.
