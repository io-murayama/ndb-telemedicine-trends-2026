#' Parse NDB open-data xlsx (A 基本診療料 初再診料) into long format.

require_pkg <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    stop(
      "Package '", pkg, "' is required. ",
      "Install with install.packages(\"", pkg, "\")",
      call. = FALSE
    )
  }
}

col_to_num <- function(col_letter) {
  chars <- strsplit(col_letter, "")[[1]]
  vals <- match(chars, LETTERS)
  Reduce(function(a, b) a * 26L + b, vals)
}

parse_ndb_count <- function(x) {
  if (is.na(x) || !nzchar(as.character(x))) {
    return(NA_real_)
  }
  val <- as.character(x)
  if (val %in% c("-", "‐", "—")) {
    return(NA_real_)
  }
  suppressWarnings(as.numeric(gsub(",", "", val)))
}

find_header_rows <- function(raw) {
  n_rows <- nrow(raw)
  code_row <- NA_integer_
  age_row <- NA_integer_

  for (i in seq_len(min(n_rows, 10L))) {
    row_vals <- as.character(unlist(raw[i, ], use.names = FALSE))
    if (any(grepl("診療行為", row_vals, fixed = TRUE), na.rm = TRUE)) {
      code_row <- i
    }
    if (any(grepl("0～4歳|0\u301c4\u6b73", row_vals), na.rm = TRUE)) {
      age_row <- i
    }
  }

  if (is.na(code_row)) {
    stop("Could not locate procedure header row", call. = FALSE)
  }
  if (is.na(age_row)) {
    age_row <- code_row + 1L
  }

  list(code_row = code_row, age_row = age_row)
}

read_ndb_sex_age_sheet <- function(path, sheet = "外来") {
  require_pkg("readxl")
  raw <- readxl::read_excel(path, sheet = sheet, col_names = FALSE, .name_repair = "minimal")
  headers <- find_header_rows(raw)

  code_row <- headers$code_row
  age_row <- headers$age_row
  header_codes <- as.character(unlist(raw[code_row, ], use.names = FALSE))
  header_ages <- as.character(unlist(raw[age_row, ], use.names = FALSE))

  sex_age_cols <- which(!is.na(header_ages) & grepl("歳", header_ages))
  if (length(sex_age_cols) == 0L) {
    stop("No sex-age columns found in: ", path, call. = FALSE)
  }

  mid <- length(sex_age_cols) %/% 2L
  sexes <- c(rep("male", mid), rep("female", length(sex_age_cols) - mid))
  age_groups <- header_ages[sex_age_cols]

  data_start <- max(code_row, age_row) + 1L
  rows <- list()
  current_category <- NA_character_

  for (i in seq.int(data_start, nrow(raw))) {
    row <- raw[i, ]
    cat_val <- as.character(row[[2]])
    if (!is.na(cat_val) && nzchar(cat_val)) {
      current_category <- gsub("\n", "", cat_val)
    }

    procedure_code <- as.character(row[[3]])
    if (is.na(procedure_code) || !grepl("^[0-9]{9}$", procedure_code)) {
      next
    }

    procedure_name <- as.character(row[[4]])
    points <- parse_ndb_count(row[[5]])
    total <- parse_ndb_count(row[[6]])

    counts <- vapply(sex_age_cols, function(j) parse_ndb_count(row[[j]]), numeric(1))

    rows[[length(rows) + 1L]] <- data.frame(
      category = current_category,
      procedure_code = procedure_code,
      procedure_name = procedure_name,
      points = points,
      total = total,
      sex = sexes,
      age_group = age_groups,
      count = counts,
      stringsAsFactors = FALSE
    )
  }

  if (length(rows) == 0L) {
    stop("No procedure rows parsed from: ", path, call. = FALSE)
  }

  do.call(rbind, rows)
}

read_ndb_sex_age_file <- function(path, fiscal_year, round_id) {
  df <- read_ndb_sex_age_sheet(path)
  df$fiscal_year <- fiscal_year
  df$round_id <- round_id
  df$source_file <- basename(path)
  df
}

load_all_sex_age <- function(root = project_root()) {
  rounds_cfg <- load_ndb_rounds(root)
  file_key <- "basic_initial_followup_sex_age"
  file_spec <- rounds_cfg$files[[file_key]]
  filename <- file_spec$filename

  pieces <- lapply(names(rounds_cfg$rounds), function(round_id) {
    round_meta <- rounds_cfg$rounds[[round_id]]
    path <- path_from_root("data", "raw", round_id, filename, root = root)
    if (!file.exists(path)) {
      stop("Missing data file: ", path, call. = FALSE)
    }
    message("[load] ", round_id, " <- ", path)
    read_ndb_sex_age_file(path, round_meta$fiscal_year, round_id)
  })

  do.call(rbind, pieces)
}

find_cross_header_rows <- function(raw) {
  pref_row <- NA_integer_
  age_row <- NA_integer_

  for (i in seq_len(min(nrow(raw), 10L))) {
    row_vals <- as.character(unlist(raw[i, ], use.names = FALSE))
    if (any(grepl("都道府県", row_vals, fixed = TRUE), na.rm = TRUE)) {
      pref_row <- i
    }
    if (any(grepl("0～4歳", row_vals), na.rm = TRUE)) {
      age_row <- i
    }
  }

  if (is.na(pref_row) || is.na(age_row)) {
    stop("Could not locate cross-tabulation header rows", call. = FALSE)
  }

  list(pref_row = pref_row, age_row = age_row)
}

read_ndb_cross_prefecture_sex_age_sheet <- function(path, sheet, metric_type) {
  require_pkg("readxl")
  raw <- readxl::read_excel(path, sheet = sheet, col_names = FALSE, .name_repair = "minimal")
  headers <- find_cross_header_rows(raw)

  header_ages <- as.character(unlist(raw[headers$age_row, ], use.names = FALSE))
  sex_age_cols <- which(!is.na(header_ages) & grepl("歳", header_ages))
  if (length(sex_age_cols) == 0L) {
    stop("No sex-age columns found in cross file: ", path, call. = FALSE)
  }

  mid <- length(sex_age_cols) %/% 2L
  sexes <- c(rep("male", mid), rep("female", length(sex_age_cols) - mid))
  age_groups <- header_ages[sex_age_cols]

  data_start <- headers$age_row + 1L
  rows <- list()

  for (i in seq.int(data_start, nrow(raw))) {
    row <- raw[i, ]
    pref_code <- as.character(row[[1]])
    pref_name <- as.character(row[[2]])
    if (is.na(pref_code) || !grepl("^[0-9]{2}$", pref_code)) {
      next
    }

    total <- parse_ndb_count(row[[3]])
    counts <- vapply(sex_age_cols, function(j) parse_ndb_count(row[[j]]), numeric(1))

    rows[[length(rows) + 1L]] <- data.frame(
      prefecture_code = pref_code,
      prefecture_name = pref_name,
      total = total,
      sex = sexes,
      age_group = age_groups,
      count = counts,
      metric_type = metric_type,
      stringsAsFactors = FALSE
    )
  }

  if (length(rows) == 0L) {
    stop("No prefecture rows parsed from cross file: ", path, call. = FALSE)
  }

  do.call(rbind, rows)
}

cross_online_sheets <- function(path) {
  require_pkg("readxl")
  sheets <- readxl::excel_sheets(path)
  sheets[grepl("^外来_", sheets)]
}

load_cross_round <- function(round_id, fiscal_year, root = project_root()) {
  rounds_cfg <- load_ndb_rounds(root)
  cross_specs <- list(
    initial = list(key = "cross_initial_prefecture_sex_age", sheet = "外来", metric = "denom_initial"),
    followup = list(key = "cross_followup_prefecture_sex_age", sheet = "外来", metric = "denom_followup"),
    outpatient = list(key = "cross_outpatient_prefecture_sex_age", sheet = "外来", metric = "denom_outpatient")
  )

  pieces <- list()
  for (nm in names(cross_specs)) {
    spec <- cross_specs[[nm]]
    filename <- rounds_cfg$files[[spec$key]]$filename
    path <- path_from_root("data", "raw", round_id, filename, root = root)
    if (!file.exists(path)) {
      stop("Missing cross file: ", path, call. = FALSE)
    }
    df <- read_ndb_cross_prefecture_sex_age_sheet(path, spec$sheet, spec$metric)
    df$fiscal_year <- fiscal_year
    df$round_id <- round_id
    pieces[[nm]] <- df
  }

  online_filename <- rounds_cfg$files$cross_online_prefecture_sex_age$filename
  online_path <- path_from_root("data", "raw", round_id, online_filename, root = root)
  if (!file.exists(online_path)) {
    stop("Missing cross file: ", online_path, call. = FALSE)
  }

  online_sheets <- cross_online_sheets(online_path)
  if (length(online_sheets) == 0L) {
    stop("No outpatient online sheets found in: ", online_path, call. = FALSE)
  }

  online_pieces <- lapply(online_sheets, function(sh) {
    metric <- switch(
      sh,
      "外来_初診料" = "online_initial",
      "外来_再診料" = "online_followup",
      "外来_外来診療料" = "online_outpatient",
      paste0("online_", gsub("^外来_", "", sh))
    )
    df <- read_ndb_cross_prefecture_sex_age_sheet(online_path, sh, metric)
    df$fiscal_year <- fiscal_year
    df$round_id <- round_id
    df
  })

  pieces$online <- do.call(rbind, online_pieces)
  do.call(rbind, pieces)
}

load_cross_prefecture_sex_age <- function(fiscal_years = NULL, root = project_root()) {
  rounds_cfg <- load_ndb_rounds(root)
  round_ids <- names(rounds_cfg$rounds)

  pieces <- lapply(round_ids, function(round_id) {
    fiscal_year <- rounds_cfg$rounds[[round_id]]$fiscal_year
    if (!is.null(fiscal_years) && !(fiscal_year %in% fiscal_years)) {
      return(NULL)
    }
    message("[load cross] ", round_id, " (", fiscal_year, ")")
    load_cross_round(round_id, fiscal_year, root = root)
  })

  pieces <- pieces[!vapply(pieces, is.null, logical(1))]
  do.call(rbind, pieces)
}
