#' Figure helpers for SAP main figures.

require_ggplot2 <- function() {
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    install.packages("ggplot2", repos = "https://cloud.r-project.org")
  }
  invisible(TRUE)
}

policy_events <- data.frame(
  event_date = as.Date(c("2018-04-01", "2020-04-01", "2022-04-01", "2024-03-01")),
  label = c(
    "2018: オンライン診療料新設",
    "2020: COVID-19 特例開始",
    "2022: ICT 初再診・外来新設",
    "2024: COVID-19 特例終了"
  ),
  stringsAsFactors = FALSE
)

visit_type_labels <- c(
  all_outpatient = "オンライン診療料（2019–21）",
  initial = "初診（ICT）",
  followup = "再診・外来（ICT）"
)

prepare_trend_plot_data <- function(trend) {
  trend$series <- visit_type_labels[trend$visit_type]
  trend$series <- factor(
    trend$series,
    levels = unname(visit_type_labels[c("all_outpatient", "initial", "followup")])
  )
  trend$proportion_pct <- trend$proportion * 100
  trend
}

prepare_cells_plot_data <- function(cells, codes_cfg) {
  age_levels <- codes_cfg$age_groups
  cells$age_group <- factor(cells$age_group, levels = age_levels)
  cells$visit_type_label <- factor(
    ifelse(cells$visit_type == "initial", "初診", "再診・外来"),
    levels = c("初診", "再診・外来")
  )
  cells$sex_label <- factor(
    ifelse(cells$sex == "male", "男", "女"),
    levels = c("男", "女")
  )
  cells$fiscal_year <- factor(cells$fiscal_year)
  cells$proportion_pct <- cells$proportion * 100
  cells
}

plot_figure1_trend <- function(trend) {
  require_ggplot2()
  df <- prepare_trend_plot_data(trend)

  count_plot <- ggplot2::ggplot(df, ggplot2::aes(fiscal_year, online_count, color = series, group = series)) +
    ggplot2::geom_line(linewidth = 0.9) +
    ggplot2::geom_point(size = 2.5) +
    ggplot2::scale_color_brewer(palette = "Dark2") +
    ggplot2::scale_x_continuous(breaks = sort(unique(df$fiscal_year))) +
    ggplot2::scale_y_continuous(labels = function(x) format(x, big.mark = ",", scientific = FALSE)) +
    ggplot2::labs(
      title = "Figure 1A. オンライン診療算定回数（2019–2024）",
      x = "年度",
      y = "算定回数",
      color = NULL
    ) +
    ggplot2::theme_bw(base_size = 11) +
    ggplot2::theme(legend.position = "bottom")

  pct_plot <- ggplot2::ggplot(df, ggplot2::aes(fiscal_year, proportion_pct, color = series, group = series)) +
    ggplot2::geom_line(linewidth = 0.9) +
    ggplot2::geom_point(size = 2.5) +
    ggplot2::scale_color_brewer(palette = "Dark2") +
    ggplot2::scale_x_continuous(breaks = sort(unique(df$fiscal_year))) +
    ggplot2::labs(
      title = "Figure 1B. オンライン診療割合（2019–2024）",
      subtitle = "2019–21 はオンライン診療料／全外来、2022–24 は初診・再診・外来別（SAP 準拠）",
      x = "年度",
      y = "割合（%）",
      color = NULL
    ) +
    ggplot2::theme_bw(base_size = 11) +
    ggplot2::theme(legend.position = "bottom")

  if (requireNamespace("patchwork", quietly = TRUE)) {
    return(patchwork::wrap_plots(count_plot, pct_plot, ncol = 1) + patchwork::plot_layout(guides = "collect"))
  }

  list(count = count_plot, proportion = pct_plot)
}

plot_figure2_age_by_visit <- function(cells, codes_cfg) {
  require_ggplot2()
  df <- prepare_cells_plot_data(cells, codes_cfg)

  ggplot2::ggplot(
    df,
    ggplot2::aes(age_group, proportion_pct, color = visit_type_label, group = visit_type_label)
  ) +
    ggplot2::geom_line(linewidth = 0.8) +
    ggplot2::geom_point(size = 1.8) +
    ggplot2::facet_wrap(~ fiscal_year, nrow = 1) +
    ggplot2::scale_color_manual(values = c("#1b9e77", "#d95f02")) +
    ggplot2::labs(
      title = "Figure 2. 年齢階級別オンライン診療割合（初診 vs 再診・外来）",
      x = "年齢階級",
      y = "割合（%）",
      color = NULL
    ) +
    ggplot2::theme_bw(base_size = 10) +
    ggplot2::theme(
      legend.position = "bottom",
      axis.text.x = ggplot2::element_text(angle = 90, hjust = 1, vjust = 0.5, size = 7)
    )
}

plot_figure3_age_sex <- function(cells, codes_cfg) {
  require_ggplot2()
  df <- prepare_cells_plot_data(cells, codes_cfg)

  ggplot2::ggplot(
    df,
    ggplot2::aes(age_group, proportion_pct, color = visit_type_label, group = visit_type_label)
  ) +
    ggplot2::geom_line(linewidth = 0.8) +
    ggplot2::geom_point(size = 1.8) +
    ggplot2::facet_grid(sex_label ~ fiscal_year) +
    ggplot2::scale_color_manual(values = c("#7570b3", "#e7298a")) +
    ggplot2::labs(
      title = "Figure 3. 年齢・性別別オンライン診療割合",
      x = "年齢階級",
      y = "割合（%）",
      color = NULL
    ) +
    ggplot2::theme_bw(base_size = 10) +
    ggplot2::theme(
      legend.position = "bottom",
      axis.text.x = ggplot2::element_text(angle = 90, hjust = 1, vjust = 0.5, size = 7)
    )
}

save_figure <- function(plot, filename, root = project_root(), width = 10, height = 6) {
  require_ggplot2()
  out_dir <- path_from_root("output", "figures", root = root)
  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }
  out_path <- file.path(out_dir, filename)
  ggplot2::ggsave(out_path, plot = plot, width = width, height = height, dpi = 150)
  message("[save] ", out_path)
  invisible(out_path)
}

plot_supplementary_prefecture <- function(std_df, fiscal_year = NULL) {
  require_ggplot2()
  df <- std_df
  if (!is.null(fiscal_year)) {
    df <- df[df$fiscal_year == fiscal_year, , drop = FALSE]
  }
  df <- df[order(df$standardized_proportion_pct), , drop = FALSE]
  df$prefecture_name <- factor(df$prefecture_name, levels = df$prefecture_name)

  year_label <- if (is.null(fiscal_year)) "2022–2024" else as.character(fiscal_year)

  ggplot2::ggplot(df, ggplot2::aes(prefecture_name, standardized_proportion_pct)) +
    ggplot2::geom_col(fill = "#377eb8") +
    ggplot2::coord_flip() +
    ggplot2::labs(
      title = "Supplementary Figure. 都道府県別年齢・性別標準化オンライン診療割合",
      subtitle = paste0(
        year_label,
        " 年度（医療機関所在地）。基準人口: ",
        year_label,
        " の全国年齢・性別構成"
      ),
      x = "都道府県（医療機関所在地）",
      y = "標準化割合（%）"
    ) +
    ggplot2::theme_bw(base_size = 10) +
    ggplot2::theme(axis.text.y = ggplot2::element_text(size = 7))
}
