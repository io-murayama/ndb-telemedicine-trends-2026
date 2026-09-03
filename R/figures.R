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

ict_visit_type_labels <- c(
  initial = "初診（ICT）",
  followup = "再診・外来（ICT）"
)

filter_ict_trend <- function(trend, fiscal_years = c(2022, 2023, 2024)) {
  trend[trend$era == "ict" & trend$visit_type %in% c("initial", "followup") &
    trend$fiscal_year %in% fiscal_years, , drop = FALSE]
}

filter_legacy_trend <- function(trend) {
  trend[trend$era == "legacy" & trend$visit_type == "all_outpatient", , drop = FALSE]
}

prepare_trend_plot_data <- function(trend, visit_labels = visit_type_labels) {
  trend$series <- visit_labels[trend$visit_type]
  trend$series <- factor(trend$series, levels = unname(visit_labels))
  trend$proportion_pct <- trend$proportion * 100
  trend
}

prepare_age_plot_data <- function(cells, codes_cfg) {
  age_cells <- aggregate_cells_by_age(cells)
  age_levels <- codes_cfg$age_groups
  age_cells$age_group <- factor(age_cells$age_group, levels = age_levels)
  age_cells$visit_type_label <- factor(
    ifelse(age_cells$visit_type == "initial", "初診", "再診・外来"),
    levels = c("初診", "再診・外来")
  )
  age_cells$fiscal_year <- factor(age_cells$fiscal_year)
  age_cells$proportion_pct <- age_cells$proportion * 100
  age_cells
}

prepare_sex_plot_data <- function(cells) {
  sex_cells <- aggregate_cells_by_sex(cells)
  sex_cells$sex_label <- factor(
    ifelse(sex_cells$sex == "male", "男", "女"),
    levels = c("男", "女")
  )
  sex_cells$visit_type_label <- factor(
    ifelse(sex_cells$visit_type == "initial", "初診", "再診・外来"),
    levels = c("初診", "再診・外来")
  )
  sex_cells$fiscal_year <- factor(sex_cells$fiscal_year)
  sex_cells$proportion_pct <- sex_cells$proportion * 100
  sex_cells
}

prepare_change_plot_data <- function(change, codes_cfg) {
  change$age_group <- factor(change$age_group, levels = codes_cfg$age_groups)
  change$visit_type_label <- factor(
    ifelse(change$visit_type == "initial", "初診", "再診・外来"),
    levels = c("初診", "再診・外来")
  )
  change
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
  ict <- filter_ict_trend(trend)
  df <- prepare_trend_plot_data(ict, visit_labels = ict_visit_type_labels)

  count_plot <- ggplot2::ggplot(df, ggplot2::aes(fiscal_year, online_count, color = series, group = series)) +
    ggplot2::geom_line(linewidth = 0.9) +
    ggplot2::geom_point(size = 2.5) +
    ggplot2::scale_color_brewer(palette = "Dark2") +
    ggplot2::scale_x_continuous(breaks = sort(unique(df$fiscal_year))) +
    ggplot2::scale_y_continuous(labels = function(x) format(x, big.mark = ",", scientific = FALSE)) +
    ggplot2::labs(
      title = "Figure 1A. ICT 算定回数（2022–2024）",
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
      title = "Figure 1B. ICT 利用割合（2022–2024）",
      subtitle = "初診: ICT 初診 / 全初診、再診・外来: ICT 再診・外来 / 全再診・外来",
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

plot_supplementary_legacy_trend <- function(trend) {
  require_ggplot2()
  legacy <- filter_legacy_trend(trend)
  if (nrow(legacy) == 0L) {
  return(NULL)
  }
  legacy$series <- visit_type_labels[legacy$visit_type]
  legacy$proportion_pct <- legacy$proportion * 100

  ggplot2::ggplot(legacy, ggplot2::aes(fiscal_year, proportion_pct, color = series, group = series)) +
    ggplot2::geom_line(linewidth = 0.9) +
    ggplot2::geom_point(size = 2.5) +
    ggplot2::scale_color_brewer(palette = "Dark2") +
    ggplot2::scale_x_continuous(breaks = sort(unique(legacy$fiscal_year))) +
    ggplot2::labs(
      title = "Supplementary Figure B. 旧オンライン診療料（2019–2021）",
      subtitle = "オンライン診療料 / 全外来（初診＋再診＋外来）。2022 年度以降の ICT とは定義が異なる。",
      x = "年度",
      y = "割合（%）",
      color = NULL
    ) +
    ggplot2::theme_bw(base_size = 11) +
    ggplot2::theme(legend.position = "bottom")
}

plot_supplementary_policy_timeline <- function() {
  require_ggplot2()
  events <- policy_events
  events$y <- seq_len(nrow(events))

  ggplot2::ggplot(events, ggplot2::aes(event_date, y)) +
    ggplot2::geom_segment(
      ggplot2::aes(xend = event_date, yend = 0),
      linewidth = 0.8,
      color = "#666666"
    ) +
    ggplot2::geom_point(size = 3, color = "#377eb8") +
    ggplot2::geom_text(
      ggplot2::aes(label = label),
      hjust = 0,
      nudge_x = 60,
      size = 3.5
    ) +
    ggplot2::scale_x_date(
      date_breaks = "1 year",
      date_labels = "%Y"
    ) +
    ggplot2::scale_y_continuous(breaks = NULL, limits = c(0, nrow(events) + 0.5)) +
    ggplot2::labs(
      title = "Supplementary Figure A. 制度変更 timeline",
      subtitle = "2018 / 2020 / 2022 / 2024 の主要イベント（記述用）",
      x = "時期",
      y = NULL
    ) +
    ggplot2::theme_bw(base_size = 11) +
    ggplot2::theme(
      panel.grid.major.y = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank()
    )
}

plot_figure2_age_by_visit <- function(cells, codes_cfg) {
  require_ggplot2()
  df <- prepare_age_plot_data(cells, codes_cfg)

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

plot_figure3_age_stratified <- function(cells, codes_cfg) {
  require_ggplot2()
  df <- prepare_age_plot_data(cells, codes_cfg)

  ggplot2::ggplot(
    df,
    ggplot2::aes(age_group, proportion_pct, color = visit_type_label, group = visit_type_label)
  ) +
    ggplot2::geom_line(linewidth = 0.8) +
    ggplot2::geom_point(size = 1.8) +
    ggplot2::facet_wrap(~ fiscal_year, nrow = 1) +
    ggplot2::scale_color_manual(values = c("#7570b3", "#e7298a")) +
    ggplot2::labs(
      title = "Figure 3A. 年齢階級別オンライン診療割合（性別集計）",
      subtitle = "男女を合算した年齢階級別の割合（2022–2024）",
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

plot_figure3_sex_stratified <- function(cells) {
  require_ggplot2()
  df <- prepare_sex_plot_data(cells)

  ggplot2::ggplot(
    df,
    ggplot2::aes(sex_label, proportion_pct, fill = visit_type_label)
  ) +
    ggplot2::geom_col(position = ggplot2::position_dodge(width = 0.8), width = 0.7) +
    ggplot2::facet_wrap(~ fiscal_year, nrow = 1) +
    ggplot2::scale_fill_manual(values = c("#1b9e77", "#d95f02")) +
    ggplot2::labs(
      title = "Figure 3B. 性別オンライン診療割合（年齢集計）",
      subtitle = "全年齢を合算した性別の割合（2022–2024）",
      x = "性別",
      y = "割合（%）",
      fill = NULL
    ) +
    ggplot2::theme_bw(base_size = 10) +
    ggplot2::theme(legend.position = "bottom")
}

plot_figure4_change_by_age <- function(change, codes_cfg) {
  require_ggplot2()
  df <- prepare_change_plot_data(change, codes_cfg)
  visit_colors <- c("初診" = "#1b9e77", "再診・外来" = "#d95f02")

  ggplot2::ggplot(df, ggplot2::aes(abs_change_pp, age_group, color = visit_type_label)) +
    ggplot2::geom_vline(xintercept = 0, color = "#cccccc", linewidth = 0.35) +
    ggplot2::geom_segment(
      ggplot2::aes(x = 0, xend = abs_change_pp, yend = age_group),
      linewidth = 0.7
    ) +
    ggplot2::geom_point(size = 2.2) +
    ggplot2::facet_wrap(~ visit_type_label, ncol = 2, scales = "free_x") +
    ggplot2::scale_color_manual(values = visit_colors, guide = "none") +
    ggplot2::coord_flip() +
    ggplot2::labs(
      title = "Figure 4. Age-specific change from 2022 to 2024",
      subtitle = "絶対差 p2024 − p2022（percentage points）。初診と再診・外来を年齢階級別に比較",
      x = "変化量（pp）",
      y = NULL
    ) +
    ggplot2::theme_bw(base_size = 10) +
    ggplot2::theme(
      panel.grid.major.y = ggplot2::element_blank(),
      axis.text.y = ggplot2::element_text(size = 8),
      strip.text = ggplot2::element_text(face = "bold")
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

plot_supplementary_prefecture_per_capita <- function(per_capita_df, fiscal_year = 2024) {
  require_ggplot2()
  df <- per_capita_df[per_capita_df$fiscal_year == fiscal_year, , drop = FALSE]
  df <- order_prefectures_north_to_south(df)

  rate_col <- if ("rate_per_population" %in% names(df)) {
    "rate_per_population"
  } else {
    "rate_per_population_pct"
  }

  df$prefecture_name <- factor(df$prefecture_name, levels = df$prefecture_name)

  y_label <- if (rate_col == "rate_per_population") "10万人あたり算定回数" else "10万人あたり算定回数（‰）"

  ggplot2::ggplot(df, ggplot2::aes(prefecture_name, .data[[rate_col]])) +
    ggplot2::geom_col(fill = "#377eb8", width = 0.8) +
    ggplot2::labs(
      title = "Supplementary Figure C. 都道府県別人口あたり ICT 算定回数",
      subtitle = paste0(
        fiscal_year,
        " 年度（医療機関所在地・北から順）。分母: 総務省統計局人口推計に基づく都道府県人口"
      ),
      x = "都道府県（医療機関所在地）",
      y = y_label
    ) +
    ggplot2::theme_bw(base_size = 10) +
    ggplot2::theme(
      axis.text.x = ggplot2::element_text(angle = 90, hjust = 1, vjust = 0.5, size = 6)
    )
}

VISIT_SCOPE_PANEL_LEVELS <- c("初診", "再診・外来", "合計")
VISIT_SCOPE_PANEL_COLORS <- c("初診" = "#1b9e77", "再診・外来" = "#d95f02", "合計" = "#7570b3")
VISIT_SCOPE_FILL_LOW <- c("初診" = "#e8f5f0", "再診・外来" = "#fdeee0", "合計" = "#edeaf3")

combine_prefecture_map_panels <- function(panels, title, subtitle) {
  if (requireNamespace("patchwork", quietly = TRUE)) {
    return(
      patchwork::wrap_plots(panels, ncol = 3) +
        patchwork::plot_annotation(
          title = title,
          subtitle = subtitle,
          theme = ggplot2::theme(
            plot.title = ggplot2::element_text(face = "bold", size = 11),
            plot.subtitle = ggplot2::element_text(size = 9, color = "#444444")
          )
        )
    )
  }
  panels[[1]]
}

theme_prefecture_map_panel <- function() {
  ggplot2::theme_minimal(base_size = 9) +
    ggplot2::theme(
      axis.text = ggplot2::element_blank(),
      axis.ticks = ggplot2::element_blank(),
      panel.grid = ggplot2::element_blank(),
      plot.title = ggplot2::element_text(face = "bold", hjust = 0.5, size = 10),
      legend.position = "bottom",
      legend.key.height = ggplot2::unit(0.35, "cm"),
      legend.title = ggplot2::element_text(size = 8),
      legend.text = ggplot2::element_text(size = 7)
    )
}

plot_supplementary_prefecture_per_capita_map <- function(per_capita_df, fiscal_year = 2024, root = project_root()) {
  require_ggplot2()
  require_sf()
  geo <- load_prefecture_geo(root)
  merged <- merge_prefecture_geo_scoped(geo, per_capita_df, fiscal_year = fiscal_year)

  panels <- lapply(VISIT_SCOPE_PANEL_LEVELS, function(scope_label) {
    panel_df <- merged[merged$visit_scope_label == scope_label, , drop = FALSE]
    use_log <- scope_label == "合計"
    fill_scale <- if (use_log) {
      ggplot2::scale_fill_gradient(
        low = "#eff3ff",
        high = "#08519c",
        trans = "log10",
        name = "10万人あたり\n（log10）",
        na.value = "grey85",
        breaks = scales::trans_breaks("log10", function(x) 10^x),
        labels = scales::trans_format("log10", scales::math_format(10^.x))
      )
    } else {
      ggplot2::scale_fill_gradient(
        low = VISIT_SCOPE_FILL_LOW[[scope_label]],
        high = VISIT_SCOPE_PANEL_COLORS[[scope_label]],
        name = "10万人\nあたり",
        na.value = "grey85"
      )
    }

    ggplot2::ggplot(panel_df) +
      ggplot2::geom_sf(ggplot2::aes(fill = rate_per_population), color = "white", linewidth = 0.12) +
      fill_scale +
      ggplot2::coord_sf(expand = FALSE) +
      ggplot2::labs(title = scope_label, x = NULL, y = NULL) +
      theme_prefecture_map_panel()
  })

  combine_prefecture_map_panels(
    panels,
    title = "Supplementary Figure D. 都道府県別人口あたり ICT 算定回数（地図）",
    subtitle = paste0(
      fiscal_year,
      " 年度（医療機関所在地）。初診・再診・外来・合計の3パネル（合計のみ log10）"
    )
  )
}

plot_supplementary_prefecture_per_capita_change <- function(change_df, baseline_year = 2022, end_year = 2024) {
  require_ggplot2()
  df <- change_df
  if (!"visit_scope_label" %in% names(df)) {
    df$visit_scope_label <- "合計"
  }
  df$visit_scope_label <- factor(
    df$visit_scope_label,
    levels = c("初診", "再診・外来", "合計")
  )
  prefecture_order <- order_prefectures_north_to_south(
    unique(df[, c("prefecture_code", "prefecture_name"), drop = FALSE])
  )$prefecture_name
  df$prefecture_name <- factor(df$prefecture_name, levels = prefecture_order)
  scope_colors <- c("初診" = "#1b9e77", "再診・外来" = "#d95f02", "合計" = "#7570b3")

  ggplot2::ggplot(df, ggplot2::aes(abs_change, prefecture_name, color = visit_scope_label)) +
    ggplot2::geom_vline(xintercept = 0, color = "#cccccc", linewidth = 0.35) +
    ggplot2::geom_segment(
      ggplot2::aes(x = 0, xend = abs_change, yend = prefecture_name),
      linewidth = 0.7
    ) +
    ggplot2::geom_point(size = 1.8) +
    ggplot2::facet_wrap(~ visit_scope_label, ncol = 3, scales = "free_x") +
    ggplot2::scale_color_manual(values = scope_colors, guide = "none") +
    ggplot2::coord_flip() +
    ggplot2::labs(
      title = "Supplementary Figure E. 都道府県別人口あたり ICT 算定回数の変化",
      subtitle = paste0(
        baseline_year,
        "→",
        end_year,
        " 年度の絶対差（10万人あたり）。初診・再診・外来・合計を並列表示（Figure 4 と同色）"
      ),
      x = "変化量（10万人あたり）",
      y = NULL
    ) +
    ggplot2::theme_bw(base_size = 10) +
    ggplot2::theme(
      panel.grid.major.y = ggplot2::element_blank(),
      axis.text.y = ggplot2::element_text(size = 5),
      strip.text = ggplot2::element_text(face = "bold")
    )
}

plot_supplementary_prefecture_per_capita_change_map <- function(
  change_df,
  baseline_year = 2022,
  end_year = 2024,
  root = project_root()
) {
  require_ggplot2()
  require_sf()
  geo <- load_prefecture_geo(root)
  merged <- merge_prefecture_geo_change(geo, change_df)

  panels <- lapply(VISIT_SCOPE_PANEL_LEVELS, function(scope_label) {
    panel_df <- merged[merged$visit_scope_label == scope_label, , drop = FALSE]
    ggplot2::ggplot(panel_df) +
      ggplot2::geom_sf(ggplot2::aes(fill = relative_change_pct), color = "white", linewidth = 0.12) +
      ggplot2::scale_fill_gradient2(
        low = "#bdbdbd",
        mid = "#f7fbff",
        high = VISIT_SCOPE_PANEL_COLORS[[scope_label]],
        midpoint = 0,
        name = "変化率\n（%）",
        na.value = "grey85",
        limits = c(-50, 200),
        oob = scales::squish
      ) +
      ggplot2::coord_sf(expand = FALSE) +
      ggplot2::labs(title = scope_label, x = NULL, y = NULL) +
      theme_prefecture_map_panel()
  })

  combine_prefecture_map_panels(
    panels,
    title = "Supplementary Figure F. 都道府県別人口あたり ICT 算定回数の変化率（地図）",
    subtitle = paste0(
      baseline_year,
      "→",
      end_year,
      " 年度の相対変化率（%）。初診・再診・外来・合計の3パネル（凡例 −50～200% でクリップ）"
    )
  )
}
