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
  df <- per_capita_df[per_capita_df$fiscal_year == fiscal_year, , drop = FALSE]
  df$prefecture_code <- sprintf("%02d", as.integer(df$prefecture_code))
  merged <- merge(geo, df, by = "prefecture_code", all.x = TRUE)
  merged[order(as.integer(merged$prefecture_code)), , drop = FALSE]
}
