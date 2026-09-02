### Generate SAP main figures (Figure 1–4) ###
### Usage: Rscript scripts/04_figures.R

source("scripts/00_setup.R")

for (f in c("codes.R", "aggregate.R", "figures.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = globalenv())
}

tables_dir <- path_from_root("output", "tables", root = PROJECT_ROOT)
trend_path <- file.path(tables_dir, "national_trend.csv")
cells_path <- file.path(tables_dir, "main_analysis_cells.csv")
change_path <- file.path(tables_dir, "change_2022_2024_by_age.csv")

if (!file.exists(trend_path) || !file.exists(cells_path) || !file.exists(change_path)) {
  stop("Run scripts/03_build_tables.R first.", call. = FALSE)
}

codes_cfg <- load_procedure_codes(PROJECT_ROOT)
trend <- utils::read.csv(trend_path, fileEncoding = "UTF-8")
cells <- utils::read.csv(cells_path, fileEncoding = "UTF-8")
change <- utils::read.csv(change_path, fileEncoding = "UTF-8")

fig1 <- plot_figure1_trend(trend)
fig2 <- plot_figure2_age_by_visit(cells, codes_cfg)
fig3a <- plot_figure3_age_stratified(cells, codes_cfg)
fig3b <- plot_figure3_sex_stratified(cells)
fig4 <- plot_figure4_change_by_age(change, codes_cfg)
fig_policy <- plot_supplementary_policy_timeline()
fig_legacy <- plot_supplementary_legacy_trend(trend)

if (inherits(fig1, "list")) {
  save_figure(fig1$count, "figure1a_ict_counts.png", root = PROJECT_ROOT, width = 9, height = 4.5)
  save_figure(fig1$proportion, "figure1b_ict_proportions.png", root = PROJECT_ROOT, width = 9, height = 4.5)
} else {
  save_figure(fig1, "figure1_trend.png", root = PROJECT_ROOT, width = 9, height = 8)
}

save_figure(fig2, "figure2_age_by_visit_type.png", root = PROJECT_ROOT, width = 12, height = 5)
save_figure(fig3a, "figure3a_age_stratified.png", root = PROJECT_ROOT, width = 12, height = 5)
save_figure(fig3b, "figure3b_sex_stratified.png", root = PROJECT_ROOT, width = 10, height = 5)
save_figure(fig4, "figure4_change_by_age.png", root = PROJECT_ROOT, width = 12, height = 8)
save_figure(fig_policy, "supplementary_policy_timeline.png", root = PROJECT_ROOT, width = 10, height = 4)
if (!is.null(fig_legacy)) {
  save_figure(fig_legacy, "supplementary_legacy_trend.png", root = PROJECT_ROOT, width = 8, height = 5)
}

message("[04_figures] done")
write_run_meta(CFG, stage = "figures", root = PROJECT_ROOT)
