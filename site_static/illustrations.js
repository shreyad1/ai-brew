// Explanatory drawings for Word of the Day, keyed by term (lowercase).
// Hand-made and reviewed like the definitions themselves. Colours come from CSS classes:
// .ink (lines/text), .glaze (cobalt), .latte (warm accent), .fill (card surface), .soft (faint).

const ARROW = (id, cls = "glaze") =>
  `<defs><marker id="${id}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="${cls}" d="M0 0 L10 5 L0 10 z"/></marker></defs>`;

window.ILLUSTRATIONS = {
  // A test suite run against two prompt versions.
  evals: `<svg viewBox="0 0 320 180" role="img" aria-label="Evals: a fixed set of test inputs, each graded pass or fail, gives each prompt version a score, so you can see if a change made things better or worse.">
    <text class="soft t10 mono" x="10" y="16">TEST CASE</text><text class="soft t10 mono" x="196" y="16">PROMPT v1</text><text class="soft t10 mono" x="262" y="16">PROMPT v2</text>
    <g class="t12">
      <rect class="fill stroke" x="8" y="24" width="304" height="26" rx="6"/><text class="ink" x="16" y="41">Refund question</text>
      <rect class="fill stroke" x="8" y="54" width="304" height="26" rx="6"/><text class="ink" x="16" y="71">Summarise a contract</text>
      <rect class="fill stroke" x="8" y="84" width="304" height="26" rx="6"/><text class="ink" x="16" y="101">Answer cites a source</text>
      <rect class="fill stroke" x="8" y="114" width="304" height="26" rx="6"/><text class="ink" x="16" y="131">Refuses unsafe request</text>
    </g>
    <g class="t14 b">
      <text class="glaze-text" x="214" y="42">✓</text><text class="glaze-text" x="280" y="42">✓</text>
      <text class="glaze-text" x="214" y="72">✓</text><text class="glaze-text" x="280" y="72">✓</text>
      <text class="latte-text" x="214" y="102">✗</text><text class="glaze-text" x="280" y="102">✓</text>
      <text class="glaze-text" x="214" y="132">✓</text><text class="latte-text" x="280" y="132">✗</text>
    </g>
    <text class="ink t12 b" x="16" y="166">Score</text>
    <text class="ink t13 b" x="206" y="166">3 / 4</text><text class="ink t13 b" x="272" y="166">3 / 4</text>
    <text class="soft t10" x="62" y="166">same score, different failures</text>
  </svg>`,

  // One model writes, a second model grades against a rubric.
  "llm-as-a-judge": `<svg viewBox="0 0 320 180" role="img" aria-label="LLM-as-a-judge: a writer model produces an answer, a judge model compares it to the source using a rubric and returns a verdict. The judge itself is checked against human labels.">
    <g class="t12">
      <rect class="glaze" x="8" y="20" width="84" height="40" rx="8"/><text class="on-glaze b" x="50" y="44" text-anchor="middle">Writer</text>
      <rect class="fill stroke" x="118" y="20" width="84" height="40" rx="8"/><text class="ink" x="160" y="38" text-anchor="middle">Answer</text><text class="soft t10" x="160" y="52" text-anchor="middle">+ its source</text>
      <rect class="fill stroke-glaze thick" x="228" y="20" width="84" height="40" rx="8"/><text class="glaze-text b" x="270" y="44" text-anchor="middle">Judge</text>
      <rect class="fill stroke" x="228" y="76" width="84" height="46" rx="6"/><text class="soft t10 mono" x="270" y="92" text-anchor="middle">RUBRIC</text>
      <text class="ink t10" x="270" y="106" text-anchor="middle">supported?</text><text class="ink t10" x="270" y="118" text-anchor="middle">invented facts?</text>
    </g>
    <g class="t11 mono">
      <rect class="glaze" x="10" y="138" width="88" height="22" rx="11"/><text class="on-glaze" x="54" y="153" text-anchor="middle">supported</text>
      <rect class="latte" x="104" y="138" width="70" height="22" rx="11" opacity="0.7"/><text class="on-glaze" x="139" y="153" text-anchor="middle">partial</text>
      <rect class="latte" x="180" y="138" width="98" height="22" rx="11"/><text class="on-glaze" x="229" y="153" text-anchor="middle">unsupported</text>
    </g>
    <text class="soft t10" x="10" y="176">Check the judge too: compare it with human labels first.</text>
    <g class="stroke-glaze" fill="none"><path d="M92 40 H114" marker-end="url(#a-judge)"/><path d="M202 40 H224" marker-end="url(#a-judge)"/><path d="M270 60 V72" marker-end="url(#a-judge)"/><path d="M250 122 C 240 132, 200 132, 190 136" marker-end="url(#a-judge)"/></g>
    ${ARROW("a-judge")}
  </svg>`,

  // Memory vs provided sources.
  grounding: `<svg viewBox="0 0 320 180" role="img" aria-label="Grounding: without it, the model answers from memory and may guess. With it, the model answers from the documents you provide and can cite them.">
    <text class="soft t10 mono" x="10" y="16">NOT GROUNDED</text>
    <g class="t12">
      <rect class="fill stroke" x="8" y="24" width="86" height="40" rx="8"/><text class="ink" x="51" y="48" text-anchor="middle">Question</text>
      <rect class="glaze" x="120" y="24" width="80" height="40" rx="8" opacity="0.55"/><text class="on-glaze" x="160" y="42" text-anchor="middle">Model</text><text class="on-glaze t10" x="160" y="56" text-anchor="middle">from memory</text>
      <rect class="fill stroke" x="226" y="24" width="86" height="40" rx="8"/><text class="latte-text t11" x="269" y="42" text-anchor="middle">"I think it's</text><text class="latte-text t11" x="269" y="56" text-anchor="middle">about 30 days"</text>
    </g>
    <text class="soft t10 mono" x="10" y="94">GROUNDED</text>
    <g class="t12">
      <rect class="fill stroke" x="8" y="102" width="86" height="40" rx="8"/><text class="ink" x="51" y="126" text-anchor="middle">Question</text>
      <rect class="fill stroke-glaze" x="14" y="150" width="76" height="24" rx="4"/><text class="glaze-text t10" x="52" y="166" text-anchor="middle">refund policy</text>
      <rect class="glaze" x="120" y="102" width="80" height="40" rx="8"/><text class="on-glaze b" x="160" y="120" text-anchor="middle">Model</text><text class="on-glaze t10" x="160" y="134" text-anchor="middle">reads the doc</text>
      <rect class="fill stroke-glaze thick" x="226" y="102" width="86" height="40" rx="8"/><text class="ink t11" x="269" y="120" text-anchor="middle">"14 days, per</text><text class="glaze-text t11" x="269" y="134" text-anchor="middle">refund policy"</text>
    </g>
    <g class="stroke-glaze" fill="none"><path d="M94 44 H116" marker-end="url(#a-gr)"/><path d="M200 44 H222" marker-end="url(#a-gr)"/><path d="M94 122 H116" marker-end="url(#a-gr)"/><path d="M90 160 C 106 160, 112 150, 120 142" marker-end="url(#a-gr)"/><path d="M200 122 H222" marker-end="url(#a-gr)"/></g>
    ${ARROW("a-gr")}
  </svg>`,

  // Checks before and after the model.
  guardrails: `<svg viewBox="0 0 320 170" role="img" aria-label="Guardrails: checks run before the model on the input and after the model on the output. Bad input or bad output is blocked or sent back to fix before it reaches the user.">
    <g class="t12">
      <rect class="fill stroke" x="4" y="50" width="58" height="40" rx="8"/><text class="ink" x="33" y="74" text-anchor="middle">Input</text>
      <rect class="fill stroke-glaze thick" x="80" y="44" width="62" height="52" rx="8"/><text class="glaze-text b t11" x="111" y="66" text-anchor="middle">input</text><text class="glaze-text b t11" x="111" y="80" text-anchor="middle">check</text>
      <rect class="glaze" x="160" y="50" width="56" height="40" rx="8"/><text class="on-glaze b" x="188" y="74" text-anchor="middle">Model</text>
      <rect class="fill stroke-glaze thick" x="234" y="44" width="62" height="52" rx="8"/><text class="glaze-text b t11" x="265" y="66" text-anchor="middle">output</text><text class="glaze-text b t11" x="265" y="80" text-anchor="middle">check</text>
    </g>
    <g class="stroke-glaze" fill="none"><path d="M62 70 H76" marker-end="url(#a-gd)"/><path d="M142 70 H156" marker-end="url(#a-gd)"/><path d="M216 70 H230" marker-end="url(#a-gd)"/><path d="M296 70 H312" marker-end="url(#a-gd)"/></g>
    <text class="ink t11" x="314" y="38" text-anchor="end">to user ✓</text>
    <g class="t10">
      <path class="stroke-latte dash" d="M111 96 V118" fill="none"/>
      <rect class="latte" x="58" y="120" width="106" height="20" rx="10"/><text class="on-glaze" x="111" y="134" text-anchor="middle">✗ off-topic / attack</text>
      <path class="stroke-latte dash" d="M265 96 V118" fill="none"/>
      <rect class="latte" x="208" y="120" width="110" height="20" rx="10"/><text class="on-glaze" x="263" y="134" text-anchor="middle">✗ link not in source</text>
    </g>
    <text class="soft t10" x="160" y="162" text-anchor="middle">blocked, or sent back to fix, before anyone sees it</text>
    ${ARROW("a-gd")}
  </svg>`,

  // Repeated prefix reused on the second call.
  "prompt caching": `<svg viewBox="0 0 320 170" role="img" aria-label="Prompt caching: two calls share the same long prefix, such as the system prompt and documents. On the second call the provider reuses the processed prefix, so only the new question is processed, which is faster and cheaper.">
    <text class="soft t10 mono" x="10" y="18">CALL 1</text>
    <rect class="glaze" x="10" y="26" width="210" height="28" rx="6"/><text class="on-glaze t11" x="115" y="44" text-anchor="middle">system prompt + 40 pages of docs</text>
    <rect class="latte" x="224" y="26" width="86" height="28" rx="6"/><text class="on-glaze t11" x="267" y="44" text-anchor="middle">question A</text>
    <text class="ink t10" x="10" y="70">all of it processed: slower, full price</text>
    <text class="soft t10 mono" x="10" y="100">CALL 2</text>
    <rect class="glaze-soft stroke-glaze dash" x="10" y="108" width="210" height="28" rx="6"/>
    <text class="glaze-text t11 b" x="115" y="126" text-anchor="middle">same prefix: reused from cache</text>
    <rect class="latte" x="224" y="108" width="86" height="28" rx="6"/><text class="on-glaze t11" x="267" y="126" text-anchor="middle">question B</text>
    <text class="ink t10" x="10" y="152">only the new part processed: faster, cheaper</text>
    <text class="soft t10" x="10" y="166">Tip: keep the unchanging part at the start of the prompt.</text>
  </svg>`,
};
