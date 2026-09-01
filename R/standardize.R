#' Direct age-sex standardization by prefecture (SAP secondary analysis).

impute_zero <- function(x) {
  ifelse(is.na(x), 0, x)
}

aggregate_cross_strata <- function(cross_df) {
  metric_types <- unique(cross_df$metric_type)

  sum_metric <- function(types) {
    subset <- cross_df[cross_df$metric_type %in% types, , drop = FALSE]
    aggregate(
      count ~ fiscal_year + prefecture_code + prefecture_name + sex + age_group,
      data = subset,
      FUN = function(x) sum(impute_zero(x), na.rm = TRUE)
    )
  }

  numer <- sum_metric(c("online_initial", "online_followup", "online_outpatient"))
  names(numer)[ncol(numer)] <- "online_count"

  denom <- sum_metric(c("denom_initial", "denom_followup", "denom_outpatient"))
  names(denom)[ncol(denom)] <- "denominator_count"

  merged <- merge(
    numer,
    denom,
    by = c("fiscal_year", "prefecture_code", "prefecture_name", "sex", "age_group"),
    all = TRUE
  )
  merged$online_count <- impute_zero(merged$online_count)
  merged$denominator_count <- impute_zero(merged$denominator_count)
  merged$stratum_rate <- ifelse(
    merged$denominator_count > 0,
    merged$online_count / merged$denominator_count,
    NA_real_
  )
  merged
}

build_standard_weights <- function(strata, reference_years) {
  ref <- strata[strata$fiscal_year %in% reference_years, , drop = FALSE]
  weights <- aggregate(
    denominator_count ~ sex + age_group,
    data = ref,
    FUN = function(x) sum(x, na.rm = TRUE)
  )
  names(weights)[3] <- "weight"
  weights$weight <- weights$weight / sum(weights$weight)
  weights
}

standardize_by_prefecture <- function(strata, weights) {
  merged <- merge(strata, weights, by = c("sex", "age_group"), all.x = TRUE)
  merged <- merged[!is.na(merged$stratum_rate) & merged$denominator_count > 0, , drop = FALSE]

  aggregate(
    cbind(weighted_rate = merged$stratum_rate * merged$weight) ~ fiscal_year + prefecture_code + prefecture_name,
    data = merged,
    FUN = function(x) sum(x, na.rm = TRUE)
  )
}

prepare_standardized_table <- function(cross_df, reference_years = c(2022, 2023, 2024)) {
  strata <- aggregate_cross_strata(cross_df)
  weights <- build_standard_weights(strata, reference_years)
  std <- standardize_by_prefecture(strata, weights)
  names(std)[ncol(std)] <- "standardized_proportion"
  std$standardized_proportion_pct <- std$standardized_proportion * 100
  std
}

save_standardized_table <- function(df, filename = "prefecture_standardized.csv", root = project_root()) {
  out_dir <- path_from_root("output", "tables", root = root)
  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }
  out_path <- file.path(out_dir, filename)
  utils::write.csv(df, out_path, row.names = FALSE, fileEncoding = "UTF-8")
  message("[save] ", out_path)
  invisible(out_path)
}
