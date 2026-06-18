from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


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


DATA_PATH = cache_file("e002_nyc_yellow_taxi_2024_01.parquet")
LOOKUP_PATH = cache_file("taxi_zone_lookup.csv")
OUT_PATH = RUN_DIR / "app" / "data" / "pulse_payload.json"

AIRPORT_IDS = {1: "EWR", 132: "JFK", 138: "LGA"}
PERIOD_ORDER = ["late_night", "dawn", "morning_peak", "midday", "evening_peak", "night"]
PERIOD_LABELS = {
    "late_night": "00-05",
    "dawn": "06",
    "morning_peak": "07-09",
    "midday": "10-15",
    "evening_peak": "16-19",
    "night": "20-23",
}


def period_from_hour(hour: pd.Series) -> pd.Series:
    h = hour.astype("int16")
    return pd.Series(
        np.select(
            [
                h.between(0, 5),
                h.eq(6),
                h.between(7, 9),
                h.between(10, 15),
                h.between(16, 19),
                h.between(20, 23),
            ],
            PERIOD_ORDER,
            default="unknown",
        ),
        index=hour.index,
    )


def df_records(df: pd.DataFrame) -> list[dict]:
    clean = df.replace([np.inf, -np.inf], np.nan)
    clean = clean.astype(object).where(pd.notnull(clean), None)
    return clean.to_dict(orient="records")


def json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (np.ndarray,)):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def quantile_summary(grouped: pd.core.groupby.DataFrameGroupBy, metric: str) -> pd.DataFrame:
    qs = grouped[metric].quantile([0.25, 0.5, 0.75]).unstack()
    qs.columns = [f"{metric}_q25", f"{metric}_median", f"{metric}_q75"]
    return qs


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    parquet = pq.ParquetFile(DATA_PATH)
    original_rows = parquet.metadata.num_rows
    original_fields = parquet.schema.names

    columns = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "RatecodeID",
        "PULocationID",
        "DOLocationID",
        "payment_type",
        "fare_amount",
        "tip_amount",
        "tolls_amount",
        "total_amount",
        "Airport_fee",
    ]
    df = pd.read_parquet(DATA_PATH, columns=columns)
    lookup = pd.read_csv(LOOKUP_PATH)
    lookup_by_id = lookup.set_index("LocationID")

    for prefix, loc_col in [("PU", "PULocationID"), ("DO", "DOLocationID")]:
        df[f"{prefix}_borough"] = df[loc_col].map(lookup_by_id["Borough"])
        df[f"{prefix}_zone"] = df[loc_col].map(lookup_by_id["Zone"])
        df[f"{prefix}_service_zone"] = df[loc_col].map(lookup_by_id["service_zone"])
        df[f"{prefix}_region"] = df[f"{prefix}_borough"].fillna("Unresolved")
        for loc_id, airport in AIRPORT_IDS.items():
            df.loc[df[loc_col].eq(loc_id), f"{prefix}_region"] = airport

    pickup = pd.to_datetime(df["tpep_pickup_datetime"])
    dropoff = pd.to_datetime(df["tpep_dropoff_datetime"])
    df["duration_min"] = (dropoff - pickup).dt.total_seconds() / 60.0
    df["pickup_hour"] = pickup.dt.hour.astype("int16")
    df["pickup_date"] = pickup.dt.date.astype("string")
    df["day_type"] = np.where(pickup.dt.dayofweek < 5, "weekday", "weekend")
    df["period"] = period_from_hour(df["pickup_hour"])

    pu_airport = df["PULocationID"].isin(AIRPORT_IDS)
    do_airport = df["DOLocationID"].isin(AIRPORT_IDS)
    df["airport_role"] = np.select(
        [
            pu_airport & ~do_airport,
            ~pu_airport & do_airport,
            pu_airport & do_airport,
        ],
        ["from_airport", "to_airport", "airport_between"],
        default="city_internal",
    )

    jan_mask = pickup.ge(pd.Timestamp("2024-01-01")) & pickup.lt(pd.Timestamp("2024-02-01"))
    resolved_mask = df["PU_borough"].notna() & df["DO_borough"].notna()
    valid_mask = (
        jan_mask
        & resolved_mask
        & df["duration_min"].between(1, 180, inclusive="both")
        & df["trip_distance"].between(0.01, 100, inclusive="both")
        & df["fare_amount"].gt(0)
        & df["total_amount"].gt(0)
    )

    valid = df.loc[valid_mask].copy()
    valid["speed_mph"] = valid["trip_distance"] / (valid["duration_min"] / 60.0)
    valid["fare_per_mile"] = valid["fare_amount"] / valid["trip_distance"]
    valid["tip_rate_fare"] = np.where(
        (valid["payment_type"].eq(1)) & valid["fare_amount"].gt(0),
        valid["tip_amount"] / valid["fare_amount"],
        np.nan,
    )
    valid["credit_trip"] = valid["payment_type"].eq(1).astype("int8")
    valid["cash_trip"] = valid["payment_type"].eq(2).astype("int8")

    flow_keys = ["day_type", "period", "airport_role", "PU_region", "DO_region"]
    flows = (
        valid.groupby(flow_keys, observed=True)
        .agg(
            trips=("trip_distance", "size"),
            distance_median=("trip_distance", "median"),
            duration_median=("duration_min", "median"),
            fare_median=("fare_amount", "median"),
            total_median=("total_amount", "median"),
            speed_median=("speed_mph", "median"),
            fare_per_mile_median=("fare_per_mile", "median"),
            credit_trips=("credit_trip", "sum"),
            cash_trips=("cash_trip", "sum"),
            credit_tip_rate_mean=("tip_rate_fare", "mean"),
            credit_tip_rate_median=("tip_rate_fare", "median"),
        )
        .reset_index()
    )
    flows = flows[flows["trips"].ge(10)].copy()
    flows["period_order"] = flows["period"].map({p: i for i, p in enumerate(PERIOD_ORDER)})
    flows["corridor_id"] = (
        flows["PU_region"].astype(str)
        + "->"
        + flows["DO_region"].astype(str)
        + "|"
        + flows["airport_role"].astype(str)
    )

    hour_day_counts = (
        valid.groupby(["pickup_date", "day_type", "pickup_hour"], observed=True)
        .size()
        .reset_index(name="trips")
    )
    hourly_overall = (
        hour_day_counts.groupby(["day_type", "pickup_hour"], observed=True)
        .agg(avg_trips_per_day=("trips", "mean"), active_days=("pickup_date", "nunique"))
        .reset_index()
    )

    hourly_corridors = (
        valid.groupby(["day_type", "pickup_hour", "airport_role", "PU_region", "DO_region"], observed=True)
        .size()
        .reset_index(name="trips")
    )
    hourly_corridors = hourly_corridors.merge(
        flows[["day_type", "airport_role", "PU_region", "DO_region"]].drop_duplicates(),
        on=["day_type", "airport_role", "PU_region", "DO_region"],
        how="inner",
    )

    top_zone_pairs = (
        valid.groupby(flow_keys + ["PULocationID", "DOLocationID", "PU_zone", "DO_zone"], observed=True)
        .size()
        .reset_index(name="trips")
        .sort_values(flow_keys + ["trips"], ascending=[True, True, True, True, True, False])
    )
    top_zone_pairs = top_zone_pairs.groupby(flow_keys, observed=True).head(3).reset_index(drop=True)

    regime_keys = ["day_type", "period", "airport_role"]
    regime_grouped = valid.groupby(regime_keys, observed=True)
    regime_base = regime_grouped.agg(trips=("trip_distance", "size")).reset_index()
    summaries = [regime_base.set_index(regime_keys)]
    for metric in ["trip_distance", "duration_min", "fare_per_mile", "speed_mph", "tip_rate_fare"]:
        summaries.append(quantile_summary(regime_grouped, metric))
    regime_baselines = pd.concat(summaries, axis=1).reset_index()
    regime_baselines["period_order"] = regime_baselines["period"].map({p: i for i, p in enumerate(PERIOD_ORDER)})

    anomaly_flags = {
        "outside_january": ~jan_mask,
        "nonpositive_duration": df["duration_min"].le(0),
        "long_duration_gt_180": df["duration_min"].gt(180),
        "zero_distance": df["trip_distance"].eq(0),
        "extreme_distance_gt_100": df["trip_distance"].gt(100),
        "negative_fare": df["fare_amount"].lt(0),
        "negative_total": df["total_amount"].lt(0),
        "negative_tip": df["tip_amount"].lt(0),
        "unresolved_zone": ~resolved_mask,
        "no_charge_payment": df["payment_type"].eq(3),
        "dispute_payment": df["payment_type"].eq(4),
        "provider_payment_0": df["payment_type"].eq(0),
    }
    anomaly_any = np.logical_or.reduce([flag.to_numpy() for flag in anomaly_flags.values()])
    anomaly_index = df.index[anomaly_any]
    anomaly_df = df.loc[anomaly_index].copy()

    flag_frame = pd.DataFrame({name: flag.loc[anomaly_index].to_numpy() for name, flag in anomaly_flags.items()})
    anomaly_for_melt = pd.concat(
        [
            anomaly_df[["day_type", "period", "airport_role", "PU_region", "DO_region"]].reset_index(drop=True),
            flag_frame.reset_index(drop=True),
        ],
        axis=1,
    )
    anomaly_groups = anomaly_for_melt.melt(
        id_vars=["day_type", "period", "airport_role", "PU_region", "DO_region"],
        var_name="anomaly_class",
        value_name="present",
    )
    anomaly_groups = (
        anomaly_groups[anomaly_groups["present"]]
        .groupby(["day_type", "period", "airport_role", "PU_region", "DO_region", "anomaly_class"], observed=True)
        .size()
        .reset_index(name="excluded_rows")
    )
    anomaly_groups["period_order"] = anomaly_groups["period"].map({p: i for i, p in enumerate(PERIOD_ORDER)})

    sample_frames = []
    sample_columns = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "PU_region",
        "DO_region",
        "PU_zone",
        "DO_zone",
        "day_type",
        "period",
        "airport_role",
        "trip_distance",
        "duration_min",
        "fare_amount",
        "tip_amount",
        "total_amount",
        "payment_type",
        "passenger_count",
        "RatecodeID",
        "Airport_fee",
    ]
    for klass, flag in anomaly_flags.items():
        sub = df.loc[flag, sample_columns].copy()
        if sub.empty:
            continue
        sub["anomaly_class"] = klass
        if klass == "extreme_distance_gt_100":
            sub = sub.sort_values("trip_distance", ascending=False)
        elif klass in {"negative_fare", "negative_total", "negative_tip"}:
            sort_col = {"negative_fare": "fare_amount", "negative_total": "total_amount", "negative_tip": "tip_amount"}[klass]
            sub = sub.sort_values(sort_col, ascending=True)
        elif klass in {"long_duration_gt_180", "nonpositive_duration"}:
            sub = sub.assign(abs_duration=sub["duration_min"].abs()).sort_values("abs_duration", ascending=False).drop(columns="abs_duration")
        else:
            sub = sub.sort_values(["period", "PU_region", "DO_region"])
        sample_frames.append(sub.head(55))
    anomaly_samples = pd.concat(sample_frames, ignore_index=True).drop_duplicates(
        subset=["tpep_pickup_datetime", "PULocationID", "DOLocationID", "trip_distance", "fare_amount", "total_amount", "anomaly_class"]
    )

    valid_counts = {
        "original_rows": int(original_rows),
        "column_count": int(len(original_fields)),
        "valid_core_rows": int(valid_mask.sum()),
        "valid_core_share": round(float(valid_mask.mean()), 5),
        "outside_january_rows": int((~jan_mask).sum()),
        "zero_distance_rows": int(df["trip_distance"].eq(0).sum()),
        "negative_fare_rows": int(df["fare_amount"].lt(0).sum()),
        "negative_total_rows": int(df["total_amount"].lt(0).sum()),
        "duration_gt_180_rows": int(df["duration_min"].gt(180).sum()),
        "distance_gt_100_rows": int(df["trip_distance"].gt(100).sum()),
        "unresolved_zone_rows": int((~resolved_mask).sum()),
    }

    regions = [
        {"id": "Manhattan", "kind": "borough", "x": 0.50, "y": 0.43, "label": "Manhattan"},
        {"id": "Brooklyn", "kind": "borough", "x": 0.37, "y": 0.70, "label": "Brooklyn"},
        {"id": "Queens", "kind": "borough", "x": 0.70, "y": 0.58, "label": "Queens"},
        {"id": "Bronx", "kind": "borough", "x": 0.54, "y": 0.18, "label": "Bronx"},
        {"id": "Staten Island", "kind": "borough", "x": 0.19, "y": 0.82, "label": "Staten Island"},
        {"id": "JFK", "kind": "airport", "x": 0.86, "y": 0.79, "label": "JFK"},
        {"id": "LGA", "kind": "airport", "x": 0.82, "y": 0.29, "label": "LGA"},
        {"id": "EWR", "kind": "airport", "x": 0.14, "y": 0.49, "label": "EWR"},
        {"id": "Unknown", "kind": "unresolved", "x": 0.07, "y": 0.17, "label": "Unknown"},
        {"id": "Unresolved", "kind": "unresolved", "x": 0.07, "y": 0.14, "label": "Unresolved"},
    ]

    payload = {
        "metadata": {
            "dataset_id": "e002_nyc_yellow_taxi_2024_01",
            "title": "NYC Yellow Taxi January 2024",
            "source": "NYC Taxi & Limousine Commission yellow taxi trip records, January 2024",
            "data_path": str(DATA_PATH),
            "zone_lookup_path": str(LOOKUP_PATH),
            "data_size_mb": round(DATA_PATH.stat().st_size / (1024 * 1024), 3),
            "zone_lookup_size_kb": round(LOOKUP_PATH.stat().st_size / 1024, 3),
            "fields_used": columns
            + [
                "PU_borough",
                "PU_zone",
                "DO_borough",
                "DO_zone",
                "duration_min",
                "pickup_hour",
                "day_type",
                "period",
                "airport_role",
                "tip_rate_fare",
                "speed_mph",
                "fare_per_mile",
            ],
            "valid_core_filter": "pickup in January 2024; 1 <= duration_min <= 180; 0.01 <= trip_distance <= 100; fare_amount > 0; total_amount > 0; pickup/dropoff zone IDs resolve in taxi_zone_lookup.csv",
            "browser_payload_strategy": "Full parquet was read locally; browser payload contains measured OD/hour/regime/anomaly aggregates plus deterministic sampled real anomaly rows, not synthetic data.",
            "sampling_strategy": "No sampling for aggregate counts or medians. Raw record trace is a deterministic evidence sample from measured anomaly rows, capped per anomaly class for browser size.",
            "counts": valid_counts,
            "periods": [{"id": p, "label": PERIOD_LABELS[p]} for p in PERIOD_ORDER],
            "airport_zone_ids": AIRPORT_IDS,
        },
        "regions": regions,
        "flows": df_records(flows.round(5)),
        "hourly_overall": df_records(hourly_overall.round(5)),
        "hourly_corridors": df_records(hourly_corridors),
        "regime_baselines": df_records(regime_baselines.round(5)),
        "top_zone_pairs": df_records(top_zone_pairs),
        "anomaly_groups": df_records(anomaly_groups),
        "anomaly_samples": df_records(anomaly_samples.round(5)),
    }

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, allow_nan=False, default=json_default, separators=(",", ":"))

    print(
        json.dumps(
            {
                "wrote": str(OUT_PATH),
                "flows": len(payload["flows"]),
                "hourly_corridors": len(payload["hourly_corridors"]),
                "anomaly_groups": len(payload["anomaly_groups"]),
                "anomaly_samples": len(payload["anomaly_samples"]),
                "valid_core_rows": valid_counts["valid_core_rows"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
