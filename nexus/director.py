import json
import requests

SYSTEM = """
Você é o DIRETOR CONTEXTUAL do NEXUS VIDEO STUDIO.
Primeiro compreenda o assunto inteiro, a intenção, os conceitos e a progressão da narrativa. Só então divida em cenas.
A narrativa determina O QUE aparece. O estilo escolhido determina COMO tudo será filmado. O estilo é bloqueado: mantenha fotografia, paleta, iluminação, textura, realismo e linguagem de câmera consistentes em todas as cenas.
Não use biblioteca fixa de cenas emocionais ou abstratas. Cada ação visual deve representar precisamente a fala correspondente.
Priorize clipes com ações concretas e observáveis. Evite imagens genéricas escolhidas por palavras isoladas, colagens, slideshows, infográficos escolares e metáforas sem clareza.
Não invente capas, páginas, citações ou características de livros e produtos. Se não houver referência visual confiável, represente a prática sem falsificar o objeto.
Crie cenas que somem à duração pedida. Para cada cena inclua fala, ação visual, justificativa semântica, ambiente, sujeitos, enquadramento, movimento, pelo menos dois microeventos e duas consultas visuais precisas em inglês.
Se houver roteiro, preserve sua intenção e não acrescente alegações factuais. Marque incertezas em vez de inventar.
Retorne somente JSON válido neste formato:
{
 "topic_interpretation":"...",
 "creative_thesis":"...",
 "style_lock":"...",
 "scenes":[
  {
   "duration_seconds":8,
   "purpose":"...",
   "voiceover":"fala exata",
   "visual_action":"ação concreta",
   "semantic_reason":"por que a ação corresponde precisamente à fala",
   "setting":"...",
   "subjects":"...",
   "shot_type":"...",
   "camera_motion":"push_in, pull_out, pan_left ou pan_right",
   "motion_events":["evento 1","evento 2"],
   "asset_search_query":"English query: exact subject + action + setting + shot + visual style",
   "fallback_search_query":"different precise English query"
  }
 ]
}
"""

def _request(prompt, secret_reader):
    key = secret_reader("GEMINI_API_KEY")
    model = secret_reader("GEMINI_MODEL", "gemini-3.8-flash")
    if not key:
        raise RuntimeError("Diretor de IA indisponível.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.45, "responseMimeType": "application/json"}
    }
    try:
        response = requests.post(url, params={"key": key}, json=payload, timeout=180)
    except requests.RequestException:
        raise RuntimeError("Não foi possível conectar ao serviço Gemini. Tente novamente.") from None
    if response.status_code == 429:
        raise RuntimeError("Limite temporário do modelo atingido. Tente novamente mais tarde.")
    if response.status_code in (401, 403):
        raise RuntimeError("O Gemini recusou a autenticação ou o acesso ao modelo. Confira a configuração da chave e do modelo.")
    if response.status_code == 404:
        raise RuntimeError(f"O modelo Gemini '{model}' não está disponível para esta chave. Em Secrets, configure GEMINI_MODEL = \"gemini-3.8-flash\".")
    if not response.ok:
        raise RuntimeError(f"Falha no Gemini (HTTP {response.status_code}). Tente novamente.")
    data = response.json()
    try:
        result = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(result)
    except (KeyError, IndexError, ValueError):
        raise RuntimeError("O diretor não retornou um storyboard válido.") from None

def create_storyboard(topic, style, duration, secret_reader):
    prompt = f"""ASSUNTO OU ROTEIRO:
{topic}

ESTILO VISUAL ÚNICO E BLOQUEADO: {style}
DURAÇÃO TOTAL: {duration} segundos.
Planeje a narrativa completa antes de dividi-la. As cenas devem cobrir toda a progressão, sem repetir a mesma imagem ou ação. Preserve a relação exata entre cada fala e sua imagem."""
    plan = _request(prompt, secret_reader)
    plan["style_lock"] = style
    return plan

def validate_storyboard(plan):
    errors = []
    scenes = plan.get("scenes", [])
    if not scenes:
        return ["O diretor não criou cenas."]
    for index, scene in enumerate(scenes, 1):
        for field in ("voiceover", "visual_action", "semantic_reason", "camera_motion", "asset_search_query"):
            if not str(scene.get(field, "")).strip():
                errors.append(f"Cena {index}: campo {field} vazio.")
        if len(scene.get("semantic_reason", "")) < 45:
            errors.append(f"Cena {index}: justificativa semântica superficial.")
        if len(scene.get("motion_events", [])) < 2:
            errors.append(f"Cena {index}: faltam microeventos.")
    return errors
