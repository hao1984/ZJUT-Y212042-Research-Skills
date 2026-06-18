#!/usr/bin/env python3
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.preprocessing import StandardScaler


RUN_DIR = Path(__file__).resolve().parents[1]


def cache_file(filename):
    roots = []
    env_cache = os.environ.get("VISPAPER_DATASET_CACHE")
    if env_cache:
        roots.append(Path(env_cache))
    roots.extend(parent / "datasets" / "cache" for parent in [RUN_DIR, *RUN_DIR.parents])
    for root in roots:
        candidate = root / filename
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find {filename}; set VISPAPER_DATASET_CACHE to the datasets/cache directory.")


DATA_PATH = cache_file("e001_palmer_penguins_morphology.csv")
OUT_PATH = RUN_DIR / "app" / "data" / "prepared.json"
FEATURES = ["bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g"]
SPECIES_ORDER = ["Adelie", "Chinstrap", "Gentoo"]


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def round_float(value, digits=4):
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def convex_path(points):
    if len(points) < 3:
        return []
    hull = ConvexHull(np.asarray(points))
    return [[round_float(points[i][0]), round_float(points[i][1])] for i in hull.vertices]


def quantile_hull(group, quantile):
    coords = group[["pc1", "pc2"]].to_numpy()
    center = coords.mean(axis=0)
    dist = np.linalg.norm(coords - center, axis=1)
    keep = dist <= np.quantile(dist, quantile)
    kept = coords[keep]
    if len(kept) < 3:
        kept = coords
    return convex_path(kept)


def corr(a, b):
    pair = pd.DataFrame({"a": a, "b": b}).dropna()
    return float(pair["a"].corr(pair["b"]))


def vector_to_pc(pca, vector):
    projected = np.asarray(vector).dot(pca.components_[:2].T)
    return projected


def build():
    df = pd.read_csv(DATA_PATH, na_values=["NA", ""])
    df = df.reset_index().rename(columns={"index": "source_row"})
    for field in FEATURES:
        df[field] = pd.to_numeric(df[field], errors="coerce")

    complete = df.dropna(subset=FEATURES).copy()
    missing = df[df[FEATURES].isna().any(axis=1)].copy()

    scaler = StandardScaler()
    z = scaler.fit_transform(complete[FEATURES])
    pca = PCA(n_components=4)
    pc = pca.fit_transform(z)

    # Stabilize PCA signs against the Stage 1 interpretation:
    # PC1 grows with flipper/body scale; PC2 grows with bill depth.
    if pca.components_[0, FEATURES.index("flipper_length_mm")] < 0:
        pca.components_[0] *= -1
        pc[:, 0] *= -1
    if pca.components_[1, FEATURES.index("bill_depth_mm")] < 0:
        pca.components_[1] *= -1
        pc[:, 1] *= -1

    complete[["pc1", "pc2", "pc3", "pc4"]] = pc
    complete["mass_radius"] = np.interp(complete["body_mass_g"], (complete["body_mass_g"].min(), complete["body_mass_g"].max()), (3.4, 7.8))

    pooled_r = corr(complete["flipper_length_mm"], complete["bill_depth_mm"])
    species_r = {
        sp: corr(g["flipper_length_mm"], g["bill_depth_mm"])
        for sp, g in complete.groupby("species")
    }

    centroids = {}
    hulls = {}
    inner_hulls = {}
    species_counts = {}
    for sp in SPECIES_ORDER:
        g = complete[complete["species"] == sp]
        species_counts[sp] = int(len(g))
        centroids[sp] = {
            "pc1": round_float(g["pc1"].mean()),
            "pc2": round_float(g["pc2"].mean()),
            "n": int(len(g)),
        }
        hulls[sp] = convex_path(g[["pc1", "pc2"]].to_numpy())
        inner_hulls[sp] = quantile_hull(g, 0.72)

    vectors = {
        "pooled": {
            "label": "pooled negative flipper-depth field",
            "r": round_float(pooled_r),
            "anchor": {
                "pc1": round_float(complete["pc1"].mean()),
                "pc2": round_float(complete["pc2"].mean()),
            },
            "delta": {
                "pc1": round_float(vector_to_pc(pca, [0, pooled_r, 1, 0])[0]),
                "pc2": round_float(vector_to_pc(pca, [0, pooled_r, 1, 0])[1]),
            },
        },
        "species": {},
    }
    for sp in SPECIES_ORDER:
        delta = vector_to_pc(pca, [0, species_r[sp], 1, 0])
        vectors["species"][sp] = {
            "r": round_float(species_r[sp]),
            "anchor": centroids[sp],
            "delta": {"pc1": round_float(delta[0]), "pc2": round_float(delta[1])},
        }

    sex_vectors = {}
    for sp in SPECIES_ORDER:
        g = complete[(complete["species"] == sp) & complete["sex"].isin(["male", "female"])]
        male = g[g["sex"] == "male"]
        female = g[g["sex"] == "female"]
        if len(male) and len(female):
            raw_diff = male[FEATURES].mean() - female[FEATURES].mean()
            standardized_diff = raw_diff.to_numpy() / scaler.scale_
            delta = vector_to_pc(pca, standardized_diff)
            sex_vectors[sp] = {
                "n_male": int(len(male)),
                "n_female": int(len(female)),
                "anchor": centroids[sp],
                "delta": {"pc1": round_float(delta[0]), "pc2": round_float(delta[1])},
                "raw_diff": {field: round_float(raw_diff[field], 3) for field in FEATURES},
                "standardized_length": round_float(np.linalg.norm(standardized_diff), 3),
            }

    ac = complete[complete["species"].isin(["Adelie", "Chinstrap"])].copy()
    lda_ac = LinearDiscriminantAnalysis()
    lda_ac.fit(scaler.transform(ac[FEATURES]), ac["species"])
    w = lda_ac.coef_[0]
    intercept = float(lda_ac.intercept_[0])
    projected_w = np.array([w.dot(pca.components_[0]), w.dot(pca.components_[1])])
    ac["boundary_score"] = lda_ac.decision_function(scaler.transform(ac[FEATURES]))
    score_abs = np.abs(ac["boundary_score"])
    lens_rows = ac[score_abs <= np.quantile(score_abs, 0.18)]["source_row"].astype(int).tolist()

    lda_all = LinearDiscriminantAnalysis()
    loo = LeaveOneOut()
    pred = cross_val_predict(lda_all, scaler.transform(complete[FEATURES]), complete["species"], cv=loo)
    complete["loo_predicted_species"] = pred
    leakage_df = complete[complete["species"] != complete["loo_predicted_species"]].copy()

    tethers = []
    for _, row in leakage_df.iterrows():
        others = complete[complete["species"] == row["loo_predicted_species"]].copy()
        rz = scaler.transform(pd.DataFrame([row[FEATURES].to_dict()]))[0]
        oz = scaler.transform(others[FEATURES])
        distances = np.linalg.norm(oz - rz, axis=1)
        nearest = others.iloc[int(np.argmin(distances))]
        tethers.append(
            {
                "source_row": int(row["source_row"]),
                "target_row": int(nearest["source_row"]),
                "species": row["species"],
                "predicted_species": row["loo_predicted_species"],
                "distance_z": round_float(float(np.min(distances)), 4),
                "reason": "4D LDA leave-one-out leakage to nearest predicted-species neighbor",
            }
        )

    # Additional closest cross-species bill-shape pairs keep the visible boundary from becoming only an error list.
    bill_scaler = StandardScaler()
    bill_z = bill_scaler.fit_transform(complete[["bill_length_mm", "bill_depth_mm"]])
    complete[["bill_z1", "bill_z2"]] = bill_z
    pair_seen = set()
    bill_pairs = []
    for _, row in complete.iterrows():
        others = complete[complete["species"] != row["species"]]
        row_bill = row[["bill_z1", "bill_z2"]].to_numpy(dtype=float)
        other_bill = others[["bill_z1", "bill_z2"]].to_numpy(dtype=float)
        distances = np.linalg.norm(other_bill - row_bill, axis=1)
        nearest = others.iloc[int(np.argmin(distances))]
        key = tuple(sorted([int(row["source_row"]), int(nearest["source_row"])]))
        if key in pair_seen:
            continue
        pair_seen.add(key)
        bill_pairs.append(
            {
                "source_row": int(row["source_row"]),
                "target_row": int(nearest["source_row"]),
                "distance_z": round_float(float(np.min(distances)), 4),
                "reason": "closest cross-species neighbor in bill-length/bill-depth space",
            }
        )
    bill_pairs = sorted(bill_pairs, key=lambda d: d["distance_z"])[:8]

    singular_rows = []
    for sp in SPECIES_ORDER:
        g = complete[complete["species"] == sp].copy()
        gz = scaler.transform(g[FEATURES])
        center = gz.mean(axis=0)
        sd = gz.std(axis=0)
        sd[sd == 0] = 1
        g["singular_score"] = np.linalg.norm((gz - center) / sd, axis=1)
        singular_rows.extend(
            [
                {
                    "source_row": int(r.source_row),
                    "species": sp,
                    "score": round_float(r.singular_score, 3),
                    "reason": "within-species standardized morphology distance",
                }
                for r in g.sort_values("singular_score", ascending=False).head(3).itertuples()
            ]
        )
    singular_rows = sorted(singular_rows, key=lambda d: d["score"], reverse=True)[:8]

    points = []
    boundary_scores = dict(zip(ac["source_row"].astype(int), ac["boundary_score"]))
    leakage_rows = set(leakage_df["source_row"].astype(int).tolist())
    singular_set = {d["source_row"] for d in singular_rows}
    lens_set = set(lens_rows)
    for _, row in complete.iterrows():
        source_row = int(row["source_row"])
        points.append(
            {
                "source_row": source_row,
                "species": row["species"],
                "island": row["island"],
                "sex": clean_value(row["sex"]),
                "year": int(row["year"]),
                "pc1": round_float(row["pc1"]),
                "pc2": round_float(row["pc2"]),
                "pc3": round_float(row["pc3"]),
                "pc4": round_float(row["pc4"]),
                "mass_radius": round_float(row["mass_radius"], 2),
                "boundary_score": round_float(boundary_scores.get(source_row)),
                "is_lda_leak": source_row in leakage_rows,
                "is_lens_candidate": source_row in lens_set,
                "is_singular": source_row in singular_set,
                "loo_predicted_species": clean_value(row["loo_predicted_species"]),
                **{field: round_float(row[field], 2) for field in FEATURES},
            }
        )

    missing_rows = []
    for _, row in missing.iterrows():
        missing_rows.append(
            {
                "source_row": int(row["source_row"]),
                "species": row["species"],
                "island": row["island"],
                "sex": clean_value(row["sex"]),
                "year": int(row["year"]),
                **{field: clean_value(row[field]) for field in FEATURES},
            }
        )

    loadings = {}
    for i, pc_name in enumerate(["PC1", "PC2", "PC3", "PC4"]):
        loadings[pc_name] = {field: round_float(pca.components_[i, j], 4) for j, field in enumerate(FEATURES)}

    payload = {
        "dataset": {
            "dataset_id": "e001_palmer_penguins_morphology",
            "title": "Palmer Penguins Morphology",
            "source": "Kristen Gorman and Palmer Station LTER, 2007-2009",
            "source_path": str(DATA_PATH),
            "file_size_bytes": os.path.getsize(DATA_PATH),
            "original_rows": int(len(df)),
            "columns": list(pd.read_csv(DATA_PATH, nrows=0).columns),
            "fields_used": ["species", "island", *FEATURES, "sex", "year"],
            "complete_morphology_rows": int(len(complete)),
            "complete_morphology_and_sex_rows": int(len(complete[complete["sex"].isin(["male", "female"])])),
            "missing_morphology_rows": missing_rows,
            "sampling_strategy": "No sampling; all 344 rows are represented. PCA geometry uses the 342 rows with complete numeric morphology.",
        },
        "pca": {
            "features": FEATURES,
            "explained_variance_ratio": [round_float(v, 4) for v in pca.explained_variance_ratio_],
            "loadings": loadings,
            "means": {field: round_float(mean, 4) for field, mean in zip(FEATURES, scaler.mean_)},
            "scales": {field: round_float(scale, 4) for field, scale in zip(FEATURES, scaler.scale_)},
        },
        "points": points,
        "geometry": {
            "species_order": SPECIES_ORDER,
            "centroids": centroids,
            "hulls": hulls,
            "inner_hulls": inner_hulls,
            "vectors": vectors,
            "sex_vectors": sex_vectors,
            "boundary": {
                "pair": ["Adelie", "Chinstrap"],
                "pc_line": {
                    "a": round_float(projected_w[0], 6),
                    "b": round_float(projected_w[1], 6),
                    "c": round_float(intercept, 6),
                },
                "lens_rows": lens_rows,
            },
            "tethers": tethers + bill_pairs,
            "singular_rows": singular_rows,
        },
        "evidence": {
            "correlations": {
                "pooled_flipper_depth": {"n": int(len(complete)), "pearson_r": round_float(pooled_r, 4)},
                "within_species_flipper_depth": {
                    sp: {"n": species_counts[sp], "pearson_r": round_float(species_r[sp], 4)}
                    for sp in SPECIES_ORDER
                },
            },
            "lda_leave_one_out": {
                "errors": int(len(leakage_df)),
                "error_rows": [
                    {
                        "source_row": int(r.source_row),
                        "species": r.species,
                        "predicted_species": r.loo_predicted_species,
                        "island": r.island,
                        "sex": clean_value(r.sex),
                        "year": int(r.year),
                        **{field: round_float(getattr(r, field), 2) for field in FEATURES},
                    }
                    for r in leakage_df.itertuples()
                ],
            },
            "island_species_counts": (
                df.groupby(["island", "species"]).size().unstack(fill_value=0).reindex(columns=SPECIES_ORDER, fill_value=0).astype(int).to_dict(orient="index")
            ),
            "missing_sex_rows": int(df["sex"].isna().sum()),
        },
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH} with {len(points)} plotted rows and {len(missing_rows)} missing morphology rows")


if __name__ == "__main__":
    build()
