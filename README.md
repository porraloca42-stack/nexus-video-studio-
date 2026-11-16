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

## Bibliotecas automáticas gratuitas
1. **Pixabay** — API gratuita com chave `PIXABAY_API_KEY`; cache e limites da API devem ser respeitados.
2. **Pexels** — API gratuita com chave `PEXELS_API_KEY`; pesquisa orientada a vídeos verticais.
3. **Wikimedia Commons** — API pública sem chave; o adaptador aceita apenas CC0, domínio público e CC BY, guardando autor, fonte e licença.

O Coverr não é fonte ativa: a chave previamente testada retornou `Invalid API_KEY` no plano Demo. O NEXUS não exige upgrade pago.

## Bancos gratuitos complementares (curadoria manual)
- **Mixkit** — [coleção vertical](https://mixkit.co/free-vertical-videos/). Usar somente itens com **Free License**; itens Restricted não podem ser usados em conteúdo comercial. A licença gratuita permite projetos comerciais e não exige atribuição, mas os termos proíbem bots/scraping e downloads em massa.
- **ISO Republic** — [vídeos CC0](https://isorepublic.com/). Uso pessoal e comercial; sem atribuição obrigatória. Confirmar a licença do item.
- **Vecteezy** — [vídeos gratuitos](https://www.vecteezy.com/free-videos). A licença Free exige atribuição e impõe limites ao uso comercial e a projetos de vídeo; a API gratuita anuncia 500 downloads/mês, mas não inclui acesso aos metadados de recursos, portanto não serve como busca automática confiável para o NEXUS.
- **Vidsplay** — [biblioteca gratuita](https://www.vidsplay.com/). Exige crédito/link visível conforme os termos.
- **National Park Service** — [multimídia e B-roll](https://www.nps.gov/media/multimedia-search.htm). Útil para natureza e parques; verificar direitos/créditos por arquivo.

Esses sites complementam a descoberta e a curadoria humana. O NEXUS não faz scraping nem simula APIs: sem uma API pública que permita pesquisa e download automatizados, o site é apresentado como fonte manual, não como biblioteca automática do render. NASA não entra na seleção comercial automática porque parte do acervo pode conter material de terceiros e as diretrizes restringem usos promocionais/comerciais.

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
