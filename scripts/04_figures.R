### Generate SAP main figures (Figure 1–3) ###
### Usage: Rscript scripts/04_figures.R

source("scripts/00_setup.R")

for (f in c("codes.R", "figures.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = globalenv())
}

tables_dir <- path_from_root("output", "tables", root = PROJECT_ROOT)
trend_path <- file.path(tables_dir, "national_trend.csv")
cells_path <- file.path(tables_dir, "main_analysis_cells.csv")

if (!file.exists(trend_path) || !file.exists(cells_path)) {
  stop("Run scripts/03_build_tables.R first.", call. = FALSE)
}

codes_cfg <- load_procedure_codes(PROJECT_ROOT)
trend <- utils::read.csv(trend_path, fileEncoding = "UTF-8")
cells <- utils::read.csv(cells_path, fileEncoding = "UTF-8")

fig1 <- plot_figure1_trend(trend)
fig2 <- plot_figure2_age_by_visit(cells, codes_cfg)
fig3 <- plot_figure3_age_sex(cells, codes_cfg)

if (inherits(fig1, "list")) {
  save_figure(fig1$count, "figure1a_online_counts.png", root = PROJECT_ROOT, width = 9, height = 4.5)
  save_figure(fig1$proportion, "figure1b_online_proportions.png", root = PROJECT_ROOT, width = 9, height = 4.5)
} else {
  save_figure(fig1, "figure1_trend.png", root = PROJECT_ROOT, width = 9, height = 8)
}

save_figure(fig2, "figure2_age_by_visit_type.png", root = PROJECT_ROOT, width = 12, height = 5)
save_figure(fig3, "figure3_age_sex.png", root = PROJECT_ROOT, width = 12, height = 7)

message("[04_figures] done")
write_run_meta(CFG, stage = "figures", root = PROJECT_ROOT)
