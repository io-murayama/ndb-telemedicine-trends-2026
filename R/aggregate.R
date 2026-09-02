#' Build SAP analysis tables from tagged procedure-level data.

aggregate_national_trend <- function(df) {
  pieces <- list()

  legacy <- df[df$era == "legacy", , drop = FALSE]
  if (nrow(legacy) > 0L) {
    online <- aggregate(
      count ~ fiscal_year,
      data = legacy[legacy$visit_type == "online_legacy", , drop = FALSE],
      FUN = function(x) sum(x, na.rm = TRUE)
    )
    names(online)[2] <- "online_count"

    denom <- aggregate(
      count ~ fiscal_year,
      data = legacy[legacy$visit_type %in% c("initial", "followup", "outpatient"), , drop = FALSE],
      FUN = function(x) sum(x, na.rm = TRUE)
    )
    names(denom)[2] <- "denominator_count"

    merged <- merge(online, denom, by = "fiscal_year", all = TRUE)
    merged$era <- "legacy"
    merged$visit_type <- "all_outpatient"
    merged$proportion <- merged$online_count / merged$denominator_count
    pieces$legacy <- merged
  }

  ict <- df[df$era == "ict", , drop = FALSE]
  if (nrow(ict) > 0L) {
    for (vt in c("initial", "followup")) {
      if (vt == "initial") {
        scope <- ict[ict$visit_type == "initial", , drop = FALSE]
      } else {
        scope <- ict[ict$visit_type %in% c("followup", "outpatient"), , drop = FALSE]
      }

      online <- aggregate(
        count ~ fiscal_year,
        data = scope[scope$is_online, , drop = FALSE],
        FUN = function(x) sum(x, na.rm = TRUE)
      )
      names(online)[2] <- "online_count"

      denom <- aggregate(
        count ~ fiscal_year,
        data = scope,
        FUN = function(x) sum(x, na.rm = TRUE)
      )
      names(denom)[2] <- "denominator_count"

      merged <- merge(online, denom, by = "fiscal_year", all = TRUE)
      merged$era <- "ict"
      merged$visit_type <- vt
      merged$proportion <- merged$online_count / merged$denominator_count
      pieces[[paste0("ict_", vt)]] <- merged
    }
  }

  do.call(rbind, pieces)
}

aggregate_main_cells <- function(df, codes_cfg) {
  ict <- df[df$era == "ict", , drop = FALSE]
  main_years <- codes_cfg$eras$ict$fiscal_years
  ict <- ict[ict$fiscal_year %in% main_years, , drop = FALSE]

  build_cells <- function(vt) {
    if (vt == "initial") {
      scope <- ict[ict$visit_type == "initial", , drop = FALSE]
    } else {
      scope <- ict[ict$visit_type %in% c("followup", "outpatient"), , drop = FALSE]
    }

    online <- aggregate(
      count ~ fiscal_year + sex + age_group,
      data = scope[scope$is_online, , drop = FALSE],
      FUN = function(x) sum(x, na.rm = TRUE)
    )
    names(online)[4] <- "online_count"

    denom <- aggregate(
      count ~ fiscal_year + sex + age_group,
      data = scope,
      FUN = function(x) sum(x, na.rm = TRUE)
    )
    names(denom)[4] <- "denominator_count"

    merged <- merge(online, denom, by = c("fiscal_year", "sex", "age_group"), all = TRUE)
    merged$visit_type <- vt
    merged$online_count[is.na(merged$online_count)] <- 0
    merged$proportion <- merged$online_count / merged$denominator_count
    merged
  }

  rbind(build_cells("initial"), build_cells("followup"))
}

aggregate_cells_by_age <- function(cells) {
  online <- aggregate(
    online_count ~ fiscal_year + age_group + visit_type,
    data = cells,
    FUN = function(x) sum(x, na.rm = TRUE)
  )
  denom <- aggregate(
    denominator_count ~ fiscal_year + age_group + visit_type,
    data = cells,
    FUN = function(x) sum(x, na.rm = TRUE)
  )
  merged <- merge(online, denom, by = c("fiscal_year", "age_group", "visit_type"), all = TRUE)
  merged$proportion <- merged$online_count / merged$denominator_count
  merged
}

aggregate_cells_by_sex <- function(cells) {
  online <- aggregate(
    online_count ~ fiscal_year + sex + visit_type,
    data = cells,
    FUN = function(x) sum(x, na.rm = TRUE)
  )
  denom <- aggregate(
    denominator_count ~ fiscal_year + sex + visit_type,
    data = cells,
    FUN = function(x) sum(x, na.rm = TRUE)
  )
  merged <- merge(online, denom, by = c("fiscal_year", "sex", "visit_type"), all = TRUE)
  merged$proportion <- merged$online_count / merged$denominator_count
  merged
}

aggregate_change_2022_2024 <- function(cells, baseline_year = 2022, end_year = 2024) {
  age_cells <- aggregate_cells_by_age(cells)
  wide <- reshape(
    age_cells,
    idvar = c("age_group", "visit_type"),
    timevar = "fiscal_year",
    direction = "wide"
  )

  prop_base <- paste0("proportion.", baseline_year)
  prop_end <- paste0("proportion.", end_year)
  if (!all(c(prop_base, prop_end) %in% names(wide))) {
    stop("Missing fiscal years for change calculation: ", baseline_year, ", ", end_year, call. = FALSE)
  }

  wide$proportion_baseline <- wide[[prop_base]]
  wide$proportion_end <- wide[[prop_end]]
  wide$abs_change_pp <- (wide$proportion_end - wide$proportion_baseline) * 100
  wide$relative_change_pct <- ifelse(
    is.na(wide$proportion_baseline) | wide$proportion_baseline <= 0,
    NA_real_,
    (wide$proportion_end / wide$proportion_baseline - 1) * 100
  )
  wide$baseline_year <- baseline_year
  wide$end_year <- end_year
  wide
}

save_analysis_table <- function(df, filename, root = project_root()) {
  out_dir <- path_from_root("output", "tables", root = root)
  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }
  out_path <- file.path(out_dir, filename)
  utils::write.csv(df, out_path, row.names = FALSE, fileEncoding = "UTF-8")
  message("[save] ", out_path)
  invisible(out_path)
}
