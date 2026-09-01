#' Load procedure code definitions and NDB round metadata.

load_procedure_codes <- function(root = project_root()) {
  path <- path_from_root("config", "procedure_codes.yml", root = root)
  if (!file.exists(path)) {
    stop("Missing config/procedure_codes.yml at: ", path, call. = FALSE)
  }
  yaml::read_yaml(path)
}

load_ndb_rounds <- function(root = project_root()) {
  path <- path_from_root("config", "ndb_rounds.yml", root = root)
  if (!file.exists(path)) {
    stop("Missing config/ndb_rounds.yml at: ", path, call. = FALSE)
  }
  yaml::read_yaml(path)
}

era_for_year <- function(fiscal_year, codes_cfg) {
  for (nm in names(codes_cfg$eras)) {
    if (fiscal_year %in% codes_cfg$eras[[nm]]$fiscal_years) {
      return(nm)
    }
  }
  stop("No era defined for fiscal year: ", fiscal_year, call. = FALSE)
}

is_online_procedure <- function(category, procedure_name, era_cfg) {
  if (!is.null(era_cfg$online)) {
    return(category %in% era_cfg$online$values)
  }

  initial_online <- !is.null(era_cfg$online_initial) &&
    category %in% era_cfg$online_initial$within_category &&
    grepl(era_cfg$online_initial$pattern, procedure_name, fixed = TRUE)

  followup_online <- !is.null(era_cfg$online_followup) &&
    category %in% era_cfg$online_followup$within_category &&
    grepl(era_cfg$online_followup$pattern, procedure_name, fixed = TRUE)

  initial_online || followup_online
}

visit_type_for_procedure <- function(category, era_cfg) {
  if (category %in% era_cfg$initial$values) {
    return("initial")
  }
  if (category %in% era_cfg$followup$values) {
    if (category == "外来診療料") {
      return("outpatient")
    }
    return("followup")
  }
  if (!is.null(era_cfg$online) && category %in% era_cfg$online$values) {
    return("online_legacy")
  }
  NA_character_
}

tag_procedures <- function(df, codes_cfg) {
  era_names <- vapply(df$fiscal_year, era_for_year, character(1), codes_cfg = codes_cfg)

  out <- df
  out$era <- era_names
  out$visit_type <- NA_character_
  out$is_online <- FALSE

  for (era_nm in unique(era_names)) {
    idx <- which(era_names == era_nm)
    era_cfg <- codes_cfg$eras[[era_nm]]
    out$visit_type[idx] <- vapply(
      seq_along(idx),
      function(i) {
        visit_type_for_procedure(out$category[idx[i]], era_cfg)
      },
      character(1)
    )
    out$is_online[idx] <- vapply(
      seq_along(idx),
      function(i) {
        is_online_procedure(out$category[idx[i]], out$procedure_name[idx[i]], era_cfg)
      },
      logical(1)
    )
  }

  out
}
