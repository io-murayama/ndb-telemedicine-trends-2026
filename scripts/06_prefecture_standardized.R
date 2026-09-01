### Prefecture-level age-sex standardized proportions (SAP secondary) ###
### Usage: Rscript scripts/06_prefecture_standardized.R

source("scripts/00_setup.R")

for (f in c("codes.R", "load_xlsx.R", "standardize.R", "figures.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = globalenv())
}

if (!requireNamespace("readxl", quietly = TRUE)) {
  install.packages("readxl", repos = "https://cloud.r-project.org")
}

codes_cfg <- load_procedure_codes(PROJECT_ROOT)
reference_years <- codes_cfg$eras$ict$fiscal_years

cross <- load_cross_prefecture_sex_age(fiscal_years = reference_years, root = PROJECT_ROOT)
std <- prepare_standardized_table(cross, reference_years = reference_years)

intermediate_dir <- path_from_root("output", "intermediate", root = PROJECT_ROOT)
if (!dir.exists(intermediate_dir)) {
  dir.create(intermediate_dir, recursive = TRUE, showWarnings = FALSE)
}
saveRDS(cross, file.path(intermediate_dir, "cross_prefecture_sex_age.rds"))
saveRDS(std, file.path(intermediate_dir, "prefecture_standardized.rds"))

save_standardized_table(std, root = PROJECT_ROOT)

for (yr in reference_years) {
  fig <- plot_supplementary_prefecture(std, fiscal_year = yr)
  save_figure(
    fig,
    paste0("supplementary_prefecture_", yr, ".png"),
    root = PROJECT_ROOT,
    width = 8,
    height = 12
  )
}

pooled <- aggregate(
  standardized_proportion ~ prefecture_code + prefecture_name,
  data = std,
  FUN = mean
)
pooled$standardized_proportion_pct <- pooled$standardized_proportion * 100
pooled_fig <- plot_supplementary_prefecture(pooled, fiscal_year = NULL)
save_figure(
  pooled_fig,
  "supplementary_prefecture_pooled.png",
  root = PROJECT_ROOT,
  width = 8,
  height = 12
)

message(sprintf(
  "[06_prefecture_standardized] prefectures=%s | years=%s",
  length(unique(std$prefecture_code)),
  paste(reference_years, collapse = ", ")
))
write_run_meta(CFG, stage = "prefecture_standardized", root = PROJECT_ROOT)
