// Explanatory drawings for Word of the Day, keyed by term (lowercase).
// Hand-made and reviewed like the definitions themselves. Colours come from CSS classes:
// .ink (lines/text), .glaze (cobalt), .latte (warm accent), .fill (card surface), .soft (faint).

window.ILLUSTRATIONS = {
  // Next-word prediction: a sentence with a blank and the model's guesses as bars.
  llm: `<svg viewBox="0 0 320 170" role="img" aria-label="An LLM reads 'An oat milk' and predicts the next word: latte is most likely, then cappuccino, then chai.">
    <rect class="fill stroke" x="10" y="14" width="300" height="44" rx="10"/>
    <text class="ink t16" x="26" y="42">An oat milk</text>
    <rect class="glaze-soft" x="128" y="25" width="74" height="24" rx="6"/>
    <text class="glaze t16 b" x="142" y="42">___ ?</text>
    <text class="soft t11 mono" x="10" y="84">MOST LIKELY NEXT WORD</text>
    <text class="ink t13" x="10" y="108">latte</text>
    <rect class="glaze" x="104" y="96" width="190" height="14" rx="7"/>
    <text class="ink t13" x="10" y="132">cappuccino</text>
    <rect class="glaze" x="104" y="120" width="96" height="14" rx="7" opacity="0.65"/>
    <text class="ink t13" x="10" y="156">chai</text>
    <rect class="glaze" x="104" y="144" width="44" height="14" rx="7" opacity="0.4"/>
  </svg>`,

  // A sentence ground into token pieces.
  token: `<svg viewBox="0 0 320 170" role="img" aria-label="The sentence 'Brewing coffee is fun' split into five tokens: Brew, ing, coffee, is, fun.">
    <text class="ink t16" x="160" y="30" text-anchor="middle">Brewing coffee is fun</text>
    <path class="stroke-glaze" d="M160 42 V58" marker-end="url(#arrow-tok)"/>
    <rect class="fill stroke" x="118" y="62" width="84" height="26" rx="13"/>
    <text class="soft t11 mono" x="160" y="79" text-anchor="middle">GRINDER</text>
    <path class="stroke-glaze" d="M160 92 V108" marker-end="url(#arrow-tok)"/>
    <g class="t14 mono">
      <rect class="glaze" x="14" y="118" width="58" height="30" rx="8"/><text class="on-glaze" x="43" y="138" text-anchor="middle">Brew</text>
      <rect class="latte" x="76" y="118" width="44" height="30" rx="8"/><text class="on-glaze" x="98" y="138" text-anchor="middle">ing</text>
      <rect class="glaze" x="124" y="118" width="74" height="30" rx="8" opacity="0.8"/><text class="on-glaze" x="161" y="138" text-anchor="middle">coffee</text>
      <rect class="latte" x="202" y="118" width="40" height="30" rx="8" opacity="0.8"/><text class="on-glaze" x="222" y="138" text-anchor="middle">is</text>
      <rect class="glaze" x="246" y="118" width="60" height="30" rx="8" opacity="0.6"/><text class="on-glaze" x="276" y="138" text-anchor="middle">fun</text>
    </g>
    <text class="soft t11" x="160" y="164" text-anchor="middle">5 tokens: the AI reads these pieces, not whole words</text>
    <defs><marker id="arrow-tok" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="glaze" d="M0 0 L10 5 L0 10 z"/></marker></defs>
  </svg>`,

  // A cup with a fixed capacity: new text fills it, the oldest spills out.
  "context window": `<svg viewBox="0 0 320 170" role="img" aria-label="A cup holds a fixed amount of text. New messages pour in at the top; the oldest message spills over the rim and is forgotten.">
    <path class="fill stroke-glaze" d="M90 40 H230 L218 150 C 216 158, 210 162, 202 162 H118 C 110 162, 104 158, 102 150 Z"/>
    <line class="stroke-soft dash" x1="86" y1="40" x2="234" y2="40"/>
    <text class="soft t11 mono" x="238" y="44">FULL</text>
    <g class="t11 mono">
      <rect class="glaze" x="110" y="128" width="100" height="20" rx="5" opacity="0.45"/><text class="on-glaze" x="160" y="142" text-anchor="middle">your question</text>
      <rect class="glaze" x="108" y="104" width="104" height="20" rx="5" opacity="0.65"/><text class="on-glaze" x="160" y="118" text-anchor="middle">pasted notes</text>
      <rect class="glaze" x="104" y="80" width="112" height="20" rx="5" opacity="0.85"/><text class="on-glaze" x="160" y="94" text-anchor="middle">AI's answer</text>
      <rect class="glaze" x="100" y="56" width="120" height="20" rx="5"/><text class="on-glaze" x="160" y="70" text-anchor="middle">newest message</text>
    </g>
    <g transform="rotate(-14 50 92)"><rect class="latte" x="4" y="82" width="92" height="20" rx="5"/><text class="on-glaze t11 mono" x="50" y="96" text-anchor="middle">first message</text></g>
    <path class="stroke-latte dash" d="M98 44 C 86 52, 74 64, 64 78" fill="none"/>
    <text class="soft t11" x="10" y="128">spills out:</text>
    <text class="soft t11" x="10" y="142">forgotten</text>
    <path class="stroke-soft" d="M160 8 V30" marker-end="url(#arrow-cw)"/>
    <text class="soft t11" x="168" y="22">new text</text>
    <defs><marker id="arrow-cw" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="soft-fill" d="M0 0 L10 5 L0 10 z"/></marker></defs>
  </svg>`,

  // Confident and wrong: the speech bubble doesn't match the carton.
  hallucination: `<svg viewBox="0 0 320 170" role="img" aria-label="A barista confidently says 'Oat milk, as you asked!' but the carton they used says whole milk.">
    <rect class="fill stroke" x="12" y="18" width="178" height="58" rx="14"/>
    <path class="fill stroke" d="M58 74 L50 96 L80 76"/>
    <rect class="fill" x="52" y="70" width="34" height="8"/>
    <text class="ink t15" x="28" y="44">"Oat milk,</text>
    <text class="ink t15" x="28" y="64">as you asked!"</text>
    <circle class="glaze" cx="170" cy="30" r="11"/><path class="stroke-white" d="M164 30 L169 35 L177 25" fill="none"/>
    <text class="soft t11 mono" x="14" y="118">SOUNDS SURE</text>
    <path class="fill stroke" d="M232 40 H292 V150 H232 Z"/>
    <path class="fill stroke" d="M232 40 L246 20 H278 L292 40"/>
    <rect class="latte" x="240" y="78" width="44" height="40" rx="4"/>
    <text class="on-glaze t12 b" x="262" y="95" text-anchor="middle">WHOLE</text>
    <text class="on-glaze t12 b" x="262" y="110" text-anchor="middle">MILK</text>
    <text class="soft t11 mono" x="232" y="166">WHAT'S TRUE</text>
    <path class="stroke-latte dash" d="M196 48 C 210 52, 218 60, 228 70" fill="none"/>
    <text class="latte-text t12 b" x="160" y="146" text-anchor="middle">confident ≠ correct</text>
  </svg>`,

  // Retrieval-augmented generation as an architecture flow.
  rag: `<svg viewBox="0 0 320 190" role="img" aria-label="RAG: a question goes to a search over documents, the most relevant recipe card is retrieved, the model reads it, and the answer cites that card: a cortado is equal parts espresso and milk.">
    <g class="t12">
      <rect class="fill stroke" x="8" y="18" width="86" height="40" rx="8"/>
      <text class="ink" x="51" y="36" text-anchor="middle">Question</text>
      <text class="soft t10" x="51" y="50" text-anchor="middle">"How do I make</text>
      <rect class="fill stroke-glaze" x="118" y="18" width="86" height="40" rx="8"/>
      <text class="glaze-text b" x="161" y="36" text-anchor="middle">1. Search</text>
      <text class="soft t10" x="161" y="50" text-anchor="middle">the recipe box</text>
      <g transform="translate(222 8)">
        <rect class="fill stroke" x="10" y="0" width="78" height="46" rx="5"/>
        <rect class="fill stroke" x="5" y="6" width="78" height="46" rx="5"/>
        <rect class="fill stroke-glaze thick" x="0" y="12" width="78" height="46" rx="5"/>
        <text class="ink t10 b" x="39" y="28" text-anchor="middle">Cortado card</text>
        <text class="soft t10" x="39" y="41" text-anchor="middle">equal parts</text>
        <text class="soft t10" x="39" y="53" text-anchor="middle">espresso + milk</text>
      </g>
      <text class="glaze-text t11 b" x="282" y="84" text-anchor="middle">2. Retrieve</text>
      <rect class="glaze" x="118" y="104" width="86" height="40" rx="8"/>
      <text class="on-glaze b" x="161" y="122" text-anchor="middle">3. LLM</text>
      <text class="on-glaze t10" x="161" y="136" text-anchor="middle">reads the card</text>
      <rect class="fill stroke" x="8" y="100" width="86" height="66" rx="8"/>
      <text class="ink" x="51" y="117" text-anchor="middle">Answer</text>
      <text class="soft t10" x="51" y="131" text-anchor="middle">"Equal parts</text>
      <text class="soft t10" x="51" y="144" text-anchor="middle">espresso + milk"</text>
      <text class="glaze-text t10" x="51" y="158" text-anchor="middle">[Cortado card]</text>
      <text class="soft t10" x="51" y="64" text-anchor="middle">a cortado?"</text>
    </g>
    <g class="stroke-glaze" fill="none">
      <path d="M94 38 H114" marker-end="url(#arrow-rag)"/>
      <path d="M204 38 H218" marker-end="url(#arrow-rag)"/>
      <path d="M261 70 V124 H208" marker-end="url(#arrow-rag)"/>
      <path d="M118 124 H98" marker-end="url(#arrow-rag)"/>
    </g>
    <text class="soft t11" x="160" y="182" text-anchor="middle">looks it up first, then answers, and shows where from</text>
    <defs><marker id="arrow-rag" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="glaze" d="M0 0 L10 5 L0 10 z"/></marker></defs>
  </svg>`,
};
