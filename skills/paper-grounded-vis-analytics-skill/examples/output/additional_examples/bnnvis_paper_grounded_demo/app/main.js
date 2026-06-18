const payload = window.__VIS_PAYLOAD__;

const domainLabels = {
  language_driven_volume_vis: "Language-driven volume VIS",
  multiscale_simulation_exploration: "Multiscale simulation VIS",
  model_uncertainty_diagnosis: "Model uncertainty diagnosis",
  paper_grounded_design: "Paper-grounded VIS design"
};

const routeLabels = {
  structure: "Structure",
  reference: "References",
  evidence: "Evidence"
};

const state = {
  selectedRefId: payload.default_selection.reference_id,
  selectedKeywordId: payload.default_selection.keyword_id,
  route: payload.default_selection.route || "structure"
};

function byId(id) {
  return document.getElementById(id);
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[ch]));
}

function selectedRef() {
  return payload.references.find((ref) => ref.id === state.selectedRefId) || payload.references[0] || null;
}

function selectedKeyword() {
  return payload.keywords.find((kw) => kw.id === state.selectedKeywordId) || payload.keywords[0] || null;
}

function colorFor(index, kind) {
  const domain = payload.domain_id;
  const palettes = {
    language_driven_volume_vis: ["#087f8c", "#2367a8", "#4f8f42", "#b77413", "#b84a43", "#5c7c8a"],
    multiscale_simulation_exploration: ["#2367a8", "#4f8f42", "#087f8c", "#b77413", "#7a6c36", "#496778"],
    model_uncertainty_diagnosis: ["#b84a43", "#2367a8", "#087f8c", "#4f8f42", "#b77413", "#5c7c8a"],
    paper_grounded_design: ["#087f8c", "#2367a8", "#4f8f42", "#b77413", "#5c7c8a", "#b84a43"]
  };
  const list = palettes[domain] || palettes.paper_grounded_design;
  return list[index % list.length];
}

function refMetric(ref, index) {
  const scorePart = Math.min(1, Math.max(0.12, Number(ref.score || 0) * 8));
  const hitPart = Math.min(1, (ref.keyword_hits || 0) / Math.max(1, payload.keywords.length));
  const borrowPart = Math.min(1, (ref.borrowed_elements || []).length / 3);
  return {
    x: scorePart,
    y: hitPart,
    z: borrowPart,
    index
  };
}

function renderHeader() {
  byId("domainLabel").textContent = domainLabels[payload.domain_id] || domainLabels.paper_grounded_design;
  byId("appTitle").textContent = payload.input.title;
  byId("primaryQuestion").textContent = payload.primary_question;
  const controls = byId("routeControls");
  controls.innerHTML = Object.keys(routeLabels).map((route) => `
    <button class="routeButton ${state.route === route ? "active" : ""}" type="button" data-route="${route}">
      ${routeLabels[route]}
    </button>
  `).join("");
  controls.querySelectorAll("[data-route]").forEach((button) => {
    button.addEventListener("click", () => {
      state.route = button.dataset.route;
      renderAll();
    });
  });
  byId("clearBtn").onclick = () => {
    state.selectedRefId = payload.default_selection.reference_id;
    state.selectedKeywordId = payload.default_selection.keyword_id;
    state.route = "structure";
    renderAll();
  };
  byId("provenanceBar").textContent = `Source: ${payload.input.path || "free text"} | Retrieval: ${payload.retrieval.mode || "unknown"} | References: ${payload.references.length} | Payload: paper-derived local artifacts`;
}

function svg(width, height, body) {
  return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="primary analytical visualization">${body}</svg>`;
}

function volumePrimary(refs) {
  const selected = selectedRef();
  const rings = [0, 1, 2].map((i) => {
    const rx = 250 - i * 42;
    const ry = 176 - i * 28;
    return `<ellipse data-mark="true" class="linkMark" cx="330" cy="238" rx="${rx}" ry="${ry}" fill="none" stroke="${colorFor(i, "ring")}" stroke-width="${2 + i}" opacity="${0.35 + i * 0.1}" />`;
  }).join("");
  const nodes = refs.map((ref, i) => {
    const m = refMetric(ref, i);
    const angle = -Math.PI / 2 + (i / Math.max(1, refs.length)) * Math.PI * 1.78;
    const radius = 120 + 62 * m.x;
    const x = 330 + Math.cos(angle) * radius;
    const y = 238 + Math.sin(angle) * radius * 0.72;
    const selectedClass = selected && selected.id === ref.id ? "selectedStroke" : "";
    return `
      <line data-mark="true" class="linkMark ${selected && selected.id !== ref.id ? "dimmed" : ""}" x1="330" y1="238" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="#b7cbd2" stroke-width="1.4" />
      <circle data-mark="true" class="nodeMark ${selectedClass}" data-ref-id="${esc(ref.id)}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(15 + 18 * m.z + 6 * m.x).toFixed(1)}" fill="${colorFor(i, "node")}" opacity="${selected && selected.id !== ref.id ? 0.46 : 0.92}" />
      <text class="markLabel" x="${(x + 18).toFixed(1)}" y="${(y + 3).toFixed(1)}">${esc(ref.rank)}</text>
    `;
  }).join("");
  const intents = payload.keywords.slice(0, 6).map((kw, i) => {
    const y = 55 + i * 25;
    const active = kw.id === state.selectedKeywordId;
    return `
      <rect data-mark="true" class="nodeMark ${active ? "selectedStroke" : ""}" data-kw-id="${esc(kw.id)}" x="28" y="${y}" width="${110 + Math.min(80, kw.weight * 3)}" height="17" rx="5" fill="${active ? "#dff1f2" : "#f4f8fa"}" stroke="${active ? "#087f8c" : "#c6d6dc"}" />
      <text class="mutedLabel" x="36" y="${y + 12}">${esc(kw.keyword)}</text>
    `;
  }).join("");
  return svg(720, 520, `
    <rect x="14" y="14" width="692" height="492" rx="8" fill="#f8fbfc" stroke="#d8e4e8" />
    <text class="markLabel" x="28" y="34">Intent rail</text>
    <text class="markLabel" x="256" y="34">Editable semantic volume object</text>
    ${intents}
    ${rings}
    <circle data-mark="true" cx="330" cy="238" r="42" fill="#e7f4f5" stroke="#087f8c" stroke-width="2" />
    <text class="markLabel" x="300" y="233">scene</text>
    <text class="mutedLabel" x="288" y="248">shared state</text>
    ${nodes}
    <text class="mutedLabel" x="470" y="480">node size = borrowed interaction evidence; links = command-to-scene trace</text>
  `);
}

function simulationPrimary(refs) {
  const selected = selectedRef();
  const bands = refs.map((ref, i) => {
    const m = refMetric(ref, i);
    const x = 90 + i * (520 / Math.max(1, refs.length));
    const y = 250 - (m.y * 120) + Math.sin(i) * 22;
    const r = 32 + m.x * 34;
    const selectedClass = selected && selected.id === ref.id ? "selectedStroke" : "";
    return `
      <circle data-mark="true" class="nodeMark ${selectedClass}" data-ref-id="${esc(ref.id)}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}" fill="${colorFor(i, "sim")}" opacity="${selected && selected.id !== ref.id ? 0.34 : 0.72}" />
      <circle data-mark="true" cx="${(x + r * 0.35).toFixed(1)}" cy="${(y - r * 0.25).toFixed(1)}" r="${(r * 0.46).toFixed(1)}" fill="none" stroke="#ffffff" stroke-width="1.4" opacity="0.7" />
      <text class="markLabel" x="${(x - 6).toFixed(1)}" y="${(y + 4).toFixed(1)}">${esc(ref.rank)}</text>
    `;
  }).join("");
  const ticks = refs.map((ref, i) => {
    const x = 74 + i * (560 / Math.max(1, refs.length - 1 || 1));
    const active = selected && selected.id === ref.id;
    return `
      <line data-mark="true" class="timeTick" data-ref-id="${esc(ref.id)}" x1="${x}" x2="${x}" y1="404" y2="${active ? 456 : 442}" stroke="${active ? "#087f8c" : "#8aa0aa"}" stroke-width="${active ? 4 : 2}" />
      <text class="mutedLabel" x="${x - 8}" y="472">R${esc(ref.rank)}</text>
    `;
  }).join("");
  return svg(720, 520, `
    <rect x="14" y="14" width="692" height="492" rx="8" fill="#f8fbfc" stroke="#d8e4e8" />
    <path data-mark="true" d="M54,305 C150,170 245,325 340,188 C445,44 520,236 664,120" fill="none" stroke="#b9ccd2" stroke-width="26" opacity="0.26" />
    <path data-mark="true" d="M50,326 C170,228 235,365 350,246 C458,138 544,314 670,218" fill="none" stroke="#bfd9cf" stroke-width="34" opacity="0.32" />
    ${bands}
    <line x1="55" x2="675" y1="404" y2="404" stroke="#c3d2d8" stroke-width="2" />
    ${ticks}
    <text class="markLabel" x="32" y="34">Spatial structure map</text>
    <text class="markLabel" x="32" y="392">time / scale evidence strip</text>
    <text class="mutedLabel" x="420" y="480">structure size = retrieval strength; height = keyword overlap</text>
  `);
}

function uncertaintyPrimary(refs) {
  const selected = selectedRef();
  const axes = `
    <line x1="72" y1="420" x2="656" y2="420" stroke="#9fb2ba" />
    <line x1="72" y1="70" x2="72" y2="420" stroke="#9fb2ba" />
    <text class="mutedLabel" x="510" y="446">retrieval confidence</text>
    <text class="mutedLabel" x="18" y="78">uncertainty evidence</text>
  `;
  const dots = refs.map((ref, i) => {
    const m = refMetric(ref, i);
    const uncertainty = Math.min(1, 0.25 + m.y * 0.65 + (ref.borrowed_elements || []).some((b) => /uncertainty/i.test(b.borrowed_element)) * 0.1);
    const x = 82 + m.x * 548;
    const y = 410 - uncertainty * 316;
    const r = 13 + m.z * 16;
    const selectedClass = selected && selected.id === ref.id ? "selectedStroke" : "";
    return `
      <circle data-mark="true" class="nodeMark ${selectedClass}" data-ref-id="${esc(ref.id)}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}" fill="${colorFor(i, "uq")}" opacity="${selected && selected.id !== ref.id ? 0.36 : 0.88}" />
      <line data-mark="true" class="linkMark" x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${y.toFixed(1)}" y2="420" stroke="${colorFor(i, "uq")}" opacity="0.35" />
      <text class="markLabel" x="${(x + 16).toFixed(1)}" y="${(y + 4).toFixed(1)}">R${esc(ref.rank)}</text>
    `;
  }).join("");
  const cells = refs.slice(0, 6).map((ref, i) => {
    const x = 420 + (i % 3) * 58;
    const y = 88 + Math.floor(i / 3) * 42;
    const active = selected && selected.id === ref.id;
    return `
      <rect data-mark="true" class="matrixCell ${active ? "selectedStroke" : ""}" data-ref-id="${esc(ref.id)}" x="${x}" y="${y}" width="44" height="28" rx="5" fill="${colorFor(i, "cell")}" opacity="${active ? 0.95 : 0.58}" />
      <text class="mutedLabel" x="${x + 11}" y="${y + 18}">R${esc(ref.rank)}</text>
    `;
  }).join("");
  return svg(720, 520, `
    <rect x="14" y="14" width="692" height="492" rx="8" fill="#f8fbfc" stroke="#d8e4e8" />
    ${axes}
    ${dots}
    <text class="markLabel" x="420" y="68">model / class relation cells</text>
    ${cells}
    <text class="mutedLabel" x="92" y="480">points = paper-derived diagnostic cases; vertical position = uncertainty/reference evidence density</text>
  `);
}

function genericPrimary(refs) {
  const selected = selectedRef();
  const centerX = 350;
  const centerY = 250;
  const refsSvg = refs.map((ref, i) => {
    const angle = (i / Math.max(1, refs.length)) * Math.PI * 2;
    const x = centerX + Math.cos(angle) * 190;
    const y = centerY + Math.sin(angle) * 145;
    const active = selected && selected.id === ref.id;
    return `
      <line data-mark="true" x1="${centerX}" y1="${centerY}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="#c1d1d7" />
      <circle data-mark="true" class="nodeMark ${active ? "selectedStroke" : ""}" data-ref-id="${esc(ref.id)}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${active ? 25 : 19}" fill="${colorFor(i, "g")}" opacity="${active ? 0.92 : 0.66}" />
      <text class="markLabel" x="${(x + 18).toFixed(1)}" y="${(y + 4).toFixed(1)}">R${esc(ref.rank)}</text>
    `;
  }).join("");
  return svg(720, 520, `
    <rect x="14" y="14" width="692" height="492" rx="8" fill="#f8fbfc" stroke="#d8e4e8" />
    <circle data-mark="true" cx="${centerX}" cy="${centerY}" r="54" fill="#e4f0f2" stroke="#087f8c" stroke-width="2" />
    <text class="markLabel" x="310" y="246">target</text>
    <text class="mutedLabel" x="292" y="262">shared evidence</text>
    ${refsSvg}
  `);
}

function renderPrimary() {
  const title = payload.view_graph[0]?.purpose || payload.primary_visual_object || "Primary analytical object";
  byId("primaryTitle").textContent = payload.view_graph[0]?.view_id || "Primary analytical view";
  byId("primaryEyebrow").textContent = title;
  const refs = payload.references;
  const domain = payload.domain_id;
  let markup = genericPrimary(refs);
  if (domain === "language_driven_volume_vis") markup = volumePrimary(refs);
  if (domain === "multiscale_simulation_exploration") markup = simulationPrimary(refs);
  if (domain === "model_uncertainty_diagnosis") markup = uncertaintyPrimary(refs);
  byId("primaryObject").innerHTML = markup;
  byId("primaryObject").querySelectorAll("[data-ref-id]").forEach((el) => {
    el.addEventListener("click", () => {
      state.selectedRefId = el.dataset.refId;
      state.route = "reference";
      renderAll();
    });
  });
  byId("primaryObject").querySelectorAll("[data-kw-id]").forEach((el) => {
    el.addEventListener("click", () => {
      state.selectedKeywordId = el.dataset.kwId;
      state.route = "structure";
      renderAll();
    });
  });
}

function renderReferences() {
  const selected = selectedRef();
  byId("referenceList").innerHTML = payload.references.map((ref) => {
    const firstBorrow = ref.borrowed_elements[0]?.borrowed_element || "reference evidence pending";
    return `
      <button class="refRow ${selected && selected.id === ref.id ? "active" : ""}" type="button" data-ref-id="${esc(ref.id)}">
        <div class="refTitle">${esc(ref.rank)}. ${esc(ref.short_title)}</div>
        <div class="refMeta">score ${esc(ref.score)} | hits ${esc(ref.keyword_hits)} | borrowed ${(ref.borrowed_elements || []).length}</div>
        <div class="borrowed">${esc(firstBorrow)}</div>
      </button>
    `;
  }).join("");
  byId("referenceList").querySelectorAll("[data-ref-id]").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedRefId = row.dataset.refId;
      state.route = "reference";
      renderAll();
    });
  });
}

function stripTitleForDomain() {
  if (payload.domain_id === "language_driven_volume_vis") return ["Intent and Region Rail", "Intent / region state"];
  if (payload.domain_id === "multiscale_simulation_exploration") return ["Time, Scale, Variable Rail", "Time / scale state"];
  if (payload.domain_id === "model_uncertainty_diagnosis") return ["Uncertainty and Class Rail", "Case / class state"];
  return ["Keyword and Evidence Rail", "Companion state"];
}

function renderStrip() {
  const selectedKw = selectedKeyword();
  const [title, eyebrow] = stripTitleForDomain();
  byId("stripTitle").textContent = title;
  byId("stripEyebrow").textContent = eyebrow;
  const kwMarkup = payload.keywords.map((kw) => `
    <button class="kwPill ${selectedKw && selectedKw.id === kw.id ? "active" : ""}" type="button" data-kw-id="${esc(kw.id)}">
      ${esc(kw.keyword)}
    </button>
  `).join("");
  const ref = selectedRef();
  const checkpoint = ref
    ? `Checkpoint: R${ref.rank} is linked to "${esc(selectedKw?.keyword || "selected focus")}" through ${(ref.borrowed_elements || []).length} borrowed design elements.`
    : "Checkpoint: select a reference or keyword to inspect linked evidence.";
  byId("stripView").innerHTML = `
    <div class="rail">
      <div class="keywordCloud">${kwMarkup}</div>
      <div class="checkpoint">${checkpoint}</div>
    </div>
  `;
  byId("stripView").querySelectorAll("[data-kw-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedKeywordId = button.dataset.kwId;
      state.route = "structure";
      renderAll();
    });
  });
}

function renderEvidence() {
  const ref = selectedRef();
  const kw = selectedKeyword();
  if (!ref) {
    byId("evidenceBody").innerHTML = `<div class="evidenceBlock"><div class="evidenceTitle">No retrieved reference</div><div class="evidenceLine">The frontend is waiting for retrieval output.</div></div>`;
    return;
  }
  const borrowed = (ref.borrowed_elements || []).map((elem) => `
    <div class="evidenceLine">- ${esc(elem.borrowed_element)}</div>
  `).join("");
  const mappings = (payload.contract_snapshot.data_task_encoding_mapping || []).slice(0, 4).map((item) => `
    <span class="tag">${esc(item.field_or_concept || "mapping")}</span>
  `).join("");
  const viewTags = (payload.view_graph || []).map((view) => `<span class="tag">${esc(view.view_id)}</span>`).join("");
  byId("evidenceBody").innerHTML = `
    <div class="evidenceBlock">
      <div class="evidenceTitle">${esc(ref.title)}</div>
      <div class="evidenceLine">Selected keyword: <strong>${esc(kw?.keyword || "none")}</strong></div>
      <div class="evidenceLine">Retrieval mode: ${esc(payload.retrieval.mode)} | Score: ${esc(ref.score)} | Keyword hits: ${esc(ref.keyword_hits)}</div>
      <div class="tagLine">${viewTags}</div>
    </div>
    <div class="evidenceBlock">
      <div class="evidenceTitle">Borrowed design evidence</div>
      ${borrowed || `<div class="evidenceLine">No explicit borrowed element; use fallback overview-detail evidence.</div>`}
    </div>
    <div class="evidenceBlock">
      <div class="evidenceTitle">Reference abstract evidence</div>
      <div class="evidenceLine">${esc(ref.abstract_snippet || "No abstract snippet available.")}</div>
    </div>
    <div class="evidenceBlock">
      <div class="evidenceTitle">L3 summary/evaluation evidence</div>
      <div class="evidenceLine">${esc(ref.l3_snippet || "No L3 snippet available.")}</div>
    </div>
    <div class="evidenceBlock">
      <div class="evidenceTitle">Design contract mapping</div>
      <div class="tagLine">${mappings}</div>
      <div class="evidenceLine">${esc(payload.contract_snapshot.why_not_dashboard || "No dashboard rejection statement available.")}</div>
    </div>
    <div class="evidenceBlock">
      <div class="evidenceTitle">File provenance</div>
      <div class="evidenceLine">${esc(ref.meta_path || "No meta path")}</div>
      <div class="evidenceLine">${esc(ref.paper_md_path || "No paper.md path")}</div>
    </div>
  `;
}

function renderAll() {
  renderHeader();
  renderPrimary();
  renderReferences();
  renderStrip();
  renderEvidence();
}

if (!payload) {
  document.body.innerHTML = "<p>Missing payload.</p>";
} else {
  renderAll();
  window.__VIS_DEMO_READY__ = true;
}
