# NEXUS — Plano de integração ComfyUI + LTX-2.5 no repositório oficial

Data da pesquisa: 17/11/2026  
Status: pesquisa técnica e arquitetura propostas; **não implementado, não implantado e não executado em GPU**.

## 1. Objetivo e decisão de arquitetura

Integrar LTX-2.5 + ComfyUI como motor-alvo definitivo diretamente no repositório oficial NEXUS (`porraloca42-stack/nexus-video-studio-`, branch `main`). Não criar projeto/repositório paralelo nem prever portabilidade posterior. Um processo/worker isolado pode ser usado por segurança e dependências, mas será um componente do próprio NEXUS, com código, workflow, testes, deploy e telemetria versionados no mesmo repositório. LTX-Video 0.9.8 permanece apenas como fallback temporário até os portões de validação serem aprovados. Nenhuma inferência, benchmark ou implantação que possa gerar custo variável será iniciada sem autorização explícita.

## 2. Evidências oficiais consultadas

- Workflow oficial de referência: `LTX-2.5_T2V_I2V_Two_Stage_Distilled.json`, em `Lightricks/ComfyUI-LTXVideo/example_workflows/2.5/`.
- O workflow oficial usa o transformer distilled de 22B em BF16, aceita uma imagem inicial opcional e faz duas etapas: geração em resolução-base, upscale espacial latente 2× e refinamento curto de 3 passos.
- A documentação da família indica que o fluxo de duas etapas é o padrão recomendado quando o detalhe espacial importa; o single-stage é mais leve e adequado a prévias.
- O workflow oficial gera áudio e vídeo conjuntamente. O NEXUS, porém, usa Fish Audio como fonte de narração. A integração deve descartar qualquer áudio gerado pelo LTX na composição final; investigar se o decode/mux de áudio pode ser removido sem quebrar o grafo.
- O workflow exige contagem de frames no formato `1 + 8n`. O JSON consultado tem 24 fps, 121 frames e dimensões padrão 960×544 (paisagem). A adaptação NEXUS deve ser vertical, com dimensões múltiplas de 32, por exemplo 544×960, e contagem 49/73/97/121 frames para durações aproximadas de 2/3/4/5 segundos a 24 fps. A linha do tempo final deve continuar sendo controlada pelo Remotion.
- O fluxo oficial carrega transformer 22B, VAE de vídeo, VAE de áudio, encoder Gemma 4 12B, enhancer Gemma 4 E2B e upscaler latente. Como o Gemini já entrega prompts dirigidos no NEXUS, o enhancer extra deve ser desativado/removido quando tecnicamente seguro para reduzir carga e dependências.
- Requisitos publicados para LTX-2.5: GPU NVIDIA com pelo menos 32 GB VRAM, 32 GB RAM, 100 GB livres, CUDA 12.7+ e Python 3.12+. Configuração recomendada: A100 80 GB ou H100, 64 GB+ RAM e 200 GB+ SSD.
- A L40S atual do NEXUS tem 48 GB VRAM: supera o mínimo publicado, mas fica abaixo da recomendação. Isso não prova que o workflow 22B BF16 caiba com folga, nem que o tempo/custo seja aceitável.
- A API nativa do ComfyUI permite submeter workflows em `POST /prompt`, acompanhar por `/ws`, consultar `/history/{prompt_id}` e recuperar arquivos por `/view`. O grafo de produção precisa estar no formato API exportado; o JSON visual do workflow não deve ser enviado diretamente como se fosse o formato API.

Fontes oficiais:
- [LTX-2.5 ComfyUI workflows](https://github.com/Lightricks/ComfyUI-LTXVideo/blob/master/example_workflows/2.5/README.md)
- [Workflow I2V/T2V two-stage distilled](https://github.com/Lightricks/ComfyUI-LTXVideo/blob/master/example_workflows/2.5/LTX-2.5_T2V_I2V_Two_Stage_Distilled.json)
- [LTX system requirements](https://docs.ltx.io/open-source-model/getting-started/system-requirements/)
- [ComfyUI server HTTP/WebSocket routes](https://github.com/Comfy-Org/docs/blob/main/development/comfyui-server/comms_routes.mdx)

## 3. Arquitetura proposta — worker separado

1. Implementar o worker ComfyUI como componente do NEXUS oficial. O runtime pode ser isolado (por exemplo, uma aplicação Modal dedicada) para controlar dependências e segurança, mas seu código e ciclo de vida permanecem neste repositório; não criar produto paralelo.
2. Fixar versões/SHAs de ComfyUI e `ComfyUI-LTXVideo`; não usar `master` flutuante em produção.
3. Construir a imagem do worker com Python/CUDA compatíveis, ComfyUI, custom nodes e dependências explicitamente pinadas.
4. Manter os pesos num Modal Volume persistente. Verificar gating/licença e necessidade de `HF_TOKEN` sem expor segredos.
5. Iniciar ComfyUI como processo local dentro do container Modal, limitado a loopback; não expor a interface/porta publicamente.
6. Carregar um workflow em formato API exportado e versionado no repositório. Fazer patch somente dos inputs autorizados: prompt I2V, imagem, duração/frame count, fps, dimensões, seed e negative prompt.
7. Enviar keyframe por `POST /upload/image`; submeter o grafo por `POST /prompt`; acompanhar a execução via WebSocket ou polling de `/history/{prompt_id}`; baixar o resultado via `/view`.
8. Normalizar o MP4 com FFmpeg: H.264, dimensões verticais, fps definido, sem áudio LTX. Validar arquivo, codec, duração, frames e stream de vídeo antes de devolver bytes.
9. Retornar telemetria por cena: modelo/revisão, GPU, cold start, tempo de carregamento, tempo de fila, inferência, duração/frames, memória máxima, tempo total faturável estimado e custo GPU estimado.
10. Integrar o adaptador ao contrato comum `nexus/video_engine.py`. Durante a transição, a seleção interna mantém LTX 0.9.8 como padrão/fallback; só depois dos portões de validação LTX-2.5 poderá assumir o padrão.

## 4. Compatibilidade com o NEXUS

- Entrada: keyframe FLUX já aprovado + `video_motion_prompt` em inglês + duração de 2–5 segundos.
- Preservar a identidade do protagonista pela imagem inicial e pelo fluxo de referência já existente.
- Não repetir `image_prompt` no prompt de movimento; descrever somente a ação que ocorre após o primeiro quadro.
- Não acrescentar zoom/pan/shake sintético no Remotion sobre o clipe gerado.
- Fish Audio continua sendo a única narração oficial do vídeo. O áudio gerado pelo LTX não deve substituir, misturar ou duplicar a voz.
- A saída deve respeitar o contrato de clipe usado por `nexus/modal_i2v.py` ou por um adaptador paralelo compatível, sem acoplar o restante do pipeline ao ComfyUI.

## 5. Trabalho de código permitido sem GPU

- Criar adaptador HTTP ComfyUI com cliente mockável.
- Versionar o workflow API exportado e validar os IDs/tipos dos nós usados pelo patch.
- Criar testes de contrato para upload de imagem, submissão, prompt_id, polling, histórico, download, timeout, erro de validação e cancelamento.
- Criar testes para dimensões 9:16, frames 1+8n, duração 2–5s, seed, saída MP4 sem áudio e contrato de telemetria.
- Testar conversão/patch do workflow apenas com dados falsos; nenhum download de pesos, boot de ComfyUI ou chamada GPU.
- Fixar commits e hashes dos artefatos, documentar tamanhos dos modelos e dependências.

## 6. Portões de custo e validação

**Não autorizado nesta fase:** baixar pesos grandes, iniciar ComfyUI em GPU, deploy que provoque download de modelos, smoke test de inferência, benchmark, geração de clipes ou render completo.

Antes de qualquer execução paga, apresentar estimativa baseada em cold start + carregamento + inferência + scaledown + CPU/RAM/armazenamento. O teto desejado permanece US$0,50 por vídeo, com reserva de US$0,08 para CPU/memória/variação e orçamento operacional de GPU de US$0,42. A estimativa não é garantia de fatura.

Após autorização específica:
1. Executar apenas um clipe de 2–3s, com keyframe/prompt idênticos ao teste comparativo do LTX 0.9.8.
2. Capturar custo real, cold start, memória, tempo de inferência e estabilidade.
3. Avaliar movimento físico, progressão temporal, aderência à ação, identidade, anatomia, flicker e detalhes.
4. Comparar lado a lado com LTX 0.9.8.
5. Só considerar troca do worker se qualidade e custo forem melhores e repetíveis.

## 7. Decisões em aberto

- Se 48 GB L40S é suficiente para o workflow two-stage 22B BF16 sem OOM e sem offload excessivamente lento.
- Se é necessário A100 80 GB/H100, e se o custo pode caber no orçamento.
- Como exportar e fixar o workflow em formato API, incluindo subgraphs.
- Como remover o decode de áudio sem alterar a geração AV de forma inválida.
- Se o modelo e os pesos exigem aceite de licença ou token Hugging Face para download automatizado.
- Quais nós/custom nodes e versões mínimas são obrigatórios no workflow oficial consultado.

## 8. Estado

- Pesquisa documental: feita.
- Arquitetura proposta: documentada.
- Código ComfyUI no NEXUS: não implementado.
- Worker ComfyUI: não criado.
- Workflow API exportado e adaptado: não criado.
- Testes de contrato: não criados.
- Deploy: não feito.
- GPU/inferência/benchmark: não executados.
- Custo variável nesta pesquisa: US$0.


## 9. Base HTTP client — implementação sem GPU (17/11/2026)
- Criado `nexus/comfyui_client.py`: cliente HTTP mockável para upload de keyframe, submissão de workflow API, leitura de histórico, espera por conclusão, detecção de erro e download de arquivo.
- Criado `tests/test_comfyui_client.py`: testes com sessão HTTP falsa para upload, fila, node_errors, sucesso, erro de execução, timeout sem reenvio automático, extração/download de MP4 e validação de URL.
- O módulo não inicia ComfyUI, não baixa pesos, não usa Modal, não importa Torch e não faz chamadas de rede durante importação. Só opera se for instanciado e chamado por um futuro worker.
- Ainda não existe workflow API exportado, mapeamento de nós, worker Modal ComfyUI ou integração ao fluxo de produção. O cliente genérico não significa que o LTX-2.5 já esteja integrado.
- Estado: código e testes gravados na branch main; execução automatizada ainda não confirmada. Nenhuma inferência, GPU, download de pesos ou deploy foi realizado; custo variável adicional US$0.


### Complemento — patch seguro de workflow API (17/11/2026)
- `nexus/comfyui_client.py` agora inclui `patch_api_workflow(workflow, bindings)`: cria cópia profunda do grafo e altera somente inputs explicitamente mapeados. Rejeita nós/inputs inexistentes, bindings incompletos e inputs que já estejam conectados por links, evitando quebrar silenciosamente a topologia.
- Testes adicionais verificam isolamento do grafo original, alteração de widgets, rejeição de links e referências desconhecidas.
- Commits: `273c047` (patcher), `9cb0830` (testes).
- O arquivo `.github/workflows/tests.yml` foi inspecionado: a job de regressão compila `nexus` e executa `python -m unittest discover -s tests -v`, portanto o novo arquivo de teste entra na descoberta padrão. Isso confirma a configuração do workflow, não o resultado de uma execução.


## 10. Decisão arquitetural atualizada — 17/11/2026

A proposta anterior de “protótipo isolado” não significa projeto paralelo e está formalmente substituída: todo o desenvolvimento ocorre diretamente no NEXUS oficial. A implementação já começou com `nexus/video_engine.py` e a delegação do orquestrador `nexus/remote_render_job.py` ao contrato comum. O adaptador LTX 0.9.8 preserva o fluxo atual. O nome `ltx25_comfyui` é deliberadamente bloqueado até existir workflow API versionado e adaptador validado. O próximo incremento é adicionar o workflow API exportado e seus testes de contrato no mesmo repositório. Nenhuma migração/portabilidade futura será necessária.


## 11. Fonte upstream fixada e estrutura verificada — 17/11/2026
- Revisão pinada: `db476dacc1469b2f17ccc5735693916afcb6fac1`.
- Manifesto versionado em `workflows/ltx25/source_manifest.json`: registra URL/licença, ID do workflow, 20 nós de topo, 34 links e seis subgrafos. A inspeção do arquivo original confirmou formato visual, não API prompt.
- Não enviar o JSON visual diretamente a `POST /prompt`. É necessário obter/exportar o API prompt verdadeiro e validar IDs/classes/inputs; a conversão de subgrafos é um item técnico explícito, não uma suposição.
- O manifesto fixa os requisitos NEXUS: 9:16, 2–5s, Fish Audio como voz oficial, áudio LTX descartado e Remotion como compositor final.
- Testes do manifesto em `tests/test_ltx25_workflow_manifest.py`. Commits: `dbbaf1b` e `71d5a61`.
- Estado: fonte fixada e estrutura verificada; API prompt, bindings, worker e GPU ainda não implementados/testados.


## 12. Correção da suíte e validação CI — 17/11/2026
- Um teste antigo da auditoria visual foi atualizado para refletir o contrato multimodal atual: três quadros temporais por cena e os campos `motion_progression_score`, `action_observed`, `continuity_score` e `temporal_progression`. O código de produção não foi alterado nesta correção.
- Commit final: `6731ed3`. CI #878 / run `44091549701` no commit `6731ed34867b08b1c63f62354167c200f854811b`: 148 testes Python aprovados, Remotion typecheck aprovado e Commons live smoke aprovado.
- A implementação oficial do ComfyUI frontend `graphToPrompt` (revisão `196dd85cde3314dffdc33b41caa3e5d9be432ffb`) gera o API prompt expandindo subgrafos por `ExecutableNodeDTO.getInnerNodes()`, resolvendo conexões e widgets e emitindo `class_type` + `inputs`. Isso reforça que o workflow visual pinado não pode ser enviado diretamente a `POST /prompt` nem convertido com uma substituição superficial.
- Próxima etapa técnica: definir como gerar/exportar o API prompt com expansão correta dos seis subgrafos (preferencialmente pelo conversor oficial ou export real do ComfyUI), versionar o resultado e testar estrutura, links e bindings antes de criar o adaptador LTX-2.5.


## 12. Investigação do exportador API e contrato de arrays — 17/11/2026
- Fonte consultada: ComfyUI frontend em 196dd85cde3314dffdc33b41caa3e5d9be432ffb, arquivo src/utils/executionUtil.ts. A função oficial graphToPrompt expande os subgrafos por meio de ExecutableNodeDTO, constrói um mapa de nós executáveis, percorre a ordem de execução, resolve inputs conectados e valores de widgets e produz o objeto API com class_type, inputs e _meta.
- O exportador oficial encapsula widgets de array em objeto com __value__; arrays sem esse encapsulamento representam links [origin_node_id, origin_slot]. Isso é parte do contrato e não pode ser ignorado por patchers.
- O cliente NEXUS agora encapsula bindings de array em __value__, preservando o comportamento do exportador. Teste de regressão adicionado.
- O workflow visual fixado possui seis subgrafos, incluindo o subgrafo Input Parameters com dois nós GemmaAPITextEncode. O caminho de API externa depende de uma chave LTX; a configuração padrão observada não fornece chave. Não usar serviço externo nem adicionar segredo sem avaliar custo e necessidade. A codificação local usa Gemma e deve ser revisada para remover o enhancer somente se isso não quebrar a topologia.
- CI #887 / run 44092812673 / commit 2d0a8068c72430cc4dd6cded0f5d49a981968ccd: 154 testes Python, Remotion typecheck e Commons live smoke aprovados.
- Estado: compatibilidade do patcher e regressões testadas; API prompt real ainda não exportado; bindings dos nós ainda não validados; worker e integração não implementados; GPU, downloads, deploy e render não executados.


## 13. Contrato real do exportador API — revisão de implementação (17/11/2026)

Foi inspecionado o código-fonte do exportador oficial do ComfyUI frontend, fixado em `196dd85cde3314dffdc33b41caa3e5d9be432ffb`:

- `src/utils/executionUtil.ts`, função `graphToPrompt`.
- `src/lib/litegraph/src/subgraph/ExecutableNodeDTO.ts`, classe `ExecutableNodeDTO`.

A exportação não é uma conversão simples do JSON visual. O frontend:
1. Percorre os nós na ordem de execução e chama `getInnerNodes()` para expandir subgrafos.
2. Cria IDs de execução compostos por caminho de instâncias de subgrafo, separados por dois-pontos.
3. Resolve cada input através dos limites dos subgrafos, incluindo conexões que entram/saem e valores de widgets pass-through.
4. Resolve nós em bypass/never, nós virtuais e links antes de montar o grafo executável.
5. Serializa widgets e conexões em `class_type` + `inputs` e anexa `_meta`.
6. Encapsula widgets cujo valor é array em `{ "__value__": [...] }`, pois arrays de dois elementos no prompt API são reservados para conexões.

O manifesto versiona agora o repositório, commit e caminhos exatos do exportador, além de manter `api_prompt_exported=false` e `export_runtime_verified=false`. O patcher NEXUS já reproduz o encapsulamento de arrays e tem teste de regressão.

**Decisão de segurança:** não reimplementar superficialmente o algoritmo nem gerar IDs a partir dos IDs visuais. A resolução completa depende do runtime LiteGraph, das definições de nós registradas e da topologia de subgrafos. O próximo passo seguro é executar a exportação oficial com ComfyUI/frontend e custom nodes compatíveis, sem carregar pesos nem iniciar inferência; depois validar o API prompt e os bindings em teste mockado. Se esse runtime não puder ser executado sem custo variável, manter o workflow bloqueado em vez de fabricar um grafo.

A inspeção também encontrou dois nós `GemmaAPITextEncode` no subgrafo de parâmetros. O workflow documenta um caminho de codificação externa quando uma chave LTX é fornecida; o NEXUS não deve configurar essa chave automaticamente. O caminho local ainda usa modelos Gemma e precisa de análise separada para decidir se o enhancer pode ser desativado sem quebrar as conexões.

Estado após esta investigação: exporter identificado e pinado; API prompt não exportado; runtime de exportação não executado; bindings não validados; worker não integrado; GPU, pesos, deploy e geração não iniciados. Custo variável adicional: US$0.


### Correção de compatibilidade da referência do frontend — 17/11/2026

O manifesto inicial havia apontado para uma revisão posterior do frontend (1.61.2). A conferência do campo workflow extra.frontendVersion mostrou que o arquivo visual LTX-2.5 foi salvo com **ComfyUI frontend 1.48.7**. Para evitar usar uma implementação posterior como se fosse a original, a referência foi corrigida para a tag oficial v1.48.7, commit `6d6af63c00f132cd25dc29307fc56bd2c094fa22`.

A função `graphToPrompt` e a classe `ExecutableNodeDTO` foram relidas nessa versão exata. O contrato de expansão de subgrafos, resolução de links/widgets e encapsulamento de arrays já existe nela. O manifesto e o teste agora verificam explicitamente a versão 1.48.7. A revisão 1.61.2 fica apenas como leitura comparativa e não é a base de compatibilidade.

Essa correção não cria um API prompt e não altera o status de integração: a exportação oficial ainda precisa ser executada em runtime compatível, com os nós registrados.


## 14. Pausa para revisão da arquitetura híbrida faceless — 17/11/2026

A decisão anterior de tratar LTX-2.5/ComfyUI como motor-alvo definitivo fica **em revisão** após a pesquisa comparativa de apps faceless comerciais. O objetivo do NEXUS é o resultado audiovisual, não adotar um modelo específico por ser mais novo.

O relatório `NEXUS_FACELESS_VIDEO_ARCHITECTURE_RESEARCH_2026-11-17.md` identifica que Revid, Crayo, Pictory, InVideo, Fliki e VEED expõem combinações de stock, imagens IA animadas, motion graphics, mídia própria/gameplay e vídeo IA. Revid recomenda vídeo premium em uma ou duas cenas hero, não em todas as cenas.

Até concluir uma comparação controlada:
- não implementar mais integração LTX-2.5;
- não baixar pesos, iniciar GPU, fazer deploy ou executar render pago;
- preservar o LTX-0.9.8 atual, sem o tornar obrigatório para todas as cenas;
- priorizar desenho/testes sem custo para roteamento de mídia por cena e recursos Remotion;
- decidir o papel futuro do LTX-2.5 apenas com dados de qualidade, tempo e custo medidos.

Esta pausa não remove os commits, o manifesto ou a investigação do exportador API. Apenas impede que o plano técnico seja interpretado como autorização para continuar investindo na adoção do LTX-2.5 antes da revisão de arquitetura.
