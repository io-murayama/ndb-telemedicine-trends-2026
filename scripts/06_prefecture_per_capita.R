### Prefecture-level per-capita ICT rates (SAP secondary) ###
### Usage: Rscript scripts/06_prefecture_per_capita.R

source("scripts/00_setup.R")

for (f in c("codes.R", "load_xlsx.R", "population.R", "per_capita.R", "map_geo.R", "figures.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = globalenv())
}

if (!requireNamespace("readxl", quietly = TRUE)) {
  install.packages("readxl", repos = "https://cloud.r-project.org")
}

analysis_years <- c(2022L, 2023L, 2024L)
fiscal_year <- 2024L
baseline_year <- 2022L

cross <- load_cross_prefecture_sex_age(fiscal_years = analysis_years, root = PROJECT_ROOT)
pop <- population_for_years(load_prefecture_population(PROJECT_ROOT), analysis_years)
per_capita_all <- prepare_all_prefecture_per_capita(cross, pop, per = 100000)
per_capita_2024_all <- per_capita_all[per_capita_all$fiscal_year == fiscal_year, , drop = FALSE]
per_capita_2024 <- per_capita_2024_all[per_capita_2024_all$visit_scope == "total", , drop = FALSE]
prefecture_change <- aggregate_prefecture_change_2022_2024(
  per_capita_all,
  baseline_year = baseline_year,
  end_year = fiscal_year
)

intermediate_dir <- path_from_root("output", "intermediate", root = PROJECT_ROOT)
if (!dir.exists(intermediate_dir)) {
  dir.create(intermediate_dir, recursive = TRUE, showWarnings = FALSE)
}
saveRDS(cross, file.path(intermediate_dir, "cross_prefecture_sex_age.rds"))
saveRDS(per_capita_all, file.path(intermediate_dir, "prefecture_per_capita.rds"))
saveRDS(prefecture_change, file.path(intermediate_dir, "prefecture_per_capita_change.rds"))

save_per_capita_table(per_capita_2024, root = PROJECT_ROOT)
save_per_capita_table(
  prefecture_change,
  filename = "prefecture_per_capita_change_2022_2024.csv",
  root = PROJECT_ROOT
)

fig_bar <- plot_supplementary_prefecture_per_capita(per_capita_2024, fiscal_year = fiscal_year)
save_figure(
  fig_bar,
  "supplementary_prefecture_per_capita_2024.png",
  root = PROJECT_ROOT,
  width = 14,
  height = 6
)

fig_map <- plot_supplementary_prefecture_per_capita_map(per_capita_2024_all, fiscal_year = fiscal_year, root = PROJECT_ROOT)
save_figure(
  fig_map,
  "supplementary_prefecture_per_capita_map_2024.png",
  root = PROJECT_ROOT,
  width = 24,
  height = 8
)

fig_change <- plot_supplementary_prefecture_per_capita_change(
  prefecture_change,
  baseline_year = baseline_year,
  end_year = fiscal_year
)
save_figure(
  fig_change,
  "supplementary_prefecture_per_capita_change_2022_2024.png",
  root = PROJECT_ROOT,
  width = 22,
  height = 9
)

fig_change_map <- plot_supplementary_prefecture_per_capita_change_map(
  prefecture_change,
  baseline_year = baseline_year,
  end_year = fiscal_year,
  root = PROJECT_ROOT
)
save_figure(
  fig_change_map,
  "supplementary_prefecture_per_capita_change_map_2022_2024.png",
  root = PROJECT_ROOT,
  width = 24,
  height = 8
)

message(sprintf(
  "[06_prefecture_per_capita] prefectures=%s | years=%s | change=%s-%s",
  length(unique(per_capita_all$prefecture_code)),
  paste(analysis_years, collapse = ","),
  baseline_year,
  fiscal_year
))
write_run_meta(CFG, stage = "prefecture_per_capita", root = PROJECT_ROOT)
