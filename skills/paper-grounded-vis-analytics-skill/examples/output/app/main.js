const SVG_NS = "http://www.w3.org/2000/svg";

const colors = {
  Adelie: "#d8462f",
  Chinstrap: "#0a9b97",
  Gentoo: "#c99a1a",
  pooled: "#2e62d6",
  sex: "#734f96",
  ink: "#11100d",
  paper: "#fffaf0"
};

const state = {
  data: null,
  activeTrace: "pooled",
  selectedRow: null,
  lensPoint: null,
  layers: {
    lens: true,
    tethers: true,
    sex: true,
    island: true,
    year: true,
    singular: true
  }
};

const svg = document.getElementById("morphospace");
const inspector = {
  title: document.getElementById("selectedTitle"),
  meta: document.getElementById("selectedMeta"),
  measures: document.getElementById("measureGrid"),
  evidence: document.getElementById("activeEvidence"),
  legend: document.getElementById("legend")
};

function el(name, attrs = {}, parent = null) {
  const node = document.createElementNS(SVG_NS, name);
  Object.entries(attrs).forEach(([key, value]) => {
    if (value !== null && value !== undefined) node.setAttribute(key, value);
  });
  if (parent) parent.appendChild(node);
  return node;
}

function htmlEscape(value) {
  return String(value ?? "NA").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[c]));
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "NA";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(digits);
  return String(value);
}

function speciesLabel(sp) {
  return sp === "Adelie" ? "Adelie" : sp;
}

function extent(values) {
  return [Math.min(...values), Math.max(...values)];
}

function padExtent([min, max], pad = 0.12) {
  const span = max - min || 1;
  return [min - span * pad, max + span * pad];
}

function scaleLinear(domain, range) {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  return (value) => r0 + ((value - d0) / (d1 - d0)) * (r1 - r0);
}

function invertScale(domain, range) {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  return (value) => d0 + ((value - r0) / (r1 - r0)) * (d1 - d0);
}

function polygonPath(points, x, y) {
  if (!points || points.length === 0) return "";
  return points.map((p, i) => `${i ? "L" : "M"}${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join(" ") + " Z";
}

function arrowPath(anchor, delta, x, y, length = 1) {
  const norm = Math.hypot(delta.pc1, delta.pc2) || 1;
  const ux = delta.pc1 / norm;
  const uy = delta.pc2 / norm;
  const start = { pc1: anchor.pc1 - ux * length * 0.42, pc2: anchor.pc2 - uy * length * 0.42 };
  const end = { pc1: anchor.pc1 + ux * length * 0.72, pc2: anchor.pc2 + uy * length * 0.72 };
  return { start, end };
}

function lineIntersections(line, xDomain, yDomain) {
  const { a, b, c } = line;
  const pts = [];
  for (const x of xDomain) {
    if (Math.abs(b) > 1e-9) {
      const y = -(a * x + c) / b;
      if (y >= yDomain[0] && y <= yDomain[1]) pts.push({ pc1: x, pc2: y });
    }
  }
  for (const y of yDomain) {
    if (Math.abs(a) > 1e-9) {
      const x = -(b * y + c) / a;
      if (x >= xDomain[0] && x <= xDomain[1]) pts.push({ pc1: x, pc2: y });
    }
  }
  return pts.slice(0, 2);
}

function rowById(id) {
  return state.data.points.find((p) => p.source_row === id);
}

function draw() {
  const data = state.data;
  if (!data) return;

  const box = svg.getBoundingClientRect();
  const width = Math.max(900, box.width);
  const height = Math.max(620, box.height);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.replaceChildren();
  svg.onmousemove = null;

  const plot = {
    left: 78,
    right: width - 372,
    top: 88,
    bottom: height - 70
  };
  const xs = padExtent(extent(data.points.map((d) => d.pc1)), 0.16);
  const ys = padExtent(extent(data.points.map((d) => d.pc2)), 0.18);
  const x = scaleLinear(xs, [plot.left, plot.right]);
  const y = scaleLinear(ys, [plot.bottom, plot.top]);
  const invX = invertScale(xs, [plot.left, plot.right]);
  const invY = invertScale(ys, [plot.bottom, plot.top]);

  drawDefs();
  drawField(data, plot, x, y, xs, ys);
  drawHulls(data, x, y);
  drawBoundary(data, x, y, xs, ys);
  drawVectors(data, x, y);
  if (state.layers.tethers) drawTethers(data, x, y);
  drawPoints(data, x, y);
  if (state.layers.lens) drawLens(data, x, y, invX, invY);
  drawBiplotLegend(data, width, height);
  drawMissingAnnotation(data, width, height);
  updateInspector();
}

function drawDefs() {
  const defs = el("defs", {}, svg);
  const markerSpecs = [
    ["arrow-pool", colors.pooled],
    ["arrow-adelie", colors.Adelie],
    ["arrow-chinstrap", colors.Chinstrap],
    ["arrow-gentoo", colors.Gentoo],
    ["arrow-sex", colors.sex],
    ["arrow-ink", colors.ink]
  ];
  markerSpecs.forEach(([id, color]) => {
    const marker = el("marker", {
      id,
      viewBox: "0 0 10 10",
      refX: "8",
      refY: "5",
      markerWidth: "7",
      markerHeight: "7",
      orient: "auto-start-reverse"
    }, defs);
    el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: color }, marker);
  });

  const filter = el("filter", { id: "soft-shadow", x: "-20%", y: "-20%", width: "140%", height: "140%" }, defs);
  el("feDropShadow", { dx: "0", dy: "10", stdDeviation: "10", "flood-color": "#11100d", "flood-opacity": "0.16" }, filter);
}

function drawField(data, plot, x, y, xs, ys) {
  const g = el("g", { class: "field" }, svg);
  el("rect", {
    x: plot.left,
    y: plot.top,
    width: plot.right - plot.left,
    height: plot.bottom - plot.top,
    fill: "rgba(255,250,240,0.2)"
  }, g);

  for (let i = Math.ceil(xs[0]); i <= Math.floor(xs[1]); i += 1) {
    el("line", {
      x1: x(i), x2: x(i), y1: plot.top, y2: plot.bottom,
      stroke: "rgba(17,16,13,0.08)", "stroke-width": 1
    }, g);
  }
  for (let i = Math.ceil(ys[0]); i <= Math.floor(ys[1]); i += 1) {
    el("line", {
      x1: plot.left, x2: plot.right, y1: y(i), y2: y(i),
      stroke: "rgba(17,16,13,0.08)", "stroke-width": 1
    }, g);
  }

  el("line", { x1: x(0), x2: x(0), y1: plot.top, y2: plot.bottom, stroke: "rgba(17,16,13,0.28)", "stroke-width": 1.2 }, g);
  el("line", { x1: plot.left, x2: plot.right, y1: y(0), y2: y(0), stroke: "rgba(17,16,13,0.28)", "stroke-width": 1.2 }, g);
  el("text", { x: plot.right - 154, y: plot.bottom + 34, class: "axis-label" }, g).textContent = `PC1 morphology scale (${Math.round(data.pca.explained_variance_ratio[0] * 100)}%)`;
  el("text", { x: plot.left - 46, y: plot.top + 226, class: "axis-label", transform: `rotate(-90 ${plot.left - 46} ${plot.top + 226})` }, g).textContent = `PC2 bill-shape axis (${Math.round(data.pca.explained_variance_ratio[1] * 100)}%)`;
}

function drawHulls(data, x, y) {
  const g = el("g", { class: "hulls" }, svg);
  data.geometry.species_order.forEach((sp) => {
    const path = polygonPath(data.geometry.hulls[sp], x, y);
    const inner = polygonPath(data.geometry.inner_hulls[sp], x, y);
    el("path", {
      d: path,
      fill: colors[sp],
      "fill-opacity": 0.075,
      stroke: colors[sp],
      "stroke-opacity": 0.35,
      "stroke-width": 2.2,
      "stroke-dasharray": sp === "Adelie" ? "1 0" : sp === "Chinstrap" ? "7 5" : "12 5 2 5"
    }, g);
    el("path", {
      d: inner,
      fill: colors[sp],
      "fill-opacity": 0.08,
      stroke: colors[sp],
      "stroke-opacity": 0.24,
      "stroke-width": 1
    }, g);
    const c = data.geometry.centroids[sp];
    el("text", {
      x: x(c.pc1) + 10,
      y: y(c.pc2) - 10,
      class: "annotation",
      fill: colors[sp]
    }, g).textContent = `${speciesLabel(sp)} cloud`;
    if (state.layers.island) {
      const islandText = sp === "Adelie" ? "3 islands" : sp === "Chinstrap" ? "Dream only" : "Biscoe only";
      el("text", {
        x: x(c.pc1) + 10,
        y: y(c.pc2) + 8,
        class: "svg-label",
        fill: colors[sp]
      }, g).textContent = islandText;
    }
  });
}

function drawBoundary(data, x, y, xs, ys) {
  const g = el("g", { class: "boundary" }, svg);
  const pts = lineIntersections(data.geometry.boundary.pc_line, xs, ys);
  if (pts.length === 2) {
    el("line", {
      x1: x(pts[0].pc1),
      y1: y(pts[0].pc2),
      x2: x(pts[1].pc1),
      y2: y(pts[1].pc2),
      stroke: "#11100d",
      "stroke-opacity": 0.15,
      "stroke-width": 54,
      "stroke-linecap": "round"
    }, g);
    const boundaryLine = el("line", {
      x1: x(pts[0].pc1),
      y1: y(pts[0].pc2),
      x2: x(pts[1].pc1),
      y2: y(pts[1].pc2),
      stroke: "#11100d",
      "stroke-opacity": 0.58,
      "stroke-width": 2.8,
      "stroke-dasharray": "9 7",
      "stroke-linecap": "round"
    }, g);
    boundaryLine.addEventListener("mouseenter", () => {
      state.selectedRow = null;
      inspector.title.textContent = "Adelie-Chinstrap leaky band";
      inspector.meta.textContent = "The band is a projected LDA boundary. The five leave-one-out errors are tethered to their nearest cross-species neighbors.";
      inspector.evidence.textContent = `4D LDA leakage records: ${data.evidence.lda_leave_one_out.errors}, all Adelie/Chinstrap. Gentoo has no 4D confusion in this run.`;
    });
    el("text", {
      x: (x(pts[0].pc1) + x(pts[1].pc1)) / 2 + 12,
      y: (y(pts[0].pc2) + y(pts[1].pc2)) / 2 - 18,
      class: "annotation"
    }, g).textContent = "Adelie-Chinstrap leakage boundary";
  }
}

function drawVectors(data, x, y) {
  const g = el("g", { class: "vectors" }, svg);
  const pooled = data.geometry.vectors.pooled;
  const p = arrowPath(pooled.anchor, pooled.delta, x, y, 2.35);
  el("line", {
    x1: x(p.start.pc1), y1: y(p.start.pc2),
    x2: x(p.end.pc1), y2: y(p.end.pc2),
    stroke: colors.pooled,
    "stroke-width": 18,
    "stroke-opacity": 0.14,
    "stroke-linecap": "round"
  }, g);
  const pooledLine = el("line", {
    x1: x(p.start.pc1), y1: y(p.start.pc2),
    x2: x(p.end.pc1), y2: y(p.end.pc2),
    stroke: colors.pooled,
    "stroke-width": 4,
    "stroke-linecap": "round",
    "marker-end": "url(#arrow-pool)"
  }, g);
  pooledLine.addEventListener("click", () => setTrace("pooled"));
  el("text", { x: x(p.end.pc1) + 10, y: y(p.end.pc2) - 6, class: "annotation", fill: colors.pooled }, g).textContent = `pooled r = ${pooled.r}`;

  Object.entries(data.geometry.vectors.species).forEach(([sp, vector]) => {
    const a = arrowPath(vector.anchor, vector.delta, x, y, 1.25);
    const line = el("line", {
      x1: x(a.start.pc1), y1: y(a.start.pc2),
      x2: x(a.end.pc1), y2: y(a.end.pc2),
      stroke: colors[sp],
      "stroke-width": state.activeTrace === sp ? 5 : 3,
      "stroke-linecap": "round",
      "marker-end": `url(#arrow-${sp.toLowerCase()})`,
      opacity: state.activeTrace === "pooled" || state.activeTrace === sp ? 1 : 0.42
    }, g);
    line.addEventListener("click", () => setTrace(sp));
    el("text", { x: x(a.end.pc1) + 8, y: y(a.end.pc2) + 4, class: "svg-label", fill: colors[sp] }, g).textContent = `${speciesLabel(sp)} r = ${vector.r}`;
  });

  if (state.layers.sex) {
    Object.entries(data.geometry.sex_vectors).forEach(([sp, vector]) => {
      const a = arrowPath(vector.anchor, vector.delta, x, y, 0.95);
      el("line", {
        x1: x(a.start.pc1), y1: y(a.start.pc2),
        x2: x(a.end.pc1), y2: y(a.end.pc2),
        stroke: colors.sex,
        "stroke-width": 2.3,
        "stroke-dasharray": "4 3",
        "marker-end": "url(#arrow-sex)",
        opacity: 0.78
      }, g);
    });
    el("text", { x: 96, y: 118, class: "svg-label", fill: colors.sex }, g).textContent = "dashed violet vectors: male minus female centroid displacement";
  }
}

function drawTethers(data, x, y) {
  const g = el("g", { class: "tethers" }, svg);
  data.geometry.tethers.forEach((tether, index) => {
    const a = rowById(tether.source_row);
    const b = rowById(tether.target_row);
    if (!a || !b) return;
    const isLeak = tether.reason.includes("LDA");
    const path = el("path", {
      d: curvedPath(x(a.pc1), y(a.pc2), x(b.pc1), y(b.pc2), index % 2 ? 20 : -20),
      fill: "none",
      stroke: isLeak ? colors.ink : "#665e51",
      "stroke-opacity": isLeak ? 0.66 : 0.28,
      "stroke-width": isLeak ? 2.2 : 1.2,
      "stroke-dasharray": isLeak ? "1 0" : "3 5"
    }, g);
    path.addEventListener("click", () => selectPoint(a));
  });
}

function curvedPath(x1, y1, x2, y2, bend) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  const cx = mx + (-dy / len) * bend;
  const cy = my + (dx / len) * bend;
  return `M${x1.toFixed(1)},${y1.toFixed(1)} Q${cx.toFixed(1)},${cy.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`;
}

function drawPoints(data, x, y) {
  const g = el("g", { class: "points" }, svg);
  const marks = el("g", { class: "point-marks" }, svg);
  data.points.forEach((d) => {
    const muted = state.activeTrace !== "pooled" && d.species !== state.activeTrace;
    const selected = state.selectedRow === d.source_row;
    const strokeDash = state.layers.island
      ? d.island === "Dream" ? "5 3" : d.island === "Torgersen" ? "1 3" : "1 0"
      : "1 0";
    const circle = el("circle", {
      class: `point${muted ? " is-muted" : ""}${selected ? " is-selected" : ""}`,
      cx: x(d.pc1),
      cy: y(d.pc2),
      r: d.is_lda_leak ? d.mass_radius + 2.6 : d.mass_radius,
      fill: colors[d.species],
      "fill-opacity": d.is_lda_leak ? 0.96 : 0.72,
      stroke: d.is_singular && state.layers.singular ? "#11100d" : "#fffaf0",
      "stroke-width": d.is_lda_leak ? 2.4 : d.is_singular && state.layers.singular ? 2 : 1.2,
      "stroke-dasharray": strokeDash
    }, g);
    circle.addEventListener("click", (event) => {
      event.stopPropagation();
      selectPoint(d);
    });
    circle.addEventListener("mouseenter", () => previewPoint(d));

    if (d.sex === "male") {
      el("line", {
        x1: x(d.pc1) - 2.5, y1: y(d.pc2) + 2.5,
        x2: x(d.pc1) + 2.5, y2: y(d.pc2) - 2.5,
        stroke: "#fffaf0", "stroke-width": 1.4, "stroke-linecap": "round", opacity: muted ? 0.4 : 0.9
      }, marks);
    } else if (d.sex === "female") {
      el("line", {
        x1: x(d.pc1) - 2.8, y1: y(d.pc2),
        x2: x(d.pc1) + 2.8, y2: y(d.pc2),
        stroke: "#fffaf0", "stroke-width": 1.4, "stroke-linecap": "round", opacity: muted ? 0.4 : 0.9
      }, marks);
    } else {
      el("circle", { cx: x(d.pc1), cy: y(d.pc2), r: 1.4, fill: "#11100d", opacity: 0.78 }, marks);
    }

    if (state.layers.year) {
      const angle = d.year === 2007 ? -Math.PI / 2 : d.year === 2008 ? Math.PI / 6 : Math.PI * 0.78;
      const r0 = d.mass_radius + 2.2;
      const r1 = d.mass_radius + 6;
      el("line", {
        x1: x(d.pc1) + Math.cos(angle) * r0,
        y1: y(d.pc2) + Math.sin(angle) * r0,
        x2: x(d.pc1) + Math.cos(angle) * r1,
        y2: y(d.pc2) + Math.sin(angle) * r1,
        stroke: "#11100d",
        "stroke-width": 1,
        opacity: muted ? 0.12 : 0.38
      }, marks);
    }

    if (d.is_lda_leak) {
      el("text", { x: x(d.pc1) + 9, y: y(d.pc2) - 9, class: "svg-label", fill: "#11100d" }, marks).textContent = `#${d.source_row}`;
    }
  });
}

function drawLens(data, x, y, invX, invY) {
  const g = el("g", { class: "lens", filter: "url(#soft-shadow)" }, svg);
  const candidates = data.points.filter((p) => p.is_lens_candidate || p.is_lda_leak);
  const defaultCenter = candidates.reduce((acc, p) => ({ pc1: acc.pc1 + p.pc1 / candidates.length, pc2: acc.pc2 + p.pc2 / candidates.length }), { pc1: 0, pc2: 0 });
  const center = state.lensPoint || defaultCenter;
  const near = candidates
    .map((p) => ({ ...p, lensDistance: Math.hypot(p.pc1 - center.pc1, p.pc2 - center.pc2) }))
    .sort((a, b) => a.lensDistance - b.lensDistance)
    .slice(0, 22);
  const cx = x(center.pc1);
  const cy = y(center.pc2);

  el("ellipse", {
    cx, cy, rx: 118, ry: 78,
    fill: "rgba(255,250,240,0.82)",
    stroke: "#11100d",
    "stroke-width": 1.5,
    "stroke-dasharray": "7 5"
  }, g);
  el("text", { x: cx - 96, y: cy - 88, class: "annotation" }, g).textContent = "decluttered boundary lens";

  near.forEach((p, i) => {
    const col = i % 6;
    const row = Math.floor(i / 6);
    const lx = cx - 72 + col * 28 + (row % 2) * 10;
    const ly = cy - 34 + row * 23;
    el("line", {
      x1: x(p.pc1), y1: y(p.pc2), x2: lx, y2: ly,
      stroke: colors[p.species], "stroke-width": 0.9, "stroke-opacity": 0.42
    }, g);
    const ghost = el("circle", {
      cx: lx, cy: ly, r: p.is_lda_leak ? 6.8 : 4.9,
      fill: colors[p.species],
      stroke: p.is_lda_leak ? "#11100d" : "#fffaf0",
      "stroke-width": p.is_lda_leak ? 2 : 1,
      "fill-opacity": 0.86
    }, g);
    ghost.addEventListener("click", () => selectPoint(p));
  });

  svg.onmousemove = (event) => {
    const rect = svg.getBoundingClientRect();
    const px = event.clientX - rect.left;
    const py = event.clientY - rect.top;
    const nx = invX(px);
    const ny = invY(py);
    const distToBoundary = Math.abs(data.geometry.boundary.pc_line.a * nx + data.geometry.boundary.pc_line.b * ny + data.geometry.boundary.pc_line.c) /
      Math.hypot(data.geometry.boundary.pc_line.a, data.geometry.boundary.pc_line.b);
    if (distToBoundary < 0.55) {
      state.lensPoint = { pc1: nx, pc2: ny };
      requestAnimationFrame(draw);
    }
  };
}

function drawBiplotLegend(data, width, height) {
  const g = el("g", { class: "biplot" }, svg);
  const origin = { x: 112, y: height - 132 };
  el("rect", {
    x: origin.x - 24,
    y: origin.y - 74,
    width: 230,
    height: 118,
    rx: 8,
    fill: "rgba(255,250,240,0.72)",
    stroke: "rgba(17,16,13,0.24)"
  }, g);
  el("text", { x: origin.x - 8, y: origin.y - 52, class: "annotation" }, g).textContent = "PCA loading rays";
  const fieldColors = {
    bill_length_mm: "#d8462f",
    bill_depth_mm: "#734f96",
    flipper_length_mm: "#2e62d6",
    body_mass_g: "#0a9b97"
  };
  const labelOffsets = {
    bill_length_mm: [8, -8],
    bill_depth_mm: [-4, -12],
    flipper_length_mm: [8, 10],
    body_mass_g: [8, 5]
  };
  Object.keys(fieldColors).forEach((field) => {
    const pc1 = data.pca.loadings.PC1[field];
    const pc2 = data.pca.loadings.PC2[field];
    const end = { x: origin.x + pc1 * 62, y: origin.y - pc2 * 62 };
    el("line", {
      x1: origin.x,
      y1: origin.y,
      x2: end.x,
      y2: end.y,
      stroke: fieldColors[field],
      "stroke-width": 2,
      "marker-end": "url(#arrow-ink)",
      opacity: 0.82
    }, g);
    el("text", {
      x: end.x + labelOffsets[field][0],
      y: end.y + labelOffsets[field][1],
      class: "svg-label",
      fill: fieldColors[field]
    }, g).textContent = field.replace("_mm", "").replace("_g", "").replaceAll("_", " ");
  });
}

function drawMissingAnnotation(data, width, height) {
  const missing = data.dataset.missing_morphology_rows;
  const g = el("g", { class: "missing-rows" }, svg);
  const x0 = width - 350;
  const y0 = height - 80;
  el("text", { x: x0, y: y0, class: "annotation" }, g).textContent = `${missing.length} rows lack numeric morphology`;
  missing.forEach((row, i) => {
    el("circle", {
      cx: x0 + 16 + i * 24,
      cy: y0 + 22,
      r: 7,
      fill: colors[row.species] || "#888",
      stroke: "#11100d",
      "stroke-dasharray": "2 3"
    }, g);
    el("text", { x: x0 + 28 + i * 24, y: y0 + 27, class: "svg-label" }, g).textContent = `#${row.source_row}`;
  });
}

function selectPoint(point) {
  state.selectedRow = point.source_row;
  updateInspector(point);
  draw();
}

function previewPoint(point) {
  if (state.selectedRow !== null) return;
  updateInspector(point);
}

function setTrace(trace) {
  state.activeTrace = trace;
  document.querySelectorAll(".trace-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.trace === trace);
  });
  updateInspector();
  draw();
}

function updateInspector(point = null) {
  const data = state.data;
  if (!data) return;
  const selected = point || (state.selectedRow !== null ? rowById(state.selectedRow) : null);
  if (selected) {
    inspector.title.textContent = `source row ${selected.source_row}`;
    const leakText = selected.is_lda_leak ? ` LDA leakage predicted as ${selected.loo_predicted_species}.` : "";
    const singularText = selected.is_singular ? " Marked as a within-species singular anchor." : "";
    inspector.meta.textContent = `${speciesLabel(selected.species)} on ${selected.island}, ${fmt(selected.sex, 0)}, ${selected.year}.${leakText}${singularText}`;
    inspector.measures.innerHTML = [
      ["bill length", selected.bill_length_mm, "mm"],
      ["bill depth", selected.bill_depth_mm, "mm"],
      ["flipper", selected.flipper_length_mm, "mm"],
      ["body mass", selected.body_mass_g, "g"]
    ].map(([label, value, unit]) => `<div class="measure"><b>${fmt(value, value > 100 ? 0 : 1)} ${unit}</b><span>${htmlEscape(label)}</span></div>`).join("");
  } else {
    inspector.title.textContent = "Boundary field";
    inspector.meta.textContent = "Click a point, tether, or vector. The map keeps all 342 complete morphology rows in one PCA-grounded analysis object.";
    inspector.measures.innerHTML = [
      ["rows plotted", data.dataset.complete_morphology_rows, "complete"],
      ["missing morph.", data.dataset.missing_morphology_rows.length, "rows"],
      ["LDA leaks", data.evidence.lda_leave_one_out.errors, "rows"],
      ["PC1+PC2", Math.round((data.pca.explained_variance_ratio[0] + data.pca.explained_variance_ratio[1]) * 100), "% variance"]
    ].map(([label, value, unit]) => `<div class="measure"><b>${fmt(value, 0)} ${unit}</b><span>${htmlEscape(label)}</span></div>`).join("");
  }

  const c = data.evidence.correlations;
  if (state.activeTrace === "pooled") {
    inspector.evidence.textContent = `Pooled flipper_length_mm vs bill_depth_mm is negative: r = ${c.pooled_flipper_depth.pearson_r} over ${c.pooled_flipper_depth.n} complete morphology rows.`;
  } else {
    const sp = c.within_species_flipper_depth[state.activeTrace];
    inspector.evidence.textContent = `${state.activeTrace} reverses the pooled sign locally: within-species flipper_length_mm vs bill_depth_mm r = ${sp.pearson_r} over ${sp.n} rows.`;
  }
}

function updateLegend() {
  inspector.legend.innerHTML = [
    ["Adelie", colors.Adelie, "species cloud and points"],
    ["Chinstrap", colors.Chinstrap, "species cloud and points"],
    ["Gentoo", colors.Gentoo, "species cloud and points"],
    ["pooled band", colors.pooled, "negative flipper-depth field"],
    ["sex vector", colors.sex, "male minus female displacement"]
  ].map(([name, color, note]) => `<div class="legend-row"><span class="swatch" style="background:${color}"></span><b>${htmlEscape(name)}</b><span>${htmlEscape(note)}</span></div>`).join("");
}

function updateProvenance() {
  const d = state.data.dataset;
  const evidence = state.data.evidence;
  const sizeKb = (d.file_size_bytes / 1024).toFixed(1);
  document.getElementById("provenance").innerHTML = `
    <b>Real data provenance.</b>
    Dataset: ${htmlEscape(d.title)} (${htmlEscape(d.dataset_id)}), ${htmlEscape(d.source)}.
    Source path: ${htmlEscape(d.source_path)}. File size: ${sizeKb} KB.
    Original shape: ${d.original_rows} rows x ${d.columns.length} fields.
    Fields used: ${d.fields_used.map(htmlEscape).join(", ")}.
    Strategy: ${htmlEscape(d.sampling_strategy)}
    Missing handling: ${d.missing_morphology_rows.length} rows with missing numeric morphology are not projected into PCA and are shown as missing-row badges; ${evidence.missing_sex_rows} rows retain an unknown-sex mark.
    Island caution: Gentoo appears only on Biscoe and Chinstrap only on Dream in this file, so island is encoded as a nesting constraint, not an independent causal effect.
  `;
}

function wireUi() {
  document.querySelectorAll(".trace-button").forEach((button) => {
    button.addEventListener("click", () => setTrace(button.dataset.trace));
  });
  document.querySelectorAll("[data-layer]").forEach((input) => {
    input.addEventListener("change", () => {
      state.layers[input.dataset.layer] = input.checked;
      draw();
    });
  });
  const provenance = document.getElementById("provenance");
  const dataTab = document.getElementById("dataTab");
  dataTab.addEventListener("click", () => {
    const open = provenance.classList.toggle("is-open");
    dataTab.setAttribute("aria-expanded", String(open));
  });
  svg.addEventListener("click", () => {
    state.selectedRow = null;
    updateInspector();
    draw();
  });
  window.addEventListener("resize", () => requestAnimationFrame(draw));
}

try {
  const payload = window.__E001_PENGUINS_CODEX_PAYLOAD__;
  if (!payload) throw new Error("Missing data/prepared.js payload");
    state.data = payload;
    updateLegend();
    updateProvenance();
    wireUi();
    updateInspector();
    draw();
} catch (error) {
  svg.replaceChildren();
  const message = el("text", { x: 40, y: 80, class: "axis-label" }, svg);
  message.textContent = error.message;
}
