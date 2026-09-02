#' Prefecture-level per-capita ICT utilization (SAP secondary analysis).

safe_sum_counts <- function(x) {
  if (length(x) == 0L || all(is.na(x))) {
    return(NA_real_)
  }
  if (any(is.na(x))) {
    return(NA_real_)
  }
  sum(x)
}

aggregate_prefecture_online <- function(cross_df) {
  online <- cross_df[cross_df$metric_type %in% c("online_initial", "online_followup", "online_outpatient"), , drop = FALSE]
  aggregate(
    count ~ fiscal_year + prefecture_code + prefecture_name,
    data = online,
    FUN = safe_sum_counts
  )
}

prepare_per_capita_table <- function(cross_df, pop_df, per = 100000) {
  online <- aggregate_prefecture_online(cross_df)
  names(online)[ncol(online)] <- "online_count"

  merged <- merge(
    online,
    pop_df[, c("prefecture_code", "prefecture_name", "fiscal_year", "population"), drop = FALSE],
    by = c("prefecture_code", "prefecture_name", "fiscal_year"),
    all.x = TRUE
  )

  merged$rate_per_population <- ifelse(
    is.na(merged$online_count) | is.na(merged$population) | merged$population <= 0,
    NA_real_,
    merged$online_count / merged$population * per
  )
  merged$rate_per_population_pct <- merged$rate_per_population / 1000
  merged$rate_denominator_label <- paste0("per ", format(per, big.mark = ","))
  merged
}

save_per_capita_table <- function(df, filename = "prefecture_per_capita.csv", root = project_root()) {
  out_dir <- path_from_root("output", "tables", root = root)
  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }
  out_path <- file.path(out_dir, filename)
  utils::write.csv(df, out_path, row.names = FALSE, fileEncoding = "UTF-8")
  message("[save] ", out_path)
  invisible(out_path)
}

aggregate_prefecture_change_2022_2024 <- function(per_capita_df, baseline_year = 2022, end_year = 2024) {
  base <- per_capita_df[per_capita_df$fiscal_year == baseline_year, , drop = FALSE]
  end <- per_capita_df[per_capita_df$fiscal_year == end_year, , drop = FALSE]
  if (nrow(base) == 0L || nrow(end) == 0L) {
    stop(
      "Missing fiscal years for prefecture change calculation: ",
      baseline_year,
      ", ",
      end_year,
      call. = FALSE
    )
  }

  rate_base <- paste0("rate_per_population.", baseline_year)
  rate_end <- paste0("rate_per_population.", end_year)
  merged <- merge(
    base[, c("prefecture_code", "prefecture_name", "rate_per_population", "online_count", "population"), drop = FALSE],
    end[, c("prefecture_code", "rate_per_population", "online_count", "population"), drop = FALSE],
    by = "prefecture_code",
    suffixes = c(paste0(".", baseline_year), paste0(".", end_year))
  )

  merged$rate_baseline <- merged[[rate_base]]
  merged$rate_end <- merged[[rate_end]]
  merged$abs_change <- merged$rate_end - merged$rate_baseline
  merged$relative_change_pct <- ifelse(
    is.na(merged$rate_baseline) | merged$rate_baseline <= 0,
    NA_real_,
    (merged$rate_end / merged$rate_baseline - 1) * 100
  )
  merged$baseline_year <- baseline_year
  merged$end_year <- end_year
  order_prefectures_north_to_south(merged)
}
