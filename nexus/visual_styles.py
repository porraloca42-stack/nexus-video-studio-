"""Internal visual style library for NEXUS. Technical art direction is never exposed in the UI."""

_STYLE_ROWS = [
  [
    "Quântico & Cósmico",
    "Universo, manifestação e geometria luminosa.",
    "cinematic cosmic visual language, deep-space color grading, luminous volumetric atmosphere, refined science-fiction production design",
    "deep indigo, midnight blue, violet, restrained gold",
    "volumetric rays, luminous nebula backlight, controlled bloom, readable silhouettes",
    "monumental wides, human silhouettes, slow orbital moves, measured push-ins",
    "cosmic dust, layered nebula clouds, subtle sacred geometry",
    "Express scale, interconnection, uncertainty and wonder through a sophisticated cosmic visual language. Use celestial and geometric visual vocabulary only when it strengthens the scene's specific meaning. The style governs atmosphere and visual treatment, never the subject matter.",
    "horoscope graphics, random equations, busy HUD, rainbow galaxies, generic stars, alegações de prova científica",
    "spaceship",
    [
      "#11152f",
      "#d9b4ff",
      "#3b3975"
    ]
  ],
  [
    "Sonho Lúcido",
    "Surrealismo, subconsciente e realidades paralelas.",
    "surrealist dream logic, liminal spatial composition, ethereal visual transitions, soft atmospheric cinematography",
    "midnight blue, lavender, pearl, desaturated teal, amber",
    "soft sunlight through haze, dreamlike shafts, reflective highlights",
    "slow dolly through impossible spaces, deliberate reveals, uncanny symmetry",
    "thin mist, glass reflections, floating dust, cloud layers",
    "Use dream logic, spatial ambiguity, symbolic transformation and controlled impossibility to express the exact psychological or narrative state. Surreal elements must emerge from the scene's meaning; no fixed dream motifs or recurring prop formula.",
    "random collages, melting faces, childish fantasy, visual glitches, kaleidoscope excess",
    "surreal",
    [
      "#26213f",
      "#c4a7ff",
      "#756b9b"
    ]
  ],
  [
    "Dark Psychology",
    "Psicologia sombria, sombra e tensão interior.",
    "neo-noir psychological thriller visual language, low-key chiaroscuro, restrained cool grading, subtle film grain",
    "near-black, graphite, cold navy, steel blue, restrained amber",
    "hard chiaroscuro, narrow practical lights, rim lighting, detailed shadows",
    "controlled close-ups, over-shoulder, negative space, slow push-ins",
    "subtle grain, rain on glass, tactile concrete and dark wood",
    "Explore psychological tension, inner conflict, ambiguity, vulnerability, control and emotional subtext through composition, contrast, gesture, distance and environment. The style does not prescribe a character type, prop, location or action; derive those independently from the script.",
    "gore, demonic clichés, hooded hackers, red eyes, sensational manipulation, crushed blacks",
    "detective",
    [
      "#10141d",
      "#a9b8d4",
      "#39475d"
    ]
  ],
  [
    "Épico Espiritual",
    "Despertar, propósito e escala monumental.",
    "epic cinematic scale, monumental production design, atmospheric perspective, warm volumetric light",
    "sandstone, bronze, muted gold, umber, twilight violet",
    "golden-hour sun, volumetric beams, atmospheric haze",
    "extreme wide shots, slow crane/aerial reveals, tiny human figures",
    "windblown sand, weathered stone, drifting dust",
    "Convey significance and emotional scale through composition, perspective, production design, atmosphere and visual rhythm. Monumentality is an expressive tool, not a requirement to use temples, deserts, heroic figures or any recurring setting.",
    "imposed religious icons, game castles, random planets, lens flare excess, landscape filler",
    "castle",
    [
      "#292238",
      "#e8c47a",
      "#826c55"
    ]
  ],
  [
    "Aura Neon",
    "Energia, chakras e experiências meditativas.",
    "bioluminescent visual language, controlled neon illumination, luminous gradients, high-contrast dark-field cinematography",
    "black, electric cyan, ultraviolet, indigo, balanced gold",
    "self-illuminated forms, neon edge light, controlled glow",
    "slow macro pushes, symmetry, fluid lateral and orbital motion",
    "bioluminescent filaments, particles, translucent energy waves",
    "Translate internal or energetic ideas into a controlled luminous visual language. The form may be abstract, environmental, material or human depending on the narrative. Do not default to glowing bodies, chakra diagrams or a fixed color-coded figure.",
    "cheap chakra charts, rainbow gradients everywhere, nightclub, neon clutter, pseudo-science as fact",
    "neon_city",
    [
      "#10172a",
      "#55e7f2",
      "#6d43a0"
    ]
  ],
  [
    "Hermetismo Clássico",
    "Filosofia antiga, simbolismo e sabedoria.",
    "classical baroque fine-art painting, Rembrandt chiaroscuro, aged pigment palette, museum-grade painterly texture",
    "burnt umber, deep brown, antique gold, olive black, parchment",
    "candle/window source, Rembrandt chiaroscuro, warm highlights",
    "painterly frames, slow push-ins, still-life inserts, classical geometry",
    "oil brushwork, aged canvas, carved wood, parchment, patinated metal",
    "Use the visual sophistication of classical painting: deliberate composition, tonal hierarchy, material richness, symbolic restraint and painterly texture. Historical or esoteric references must be relevant to the script, not decorative defaults.",
    "random occult sigils, wizard props, modern objects, fake readable text, excessive gold, symbolism as scientific evidence",
    "watch",
    [
      "#211a17",
      "#d5ad68",
      "#6d5140"
    ]
  ],
  [
    "Visual ASMR / Hipnótico",
    "Macro, fluidos e estímulo visual sensorial.",
    "hypnotic macro cinematography, fluid-motion visual language, precise specular highlights, high-detail material rendering",
    "black, liquid gold, violet, cyan, selective pigments",
    "precise specular highlights, glossy reflections, backlit fluids",
    "extreme macro, smooth tracking, slow motion, stable compositions",
    "viscous liquid, metallic surfaces, pigment diffusion, bubbles, ripples",
    "Prioritize precise material behavior, tactile detail, rhythm and controlled visual fascination. Macro abstraction is appropriate only when it communicates the scene's idea; do not default to liquid metal, droplets or endlessly repeating fluid patterns.",
    "kaleidoscope loops, abstract filler, impossible physics, repeated gold liquid, flashing/strobing",
    "droplet",
    [
      "#11151c",
      "#e4c46f",
      "#5945a1"
    ]
  ],
  [
    "Cinematográfico",
    "Fotografia de cinema realista e versátil.",
    "naturalistic cinematic photography, 35mm film language, motivated light, restrained color grading",
    "natural restrained colors, balanced skin tones, warm-cool contrast",
    "motivated natural/practical light, soft directional key",
    "24–50mm perspective, intentional medium/wide shots, restrained dolly/handheld",
    "organic grain, realistic skin/materials, subtle atmospheric depth",
    "Apply believable live-action cinematography. Let the script determine subjects, actions, locations and emotional register; use lensing, motivated light, composition and restrained movement to make the scene feel photographed rather than templated.",
    "plastic CGI, excessive teal-orange, artificial flares, generic stock poses, fake text",
    "mountain",
    [
      "#182638",
      "#d59b58",
      "#526b78"
    ]
  ],
  [
    "Dark Cinematográfico",
    "Cinema dramático com sombras profundas.",
    "dark cinematic photography, low-key exposure, sculpted rim light, deep but detailed shadows",
    "charcoal, midnight blue, desaturated green, restrained amber/cold white",
    "low-key, practical sources, rim light, preserved shadow detail",
    "measured push-ins, silhouettes, selective close-ups, layered frames",
    "subtle grain, motivated haze/rain/smoke",
    "Use shadow, selective visibility, contrast and controlled atmosphere to establish a darker emotional register. Preserve clear visual storytelling. Darkness is a treatment, not a mandate for night scenes, anonymous figures or thriller props.",
    "underexposure, horror clichés, constant smoke, crushed blacks, arbitrary neon",
    "silhouette",
    [
      "#101522",
      "#8b76a8",
      "#30384f"
    ]
  ],
  [
    "Ilustração Editorial",
    "Metáforas visuais e arte conceitual sofisticada.",
    "premium editorial illustration, conceptual graphic language, refined shape design, limited color palette",
    "limited 3–5 color palette, deliberate accent",
    "illustrative tonal modeling, clean separation, negative space",
    "graphic composition, strong silhouette, clear hierarchy",
    "paper grain, screenprint or painterly digital texture",
    "Translate the scene's meaning into a concise, high-concept editorial image with clear hierarchy and intentional shape language. The metaphor must be specific to the narration, not a recurring icon or generic infographic.",
    "clip-art, generic icons, school infographic, text-heavy poster, inconsistent technique",
    "editorial",
    [
      "#e4d6b9",
      "#d78b63",
      "#63818a"
    ]
  ],
  [
    "Filme Noir",
    "Mistério, contraste e linguagem noir clássica.",
    "classic black-and-white noir cinematography, silver-gelatin tonal range, hard chiaroscuro, expressive shadow design",
    "monochrome black, charcoal, silver, nuanced gray",
    "hard directional light, long shadows, silhouettes, pools of practical light",
    "low angles, reflective surfaces, door frames, deliberate close-ups",
    "silver-gelatin grain, wet pavement, motivated smoke",
    "Apply classic noir visual grammar through tonal contrast, framing, negative space and expressive shadow. Use it as a photographic language across subjects and genres; do not force crime stories, detectives, period costumes or familiar noir props.",
    "color neon, cyberpunk, fedora clichés, unreadable darkness, random crime props",
    "detective",
    [
      "#101319",
      "#d6d1c5",
      "#454b56"
    ]
  ],
  [
    "Aquarela Artística",
    "Pintura delicada, orgânica e contemplativa.",
    "fine-art watercolor medium, translucent pigment behavior, organic paper texture, soft tonal transitions",
    "muted pigments, watercolor transparency, warm paper white",
    "soft diffuse light, luminous paper, gentle transitions",
    "illustrative framing, breathing room, clear focal point",
    "pigment blooms, granulation, paper fibers, wet-on-wet edges",
    "Preserve the scene's recognizable subject and action while translating surfaces, edges, light and color into a coherent watercolor medium. The medium is constant; subject matter remains entirely script-led.",
    "photorealistic inserts, muddy colors, splashes hiding subjects, childish clip-art",
    "vase",
    [
      "#c4d9d2",
      "#edc58e",
      "#8aaeb1"
    ]
  ],
  [
    "Fantasia Cinematográfica",
    "Fantasia imersiva com escala e encantamento.",
    "cinematic fantasy production design, atmospheric magical realism, coherent world-building, tactile materials",
    "earthy natural colors, deep teal, forest green, muted violet, gold",
    "motivated moonlight/firelight, magical practical glow, volumetric beams",
    "immersive wides, character-led tracking, revealing moves, depth",
    "weathered stone, organic landscapes, mist, embers, tactile costumes",
    "Create a coherent cinematic fantasy treatment only when the narrative supports it. Establish believable visual rules, tactile environments and purposeful extraordinary elements; never inject fantasy creatures, castles or magic simply because the style is selected.",
    "generic game art, random dragons/castles, particle excess, cartoon proportions",
    "castle",
    [
      "#29264c",
      "#f0c16e",
      "#78689d"
    ]
  ],
  [
    "Graphic Novel",
    "Narrativa ilustrada, traço forte e impacto.",
    "premium graphic-novel illustration, expressive ink language, controlled halftone, dramatic graphic contrast",
    "limited dramatic palette, ink black, warm paper, accent colors",
    "graphic chiaroscuro, hard-edged shadows, strong silhouettes",
    "dynamic perspective, expressive angles, single-frame storytelling",
    "ink hatching, brush strokes, restrained halftone, paper texture",
    "Use a unified graphic-novel drawing language, expressive line, deliberate shadow shapes and strong readable staging. Render a single cinematic scene, not a comic page; do not default to action poses, speech bubbles or superhero conventions.",
    "comic panels, speech bubbles, captions, lettering, sound effects, collage",
    "comic",
    [
      "#252b38",
      "#e5b44f",
      "#a94d50"
    ]
  ],
  [
    "Minimalista Clean",
    "Composição limpa, elegante e essencial.",
    "minimalist visual composition, restrained neutral palette, precise negative space, low visual noise",
    "soft neutrals, off-white, stone, muted gray, one accent",
    "soft diffused light, gentle shadows, clean separation",
    "restrained movement, negative space, precise subject placement",
    "matte surfaces, subtle natural materials, low visual noise",
    "Reduce visual noise and retain only the elements essential to communicate the scene. Minimalism governs hierarchy, spacing and restraint, not emptiness; preserve the concrete action and context required by the narration.",
    "empty decorative frames, generic gradients, excess props, tiny subjects, UI mockups, text overlays",
    "vase",
    [
      "#dce5e8",
      "#f2c987",
      "#9bb1b8"
    ]
  ],
  [
    "Realismo Humano Emocional",
    "Pessoas reais, emoções e transformação cotidiana.",
    "cinematic human realism, natural skin texture, authentic performance, observational photography",
    "natural skin tones, warm neutrals, earthy colors, gentle cool shadows",
    "window light, practical lamps, soft backlight, believable exposure",
    "intimate close-ups, observational medium shots, eye-level, subtle handheld",
    "real skin, natural imperfections, tactile clothing, lived-in spaces",
    "Prioritize credible human behavior, nuanced emotion, natural physical detail and lived-in environments. Derive people, gestures and settings from the actual story; avoid stock-photo expressions and repeated generic protagonists.",
    "plastic retouching, stock smiles, staged handshakes, melodrama, uncanny faces, anonymous same person",
    "silhouette",
    [
      "#302b2a",
      "#e6b18a",
      "#6f7779"
    ]
  ],
  [
    "Reconstituição Histórica",
    "Épocas, personagens e ambientes historicamente coerentes.",
    "historically grounded production design, period-accurate material culture, natural practical lighting",
    "period-appropriate muted pigments, natural dyes, aged wood, stone, bronze",
    "firelight, candlelight, window daylight, plausible practical sources",
    "observational wides, medium character scenes, tactile tool/manuscript inserts",
    "aged paper, worn stone, hand-forged metal, woven fabrics",
    "Reconstruct a historical period only when supported by the script or verified context. Maintain consistency in materials, clothing, architecture and technology; when details are uncertain, avoid invented specificity.",
    "anachronisms, fantasy armor, fake manuscript text, unsupported likenesses, mixing centuries",
    "watch",
    [
      "#342a24",
      "#c8a36a",
      "#79624c"
    ]
  ],
  [
    "Natureza Contemplativa",
    "Natureza, serenidade e reflexão.",
    "contemplative nature cinematography, natural atmospheric light, organic motion, restrained earth-tone grading",
    "moss green, muted teal, mist gray, sunrise gold, earth tones",
    "soft dawn/dusk, diffused sun, natural haze, gentle reflections",
    "slow stable tracking, landscape reveals, water-level details",
    "moving leaves, ripples, mist, wet stone, natural surface detail",
    "Use the natural world as subject, setting or metaphor only when it supports the narration. Emphasize observed movement, atmosphere and ecological plausibility; do not substitute generic landscapes for specific human or narrative actions.",
    "repeated generic sunsets, fantasy glowing forests, oversaturated greens, unrelated wallpaper landscapes",
    "waterfall",
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


def build_visual_style_directive(style):
    """Build the private, detailed art-direction brief injected into Gemini prompts."""
    profile = STYLE_PROFILES.get(style)
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
