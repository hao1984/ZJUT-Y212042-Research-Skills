#!/usr/bin/env python3
"""Build a runnable static frontend demo from a paper-grounded VIS run.

The builder consumes the deterministic Stage 0-3 artifacts created by
prepare_vis_design_run.py and writes a self-contained app under run_dir/app.
It does not invent random data. The rendered payload is derived from the input
paper/dataset profile, extracted keywords, retrieved paper references, and the
visual system specification.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact(text: str, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def safe_id(value: str, prefix: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "")).strip("-").lower()
    return value or prefix


def count_keyword_hits(text: str, keywords: list[dict[str, Any]]) -> int:
    blob = str(text or "").lower()
    hits = 0
    for item in keywords:
        keyword = str(item.get("keyword") or item.get("term") or "").lower()
        if keyword and keyword in blob:
            hits += 1
    return hits


def keyword_group(keyword: str, domain_id: str) -> str:
    k = keyword.lower()
    if any(term in k for term in ["language", "intent", "agent", "semantic", "command", "llm"]):
        return "intent"
    if any(term in k for term in ["volume", "3d", "gaussian", "spatial", "scene", "segmentation"]):
        return "structure"
    if any(term in k for term in ["time", "dynamic", "tracking", "simulation", "scale", "temporal", "cosmo"]):
        return "time_scale"
    if any(term in k for term in ["uncertainty", "bayesian", "prediction", "neural", "classification", "matrix"]):
        return "uncertainty"
    if any(term in k for term in ["evidence", "provenance", "reference", "explain"]):
        return "evidence"
    if domain_id == "model_uncertainty_diagnosis":
        return "model"
    if domain_id == "multiscale_simulation_exploration":
        return "simulation"
    return "concept"


def normalize_keywords(keyword_profile: dict[str, Any], input_profile: dict[str, Any], domain_id: str) -> list[dict[str, Any]]:
    raw_keywords = keyword_profile.get("keywords") or []
    title_blob = " ".join([input_profile.get("title") or "", input_profile.get("abstract") or "", input_profile.get("description") or ""])
    normalized = []
    for index, keyword in enumerate(raw_keywords[:24]):
        weight = max(1, title_blob.lower().count(str(keyword).lower()) + len(raw_keywords) - index)
        normalized.append(
            {
                "id": f"kw-{index + 1}",
                "keyword": str(keyword),
                "rank": index + 1,
                "weight": weight,
                "group": keyword_group(str(keyword), domain_id),
            }
        )
    return normalized


def normalize_references(digest: dict[str, Any], keywords: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs = []
    for index, ref in enumerate(digest.get("selected_references") or []):
        borrowed = ref.get("borrowed_elements") or []
        title = str(ref.get("title") or f"Reference {index + 1}")
        text_blob = " ".join([title, str(ref.get("abstract_snippet") or ""), str(ref.get("l3_snippet") or "")])
        score = float(ref.get("score") or 0.0)
        refs.append(
            {
                "id": ref.get("paper_id") or f"ref-{index + 1}",
                "rank": int(ref.get("rank") or index + 1),
                "title": title,
                "short_title": compact(re.sub(r"<[^>]+>", "", title), 58),
                "year": ref.get("year"),
                "journal": ref.get("journal"),
                "score": round(score, 6),
                "keyword_hits": count_keyword_hits(text_blob, keywords),
                "abstract_snippet": compact(ref.get("abstract_snippet") or "", 360),
                "l3_snippet": compact(ref.get("l3_snippet") or "", 420),
                "meta_path": ref.get("meta_path"),
                "paper_md_path": ref.get("paper_md_path"),
                "borrowed_elements": [
                    {
                        "borrowed_element": compact(elem.get("borrowed_element") or "", 180),
                        "mapped_to_view_ids": elem.get("mapped_to_view_ids") or [],
                        "mapped_to_interaction_ids": elem.get("mapped_to_interaction_ids") or [],
                        "confidence": elem.get("confidence") or "unknown",
                    }
                    for elem in borrowed
                ],
            }
        )
    return refs


def build_payload(run_dir: Path) -> dict[str, Any]:
    input_profile = read_json(run_dir / "stage0_input" / "input_profile.json")
    keyword_profile = read_json(run_dir / "stage0_input" / "keyword_profile.json")
    visual_spec = read_json(run_dir / "stage3_visual_spec" / "visual_system_spec.json")
    contract_path = run_dir / "stage2_idea" / "e_idea_contract.json"
    contract = read_json(contract_path) if contract_path.exists() else {}
    digest_path = run_dir / "stage2_idea" / "vis_reference_digest.json"
    if not digest_path.exists():
        raise FileNotFoundError(f"Missing {digest_path}. Re-run prepare_vis_design_run.py after the JSON output update.")
    digest = read_json(digest_path)

    domain_id = visual_spec.get("domain_id") or "paper_grounded_design"
    keywords = normalize_keywords(keyword_profile, input_profile, domain_id)
    refs = normalize_references(digest, keywords)
    schema_columns = input_profile.get("data_schema", {}).get("columns") or []
    primary_ref = refs[0] if refs else {}
    payload = {
        "schema_version": "paper_grounded_frontend_payload_v0.1",
        "created_at": now_iso(),
        "run_dir": str(run_dir),
        "input": {
            "title": input_profile.get("title") or "Untitled input",
            "type": input_profile.get("input_type") or "unknown",
            "path": input_profile.get("input_path"),
            "description": compact(input_profile.get("description") or "", 240),
            "abstract": compact(input_profile.get("abstract") or "", 480),
            "data_schema_columns": schema_columns[:36],
        },
        "domain_id": domain_id,
        "analysis_target": visual_spec.get("analysis_target") or {},
        "primary_question": visual_spec.get("primary_question") or "",
        "primary_visual_object": visual_spec.get("primary_visual_object") or "",
        "view_graph": visual_spec.get("view_graph") or [],
        "shared_state": visual_spec.get("shared_state") or [],
        "linked_interactions": visual_spec.get("linked_interactions") or [],
        "guided_open_exploration": visual_spec.get("guided_open_exploration") or {},
        "viewport_contract": visual_spec.get("viewport_contract") or {},
        "visual_style_system": visual_spec.get("visual_style_system") or {},
        "keywords": keywords,
        "references": refs,
        "retrieval": {
            "status": digest.get("retrieval_status"),
            "mode": digest.get("retrieval_mode"),
            "query": digest.get("query"),
            "coverage_summary": digest.get("coverage_summary"),
        },
        "contract_snapshot": {
            "why_not_dashboard": (
                contract.get("mechanism_context", {})
                .get("data_driven", {})
                .get("why_not_dashboard", "")
            ),
            "data_task_encoding_mapping": (
                contract.get("mechanism_context", {})
                .get("data_driven", {})
                .get("data_task_encoding_mapping", [])
            ),
        },
        "default_selection": {
            "reference_id": primary_ref.get("id"),
            "keyword_id": keywords[0]["id"] if keywords else None,
            "route": "structure",
        },
    }
    return payload


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Paper-Grounded VIS Demo</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="app">
    <header class="topbar">
      <div class="titleBlock">
        <div class="kicker" id="domainLabel">Paper-grounded VIS</div>
        <h1 id="appTitle">Loading...</h1>
      </div>
      <div class="question" id="primaryQuestion"></div>
      <div class="controls" id="routeControls" aria-label="Analysis routes"></div>
    </header>

    <main class="workspace">
      <section class="panel primaryPanel" data-view-slot="primary">
        <div class="panelHead">
          <div>
            <span class="eyebrow" id="primaryEyebrow">Primary object</span>
            <h2 id="primaryTitle">Primary View</h2>
          </div>
          <button id="clearBtn" class="iconTextButton" type="button">Clear</button>
        </div>
        <div class="primaryObject" id="primaryObject"></div>
      </section>

      <section class="panel companionTop" data-view-slot="reference">
        <div class="panelHead compactHead">
          <div>
            <span class="eyebrow">Reference patterns</span>
            <h2 id="referenceTitle">Paper Grounding</h2>
          </div>
        </div>
        <div class="referenceList" id="referenceList"></div>
      </section>

      <section class="panel companionBottom" data-view-slot="route">
        <div class="panelHead compactHead">
          <div>
            <span class="eyebrow" id="stripEyebrow">Companion view</span>
            <h2 id="stripTitle">Keyword and State Rail</h2>
          </div>
        </div>
        <div class="stripView" id="stripView"></div>
      </section>

      <section class="panel evidencePanel" data-view-slot="evidence">
        <div class="panelHead compactHead">
          <div>
            <span class="eyebrow">Evidence detail</span>
            <h2>Selection Evidence</h2>
          </div>
        </div>
        <div class="evidenceBody" id="evidenceBody"></div>
      </section>
    </main>

    <footer class="provenance" id="provenanceBar"></footer>
  </div>
  <script src="data/payload.js"></script>
  <script src="main.js"></script>
</body>
</html>
"""


CSS = """
:root {
  --bg: #eef3f5;
  --panel: #ffffff;
  --ink: #17212b;
  --muted: #5f6d78;
  --line: #c9d6dc;
  --teal: #087f8c;
  --blue: #2367a8;
  --green: #4f8f42;
  --amber: #b77413;
  --red: #b84a43;
  --soft: #e7f0f2;
  --shadow: 0 8px 20px rgba(35, 54, 66, 0.08);
}

* {
  box-sizing: border-box;
}

html,
body {
  width: 100%;
  height: 100%;
  margin: 0;
  overflow: hidden;
  color: var(--ink);
  background: var(--bg);
  font: 13px/1.35 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: 0;
}

button {
  font: inherit;
}

#app {
  height: 100vh;
  min-height: 0;
  display: grid;
  grid-template-rows: 66px minmax(0, 1fr) 24px;
}

.topbar {
  min-height: 0;
  padding: 9px 14px 8px;
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(320px, 1.25fr) auto;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid var(--line);
  background: #f8fbfc;
}

.titleBlock {
  min-width: 0;
}

.kicker,
.eyebrow {
  color: var(--teal);
  font-size: 10px;
  font-weight: 760;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  overflow: hidden;
  color: var(--ink);
  font-size: 17px;
  font-weight: 760;
  line-height: 1.18;
  text-overflow: ellipsis;
  white-space: nowrap;
}

h2 {
  font-size: 13px;
  font-weight: 760;
  line-height: 1.15;
}

.question {
  min-width: 0;
  color: #33444f;
  font-size: 12px;
  line-height: 1.25;
}

.controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 7px;
}

.routeButton,
.iconTextButton {
  height: 30px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #ffffff;
  color: #273640;
  cursor: pointer;
}

.routeButton {
  min-width: 86px;
  padding: 0 11px;
}

.iconTextButton {
  padding: 0 10px;
}

.routeButton.active {
  border-color: var(--teal);
  background: #dff1f2;
  color: #084f59;
  font-weight: 760;
}

.workspace {
  min-height: 0;
  padding: 10px;
  display: grid;
  grid-template-columns: minmax(520px, 1.42fr) minmax(330px, 0.85fr) minmax(340px, 0.9fr);
  grid-template-rows: minmax(0, 1fr) minmax(182px, 0.45fr);
  gap: 10px;
  overflow: hidden;
}

.panel {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  box-shadow: var(--shadow);
}

.primaryPanel {
  grid-row: 1 / 3;
}

.evidencePanel {
  grid-column: 3;
  grid-row: 1 / 3;
}

.panelHead {
  min-height: 48px;
  padding: 10px 11px 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid #dde7eb;
}

.compactHead {
  min-height: 44px;
}

.primaryObject,
.referenceList,
.stripView,
.evidenceBody {
  min-height: 0;
  overflow: hidden;
}

.primaryObject {
  position: relative;
  padding: 8px;
}

.primaryObject svg {
  width: 100%;
  height: 100%;
  display: block;
}

.referenceList,
.evidenceBody {
  overflow-y: auto;
  padding: 8px;
}

.refRow {
  width: 100%;
  margin: 0 0 7px;
  padding: 8px;
  border: 1px solid #d7e1e6;
  border-left: 4px solid #a7b8bf;
  border-radius: 6px;
  background: #fbfdfe;
  text-align: left;
  cursor: pointer;
}

.refRow.active {
  border-left-color: var(--teal);
  background: #e9f5f5;
}

.refTitle {
  color: var(--ink);
  font-size: 12px;
  font-weight: 760;
  line-height: 1.2;
}

.refMeta,
.smallText {
  margin-top: 4px;
  color: var(--muted);
  font-size: 11px;
}

.borrowed {
  margin-top: 5px;
  color: #263a44;
  font-size: 11px;
}

.stripView {
  padding: 8px;
}

.rail {
  height: 100%;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 8px;
}

.keywordCloud {
  min-height: 0;
  overflow: auto;
  display: flex;
  align-content: flex-start;
  flex-wrap: wrap;
  gap: 6px;
}

.kwPill {
  max-width: 100%;
  border: 1px solid #c7d7dd;
  border-radius: 6px;
  padding: 4px 7px;
  background: #f7fbfc;
  color: #2b3b45;
  cursor: pointer;
}

.kwPill.active {
  border-color: var(--blue);
  background: #e0edf8;
  color: #173f67;
  font-weight: 760;
}

.checkpoint {
  min-height: 42px;
  padding: 7px;
  border: 1px solid #d8e3e7;
  border-radius: 6px;
  background: #f3f8f9;
  color: #243741;
}

.evidenceBlock {
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid #dce6ea;
}

.evidenceBlock:last-child {
  border-bottom: 0;
}

.evidenceTitle {
  margin-bottom: 5px;
  color: var(--ink);
  font-size: 13px;
  font-weight: 780;
}

.evidenceLine {
  margin-top: 5px;
  color: #33444f;
  font-size: 12px;
}

.tagLine {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 6px;
}

.tag {
  border: 1px solid #d3e0e5;
  border-radius: 5px;
  padding: 2px 5px;
  background: #f8fbfc;
  color: #36515f;
  font-size: 10px;
}

.provenance {
  min-width: 0;
  overflow: hidden;
  padding: 4px 12px;
  border-top: 1px solid var(--line);
  background: #f8fbfc;
  color: #60717c;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.markLabel {
  fill: #22333d;
  font-size: 11px;
  font-weight: 650;
  pointer-events: none;
}

.mutedLabel {
  fill: #62727c;
  font-size: 10px;
  pointer-events: none;
}

.nodeMark,
.linkMark,
.matrixCell,
.timeTick {
  cursor: pointer;
  transition: opacity 120ms ease, stroke-width 120ms ease;
}

.dimmed {
  opacity: 0.32;
}

.selectedStroke {
  stroke: #111f27;
  stroke-width: 3;
}

@media (max-width: 1500px) {
  #app {
    grid-template-rows: 62px minmax(0, 1fr) 22px;
  }

  .topbar {
    grid-template-columns: minmax(260px, 0.9fr) minmax(300px, 1fr) auto;
    gap: 9px;
    padding: 7px 10px;
  }

  h1 {
    font-size: 15px;
  }

  .question {
    font-size: 11px;
  }

  .workspace {
    padding: 8px;
    gap: 8px;
    grid-template-columns: minmax(470px, 1.34fr) minmax(285px, 0.82fr) minmax(300px, 0.88fr);
    grid-template-rows: minmax(0, 1fr) minmax(160px, 0.42fr);
  }

  .panelHead {
    min-height: 40px;
    padding: 7px 8px 6px;
  }

  .routeButton {
    min-width: 74px;
    padding: 0 8px;
  }
}
"""


JS = r"""
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
"""


def write_demo_files(run_dir: Path, payload: dict[str, Any]) -> None:
    app_dir = run_dir / "app"
    write_text(app_dir / "index.html", HTML)
    write_text(app_dir / "style.css", CSS.lstrip())
    write_text(app_dir / "main.js", JS.lstrip())
    write_json(app_dir / "data" / "payload.json", payload)
    payload_js = "window.__VIS_PAYLOAD__ = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    write_text(app_dir / "data" / "payload.js", payload_js)


def write_build_report(run_dir: Path, payload: dict[str, Any]) -> None:
    files = [
        "app/index.html",
        "app/style.css",
        "app/main.js",
        "app/data/payload.json",
        "app/data/payload.js",
    ]
    report = [
        "# Frontend Demo Build Report",
        "",
        f"- Built at: {now_iso()}",
        f"- Domain: `{payload.get('domain_id')}`",
        f"- Input: {payload.get('input', {}).get('title')}",
        f"- References: {len(payload.get('references') or [])}",
        f"- Keywords: {len(payload.get('keywords') or [])}",
        f"- Retrieval mode: `{payload.get('retrieval', {}).get('mode')}`",
        "",
        "## Outputs",
        "",
    ]
    report.extend(f"- `{item}`" for item in files)
    report.extend(
        [
            "",
            "## Frontend Contract",
            "",
            "- Static, dependency-free single-page app.",
            "- Data payload is derived from local paper/index artifacts, not random data.",
            "- Initial screen includes a primary view, reference pattern view, companion state rail, evidence panel, route controls, and provenance.",
            "- `html, body` use fixed-height hidden overflow; long evidence uses bounded local scroll.",
        ]
    )
    write_text(run_dir / "artifacts" / "frontend_build_report.md", "\n".join(report).rstrip() + "\n")


def build_demo(run_dir: Path) -> dict[str, Any]:
    payload = build_payload(run_dir)
    write_demo_files(run_dir, payload)
    write_build_report(run_dir, payload)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Run directory containing Stage 0-3 artifacts.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    payload = build_demo(run_dir)
    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "app": str(run_dir / "app" / "index.html"),
                "domain_id": payload.get("domain_id"),
                "references": len(payload.get("references") or []),
                "keywords": len(payload.get("keywords") or []),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
