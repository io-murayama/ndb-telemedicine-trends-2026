### Build SAP analysis tables from intermediate claims data ###
### Usage: Rscript scripts/03_build_tables.R

source("scripts/00_setup.R")

for (f in c("codes.R", "aggregate.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = environment())
}

claims_path <- path_from_root("output", "intermediate", "claims_sex_age.rds", root = PROJECT_ROOT)
if (!file.exists(claims_path)) {
  stop("Run scripts/02_load_opendata.R first. Missing: ", claims_path, call. = FALSE)
}

codes_cfg <- load_procedure_codes(PROJECT_ROOT)
claims <- readRDS(claims_path)

trend <- aggregate_national_trend(claims)
cells <- aggregate_main_cells(claims, codes_cfg)

save_analysis_table(trend, "national_trend.csv", root = PROJECT_ROOT)
save_analysis_table(cells, "main_analysis_cells.csv", root = PROJECT_ROOT)

message(sprintf("[03_build_tables] trend rows=%s | cell rows=%s", nrow(trend), nrow(cells)))
write_run_meta(CFG, stage = "build_tables", root = PROJECT_ROOT)
