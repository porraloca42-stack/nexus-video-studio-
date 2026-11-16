# Configuração do Modal para o NEXUS

Este procedimento prepara a conta Modal e implanta o worker LTX. **Não envie tokens no chat.**

## 1. Criar os tokens do Modal
1. Entre no [Modal Dashboard](https://modal.com/).
2. Abra as configurações do Workspace e procure **API Tokens**.
3. Crie um token e copie os dois valores exibidos:
   - Token ID → será o secret `MODAL_TOKEN_ID`.
   - Token Secret → será o secret `MODAL_TOKEN_SECRET`.
4. Guarde-os temporariamente em local seguro. O Token Secret não deve ser publicado nem enviado por mensagem.

A documentação oficial confirma que os tokens podem ser criados nas configurações do Workspace: https://modal.com/docs/sdk/js/latest

## 2. Guardar os tokens no GitHub
1. Abra o repositório [NEXUS VIDEO STUDIO](https://github.com/porraloca42-stack/nexus-video-studio-).
2. Vá em **Settings → Secrets and variables → Actions**.
3. Clique em **New repository secret**.
4. Crie `MODAL_TOKEN_ID` e cole somente o Token ID.
5. Crie `MODAL_TOKEN_SECRET` e cole somente o Token Secret.

Não coloque os valores no código, no Streamlit, neste arquivo ou em mensagens.

## 3. Configurar proteção de gastos
No Modal Dashboard, abra **Usage & Billing** e configure:
- Spend limit para **US$0 de cobrança líquida adicional**, se essa opção estiver disponível para o Workspace.
- Acompanhe o consumo dos créditos incluídos e não aumente o limite até o piloto ser aprovado.

O Starter atualmente custa US$0/mês e inclui US$30/mês em créditos de computação. GPU exige método de pagamento válido. Os créditos cobrem computação elegível; não são dinheiro pago ao usuário e não cobrem todo tipo de serviço. Consulte https://modal.com/pricing.

## 4. Implantar o worker
Depois de salvar os dois GitHub Secrets:
1. No repositório, abra **Actions**.
2. Selecione **Deploy NEXUS Modal video worker**.
3. Clique em **Run workflow** e confirme.
4. Aguarde o workflow terminar com sucesso.

O deploy instala o worker `modal_worker.py`, cria/usa o Volume de cache `nexus-ltx-model-cache` e publica a aplicação Modal `nexus-video-i2v`. O primeiro carregamento do modelo pode demorar e usar créditos.

## 5. Piloto controlado
Depois do deploy, a primeira produção deve ser um piloto de uma cena. Conferir:
- movimento orgânico e natural;
- identidade e anatomia estáveis;
- composição vertical 9:16;
- duração/codec do MP4;
- tempo de cold start e inferência;
- consumo real no painel Modal.

Não ampliar para todas as cenas de vídeos diários antes de revisar o resultado e o custo do piloto.
