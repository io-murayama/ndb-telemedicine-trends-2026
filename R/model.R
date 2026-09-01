#' Binomial regression for SAP main analysis (2022–2024).

prepare_model_data <- function(cells, codes_cfg) {
  df <- cells
  df <- df[df$fiscal_year %in% codes_cfg$eras$ict$fiscal_years, , drop = FALSE]
  df$non_online_count <- df$denominator_count - df$online_count
  df <- df[df$denominator_count > 0, , drop = FALSE]

  df$age_group <- factor(df$age_group, levels = codes_cfg$age_groups)
  df$sex <- factor(df$sex, levels = codes_cfg$sexes)
  df$visit_type <- factor(df$visit_type, levels = c("initial", "followup"))
  df$fiscal_year <- factor(df$fiscal_year, levels = codes_cfg$eras$ict$fiscal_years)

  df
}

fit_binomial_model <- function(df) {
  fit_log <- tryCatch(
    stats::glm(
      cbind(online_count, non_online_count) ~ age_group + sex + visit_type + fiscal_year +
        age_group:visit_type + age_group:fiscal_year + visit_type:fiscal_year,
      family = stats::binomial(link = "log"),
      data = df
    ),
    error = function(e) e
  )

  if (inherits(fit_log, "error") || !fit_log$converged) {
    message("[model] log-link did not converge; falling back to logit link")
    fit_log <- stats::glm(
      cbind(online_count, non_online_count) ~ age_group + sex + visit_type + fiscal_year +
        age_group:visit_type + age_group:fiscal_year + visit_type:fiscal_year,
      family = stats::binomial(link = "logit"),
      data = df
    )
    fit_log$link_used <- "logit"
  } else {
    fit_log$link_used <- "log"
  }

  fit_log
}

extract_fixed_effects <- function(fit) {
  sm <- summary(fit)$coefficients
  out <- data.frame(
    term = rownames(sm),
    estimate = sm[, 1],
    se = sm[, 2],
    stringsAsFactors = FALSE
  )

  if (identical(fit$link_used, "log")) {
    out$rr <- exp(out$estimate)
    out$rr_lcl <- exp(out$estimate - 1.96 * out$se)
    out$rr_ucl <- exp(out$estimate + 1.96 * out$se)
  } else {
    out$or <- exp(out$estimate)
    out$or_lcl <- exp(out$estimate - 1.96 * out$se)
    out$or_ucl <- exp(out$estimate + 1.96 * out$se)
  }

  out
}

predict_margin <- function(fit, newdata) {
  link <- stats::predict(fit, newdata = newdata, type = "link", se.fit = TRUE)
  prob <- stats::binomial(link = fit$family$link)$linkinv(link$fit)
  prob_se <- link$se.fit * prob * (1 - prob)
  data.frame(
    newdata,
    proportion = prob,
    proportion_lcl = pmax(0, prob - 1.96 * prob_se),
    proportion_ucl = pmin(1, prob + 1.96 * prob_se),
    stringsAsFactors = FALSE
  )
}

build_key_contrasts <- function(fit, df) {
  ref_age <- levels(df$age_group)[1]
  ref_year <- levels(df$fiscal_year)[1]
  last_year <- tail(levels(df$fiscal_year), 1)

  grid <- function(age_group, sex, visit_type, fiscal_year) {
    data.frame(
      age_group = factor(age_group, levels = levels(df$age_group)),
      sex = factor(sex, levels = levels(df$sex)),
      visit_type = factor(visit_type, levels = levels(df$visit_type)),
      fiscal_year = factor(fiscal_year, levels = levels(df$fiscal_year)),
      stringsAsFactors = FALSE
    )
  }

  pred_female <- predict_margin(fit, grid(ref_age, "female", "initial", ref_year))
  pred_male <- predict_margin(fit, grid(ref_age, "male", "initial", ref_year))
  pred_followup <- predict_margin(fit, grid(ref_age, "male", "followup", ref_year))
  pred_year_last <- predict_margin(fit, grid(ref_age, "male", "initial", last_year))
  pred_year_first <- predict_margin(fit, grid(ref_age, "male", "initial", ref_year))

  out <- data.frame(
    contrast = c(
      "女性 vs 男性（初診、基準年齢・年度）",
      "再診・外来 vs 初診（基準年齢・男性・基準年度）",
      paste0(last_year, " vs ", ref_year, "（初診、基準年齢・男性）")
    ),
    proportion_a = c(pred_female$proportion, pred_followup$proportion, pred_year_last$proportion),
    proportion_b = c(pred_male$proportion, pred_male$proportion, pred_year_first$proportion),
    stringsAsFactors = FALSE
  )
  out$abs_diff_pp <- (out$proportion_a - out$proportion_b) * 100

  if (identical(fit$link_used, "log") && "sexfemale" %in% names(coef(fit))) {
    female_coef <- coef(fit)["sexfemale"]
    female_se <- sqrt(vcov(fit)["sexfemale", "sexfemale"])
    out$rr <- c(exp(female_coef), NA_real_, NA_real_)
    out$rr_lcl <- c(exp(female_coef - 1.96 * female_se), NA_real_, NA_real_)
    out$rr_ucl <- c(exp(female_coef + 1.96 * female_se), NA_real_, NA_real_)
  }

  out
}

save_model_outputs <- function(fit, effects, contrasts, root = project_root()) {
  out_dir <- path_from_root("output", "tables", root = root)
  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  saveRDS(fit, path_from_root("output", "intermediate", "binomial_model.rds", root = root))
  utils::write.csv(effects, file.path(out_dir, "model_fixed_effects.csv"), row.names = FALSE, fileEncoding = "UTF-8")
  utils::write.csv(contrasts, file.path(out_dir, "model_key_contrasts.csv"), row.names = FALSE, fileEncoding = "UTF-8")

  message("[save] ", file.path(out_dir, "model_fixed_effects.csv"))
  message("[save] ", file.path(out_dir, "model_key_contrasts.csv"))
}
