### Prefecture-level per-capita ICT rates (SAP secondary, 2024 only) ###
### Usage: Rscript scripts/06_prefecture_per_capita.R

source("scripts/00_setup.R")

for (f in c("codes.R", "load_xlsx.R", "population.R", "per_capita.R", "figures.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = globalenv())
}

if (!requireNamespace("readxl", quietly = TRUE)) {
  install.packages("readxl", repos = "https://cloud.r-project.org")
}

fiscal_year <- 2024L

cross <- load_cross_prefecture_sex_age(fiscal_years = fiscal_year, root = PROJECT_ROOT)
pop <- population_for_years(load_prefecture_population(PROJECT_ROOT), fiscal_year)
per_capita <- prepare_per_capita_table(cross, pop, per = 100000)

intermediate_dir <- path_from_root("output", "intermediate", root = PROJECT_ROOT)
if (!dir.exists(intermediate_dir)) {
  dir.create(intermediate_dir, recursive = TRUE, showWarnings = FALSE)
}
saveRDS(cross, file.path(intermediate_dir, "cross_prefecture_sex_age.rds"))
saveRDS(per_capita, file.path(intermediate_dir, "prefecture_per_capita.rds"))

save_per_capita_table(per_capita, root = PROJECT_ROOT)

fig <- plot_supplementary_prefecture_per_capita(per_capita, fiscal_year = fiscal_year)
save_figure(
  fig,
  "supplementary_prefecture_per_capita_2024.png",
  root = PROJECT_ROOT,
  width = 14,
  height = 6
)

message(sprintf(
  "[06_prefecture_per_capita] prefectures=%s | year=%s",
  length(unique(per_capita$prefecture_code)),
  fiscal_year
))
write_run_meta(CFG, stage = "prefecture_per_capita", root = PROJECT_ROOT)
