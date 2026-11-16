# Ativação do Cloudflare Workers AI + Remotion

O modo de imagens originais é opcional até a validação de produção. Não envie tokens pelo chat nem os coloque em arquivos do repositório.

## 1. Criar token Cloudflare

No painel Cloudflare, crie um API Token limitado à conta do NEXUS com permissão **Workers AI Read**. A chamada \`POST /accounts/{account_id}/ai/run/{model}\` aceita Workers AI Read ou Workers AI Write.

Guarde:
- Account ID da conta Cloudflare.
- API Token criado.

## 2. GitHub Actions Secrets

No repositório \`porraloca42-stack/nexus-video-studio-\`:
1. Abra **Settings → Secrets and variables → Actions**.
2. Selecione **New repository secret**.
3. Crie:
   - \`CLOUDFLARE_ACCOUNT_ID\` — Account ID.
   - \`CLOUDFLARE_API_TOKEN\` — token Cloudflare.

O worker usa o token para gerar imagens e para derivar a chave Fernet que protege o manifesto e o MP4.

## 3. Streamlit Secrets

No Streamlit Cloud:
1. Abra o app NEXUS.
2. Vá a **Manage app → Settings → Secrets**.
3. Adicione:

\`\`\`toml
GITHUB_ACTIONS_TOKEN = "seu_token_fine_grained_do_github"
CLOUDFLARE_API_TOKEN = "o_mesmo_token_cloudflare"
\`\`\`

Crie o GitHub fine-grained personal access token limitado ao repositório NEXUS com:
- **Actions: Read and write** — disparar o workflow e consultar runs/artifacts.
- **Contents: Read** — leitura do repositório e workflow.

O token GitHub fica somente no Streamlit Secrets. O token Cloudflare deve existir tanto no Streamlit Secrets quanto no GitHub Actions Secrets. Não cole valores no código, issues, commits ou chat.

## 4. Testar

Após salvar os Secrets:
1. Aguarde o Streamlit reiniciar.
2. Abra o NEXUS e escolha **Imagens originais · Cloudflare AI + Remotion**.
3. Gere um storyboard curto e produza o vídeo.
4. O app envia o manifesto criptografado, acompanha o GitHub Actions e recupera o MP4 descriptografado.
5. Confirme resolução 720×1280, áudio, duração e aparência visual antes de usar em produção.

## Modelo e orçamento

Modelo inicial: \`@cf/black-forest-labs/flux-2-klein-4b\`, 512×910, quatro passos fixos. A variante 4B usa Apache 2.0, compatível com uso comercial. A estimativa de ~191 imagens/dia considera dois tiles de saída por imagem e 10.000 Neurons/dia no plano Free; não é uma cota garantida.
