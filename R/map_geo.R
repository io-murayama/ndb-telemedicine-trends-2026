#' Prefecture map geometry for choropleth plots.

require_sf <- function() {
  if (!requireNamespace("sf", quietly = TRUE)) {
    install.packages("sf", repos = "https://cloud.r-project.org")
  }
  invisible(TRUE)
}

load_prefecture_geo <- function(root = project_root()) {
  require_sf()
  path <- path_from_root("data", "reference", "prefectures.geojson", root = root)
  if (!file.exists(path)) {
    stop("Missing prefecture geometry file: ", path, call. = FALSE)
  }
  geo <- sf::st_read(path, quiet = TRUE)
  geo$prefecture_code <- sprintf("%02d", as.integer(geo$id))
  geo
}

order_prefectures_north_to_south <- function(df) {
  df$prefecture_code <- sprintf("%02d", as.integer(df$prefecture_code))
  df[order(as.integer(df$prefecture_code)), , drop = FALSE]
}

merge_prefecture_geo <- function(geo, per_capita_df, fiscal_year = 2024) {
  merge_prefecture_geo_scoped(geo, per_capita_df, fiscal_year = fiscal_year)
}

merge_prefecture_geo_scoped <- function(geo, df, fiscal_year = NULL) {
  if (!is.null(fiscal_year)) {
    df <- df[df$fiscal_year == fiscal_year, , drop = FALSE]
  }
  if (!"visit_scope_label" %in% names(df)) {
    df$visit_scope_label <- "合計"
  }
  df$visit_scope_label <- factor(
    df$visit_scope_label,
    levels = c("初診", "再診・外来", "合計")
  )
  df$prefecture_code <- sprintf("%02d", as.integer(df$prefecture_code))
  merged <- merge(geo, df, by = "prefecture_code", all.x = TRUE)
  merged[order(as.integer(merged$prefecture_code), merged$visit_scope_label), , drop = FALSE]
}

merge_prefecture_geo_change <- function(geo, change_df) {
  merge_prefecture_geo_scoped(geo, change_df, fiscal_year = NULL)
}
