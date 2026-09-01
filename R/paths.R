#' Project root detection and path helpers.
#'
#' Root is the directory containing DESCRIPTION (preferred) or
#' ndb-telemedicine-trends-2026.Rproj.

project_root <- function(start = getwd()) {
  cur <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in seq_len(16L)) {
    if (file.exists(file.path(cur, "DESCRIPTION")) ||
        file.exists(file.path(cur, "ndb-telemedicine-trends-2026.Rproj"))) {
      return(cur)
    }
    parent <- dirname(cur)
    if (identical(parent, cur)) break
    cur <- parent
  }
  stop(
    "Could not find project root from: ", start,
    "\nExpected DESCRIPTION or ndb-telemedicine-trends-2026.Rproj upward.",
    call. = FALSE
  )
}

path_from_root <- function(..., root = project_root()) {
  file.path(root, ...)
}

ensure_output_dirs <- function(root = project_root()) {
  dirs <- c(
    path_from_root("data", root = root),
    path_from_root("data", "raw", root = root),
    path_from_root("output", root = root),
    path_from_root("output", "logs", root = root)
  )
  for (d in dirs) {
    if (!dir.exists(d)) dir.create(d, recursive = TRUE, showWarnings = FALSE)
  }
  invisible(dirs)
}
