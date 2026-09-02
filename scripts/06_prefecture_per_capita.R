### Prefecture-level per-capita ICT rates (SAP secondary) ###
### Usage: Rscript scripts/06_prefecture_per_capita.R

source("scripts/00_setup.R")

for (f in c("codes.R", "load_xlsx.R", "population.R", "per_capita.R", "figures.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = globalenv())
}

if (!requireNamespace("readxl", quietly = TRUE)) {
  install.packages("readxl", repos = "https://cloud.r-project.org")
}

codes_cfg <- load_procedure_codes(PROJECT_ROOT)
reference_years <- codes_cfg$eras$ict$fiscal_years

cross <- load_cross_prefecture_sex_age(fiscal_years = reference_years, root = PROJECT_ROOT)
pop <- population_for_years(load_prefecture_population(PROJECT_ROOT), reference_years)
per_capita <- prepare_per_capita_table(cross, pop, per = 100000)

intermediate_dir <- path_from_root("output", "intermediate", root = PROJECT_ROOT)
if (!dir.exists(intermediate_dir)) {
  dir.create(intermediate_dir, recursive = TRUE, showWarnings = FALSE)
}
saveRDS(cross, file.path(intermediate_dir, "cross_prefecture_sex_age.rds"))
saveRDS(per_capita, file.path(intermediate_dir, "prefecture_per_capita.rds"))

save_per_capita_table(per_capita, root = PROJECT_ROOT)

for (yr in reference_years) {
  fig <- plot_supplementary_prefecture_per_capita(per_capita, fiscal_year = yr)
  save_figure(
    fig,
    paste0("supplementary_prefecture_per_capita_", yr, ".png"),
    root = PROJECT_ROOT,
    width = 8,
    height = 12
  )
}

pooled <- aggregate(
  rate_per_population ~ prefecture_code + prefecture_name,
  data = per_capita,
  FUN = mean,
  na.rm = TRUE
)
pooled$rate_per_population_pct <- pooled$rate_per_population / 1000
pooled_fig <- plot_supplementary_prefecture_per_capita(pooled, fiscal_year = NULL)
save_figure(
  pooled_fig,
  "supplementary_prefecture_per_capita_pooled.png",
  root = PROJECT_ROOT,
  width = 8,
  height = 12
)

message(sprintf(
  "[06_prefecture_per_capita] prefectures=%s | years=%s",
  length(unique(per_capita$prefecture_code)),
  paste(reference_years, collapse = ", ")
))
write_run_meta(CFG, stage = "prefecture_per_capita", root = PROJECT_ROOT)
