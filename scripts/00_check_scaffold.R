### Verify scaffold layout and config load ###
### Usage:
###   Rscript scripts/00_check_scaffold.R

source_path <- local({
  args <- commandArgs(trailingOnly = FALSE)
  f <- grep("^--file=", args, value = TRUE)
  if (length(f)) {
    return(normalizePath(sub("^--file=", "", f[[1]]), winslash = "/"))
  }
  normalizePath("scripts/00_check_scaffold.R", winslash = "/", mustWork = FALSE)
})
script_dir <- dirname(source_path)
root_guess <- normalizePath(file.path(script_dir, ".."), winslash = "/", mustWork = TRUE)
setwd(root_guess)

source("scripts/00_setup.R")

required_paths <- c(
  "DESCRIPTION",
  "LICENSE",
  "README.md",
  ".gitignore",
  "config/defaults.yml",
  "R/paths.R",
  "R/config.R",
  "R/bootstrap.R",
  "scripts/00_setup.R",
  "scripts/00_check_scaffold.R",
  "scripts/bootstrap.sh",
  "data/.gitkeep",
  "data/raw/.gitkeep",
  "output/.gitkeep",
  "output/logs/.gitkeep"
)

missing <- required_paths[!vapply(required_paths, function(p) {
  file.exists(file.path(PROJECT_ROOT, p))
}, logical(1))]

if (length(missing)) {
  stop("Missing scaffold files:\n  - ", paste(missing, collapse = "\n  - "), call. = FALSE)
}

cfg <- load_defaults(PROJECT_ROOT)

stopifnot(
  is.list(cfg$project),
  is.list(cfg$ndb),
  identical(cfg$ndb$procedure_code, "112023210")
)

ensure_output_dirs(PROJECT_ROOT)
write_run_meta(cfg, stage = "scaffold_check", root = PROJECT_ROOT)

message("[00_check_scaffold] OK")
message(sprintf(
  "[00_check_scaffold] project=%s | procedure=%s",
  cfg$project$name,
  cfg$ndb$procedure_name
))
message("[00_check_scaffold] meta: output/logs/meta_scaffold_check.yml")
