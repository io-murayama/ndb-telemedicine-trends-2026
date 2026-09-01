#' Write small run metadata under output/logs/.

write_run_meta <- function(cfg, stage, root = project_root()) {
  ensure_output_dirs(root)
  meta <- list(
    stage = stage,
    project = cfg$project,
    ndb = cfg$ndb,
    seeds = cfg$seeds,
    timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
    r_version = paste(R.version$major, R.version$minor, sep = ".")
  )
  out <- path_from_root("output", "logs", paste0("meta_", stage, ".yml"), root = root)
  if (requireNamespace("yaml", quietly = TRUE)) {
    yaml::write_yaml(meta, out)
  } else {
    writeLines(paste0("# yaml package missing; stage=", stage), out)
  }
  invisible(out)
}
