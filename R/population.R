#' Prefecture population reference data for per-capita rates.

load_prefecture_population <- function(root = project_root()) {
  path <- path_from_root("data", "reference", "prefecture_population.csv", root = root)
  if (!file.exists(path)) {
    stop(
      "Missing population reference file: ", path,
      "\nPlace 総務省統計局 人口推計（都道府県別総人口）を data/reference/prefecture_population.csv に配置してください。",
      call. = FALSE
    )
  }
  df <- utils::read.csv(path, fileEncoding = "UTF-8", stringsAsFactors = FALSE)
  required <- c("prefecture_code", "prefecture_name", "fiscal_year", "population")
  missing <- setdiff(required, names(df))
  if (length(missing) > 0L) {
    stop("prefecture_population.csv is missing columns: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  df$prefecture_code <- sprintf("%02d", as.integer(df$prefecture_code))
  df
}

population_for_years <- function(pop_df, fiscal_years) {
  pop_df[pop_df$fiscal_year %in% fiscal_years, , drop = FALSE]
}
