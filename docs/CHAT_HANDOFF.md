# NEXUS VIDEO STUDIO — HANDOFF PARA NOVO CHAT

Atualizado em: 16/11/2026
Repositório: https://github.com/porraloca42-stack/nexus-video-studio-
Branch: main
App: https://htykbebk3hceoen5bvopax.streamlit.app/

## REGRA OBRIGATÓRIA PARA RETOMADA
Antes de qualquer ação técnica:
1. Ler integralmente `NEXUS_MASTER_STATE.md` na branch `main`.
2. Ler este arquivo de handoff.
3. Conferir no GitHub o estado atual do workflow e os arquivos relevantes; este handoff é um registro, não substitui a verificação ao vivo.
4. Não repetir passos já feitos, não disparar novo deploy e não alterar código enquanto o deploy atual estiver em andamento.
5. Dar ao usuário instruções curtas, uma ação por vez. Nunca pedir tokens no chat.
6. Não declarar Modal implantado até haver confirmação explícita de sucesso no GitHub/Modal.

## PONTO EXATO ONDE A CONVERSA PAROU
O usuário executou manualmente o workflow GitHub Actions:
- Workflow: `Deploy NEXUS Modal video worker`
- Arquivo: `.github/workflows/modal-deploy.yml`
- Execução: run #1
- Commit exibido: `82ab49d` (branch `main`)
- Job: `deploy`
- Última captura enviada pelo usuário: status **In progress**, duração do job **30m 39s** e execução iniciada manualmente há 30 minutos.
- A captura mostra que o job continuava em andamento depois de 30 minutos, apesar de o YAML conter `timeout-minutes: 30`.
- Portanto, a afirmação anterior de que o GitHub cancelaria necessariamente a execução exatamente aos 30 minutos estava incorreta. A observação da tela é a evidência mais recente; não presumir cancelamento.
- Instrução dada ao usuário: não cancelar nem reiniciar; deixar a execução atual terminar e enviar o resultado.
- Próxima ação: aguardar. Se ainda estiver em andamento, pedir apenas a tela dos logs finais/etapa atual; se terminar, inspecionar o resultado e logs antes de qualquer mudança.
- Não iniciar outra execução até entender o resultado da primeira.

## CONFIGURAÇÃO JÁ FEITA PELO USUÁRIO
O usuário confirmou que:
- Criou uma API token no Modal.
- Cadastrou no GitHub Actions Secrets os dois nomes `MODAL_TOKEN_ID` e `MODAL_TOKEN_SECRET`.
- Não se deve solicitar nem reproduzir valores desses secrets.
- Em momento anterior, o usuário colou um comando contendo token ID e secret no chat. Não está confirmado se esse token exposto foi revogado ou se foi o mesmo usado nos secrets. Tratar como potencialmente comprometido; quando oportuno, orientar uma única vez a revogar o token exposto e substituir os secrets por um token novo. Nunca pedir que compartilhe o valor.

## CONFIGURAÇÃO DO WORKFLOW
O arquivo atual `.github/workflows/modal-deploy.yml` foi relido diretamente da branch main nesta conversa. Contém:
- `timeout-minutes: 30`
- Python 3.12
- instalação do CLI Modal com `python -m pip install --upgrade modal`
- validação de presença dos secrets
- comando `modal deploy modal_worker.py`

O arquivo `modal_worker.py` também foi relido. Define:
- app Modal `nexus-video-i2v`
- classe `Inference`
- GPU H100
- modelo `Lightricks/LTX-Video`, revisão fixada
- volume persistente `nexus-ltx-model-cache`
- timeout do container de inferência de 45 minutos
- escala a zero após 60 segundos sem uso
- geração de clipes em lote, 512×896, 24 fps, 2–5 segundos por cena.

Importante: o `timeout=45 * MINUTES` no worker Modal é diferente do `timeout-minutes: 30` do job GitHub Actions. Não confundir os dois limites.

## ESTADO CONFIRMADO VS. NÃO CONFIRMADO
Confirmado:
- Integração Modal/LTX está implementada na branch main.
- Workflow manual existe.
- Usuário criou token Modal e informou que cadastrou os dois GitHub Secrets.
- Run #1 foi disparado e apareceu como In progress com 30m39s na última captura.

Ainda NÃO confirmado:
- Se run #1 terminou com sucesso ou falha.
- Se o app `nexus-video-i2v` foi realmente implantado no Modal.
- Se o modelo foi baixado/carregado.
- Se houve consumo de GPU/créditos.
- Qualquer teste real de geração image-to-video.
- Qualidade, latência e custo real por clipe ou vídeo.

Não dizer que o deploy está concluído até verificar a execução final.

## DECISÕES DE SEGURANÇA E CUSTO
- Não disparar geração GPU de teste sem autorização explícita.
- O usuário queria manter gastos adicionais em zero; a tela de billing anteriormente mostrava Credits $0, Debits $0 e Usage $0 of $42.50. O valor US$42.50 era limite de utilização, não crédito grátis. Confirmar saldo e limites diretamente no painel antes de qualquer teste pago.
- O usuário adicionou cartão virtual Nubank com limite configurado de R$1; não assumir que isso garante ausência absoluta de cobrança.
- Não afirmar que créditos mensais cobrem dois vídeos/dia sem benchmark real.
- O primeiro teste de GPU, quando autorizado, deve ser pequeno e controlado; o plano anterior recomendava começar por uma cena representativa antes do vídeo completo.

## PRÓXIMOS PASSOS — ORDEM EXATA
1. Aguardar o run #1 atual, sem cancelar ou reiniciar.
2. Quando terminar, verificar status e logs completos.
3. Se sucesso: confirmar no painel Modal que `nexus-video-i2v` foi implantado; não executar geração GPU sem autorização.
4. Se falha: diagnosticar a mensagem concreta. Só então corrigir o workflow/código. Não presumir que aumentar timeout resolverá; identificar a etapa lenta.
5. Se for necessário alterar o timeout, primeiro atualizar este handoff/master state e explicar que um novo workflow run precisará ser disparado manualmente pelo usuário. Não fazer novo deploy sem combinar.
6. Depois de deploy confirmado e autorização explícita para custo, executar piloto controlado e medir tempo/custo/qualidade antes de produzir vídeo de 40–50s.

## DIREÇÃO CRIATIVA — NÃO ESQUECER NO FECHAMENTO
O usuário decidiu que o NEXUS será usado principalmente para vídeos faceless cinematográficos. Não colocar Gabriel nas cenas: não há lip-sync no NEXUS e ele ficaria artificial/robótico. Vídeos anteriores com Gabriel tiveram baixo engajamento e davam muito trabalho; isso não prova que o personagem era a causa, mas reforça a mudança de abordagem.
Estilos a desenvolver depois da estabilização:
- Cosmic Cinematic: universo, espaço, luz e escalas monumentais.
- Hypnotic Surrealism: fenômenos visuais fascinantes, fluidos e movimentos orgânicos.
- Mystical Realism: mistério, espiritualidade e simbolismo.
- Quantum Visuals: visualizações conceituais, sem apresentar metáforas como fatos científicos.
- Emotional Cinematic: histórias humanas e transformação.
- Philosophical Documentary: conhecimento, livros e reflexão.
Três funções editoriais: Atrair (impacto visual e hook), Conectar (narrativa e identificação), Converter (livros como aprofundamento, sem propaganda artificial).
Prioridade: cenas hipnotizantes, movimentos orgânicos em todas as cenas, narração de impacto, hooks fortes e retenção. Após estabilizar o NEXUS, estudar retenção e vendas e então revisar as opções de estilos.
Essa pauta deve ser retomada antes de considerar o projeto encerrado.

## ORIENTAÇÃO DE COMUNICAÇÃO
O usuário ficou frustrado com orientações longas/repetitivas e com uma previsão errada sobre o timeout. Ser direto, assumir erros com clareza, não discutir, não mandar reiniciar sem evidência. O usuário não é programador; executar mudanças diretamente no GitHub.
