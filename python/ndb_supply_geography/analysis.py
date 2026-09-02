"""Derived measures and exploratory tests for NDB provider-location geography."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def split_area_and_national(records: list[dict[str, object]]) -> tuple[pd.DataFrame, dict[str, object]]:
    national = next(dict(row["national"]) for row in records if "national" in row)
    areas = pd.DataFrame([row for row in records if "national" not in row])
    return areas, national


def add_prefecture_context(
    prefecture: pd.DataFrame,
    population: pd.DataFrame,
    facilities: pd.DataFrame,
) -> pd.DataFrame:
    data = prefecture.merge(population, on=["prefecture_code", "prefecture_name"], validate="many_to_one")
    data = data.merge(
        facilities.drop(columns="prefecture_name"), on="prefecture_code", validate="many_to_one"
    )
    data["online_per_100k_provider_location"] = (
        data["online_primary_count"] * 100 / data["population_known_thousand"]
    )
    data["standard_base_per_100k_provider_location"] = (
        data["standard_base_count"] * 100 / data["population_known_thousand"]
    )
    data["online_per_10000_standard_base"] = (
        data["online_primary_count"] / data["standard_base_count"] * 10000
    )
    data["clinic_per_100k"] = data["clinic_count_2023"] * 100 / data["population_known_thousand"]
    data["online_per_clinic"] = data["online_primary_count"] / data["clinic_count_2023"]
    data["online_components_complete"] = data["online_primary_missing_components"].eq(0)
    data["standard_base_components_complete"] = data["standard_base_missing_components"].eq(0)
    return data


def pooled_prefecture(prefecture: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "online_primary_count",
        "standard_base_count",
        "online_per_100k_provider_location",
        "standard_base_per_100k_provider_location",
        "online_per_10000_standard_base",
        "online_per_clinic",
    ]
    context_columns = [
        "population_known_thousand",
        "population_65plus_thousand",
        "population_75plus_thousand",
        "share_65plus",
        "share_75plus",
        "clinic_count_2023",
        "clinic_per_100k",
    ]
    pooled = prefecture.groupby(["prefecture_code", "prefecture_name"], as_index=False)[metric_columns].mean()
    context = prefecture.groupby(["prefecture_code", "prefecture_name"], as_index=False)[context_columns].first()
    pooled = pooled.merge(context, on=["prefecture_code", "prefecture_name"], validate="one_to_one")
    for column in (
        "online_per_100k_provider_location",
        "online_per_10000_standard_base",
        "online_per_clinic",
    ):
        pooled[f"{column}_rank"] = pooled[column].rank(ascending=False, method="min")
    return pooled.sort_values("online_per_100k_provider_location", ascending=False).reset_index(drop=True)


def pooled_sma(sma: pd.DataFrame) -> pd.DataFrame:
    numeric = ["online_primary_count", "standard_base_count"]
    pooled = sma.groupby(["prefecture_code", "sma_code", "area_name"], as_index=False)[numeric].mean()
    pooled["online_per_10000_standard_base"] = (
        pooled["online_primary_count"] / pooled["standard_base_count"] * 10000
    )
    component = sma.groupby(["prefecture_code", "sma_code", "area_name"], as_index=False)[
        "online_primary_missing_components"
    ].max()
    pooled = pooled.merge(component, on=["prefecture_code", "sma_code", "area_name"], validate="one_to_one")
    return pooled.sort_values("online_primary_count", ascending=False).reset_index(drop=True)


def correlation_table(prefecture: pd.DataFrame) -> pd.DataFrame:
    hypotheses = {
        "高齢化（65歳以上割合）": "share_65plus",
        "高齢化（75歳以上割合）": "share_75plus",
        "一般診療所密度": "clinic_per_100k",
        "一般診療所数": "clinic_count_2023",
    }
    outcomes = {
        "供給地人口10万人当たり主要オンライン算定回数": "online_per_100k_provider_location",
        "標準基本料1万回当たり主要オンライン算定回数": "online_per_10000_standard_base",
        "一般診療所当たり主要オンライン算定回数": "online_per_clinic",
    }
    rows = []
    pooled = pooled_prefecture(prefecture)
    frames = [
        ("3年平均", pooled),
        ("3年平均（東京都除外）", pooled.loc[pooled["prefecture_code"].ne("13")]),
        *prefecture.groupby("fiscal_year"),
    ]
    for fiscal_year, frame in frames:
        for hypothesis_label, hypothesis in hypotheses.items():
            for outcome_label, outcome in outcomes.items():
                complete = frame[[hypothesis, outcome]].dropna()
                result = spearmanr(complete[hypothesis], complete[outcome])
                rows.append(
                    {
                        "fiscal_year": fiscal_year,
                        "hypothesis": hypothesis_label,
                        "outcome": outcome_label,
                        "n_prefectures": len(complete),
                        "spearman_rho": result.statistic,
                        "p_value": result.pvalue,
                    }
                )
    return pd.DataFrame(rows)


def concentration_table(sma: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fiscal_year, frame in sma.groupby("fiscal_year"):
        total = frame["online_primary_count"].sum()
        ranked = frame.sort_values("online_primary_count", ascending=False)
        for n in (1, 5, 10, 20):
            rows.append(
                {
                    "fiscal_year": fiscal_year,
                    "top_n_sma": n,
                    "online_primary_count": ranked.head(n)["online_primary_count"].sum(),
                    "share_of_all_sma_online_primary_pct": ranked.head(n)["online_primary_count"].sum() / total * 100,
                }
            )
        complete = frame.loc[frame["online_primary_missing_components"].eq(0)]
        rows.append(
            {
                "fiscal_year": fiscal_year,
                "top_n_sma": "confirmed_zero_primary_codes",
                "online_primary_count": int(complete["online_primary_count"].eq(0).sum()),
                "share_of_all_sma_online_primary_pct": None,
            }
        )
        rows.append(
            {
                "fiscal_year": fiscal_year,
                "top_n_sma": "masked_primary_components",
                "online_primary_count": int(frame["online_primary_missing_components"].gt(0).sum()),
                "share_of_all_sma_online_primary_pct": None,
            }
        )
    return pd.DataFrame(rows)


def capture_table(national: list[dict[str, object]]) -> pd.DataFrame:
    table = pd.DataFrame(national)
    table["primary_online_capture_pct"] = (
        table["online_primary_count"] / table["online_all_codes_count"] * 100
    )
    return table.sort_values("fiscal_year").reset_index(drop=True)


def outlier_table(pooled: pd.DataFrame) -> pd.DataFrame:
    measures = [
        "online_per_100k_provider_location_rank",
        "online_per_10000_standard_base_rank",
        "online_per_clinic_rank",
    ]
    columns = [
        "prefecture_code",
        "prefecture_name",
        "online_primary_count",
        "online_per_100k_provider_location",
        "online_per_10000_standard_base",
        "online_per_clinic",
        "share_65plus",
        "clinic_per_100k",
        *measures,
    ]
    high = pooled.nsmallest(8, "online_per_100k_provider_location_rank")
    low = pooled.nlargest(8, "online_per_100k_provider_location_rank")
    output = pd.concat([high, low]).drop_duplicates("prefecture_code")
    return output.loc[:, columns].sort_values("online_per_100k_provider_location_rank")


def shimane_neighbor_comparison(prefecture: pd.DataFrame) -> pd.DataFrame:
    """Compare Shimane with its immediate western-Japan neighbors by year."""
    codes = {"31": "鳥取県", "32": "島根県", "34": "広島県", "35": "山口県"}
    values = prefecture.loc[prefecture["prefecture_code"].isin(codes)].copy()
    values = values[
        [
            "fiscal_year",
            "prefecture_code",
            "prefecture_name",
            "online_primary_count",
            "standard_base_count",
            "online_per_10000_standard_base",
            "online_per_100k_provider_location",
            "share_65plus",
            "clinic_per_100k",
        ]
    ]
    shimane_rate = values.loc[values["prefecture_code"].eq("32"), ["fiscal_year", "online_per_10000_standard_base"]]
    shimane_rate = shimane_rate.rename(columns={"online_per_10000_standard_base": "shimane_rate"})
    values = values.merge(shimane_rate, on="fiscal_year", validate="many_to_one")
    values["shimane_to_prefecture_rate_ratio"] = values["shimane_rate"] / values["online_per_10000_standard_base"]
    return values.sort_values(["fiscal_year", "prefecture_code"]).reset_index(drop=True)


def shimane_sma_concentration(sma: pd.DataFrame) -> pd.DataFrame:
    """Quantify the within-Shimane concentration in the Izumo medical area."""
    rows = []
    for fiscal_year, frame in sma.loc[sma["prefecture_code"].eq("32")].groupby("fiscal_year"):
        izumo = frame.loc[frame["sma_code"].eq("3203")].iloc[0]
        rest = frame.loc[frame["sma_code"].ne("3203")]
        rest_online = rest["online_primary_count"].sum()
        rest_base = rest["standard_base_count"].sum()
        rest_rate = rest_online / rest_base * 10000
        izumo_rate = izumo["online_primary_count"] / izumo["standard_base_count"] * 10000
        expected_at_rest_rate = izumo["standard_base_count"] * rest_rate / 10000
        rows.append(
            {
                "fiscal_year": fiscal_year,
                "izumo_online_primary_count": izumo["online_primary_count"],
                "shimane_online_primary_count": frame["online_primary_count"].sum(),
                "izumo_share_of_shimane_observed_pct": izumo["online_primary_count"]
                / frame["online_primary_count"].sum()
                * 100,
                "izumo_standard_base_count": izumo["standard_base_count"],
                "izumo_online_per_10000_standard_base": izumo_rate,
                "rest_of_shimane_online_primary_count": rest_online,
                "rest_of_shimane_standard_base_count": rest_base,
                "rest_of_shimane_online_per_10000_standard_base": rest_rate,
                "izumo_to_rest_rate_ratio": izumo_rate / rest_rate,
                "izumo_expected_at_rest_rate": expected_at_rest_rate,
                "izumo_excess_over_rest_rate": izumo["online_primary_count"] - expected_at_rest_rate,
                "izumo_missing_primary_components": izumo["online_primary_missing_components"],
                "rest_of_shimane_missing_primary_components": rest["online_primary_missing_components"].sum(),
            }
        )
    return pd.DataFrame(rows).sort_values("fiscal_year").reset_index(drop=True)


def shimane_code_composition(details: pd.DataFrame) -> pd.DataFrame:
    """Return observed initial/repeat-visit components for the Izumo medical area."""
    composition = online_code_composition_by_area(details)
    izumo = composition.loc[
        (composition["prefecture_code"].eq("32")) & (composition["sma_code"].eq("3203"))
    ].copy()
    izumo = izumo.rename(
        columns={
            "online_initial_observed_count": "initial_observed",
            "online_repeat_observed_count": "repeat_observed",
            "online_total_observed_count": "observed_total",
            "repeat_share_observed_pct": "repeat_share_of_observed_pct",
        }
    )
    izumo["initial_masked"] = izumo["initial_components_masked"]
    izumo["repeat_masked"] = izumo["repeat_components_masked"]
    return izumo[
        [
            "fiscal_year",
            "initial_observed",
            "repeat_observed",
            "initial_masked",
            "repeat_masked",
            "observed_total",
            "repeat_share_of_observed_pct",
        ]
    ].sort_values("fiscal_year").reset_index(drop=True)


def online_code_composition_by_area(details: pd.DataFrame) -> pd.DataFrame:
    """Calculate fully observed initial/repeat shares for each NDB geography."""
    expected_codes = {"111014210", "112024210", "112024710"}
    if set(details["procedure_code"].unique()) != expected_codes:
        raise ValueError("Expected exactly the three primary online-care codes")
    area_type = details["area_type"].dropna().unique()
    if len(area_type) != 1:
        raise ValueError("Procedure detail table must contain one geographic level")
    group_columns = ["fiscal_year", "prefecture_code", "area_name"]
    if area_type[0] == "secondary_medical_area":
        group_columns.insert(2, "sma_code")
    wide = details.pivot(index=group_columns, columns="procedure_code", values="count").reset_index()
    wide.columns.name = None
    wide["initial_components_masked"] = wide["111014210"].isna().astype(int)
    wide["repeat_components_masked"] = wide[["112024210", "112024710"]].isna().sum(axis=1)
    wide["online_initial_observed_count"] = wide["111014210"]
    wide["online_repeat_observed_count"] = wide[["112024210", "112024710"]].sum(axis=1, min_count=1)
    wide["online_total_observed_count"] = (
        wide["online_initial_observed_count"] + wide["online_repeat_observed_count"]
    )
    wide["online_initial_count"] = wide["111014210"]
    wide["online_repeat_count"] = wide["112024210"] + wide["112024710"]
    wide["online_total_count"] = wide["online_initial_count"] + wide["online_repeat_count"]
    wide["all_components_complete"] = wide[
        ["111014210", "112024210", "112024710"]
    ].notna().all(axis=1)
    wide["repeat_share_pct"] = np.where(
        wide["all_components_complete"] & wide["online_total_count"].gt(0),
        wide["online_repeat_count"] / wide["online_total_count"] * 100,
        np.nan,
    )
    wide["repeat_share_observed_pct"] = np.where(
        wide["online_total_observed_count"].gt(0),
        wide["online_repeat_observed_count"] / wide["online_total_observed_count"] * 100,
        np.nan,
    )
    return wide.drop(columns=["111014210", "112024210", "112024710"])


def repeat_share_benchmark(
    composition: pd.DataFrame,
    target_query: pd.Series,
    geography_label: str,
    minimum_total: float = 1000,
) -> pd.DataFrame:
    """Benchmark a target area's repeat share among comparable complete cells."""
    rows = []
    target = composition.loc[target_query].copy()
    for fiscal_year, target_row in target.groupby("fiscal_year"):
        row = target_row.iloc[0]
        comparison = composition.loc[
            (composition["fiscal_year"].eq(fiscal_year))
            & (composition["all_components_complete"])
            & (composition["online_total_count"].ge(minimum_total))
        ].copy()
        comparable = bool(row["all_components_complete"] and row["online_total_count"] >= minimum_total)
        rows.append(
            {
                "geography": geography_label,
                "fiscal_year": fiscal_year,
                "minimum_total_count": minimum_total,
                "target_repeat_share_pct": row["repeat_share_pct"],
                "target_components_complete": row["all_components_complete"],
                "n_comparison_areas": len(comparison),
                "rank_descending_repeat_share": (
                    int(comparison["repeat_share_pct"].gt(row["repeat_share_pct"]).sum()) + 1
                    if comparable
                    else np.nan
                ),
                "median_repeat_share_pct": comparison["repeat_share_pct"].median(),
                "p90_repeat_share_pct": comparison["repeat_share_pct"].quantile(0.9),
            }
        )
    return pd.DataFrame(rows).sort_values(["geography", "fiscal_year"]).reset_index(drop=True)


def shimane_context_residual(prefecture: pd.DataFrame, bootstrap_reps: int = 1000) -> pd.DataFrame:
    """Estimate how unusual Shimane is after simple measured prefectural context.

    This is a diagnostic prediction exercise, not a causal model.  It uses a
    leave-Shimane-out log-rate regression with age structure, clinic density,
    population scale, and year indicators.  Whole prefecture three-year blocks
    are resampled to give a stability interval for the predicted rate.
    """
    data = prefecture.copy()
    data["log_rate"] = np.log(data["online_per_10000_standard_base"])
    data["log_population"] = np.log(data["population_known_thousand"])
    data["log_clinic_density"] = np.log(data["clinic_per_100k"])
    target = data.loc[data["prefecture_code"].eq("32")].sort_values("fiscal_year").copy()

    def design(frame: pd.DataFrame) -> np.ndarray:
        return np.column_stack(
            [
                np.ones(len(frame)),
                frame["fiscal_year"].eq(2023).astype(float),
                frame["fiscal_year"].eq(2024).astype(float),
                frame["share_65plus"].to_numpy(),
                frame["log_clinic_density"].to_numpy(),
                frame["log_population"].to_numpy(),
            ]
        )

    rows = []
    specifications = {
        "島根以外の46都道府県": data.loc[data["prefecture_code"].ne("32")],
        "島根・東京以外の45都道府県": data.loc[~data["prefecture_code"].isin(["13", "32"])],
    }
    generator = np.random.default_rng(20260902)
    for specification, training in specifications.items():
        x_train = design(training)
        coefficients, _, _, _ = np.linalg.lstsq(x_train, training["log_rate"].to_numpy(), rcond=None)
        point_predictions = np.exp(design(target) @ coefficients)
        prefecture_blocks = {code: frame for code, frame in training.groupby("prefecture_code")}
        codes = list(prefecture_blocks)
        bootstrap_predictions = np.empty((bootstrap_reps, len(target)))
        for index in range(bootstrap_reps):
            sampled = pd.concat([prefecture_blocks[code] for code in generator.choice(codes, len(codes), replace=True)])
            sampled_coefficients, _, _, _ = np.linalg.lstsq(
                design(sampled), sampled["log_rate"].to_numpy(), rcond=None
            )
            bootstrap_predictions[index] = np.exp(design(target) @ sampled_coefficients)
        for position, (_, row) in enumerate(target.iterrows()):
            predictions = bootstrap_predictions[:, position]
            rows.append(
                {
                    "specification": specification,
                    "fiscal_year": row["fiscal_year"],
                    "observed_online_per_10000_standard_base": row["online_per_10000_standard_base"],
                    "predicted_online_per_10000_standard_base": point_predictions[position],
                    "bootstrap_predicted_p2_5": np.quantile(predictions, 0.025),
                    "bootstrap_predicted_p97_5": np.quantile(predictions, 0.975),
                    "observed_to_predicted_ratio": row["online_per_10000_standard_base"] / point_predictions[position],
                }
            )
    return pd.DataFrame(rows).sort_values(["specification", "fiscal_year"]).reset_index(drop=True)
