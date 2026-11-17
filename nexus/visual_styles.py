"""Internal visual style library for NEXUS. Technical art direction is never exposed in the UI."""

_STYLE_ROWS = [
  [
    "Quântico & Cósmico",
    "Universo, manifestação e geometria luminosa.",
    "cosmic color grading, volumetric illumination, refined science-fiction visual language",
    "deep indigo, midnight blue, violet, restrained gold",
    "soft volumetric illumination, controlled bloom, luminous contrast",
    "layered wide compositions, slow orbital camera movement, measured push-ins",
    "fine film grain, atmospheric depth, subtle luminous particulate texture",
    "Express scale, interconnection, uncertainty and wonder through spatial depth, luminous contrast and a refined cosmic visual language. Let the script determine what is depicted; celestial motifs are not a default subject.",
    "horoscope-style graphics, pseudo-scientific claims, interface clutter, oversaturation, generic visual filler",
    "abstract",
    [
      "#11152f",
      "#d9b4ff",
      "#3b3975"
    ]
  ],
  [
    "Sonho Lúcido",
    "Surrealismo, subconsciente e realidades paralelas.",
    "surrealist visual language, liminal composition, ethereal transitions",
    "midnight blue, lavender, pearl, desaturated teal, amber",
    "diffused illumination, soft directional gradients, reflective tonal accents",
    "spatially ambiguous framing, deliberate reveals, controlled symmetry",
    "soft diffusion, translucent layering, subtle optical distortion",
    "Use spatial ambiguity, dream logic and controlled visual transitions to express the exact narrative or psychological state. Keep every transformation purposeful and legible.",
    "random surreal collage, incoherent transformations, excessive distortion, childish rendering, visual noise",
    "abstract",
    [
      "#26213f",
      "#c4a7ff",
      "#756b9b"
    ]
  ],
  [
    "Dark Psychology",
    "Psicologia sombria, sombra e tensão interior.",
    "neo-noir psychological cinematography, low-key chiaroscuro, restrained cool grading",
    "near-black, graphite, cold navy, steel blue, restrained amber",
    "hard chiaroscuro, narrow light sources, sculpted highlights, detailed shadows",
    "controlled framing, negative space, shallow depth of field, slow push-ins",
    "subtle film grain, tactile surface detail, deep tonal separation",
    "Express psychological tension, inner conflict, ambiguity, vulnerability and control through contrast, framing, gesture, distance and emotional subtext. The style does not prescribe character, prop, location or action.",
    "sensationalized menace, horror exaggeration, stereotyped characterization, manipulative visual tropes, unreadable shadows",
    "abstract",
    [
      "#10141d",
      "#a9b8d4",
      "#39475d"
    ]
  ],
  [
    "Épico Espiritual",
    "Despertar, propósito e escala monumental.",
    "epic cinematic visual language, monumental scale, atmospheric perspective",
    "sandstone, bronze, muted gold, umber, twilight violet",
    "warm volumetric illumination, atmospheric diffusion, high dynamic range",
    "monumental framing, deep perspective, slow crane movement, deliberate reveals",
    "fine particulate atmosphere, weathered surface treatment, cinematic depth",
    "Convey significance and emotional scale through composition, perspective, atmosphere and visual rhythm. Monumentality is a formal quality, not a prescribed subject or setting.",
    "unmotivated spectacle, game-like rendering, forced symbolism, empty grandeur, excessive lens effects",
    "abstract",
    [
      "#292238",
      "#e8c47a",
      "#826c55"
    ]
  ],
  [
    "Aura Neon",
    "Energia, chakras e experiências meditativas.",
    "bioluminescent visual language, controlled neon illumination, luminous gradients",
    "black, electric cyan, ultraviolet, indigo, balanced gold",
    "controlled glow, luminous edge lighting, high contrast, soft bloom",
    "symmetry, slow macro movement, fluid lateral and orbital camera motion",
    "luminous gradients, translucent layering, fine particulate detail",
    "Translate abstract or internal ideas into a controlled luminous visual language. Choose human, material, environmental or abstract depiction only when supported by the narration.",
    "diagrammatic explanations, pseudo-scientific presentation, uncontrolled neon, rainbow overload, visual clutter",
    "abstract",
    [
      "#10172a",
      "#55e7f2",
      "#6d43a0"
    ]
  ],
  [
    "Hermetismo Clássico",
    "Filosofia antiga, simbolismo e sabedoria.",
    "classical fine-art painting, baroque tonal hierarchy, aged pigment treatment",
    "burnt umber, deep brown, antique gold, olive black, parchment",
    "Rembrandt-style chiaroscuro, warm directional highlights, soft falloff",
    "deliberate painterly framing, balanced geometry, restrained push-ins",
    "aged pigment texture, visible brushwork, canvas grain, patinated surface",
    "Apply classical fine-art composition, tonal hierarchy, material richness and painterly restraint. Historical or symbolic specificity must come from the script, never from the style label alone.",
    "random ornament, anachronistic styling, excessive decoration, illegible detail, inconsistent painterly treatment",
    "abstract",
    [
      "#211a17",
      "#d5ad68",
      "#6d5140"
    ]
  ],
  [
    "Visual ASMR / Hipnótico",
    "Macro, fluidos e estímulo visual sensorial.",
    "hypnotic macro cinematography, fluid-motion language, precise specular rendering",
    "black, metallic gold, violet, cyan, selective pigments",
    "precise specular highlights, glossy reflections, controlled backlighting",
    "extreme macro framing, smooth tracking, slow motion, stable compositions",
    "fine surface detail, fluid gradients, pigment diffusion, controlled microtexture",
    "Prioritize precise material behavior, tactile detail, rhythm and controlled visual fascination. Macro abstraction is appropriate only when it communicates the scene's meaning.",
    "abstract filler without narrative purpose, implausible material behavior, repetitive motion, sensory overload, strobing",
    "abstract",
    [
      "#11151c",
      "#e4c46f",
      "#5945a1"
    ]
  ],
  [
    "Cinematográfico",
    "Fotografia de cinema realista e versátil.",
    "naturalistic cinematic photography, 35mm film language, motivated light",
    "natural restrained colors, balanced skin tones, warm-cool contrast",
    "motivated naturalistic lighting, soft directional key, preserved highlights",
    "24–50mm perspective, intentional framing, restrained dolly and handheld movement",
    "organic film grain, realistic material rendering, subtle atmospheric depth",
    "Apply believable live-action cinematography. The script determines subjects, actions, locations and emotional register; use lensing, motivated light and restrained movement to support it.",
    "plastic rendering, excessive color grading, artificial effects, stock-photo staging, visual inconsistency",
    "abstract",
    [
      "#182638",
      "#d59b58",
      "#526b78"
    ]
  ],
  [
    "Dark Cinematográfico",
    "Cinema dramático com sombras profundas.",
    "dark cinematic photography, low-key exposure, sculpted rim lighting",
    "charcoal, midnight blue, desaturated green, restrained amber and cold white",
    "low-key illumination, practical light sources, rim lighting, preserved shadow detail",
    "measured push-ins, selective framing, layered depth, controlled silhouettes",
    "subtle grain, detailed shadow texture, restrained atmospheric diffusion",
    "Use shadow, selective visibility, contrast and controlled atmosphere to establish a darker emotional register. Darkness is a treatment, not a mandate for a particular subject, time or setting.",
    "unreadable underexposure, horror exaggeration, gratuitous atmosphere, crushed shadows, arbitrary color accents",
    "abstract",
    [
      "#101522",
      "#8b76a8",
      "#30384f"
    ]
  ],
  [
    "Ilustração Editorial",
    "Metáforas visuais e arte conceitual sofisticada.",
    "premium editorial illustration, conceptual graphic language, refined shape design",
    "limited three-to-five color palette, deliberate accent color",
    "illustrative tonal modeling, clean separation, controlled contrast",
    "graphic composition, strong visual hierarchy, intentional negative space",
    "paper grain, screenprint texture, refined painterly digital finish",
    "Translate the scene's meaning into a concise high-concept editorial image with clear hierarchy and intentional shape language. Any metaphor must be specific to the narration.",
    "generic clip-art, explanatory infographic layouts, excessive detail, weak hierarchy, decorative metaphors without meaning",
    "abstract",
    [
      "#e4d6b9",
      "#d78b63",
      "#63818a"
    ]
  ],
  [
    "Filme Noir",
    "Mistério, contraste e linguagem noir clássica.",
    "classic black-and-white noir cinematography, silver-gelatin tonal range",
    "monochrome black, charcoal, silver, nuanced gray",
    "hard directional illumination, long tonal shadows, controlled practical highlights",
    "low-angle framing, reflective composition, deliberate close-up and wide-shot contrast",
    "silver-gelatin grain, rich monochrome texture, deep tonal separation",
    "Apply classic noir tonal grammar through contrast, framing, negative space and expressive shadow. The photographic language can serve any subject or genre.",
    "genre clichés without narrative reason, inconsistent monochrome treatment, muddy tonal range, unreadable darkness",
    "abstract",
    [
      "#101319",
      "#d6d1c5",
      "#454b56"
    ]
  ],
  [
    "Aquarela Artística",
    "Pintura delicada, orgânica e contemplativa.",
    "fine-art watercolor medium, translucent pigment behavior, organic paper texture",
    "soft natural pigments, muted earth tones, restrained chromatic accents",
    "diffused natural illumination, soft tonal transitions, translucent highlights",
    "airy composition, layered washes, gentle camera movement",
    "watercolor blooms, paper fibers, pigment granulation, organic edge diffusion",
    "Preserve the scene's recognizable subject and action while translating surfaces, edges, light and color into a coherent watercolor medium. The medium remains consistent; content remains script-led.",
    "mixed incompatible media, muddy pigment, excessive decorative texture, loss of subject readability",
    "abstract",
    [
      "#c4d9d2",
      "#edc58e",
      "#8aaeb1"
    ]
  ],
  [
    "Fantasia Cinematográfica",
    "Fantasia imersiva com escala e encantamento.",
    "cinematic fantasy visual language, atmospheric world-building, tactile material rendering",
    "deep jewel tones, muted gold, atmospheric complementary colors",
    "volumetric light, motivated luminous accents, atmospheric perspective",
    "immersive wide framing, layered depth, deliberate tracking and reveals",
    "tactile surface rendering, atmospheric particles, coherent material detail",
    "Use coherent cinematic fantasy treatment only when supported by the narrative. Establish believable visual rules, tactile rendering and purposeful extraordinary elements.",
    "unmotivated spectacle, incoherent world rules, generic game-art finish, excessive decorative effects",
    "abstract",
    [
      "#29264c",
      "#f0c16e",
      "#78689d"
    ]
  ],
  [
    "Graphic Novel",
    "Narrativa ilustrada, traço forte e impacto.",
    "graphic-novel illustration, expressive ink language, controlled halftone",
    "bold limited palette, intentional accent colors, high graphic contrast",
    "directional cel shading, controlled highlights, graphic shadow shapes",
    "dynamic but readable framing, clear staging, purposeful perspective",
    "expressive linework, ink texture, restrained halftone, consistent rendering",
    "Use unified graphic-novel linework, deliberate shadow shapes and readable staging. Maintain a single cinematic frame rather than changing the narrative into a page layout.",
    "comic-page layouts, lettering, inconsistent line language, cluttered composition, weak action readability",
    "abstract",
    [
      "#252b38",
      "#e5b44f",
      "#a94d50"
    ]
  ],
  [
    "Minimalista Clean",
    "Composição limpa, elegante e essencial.",
    "minimalist visual composition, restrained neutral palette, precise negative space",
    "neutral monochrome, subtle tonal variation, one restrained accent",
    "soft even illumination, subtle directional contrast, clean tonal separation",
    "precise framing, balanced spacing, low visual noise, restrained movement",
    "smooth surfaces, fine grain, minimal texture, clean edges",
    "Reduce visual noise and retain only elements essential to communicate the scene. Minimalism governs hierarchy and restraint, never the removal of necessary narrative context.",
    "empty minimalism, generic gradients, weak focal hierarchy, excessive decoration, loss of narrative context",
    "abstract",
    [
      "#dce5e8",
      "#f2c987",
      "#9bb1b8"
    ]
  ],
  [
    "Realismo Humano Emocional",
    "Pessoas reais, emoções e transformação cotidiana.",
    "cinematic human realism, natural skin texture, authentic performance",
    "natural skin tones, restrained saturation, balanced warm-cool contrast",
    "soft motivated lighting, realistic falloff, preserved skin detail",
    "observational framing, natural lens perspective, restrained handheld movement",
    "authentic skin and material texture, subtle grain, natural depth",
    "Prioritize credible human behavior, nuanced emotion, natural physical detail and authentic performance. Derive people and settings from the actual story.",
    "beauty retouching, exaggerated acting, stock-photo emotion, artificial skin, repetitive protagonist casting",
    "abstract",
    [
      "#302b2a",
      "#e6b18a",
      "#6f7779"
    ]
  ],
  [
    "Reconstituição Histórica",
    "Épocas, personagens e ambientes historicamente coerentes.",
    "historically grounded production design, period-consistent visual language",
    "period-appropriate muted palette, natural pigments, restrained contrast",
    "practical-source lighting, natural falloff, historically coherent exposure",
    "measured framing, period-appropriate perspective, restrained camera movement",
    "material authenticity, age-consistent surface treatment, subtle film grain",
    "Reconstruct a historical period only when supported by the script or verified context. Maintain consistency in materials, clothing, architecture and technology without invented specificity.",
    "anachronistic details, unsupported historical specificity, mixed-period design, fantasy embellishment",
    "abstract",
    [
      "#342a24",
      "#c8a36a",
      "#79624c"
    ]
  ],
  [
    "Natureza Contemplativa",
    "Natureza, serenidade e reflexão.",
    "contemplative nature cinematography, organic motion, natural atmospheric light",
    "restrained earth tones, organic greens, mineral neutrals, soft sky tones",
    "natural diffuse daylight, atmospheric backlight, realistic shadow softness",
    "patient wide and macro framing, slow tracking, observational camera movement",
    "organic surface detail, natural motion, atmospheric depth, restrained grain",
    "Use the natural world as subject, setting or metaphor only when it supports the narration. Emphasize observed movement, atmosphere and ecological plausibility.",
    "generic scenic filler, oversaturated grading, artificial natural effects, repetitive compositions, lack of narrative connection",
    "abstract",
    [
      "#193b35",
      "#e6c77b",
      "#668d62"
    ]
  ]
]

STYLE_PROFILES = {
    row[0]: {
        "short": row[1], "search_terms": row[2], "palette": row[3],
        "lighting": row[4], "camera": row[5], "texture": row[6],
        "direction": row[7], "avoid": row[8], "preview_scene": row[9], "ui": tuple(row[10]),
    }
    for row in _STYLE_ROWS
}
STYLE_OPTIONS = list(STYLE_PROFILES)
STYLE_SEARCH_TERMS = {name: p["search_terms"] for name, p in STYLE_PROFILES.items()}
STYLE_META = {name: (*p["ui"], p["short"]) for name, p in STYLE_PROFILES.items()}
STYLE_PREVIEW_SCENES = {name: p["preview_scene"] for name, p in STYLE_PROFILES.items()}

# Hidden compatibility profiles keep older saved storyboards and regression
# fixtures readable. They are deliberately excluded from STYLE_OPTIONS and UI.
LEGACY_STYLE_PROFILES = {
    "Cinematográfico realista": {
        **STYLE_PROFILES["Cinematográfico"],
        "search_terms": "cinematic realistic natural light, 35mm film language, restrained color grading",
        "direction": "Apply believable live-action cinematography with natural performance, motivated lighting and authentic material detail. Subjects, actions and locations must come from the script, not from a fixed stock-scene formula.",
    },
    "Anime 2D": {
        "short": "Compatibilidade com projetos antigos em animação 2D.",
        "search_terms": "2D anime style, hand-drawn animation language, expressive linework, coherent cel shading",
        "palette": "intentional anime color design, controlled saturation, coherent shadow colors",
        "lighting": "illustrative directional lighting, readable cel-shaded forms, consistent light source",
        "camera": "expressive animation framing, dynamic perspective only when motivated by the scene",
        "texture": "clean hand-drawn linework, coherent cel shading, restrained painted backgrounds",
        "direction": "Use a consistent 2D anime visual medium with coherent character design, linework, color and shading. The script determines all subjects, actions and settings; the medium must not force genre tropes or recurring character archetypes.",
        "avoid": "inconsistent character design, mixed 2D/3D rendering, generic anime clichés, visual clutter, weak action readability",
        "preview_scene": "abstract",
        "ui": ("#26344c", "#e5a66e", "#526c85"),
    },
}
LEGACY_STYLE_SEARCH_TERMS = {
    name: profile["search_terms"] for name, profile in LEGACY_STYLE_PROFILES.items()
}
STYLE_SEARCH_TERMS.update(LEGACY_STYLE_SEARCH_TERMS)


def build_visual_style_directive(style):
    """Build the private, detailed art-direction brief injected into Gemini prompts."""
    profile = STYLE_PROFILES.get(style) or LEGACY_STYLE_PROFILES.get(style)
    if not profile:
        raise ValueError(f"Estilo visual não cadastrado: {style}")
    return (
        f"ESTILO VISUAL BLOQUEADO: {style}\n"
        f"IDENTIDADE E INTENÇÃO: {profile['direction']}\n"
        f"PALETA: {profile['palette']}\n"
        f"ILUMINAÇÃO: {profile['lighting']}\n"
        f"FOTOGRAFIA E COMPOSIÇÃO: {profile['camera']}\n"
        f"TEXTURAS E ATMOSFERA: {profile['texture']}\n"
        f"TERMOS PARA BUSCA: {profile['search_terms']}\n"
        f"EVITAR: {profile['avoid']}\n"
        "CONTINUIDADE: mantenha a identidade artística em todas as cenas, variando "
        "pessoas, ambientes, planos, ações e enquadramentos. O estilo nunca substitui "
        "a correspondência semântica com a narração. Não inserir texto, legendas, "
        "logotipos ou tipografia nas imagens. Cada cena deve continuar específica "
        "ao trecho narrado.\n"
        "REGRA ANTI-TEMPLATE: estilo visual não é tema, personagem, objeto, cenário ou ação. "
        "Não escolha automaticamente sujeitos, lugares, símbolos ou adereços associados ao nome do estilo. "
        "Não transforme qualquer referência conceitual em cena obrigatória; referências são possibilidades, nunca receitas. "
        "Derive primeiro sujeito, ação, ambiente e metáfora do trecho específico do roteiro. "
        "Depois aplique a gramática visual do estilo. "
        "Varie soluções entre cenas do mesmo vídeo e evite repetir motivos centrais, mesmo quando o estilo permitir. "
        "Se duas soluções forem igualmente coerentes, prefira a que amplia a variedade visual sem perder a identidade artística."
    )
