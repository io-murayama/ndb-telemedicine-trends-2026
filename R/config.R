#' Load YAML config and merge project defaults.

load_defaults <- function(root = project_root()) {
  path <- path_from_root("config", "defaults.yml", root = root)
  if (!file.exists(path)) {
    stop("Missing config/defaults.yml at: ", path, call. = FALSE)
  }
  if (!requireNamespace("yaml", quietly = TRUE)) {
    stop(
      "Package 'yaml' is required to load config. Install with install.packages(\"yaml\").",
      call. = FALSE
    )
  }
  cfg <- yaml::read_yaml(path)
  cfg$`.loaded_from` <- path
  cfg
}
