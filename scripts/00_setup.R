### Scaffold entry: project root helpers + defaults ###
### Usage (from anywhere under the repo):
###   Rscript scripts/00_setup.R
###   source("scripts/00_setup.R")  # if getwd() is project root

find_project_root <- function(start = getwd()) {
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
  stop("Could not locate project root from: ", start, call. = FALSE)
}

ROOT <- find_project_root()
setwd(ROOT)

sys.source(file.path(ROOT, "R", "paths.R"), envir = environment())
sys.source(file.path(ROOT, "R", "config.R"), envir = environment())
sys.source(file.path(ROOT, "R", "bootstrap.R"), envir = environment())

for (nm in c(
  "project_root", "path_from_root", "ensure_output_dirs",
  "load_defaults", "write_run_meta"
)) {
  if (exists(nm, inherits = FALSE)) {
    assign(nm, get(nm, inherits = FALSE), envir = globalenv())
  }
}
assign("PROJECT_ROOT", ROOT, envir = globalenv())

CFG <- load_defaults(ROOT)
ensure_output_dirs(ROOT)

message(sprintf(
  "[00_setup] root=%s | procedure=%s (%s) | data=%s | output=%s",
  ROOT,
  CFG$ndb$procedure_code,
  CFG$ndb$procedure_name,
  CFG$paths$data,
  CFG$paths$output
))

if (!interactive() && identical(sys.nframe(), 0L)) {
  write_run_meta(CFG, stage = "setup", root = ROOT)
  message("[00_setup] wrote output/logs/meta_setup.yml")
}
