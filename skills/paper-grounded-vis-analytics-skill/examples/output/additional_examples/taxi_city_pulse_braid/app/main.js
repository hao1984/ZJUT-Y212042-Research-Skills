const svgNS = "http://www.w3.org/2000/svg";

const periodHours = {
  late_night: [0, 1, 2, 3, 4, 5],
  dawn: [6],
  morning_peak: [7, 8, 9],
  midday: [10, 11, 12, 13, 14, 15],
  evening_peak: [16, 17, 18, 19],
  night: [20, 21, 22, 23],
};

const periodLabels = {
  late_night: "late night 00-05",
  dawn: "dawn 06",
  morning_peak: "morning peak 07-09",
  midday: "midday 10-15",
  evening_peak: "evening peak 16-19",
  night: "night 20-23",
};

const roleLabels = {
  city_internal: "city internal",
  to_airport: "to airport",
  from_airport: "from airport",
  airport_between: "airport between",
};

const roleColors = {
  city_internal: "#62b6a8",
  to_airport: "#e5b95f",
  from_airport: "#e66b4f",
  airport_between: "#b98cff",
};

const metricSpecs = [
  {
    label: "distance",
    unit: "mi",
    selected: "distance_median",
    base: "trip_distance",
    format: (v) => number(v, 1),
  },
  {
    label: "duration",
    unit: "min",
    selected: "duration_median",
    base: "duration_min",
    format: (v) => number(v, 0),
  },
  {
    label: "fare per mile",
    unit: "$/mi",
    selected: "fare_per_mile_median",
    base: "fare_per_mile",
    format: (v) => `$${number(v, 2)}`,
  },
  {
    label: "speed",
    unit: "mph",
    selected: "speed_median",
    base: "speed_mph",
    format: (v) => number(v, 0),
  },
  {
    label: "credit tip rate",
    unit: "fare",
    selected: "credit_tip_rate_median",
    base: "tip_rate_fare",
    format: (v) => `${number((v || 0) * 100, 0)}%`,
  },
];

let payload;
let regionById;
let state = {
  dayType: "weekday",
  period: "morning_peak",
  selected: {
    PU_region: "Brooklyn",
    DO_region: "Manhattan",
    airport_role: "city_internal",
  },
  focusRole: null,
  anomalyClass: null,
  hoverFlow: null,
};

const $ = (id) => document.getElementById(id);

function node(name, attrs = {}, children = []) {
  const n = document.createElementNS(svgNS, name);
  Object.entries(attrs).forEach(([k, v]) => {
    if (v !== undefined && v !== null) n.setAttribute(k, String(v));
  });
  children.forEach((c) => n.appendChild(c));
  return n;
}

function clear(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

function number(v, digits = 0) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "n/a";
  return Number(v).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function compact(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "n/a";
  if (v >= 1000000) return `${number(v / 1000000, 1)}M`;
  if (v >= 1000) return `${number(v / 1000, 1)}k`;
  return number(v, 0);
}

function flowId(f) {
  return `${f.PU_region}->${f.DO_region}|${f.airport_role}`;
}

function selectedId() {
  return `${state.selected.PU_region}->${state.selected.DO_region}|${state.selected.airport_role}`;
}

function sameFlow(f, sel = state.selected) {
  return f.PU_region === sel.PU_region && f.DO_region === sel.DO_region && f.airport_role === sel.airport_role;
}

function currentFlows() {
  return payload.flows.filter(
    (f) =>
      f.day_type === state.dayType &&
      f.period === state.period &&
      f.PU_region !== f.DO_region &&
      f.PU_region !== "Unresolved" &&
      f.DO_region !== "Unresolved"
  );
}

function exactSelectedFlow() {
  return payload.flows.find(
    (f) =>
      f.day_type === state.dayType &&
      f.period === state.period &&
      f.PU_region === state.selected.PU_region &&
      f.DO_region === state.selected.DO_region &&
      f.airport_role === state.selected.airport_role
  );
}

function ensureSelectedFlow() {
  if (exactSelectedFlow()) return;
  const fallback = currentFlows()
    .filter((f) => f.airport_role === "city_internal")
    .sort((a, b) => b.trips - a.trips)[0] || currentFlows().sort((a, b) => b.trips - a.trips)[0];
  if (fallback) {
    state.selected = {
      PU_region: fallback.PU_region,
      DO_region: fallback.DO_region,
      airport_role: fallback.airport_role,
    };
  }
}

function visibleFlows() {
  const flows = currentFlows().sort((a, b) => b.trips - a.trips);
  const selected = exactSelectedFlow();
  const keep = flows.slice(0, 32);
  if (selected && !keep.some((f) => flowId(f) === flowId(selected))) keep.push(selected);
  return keep;
}

function pointForRegion(id) {
  const r = regionById.get(id);
  return { x: r.x * 1000, y: r.y * 650 };
}

function hashSign(text) {
  let h = 0;
  for (let i = 0; i < text.length; i += 1) h = (h * 31 + text.charCodeAt(i)) | 0;
  return h % 2 === 0 ? 1 : -1;
}

function curveSpec(f) {
  const p0 = pointForRegion(f.PU_region);
  const p2 = pointForRegion(f.DO_region);
  const dx = p2.x - p0.x;
  const dy = p2.y - p0.y;
  const d = Math.hypot(dx, dy) || 1;
  const nx = -dy / d;
  const ny = dx / d;
  const roleBoost = f.airport_role === "city_internal" ? 0.17 : 0.25;
  const sign = hashSign(flowId(f));
  const p1 = {
    x: (p0.x + p2.x) / 2 + nx * d * roleBoost * sign,
    y: (p0.y + p2.y) / 2 + ny * d * roleBoost * sign,
  };
  return { p0, p1, p2 };
}

function quadPoint({ p0, p1, p2 }, t) {
  const a = (1 - t) * (1 - t);
  const b = 2 * (1 - t) * t;
  const c = t * t;
  return {
    x: a * p0.x + b * p1.x + c * p2.x,
    y: a * p0.y + b * p1.y + c * p2.y,
  };
}

function quadDerivative({ p0, p1, p2 }, t) {
  return {
    x: 2 * (1 - t) * (p1.x - p0.x) + 2 * t * (p2.x - p1.x),
    y: 2 * (1 - t) * (p1.y - p0.y) + 2 * t * (p2.y - p1.y),
  };
}

function centerPath(spec) {
  return `M ${spec.p0.x} ${spec.p0.y} Q ${spec.p1.x} ${spec.p1.y} ${spec.p2.x} ${spec.p2.y}`;
}

function ribbonPath(spec, width) {
  const left = [];
  const right = [];
  const steps = 22;
  for (let i = 0; i <= steps; i += 1) {
    const t = i / steps;
    const p = quadPoint(spec, t);
    const d = quadDerivative(spec, t);
    const len = Math.hypot(d.x, d.y) || 1;
    const nx = -d.y / len;
    const ny = d.x / len;
    const localW = width * (1 - 0.64 * t) + 1.2;
    left.push([p.x + nx * localW, p.y + ny * localW]);
    right.push([p.x - nx * localW, p.y - ny * localW]);
  }
  const points = left.concat(right.reverse());
  return `M ${points.map((p) => `${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join(" L ")} Z`;
}

function notchPath(spec, width) {
  const p = quadPoint(spec, 0.82);
  const d = quadDerivative(spec, 0.82);
  const len = Math.hypot(d.x, d.y) || 1;
  const ux = d.x / len;
  const uy = d.y / len;
  const nx = -uy;
  const ny = ux;
  const w = Math.max(5, width * 0.8);
  const p1 = [p.x + ux * w * 1.4, p.y + uy * w * 1.4];
  const p2 = [p.x - ux * w * 0.7 + nx * w, p.y - uy * w * 0.7 + ny * w];
  const p3 = [p.x - ux * w * 0.7 - nx * w, p.y - uy * w * 0.7 - ny * w];
  return `M ${p1.join(" ")} L ${p2.join(" ")} L ${p3.join(" ")} Z`;
}

function showTooltip(evt, html) {
  const t = $("tooltip");
  t.innerHTML = html;
  t.hidden = false;
  t.style.left = `${Math.min(window.innerWidth - 350, evt.clientX + 16)}px`;
  t.style.top = `${Math.min(window.innerHeight - 150, evt.clientY + 12)}px`;
}

function hideTooltip() {
  $("tooltip").hidden = true;
}

function anomalyGroupsForFlow(f, restrictClass = state.anomalyClass) {
  return payload.anomaly_groups.filter(
    (g) =>
      g.day_type === state.dayType &&
      g.period === state.period &&
      g.PU_region === f.PU_region &&
      g.DO_region === f.DO_region &&
      g.airport_role === f.airport_role &&
      (!restrictClass || g.anomaly_class === restrictClass)
  );
}

function renderPrimary() {
  ensureSelectedFlow();
  const svg = $("pulse-braid");
  clear(svg);
  svg.appendChild(node("rect", { x: 0, y: 0, width: 1000, height: 650, fill: "rgba(255,255,255,0.012)" }));
  svg.appendChild(node("path", { class: "membrane", d: "M 770 130 C 925 195 955 510 835 585" }));
  svg.appendChild(node("path", { class: "membrane", d: "M 90 360 C 60 435 95 525 170 575" }));

  const flows = visibleFlows();
  const maxTrips = Math.max(...flows.map((f) => f.trips), 1);

  flows.forEach((f) => {
    const spec = curveSpec(f);
    const width = 4 + 20 * Math.sqrt(f.trips / maxTrips);
    const selected = flowId(f) === selectedId();
    const roleDim = state.focusRole && f.airport_role !== state.focusRole;
    const color = roleColors[f.airport_role] || "#9aa";
    const path = node("path", {
      class: `corridor${selected ? " selected" : ""}${roleDim ? " dimmed" : ""}`,
      d: ribbonPath(spec, width),
      fill: color,
      opacity: selected ? 0.78 : 0.43,
    });
    path.addEventListener("mouseenter", (evt) => {
      state.hoverFlow = f;
      showTooltip(
        evt,
        `<strong>${f.PU_region} -> ${f.DO_region}</strong><br>${roleLabels[f.airport_role] || f.airport_role}, ${compact(f.trips)} valid trips<small>median distance ${number(f.distance_median, 1)} mi, credit-card visible tip rate ${number((f.credit_tip_rate_median || 0) * 100, 0)}%</small>`
      );
    });
    path.addEventListener("mousemove", (evt) => showTooltip(evt, $("tooltip").innerHTML));
    path.addEventListener("mouseleave", () => {
      state.hoverFlow = null;
      hideTooltip();
    });
    path.addEventListener("click", () => {
      state.selected = {
        PU_region: f.PU_region,
        DO_region: f.DO_region,
        airport_role: f.airport_role,
      };
      state.focusRole = null;
      updateAll();
    });
    svg.appendChild(path);
    svg.appendChild(node("path", { class: "direction-notch", d: notchPath(spec, width), fill: "#f7eee0", opacity: selected ? 0.9 : 0.42 }));

    const anoms = anomalyGroupsForFlow(f);
    const excluded = anoms.reduce((sum, g) => sum + g.excluded_rows, 0);
    if (excluded > 0) {
      const top = anoms.slice().sort((a, b) => b.excluded_rows - a.excluded_rows)[0];
      const p = quadPoint(spec, 0.56);
      const r = Math.min(13, 3 + Math.sqrt(excluded) / 5);
      const spark = node("circle", {
        class: `spark${state.anomalyClass && top.anomaly_class === state.anomalyClass ? " selected" : ""}`,
        cx: p.x,
        cy: p.y,
        r,
        opacity: selected ? 0.92 : 0.62,
      });
      spark.addEventListener("mouseenter", (evt) => {
        showTooltip(evt, `<strong>${top.anomaly_class.replaceAll("_", " ")}</strong><br>${compact(excluded)} excluded or anomaly-class rows near this state<small>click to scope the record trace</small>`);
      });
      spark.addEventListener("mouseleave", hideTooltip);
      spark.addEventListener("click", (evt) => {
        evt.stopPropagation();
        state.selected = {
          PU_region: f.PU_region,
          DO_region: f.DO_region,
          airport_role: f.airport_role,
        };
        state.anomalyClass = top.anomaly_class;
        updateAll();
      });
      svg.appendChild(spark);
    }
  });

  payload.regions
    .filter((r) => r.id !== "Unresolved")
    .forEach((r) => {
      const x = r.x * 1000;
      const y = r.y * 650;
      const isAirport = r.kind === "airport";
      svg.appendChild(node(isAirport ? "rect" : "circle", isAirport ? { class: "anchor airport", x: x - 12, y: y - 12, width: 24, height: 24, rx: 5 } : { class: "anchor", cx: x, cy: y, r: 18 }));
      if (r.kind !== "unresolved") {
        svg.appendChild(node("text", { class: "region-label", x: x + 22, y: y + 5 }, [document.createTextNode(r.label)]));
      }
    });

  const selected = exactSelectedFlow();
  if (selected) {
    const topZone = matchingZonePairs().slice(0, 1)[0];
    const text = topZone ? `${topZone.PU_zone} -> ${topZone.DO_zone}` : `${selected.PU_region} -> ${selected.DO_region}`;
    svg.appendChild(
      node("text", { x: 22, y: 625, fill: "#f2efe5", "font-size": 13 }, [
        document.createTextNode(`Selected strand: ${text} | ${compact(selected.trips)} valid trips in ${periodLabels[state.period]}`),
      ])
    );
  }
}

function renderPhaseRail() {
  const svg = $("phase-rail");
  clear(svg);
  const left = 84;
  const top = 26;
  const hourW = 40;
  const rowH = 34;
  const maxOverall = Math.max(...payload.hourly_overall.map((d) => d.avg_trips_per_day), 1);
  const dayY = { weekday: top + 18, weekend: top + 64 };

  Object.entries(periodHours).forEach(([period, hours]) => {
    const x = left + Math.min(...hours) * hourW;
    const w = hours.length * hourW;
    const band = node("rect", {
      class: `phase-band${period === state.period ? " active" : ""}`,
      x,
      y: 10,
      width: w,
      height: 105,
      rx: 7,
    });
    band.addEventListener("click", () => {
      state.period = period;
      state.anomalyClass = null;
      updateAll();
    });
    svg.appendChild(band);
    svg.appendChild(node("text", { class: "phase-label", x: x + 5, y: 24 }, [document.createTextNode(periodLabels[period].split(" ")[0])]));
  });

  ["weekday", "weekend"].forEach((day) => {
    const label = node("text", { class: "phase-day-label", x: 16, y: dayY[day] + 6 }, [document.createTextNode(day)]);
    label.addEventListener("click", () => {
      state.dayType = day;
      state.anomalyClass = null;
      updateAll();
    });
    svg.appendChild(label);
    for (let h = 0; h < 24; h += 1) {
      const rec = payload.hourly_overall.find((d) => d.day_type === day && Number(d.pickup_hour) === h);
      const barH = rec ? 27 * (rec.avg_trips_per_day / maxOverall) : 0;
      const activeHour = periodHours[state.period].includes(h);
      const rect = node("rect", {
        class: "phase-hour",
        x: left + h * hourW + 4,
        y: dayY[day] - barH,
        width: hourW - 8,
        height: Math.max(1, barH),
        fill: day === state.dayType ? (activeHour ? "#f7eee0" : "#8a8f80") : "#4f5549",
        opacity: day === state.dayType ? (activeHour ? 0.72 : 0.34) : 0.25,
        rx: 3,
      });
      rect.addEventListener("click", () => {
        state.dayType = day;
        const found = Object.entries(periodHours).find(([, hrs]) => hrs.includes(h));
        state.period = found ? found[0] : state.period;
        state.anomalyClass = null;
        updateAll();
      });
      svg.appendChild(rect);
    }
  });

  const profile = payload.hourly_corridors.filter(
    (d) =>
      d.day_type === state.dayType &&
      d.PU_region === state.selected.PU_region &&
      d.DO_region === state.selected.DO_region &&
      d.airport_role === state.selected.airport_role
  );
  const maxProfile = Math.max(...profile.map((d) => d.trips), 1);
  profile.forEach((d) => {
    const h = Number(d.pickup_hour);
    const barH = 29 * (d.trips / maxProfile);
    svg.appendChild(
      node("rect", {
        x: left + h * hourW + 11,
        y: dayY[state.dayType] + rowH - barH,
        width: hourW - 22,
        height: Math.max(1, barH),
        fill: roleColors[state.selected.airport_role] || "#ddd",
        opacity: periodHours[state.period].includes(h) ? 0.92 : 0.44,
        rx: 2,
      })
    );
  });

  for (let h = 0; h < 24; h += 3) {
    svg.appendChild(node("text", { class: "axis-label", x: left + h * hourW + 2, y: 126 }, [document.createTextNode(String(h).padStart(2, "0"))]));
  }
  svg.appendChild(node("text", { class: "axis-label", x: 840, y: 126 }, [document.createTextNode("thin overlay shows selected corridor hour profile")]));
}

function matchingZonePairs() {
  return payload.top_zone_pairs
    .filter(
      (z) =>
        z.day_type === state.dayType &&
        z.period === state.period &&
        z.airport_role === state.selected.airport_role &&
        z.PU_region === state.selected.PU_region &&
        z.DO_region === state.selected.DO_region
    )
    .sort((a, b) => b.trips - a.trips);
}

function renderRoleChips() {
  const holder = $("role-chips");
  holder.replaceChildren();
  const all = document.createElement("button");
  all.textContent = "all roles";
  all.className = state.focusRole ? "" : "active";
  all.addEventListener("click", () => {
    state.focusRole = null;
    updateAll();
  });
  holder.appendChild(all);
  Object.keys(roleLabels).forEach((role) => {
    const b = document.createElement("button");
    b.textContent = roleLabels[role];
    b.className = `role-${role}${state.focusRole === role ? " active" : ""}`;
    b.addEventListener("click", () => {
      state.focusRole = state.focusRole === role ? null : role;
      updateAll();
    });
    holder.appendChild(b);
  });
}

function renderEvidence() {
  renderRoleChips();
  const svg = $("regime-evidence");
  clear(svg);
  const selected = exactSelectedFlow();
  const baselines = payload.regime_baselines.filter((d) => d.day_type === state.dayType && d.period === state.period);
  const x0 = 138;
  const x1 = 420;
  const y0 = 34;
  const rowGap = 35;

  svg.appendChild(node("text", { x: 14, y: 18, fill: "#f2efe5", "font-size": 13 }, [document.createTextNode(`${state.selected.PU_region} -> ${state.selected.DO_region}`)]));
  svg.appendChild(node("text", { x: 14, y: 34, fill: "#a7a294", "font-size": 11 }, [document.createTextNode(roleLabels[state.selected.airport_role] || state.selected.airport_role)]));

  metricSpecs.forEach((m, i) => {
    const y = y0 + i * rowGap;
    const vals = [];
    baselines.forEach((b) => {
      ["q25", "median", "q75"].forEach((q) => {
        const v = b[`${m.base}_${q}`];
        if (v !== null && v !== undefined) vals.push(Number(v));
      });
    });
    if (selected && selected[m.selected] !== null) vals.push(Number(selected[m.selected]));
    const max = Math.max(...vals.filter((v) => Number.isFinite(v)), m.base === "tip_rate_fare" ? 0.35 : 1) * 1.2;
    const sx = (v) => x0 + Math.max(0, Math.min(1, Number(v || 0) / max)) * (x1 - x0);

    svg.appendChild(node("text", { class: "metric-label", x: 14, y: y + 4 }, [document.createTextNode(m.label)]));
    svg.appendChild(node("line", { x1: x0, x2: x1, y1: y, y2: y, stroke: "#383c32", "stroke-width": 1 }));

    baselines.forEach((b) => {
      const q25 = b[`${m.base}_q25`];
      const med = b[`${m.base}_median`];
      const q75 = b[`${m.base}_q75`];
      if (q25 === null || med === null || q75 === null) return;
      const role = b.airport_role;
      const opacity = role === state.selected.airport_role ? 0.58 : 0.22;
      svg.appendChild(node("line", { x1: sx(q25), x2: sx(q75), y1: y, y2: y, stroke: roleColors[role] || "#777", "stroke-width": role === state.selected.airport_role ? 8 : 4, "stroke-linecap": "round", opacity }));
      svg.appendChild(node("circle", { cx: sx(med), cy: y, r: role === state.selected.airport_role ? 4 : 2.5, fill: roleColors[role] || "#777", opacity: role === state.selected.airport_role ? 0.9 : 0.45 }));
    });

    if (selected && selected[m.selected] !== null && selected[m.selected] !== undefined) {
      const x = sx(selected[m.selected]);
      svg.appendChild(node("path", { d: `M ${x} ${y - 7} L ${x + 7} ${y} L ${x} ${y + 7} L ${x - 7} ${y} Z`, fill: "#f7eee0" }));
      svg.appendChild(node("text", { x: x + 10, y: y + 4, fill: "#f7eee0", "font-size": 11 }, [document.createTextNode(`${m.format(selected[m.selected])} ${m.unit}`)]));
    }
  });

  svg.appendChild(node("text", { class: "axis-label", x: 138, y: 212 }, [document.createTextNode("colored bands: regime q25-q75; diamond: selected corridor median")]));

  const zones = matchingZonePairs();
  const zoneEl = $("zone-evidence");
  if (zones.length) {
    zoneEl.innerHTML = `<strong>Top measured zone strands:</strong> ${zones
      .slice(0, 3)
      .map((z) => `${z.PU_zone} -> ${z.DO_zone} (${compact(z.trips)})`)
      .join("; ")}`;
  } else {
    zoneEl.innerHTML = `<strong>Top measured zone strands:</strong> none above the current aggregate threshold.`;
  }
}

function classLabel(c) {
  return c.replaceAll("_", " ");
}

function matchingAnomalyGroupsBroad() {
  const exact = payload.anomaly_groups.filter(
    (g) =>
      g.day_type === state.dayType &&
      g.period === state.period &&
      g.PU_region === state.selected.PU_region &&
      g.DO_region === state.selected.DO_region &&
      g.airport_role === state.selected.airport_role
  );
  if (exact.length) return exact;
  return payload.anomaly_groups.filter((g) => g.day_type === state.dayType && g.period === state.period);
}

function renderTrace() {
  const selected = exactSelectedFlow();
  const groups = matchingAnomalyGroupsBroad();
  const byClass = new Map();
  groups.forEach((g) => byClass.set(g.anomaly_class, (byClass.get(g.anomaly_class) || 0) + g.excluded_rows));
  const sortedClasses = Array.from(byClass.entries()).sort((a, b) => b[1] - a[1]).slice(0, 9);
  const effectiveClass = state.anomalyClass || (sortedClasses[0] ? sortedClasses[0][0] : null);
  const selectedExcluded = groups
    .filter((g) => !effectiveClass || g.anomaly_class === effectiveClass)
    .reduce((sum, g) => sum + g.excluded_rows, 0);

  $("trace-boundary").innerHTML = `<strong>Boundary:</strong> ${state.dayType}, ${periodLabels[state.period]}, ${state.selected.PU_region} -> ${state.selected.DO_region}, ${roleLabels[state.selected.airport_role] || state.selected.airport_role}. Valid aggregate: <strong>${compact(selected ? selected.trips : 0)}</strong>. Excluded/anomaly trace: <strong>${compact(selectedExcluded)}</strong>.`;

  const classHolder = $("anomaly-classes");
  classHolder.replaceChildren();
  sortedClasses.forEach(([klass, count]) => {
    const b = document.createElement("button");
    b.textContent = `${classLabel(klass)} ${compact(count)}`;
    b.className = effectiveClass === klass ? "active" : "";
    b.addEventListener("click", () => {
      state.anomalyClass = state.anomalyClass === klass ? null : klass;
      updateAll();
    });
    classHolder.appendChild(b);
  });

  let rows = payload.anomaly_samples.filter(
    (r) =>
      (!effectiveClass || r.anomaly_class === effectiveClass) &&
      r.day_type === state.dayType &&
      r.period === state.period &&
      r.PU_region === state.selected.PU_region &&
      r.DO_region === state.selected.DO_region &&
      r.airport_role === state.selected.airport_role
  );
  if (!rows.length) {
    rows = payload.anomaly_samples.filter((r) => (!effectiveClass || r.anomaly_class === effectiveClass) && r.day_type === state.dayType && r.period === state.period);
  }
  if (!rows.length) rows = payload.anomaly_samples.filter((r) => !effectiveClass || r.anomaly_class === effectiveClass);
  rows = rows.slice(0, 7);

  const trace = $("record-trace");
  trace.replaceChildren();
  if (!rows.length) {
    const empty = document.createElement("div");
    empty.className = "trace-row";
    empty.textContent = "No capped trace rows matched this boundary; aggregate counts still come from the full measured data.";
    trace.appendChild(empty);
    return;
  }

  rows.forEach((r) => {
    const div = document.createElement("div");
    div.className = "trace-row";
    div.innerHTML = `<strong>${classLabel(r.anomaly_class)} | ${r.PU_zone || r.PU_region} -> ${r.DO_zone || r.DO_region}</strong>
      pickup ${String(r.tpep_pickup_datetime).replace("T", " ").slice(0, 16)}, payment ${r.payment_type}, distance ${number(r.trip_distance, 2)} mi, duration ${number(r.duration_min, 1)} min, fare $${number(r.fare_amount, 2)}, tip $${number(r.tip_amount, 2)}, total $${number(r.total_amount, 2)}`;
    trace.appendChild(div);
  });
}

function renderProvenance() {
  const m = payload.metadata;
  const c = m.counts;
  $("data-provenance").textContent = `Real data: ${m.source}. Original table ${compact(c.original_rows)} rows x ${c.column_count} fields, ${number(m.data_size_mb, 1)} MB parquet; lookup ${Object.keys(m.airport_zone_ids).length} airport zone IDs plus ${m.zone_lookup_path.split("/").pop()}. Browser payload uses full-data OD/hour/regime/anomaly aggregates; no synthetic data; raw anomaly trace is deterministic capped real rows. Valid-core filter retained ${compact(c.valid_core_rows)} rows (${number(c.valid_core_share * 100, 2)}%). Fields used include pickup/dropoff time, PU/DO zone, distance, fare, tip, payment, total, lookup borough/zone, duration, hour, period, airport_role, speed, and fare_per_mile.`;
}

function updateStateStrip() {
  $("state-day").textContent = state.dayType;
  $("state-period").textContent = periodLabels[state.period];
  $("state-corridor").textContent = `${state.selected.PU_region} -> ${state.selected.DO_region}`;
}

function updateAll() {
  ensureSelectedFlow();
  updateStateStrip();
  renderPhaseRail();
  renderPrimary();
  renderEvidence();
  renderTrace();
}

function boot() {
  payload = window.__E006_TAXI_REFERENCE_PAYLOAD__;
  if (!payload) throw new Error("Missing data/pulse_payload.js payload");
  regionById = new Map(payload.regions.map((r) => [r.id, r]));
  ensureSelectedFlow();
  renderProvenance();
  updateAll();
}

try {
  boot();
} catch (err) {
  document.body.innerHTML = `<pre style="padding:20px;color:#f2efe5;background:#121411;">Failed to load pulse payload: ${err.message}</pre>`;
}
