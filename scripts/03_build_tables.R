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
# Main figures (Fig1–4) pool 初診 + 再診・外来; model keeps visit-type cells.
cells_pooled <- pool_visit_types_cells(cells)
change <- aggregate_change_2022_2024(cells_pooled)

save_analysis_table(trend, "national_trend.csv", root = PROJECT_ROOT)
save_analysis_table(cells, "main_analysis_cells.csv", root = PROJECT_ROOT)
save_analysis_table(cells_pooled, "main_analysis_cells_pooled.csv", root = PROJECT_ROOT)
save_analysis_table(change, "change_2022_2024_by_age.csv", root = PROJECT_ROOT)

message(sprintf(
  "[03_build_tables] trend rows=%s | cell rows=%s | pooled rows=%s | change rows=%s",
  nrow(trend), nrow(cells), nrow(cells_pooled), nrow(change)
))
write_run_meta(CFG, stage = "build_tables", root = PROJECT_ROOT)
