### Load NDB open-data xlsx into tagged long format ###
### Usage: Rscript scripts/02_load_opendata.R

source("scripts/00_setup.R")

for (f in c("codes.R", "load_xlsx.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = globalenv())
}

if (!requireNamespace("readxl", quietly = TRUE)) {
  install.packages("readxl", repos = "https://cloud.r-project.org")
}

codes_cfg <- load_procedure_codes(PROJECT_ROOT)
claims <- load_all_sex_age(PROJECT_ROOT)
claims <- tag_procedures(claims, codes_cfg)

intermediate_dir <- path_from_root("output", "intermediate", root = PROJECT_ROOT)
if (!dir.exists(intermediate_dir)) {
  dir.create(intermediate_dir, recursive = TRUE, showWarnings = FALSE)
}

out_rds <- file.path(intermediate_dir, "claims_sex_age.rds")
saveRDS(claims, out_rds)

message(sprintf(
  "[02_load_opendata] rows=%s | years=%s | saved=%s",
  nrow(claims),
  paste(sort(unique(claims$fiscal_year)), collapse = ", "),
  out_rds
))

write_run_meta(CFG, stage = "load_opendata", root = PROJECT_ROOT)
