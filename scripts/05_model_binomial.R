### Binomial regression for SAP main analysis (2022–2024) ###
### Usage: Rscript scripts/05_model_binomial.R

source("scripts/00_setup.R")

for (f in c("codes.R", "model.R")) {
  sys.source(file.path(PROJECT_ROOT, "R", f), envir = globalenv())
}

cells_path <- path_from_root("output", "tables", "main_analysis_cells.csv", root = PROJECT_ROOT)
if (!file.exists(cells_path)) {
  stop("Run scripts/03_build_tables.R first.", call. = FALSE)
}

codes_cfg <- load_procedure_codes(PROJECT_ROOT)
cells <- utils::read.csv(cells_path, fileEncoding = "UTF-8")
model_df <- prepare_model_data(cells, codes_cfg)

fit <- fit_binomial_model(model_df)
effects <- extract_fixed_effects(fit)
contrasts <- build_key_contrasts(fit, model_df)

save_model_outputs(fit, effects, contrasts, root = PROJECT_ROOT)

message(sprintf(
  "[05_model_binomial] link=%s | terms=%s | converged=%s",
  fit$link_used,
  nrow(effects),
  isTRUE(fit$converged)
))

write_run_meta(CFG, stage = "model_binomial", root = PROJECT_ROOT)
