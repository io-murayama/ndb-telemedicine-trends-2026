#!/usr/bin/env Rscript

# 患者居住地・医療機関所在地の比較図を、追加パッケージなしの R 標準描画で作成する。
# GeoJSON は都道府県境界の座標を読むためだけに用い、地図上に都道府県名等は表示しない。

options(stringsAsFactors = FALSE)

project_root <- normalizePath(file.path(getwd()), mustWork = TRUE)
fig_dir <- file.path(project_root, "output", "figures")
table_dir <- file.path(project_root, "output", "tables")
geo_path <- file.path(project_root, "data", "reference", "prefectures.geojson")

if (!file.exists(geo_path)) stop("都道府県GeoJSONが見つかりません: ", geo_path)
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

read_utf8_csv <- function(path) {
  utils::read.csv(path, fileEncoding = "UTF-8-BOM", check.names = FALSE)
}

# このリポジトリの整形済みGeoJSONは、1座標が4行（[, x, y, ]）で表される。
# 外部JSONパッケージを使わず、閉じたリング単位で多角形を抽出する。
read_prefecture_rings <- function(path) {
  lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
  rings <- list()
  current_code <- NA_integer_
  ring_x <- numeric(0)
  ring_y <- numeric(0)

  number_line <- function(x) grepl("^\\s*-?[0-9]+(?:\\.[0-9]+)?(?:[eE][-+]?[0-9]+)?[,]?\\s*$", x)
  numeric_value <- function(x) as.numeric(sub(",.*$", "", trimws(x)))

  for (i in seq_len(length(lines) - 2L)) {
    id <- regexec("\\\"id\\\"\\s*:\\s*([0-9]+)", lines[[i]])
    id_value <- regmatches(lines[[i]], id)[[1L]]
    if (length(id_value) == 2L) {
      current_code <- as.integer(id_value[[2L]])
      ring_x <- numeric(0)
      ring_y <- numeric(0)
      next
    }

    coordinate_open <- grepl("^\\s*\\[\\s*$", lines[[i]])
    if (!is.na(current_code) && coordinate_open && number_line(lines[[i + 1L]]) && number_line(lines[[i + 2L]])) {
      ring_x <- c(ring_x, numeric_value(lines[[i + 1L]]))
      ring_y <- c(ring_y, numeric_value(lines[[i + 2L]]))

      # GeoJSONポリゴンは始点と終点が一致する。そこでリングを確定する。
      if (length(ring_x) >= 4L &&
          abs(ring_x[[1L]] - ring_x[[length(ring_x)]]) < 1e-8 &&
          abs(ring_y[[1L]] - ring_y[[length(ring_y)]]) < 1e-8) {
        rings[[length(rings) + 1L]] <- list(code = current_code, x = ring_x, y = ring_y)
        ring_x <- numeric(0)
        ring_y <- numeric(0)
      }
    }
  }

  codes <- sort(unique(vapply(rings, function(x) x$code, integer(1))))
  if (!identical(codes, 1:47)) {
    stop("GeoJSONから47都道府県を正しく読み込めませんでした（取得数: ", length(codes), "）")
  }
  rings
}

value_colours <- function(values, limits, palette, n = 101L, na_colour = "grey88") {
  palette_values <- grDevices::colorRampPalette(palette)(n)
  clipped <- pmin(pmax(values, limits[[1L]]), limits[[2L]])
  index <- floor((clipped - limits[[1L]]) / diff(limits) * (n - 1L)) + 1L
  result <- palette_values[pmax(1L, pmin(n, index))]
  result[is.na(values)] <- na_colour
  result
}

draw_map_panel <- function(rings, values_by_code, limits, palette, title, subtitle = NULL, na_colour = "grey88") {
  x_all <- unlist(lapply(rings, `[[`, "x"), use.names = FALSE)
  y_all <- unlist(lapply(rings, `[[`, "y"), use.names = FALSE)
  xlim <- range(x_all)
  ylim <- range(y_all)

  graphics::plot.new()
  graphics::plot.window(xlim = xlim, ylim = ylim, asp = 1)
  for (ring in rings) {
    code <- sprintf("%02d", ring$code)
    fill <- value_colours(values_by_code[[code]], limits, palette, na_colour = na_colour)
    graphics::polygon(ring$x, ring$y, col = fill, border = "white", lwd = 0.25)
  }
  graphics::box(col = "grey72", lwd = 0.4)
  graphics::title(main = title, cex.main = 1.0, line = 0.2)
  if (!is.null(subtitle)) graphics::mtext(subtitle, side = 3, line = -1.0, cex = 0.72, col = "grey30")
}

draw_colour_legend <- function(limits, palette, label, digits = 1L, suffix = "", midpoint = NULL) {
  n <- 100L
  cols <- grDevices::colorRampPalette(palette)(n)
  graphics::plot.new()
  graphics::plot.window(xlim = c(0, 1), ylim = limits)
  ys <- seq(limits[[1L]], limits[[2L]], length.out = n + 1L)
  for (i in seq_len(n)) graphics::rect(0.10, ys[[i]], 0.52, ys[[i + 1L]], col = cols[[i]], border = NA)
  ticks <- if (is.null(midpoint)) {
    pretty(limits, n = 5L)
  } else {
    sort(unique(c(pretty(limits, n = 5L), midpoint)))
  }
  ticks <- ticks[ticks >= limits[[1L]] & ticks <= limits[[2L]]]
  graphics::axis(4, at = ticks, labels = paste0(formatC(ticks, format = "f", digits = digits), suffix), las = 1, cex.axis = 0.72, lwd = 0, lwd.ticks = 0.35)
  graphics::mtext(label, side = 4, line = 2.8, cex = 0.78)
}

save_triptych_map <- function(path, rings, value_sets, limits, palette, titles, legend_label, digits = 1L, suffix = "", midpoint = NULL) {
  grDevices::png(path, width = 2400, height = 940, res = 180)
  old <- graphics::par(no.readonly = TRUE)
  on.exit({ graphics::par(old); grDevices::dev.off() }, add = TRUE)
  graphics::layout(matrix(c(1, 2, 3, 4), nrow = 1L), widths = c(1, 1, 1, 0.22))
  for (i in seq_along(value_sets)) {
    graphics::par(mar = c(0.5, 0.5, 2.3, 0.2), family = "Hiragino Sans")
    draw_map_panel(rings, value_sets[[i]], limits, palette, titles[[i]])
  }
  graphics::par(mar = c(3.3, 0.1, 2.3, 3.9), family = "Hiragino Sans")
  draw_colour_legend(limits, palette, legend_label, digits, suffix, midpoint)
}

save_double_map <- function(path, rings, value_sets, limits, palette, titles, legend_label, digits = 1L, suffix = "", midpoint = NULL) {
  grDevices::png(path, width = 1900, height = 940, res = 180)
  old <- graphics::par(no.readonly = TRUE)
  on.exit({ graphics::par(old); grDevices::dev.off() }, add = TRUE)
  graphics::layout(matrix(c(1, 2, 3), nrow = 1L), widths = c(1, 1, 0.22))
  for (i in seq_along(value_sets)) {
    graphics::par(mar = c(0.5, 0.5, 2.3, 0.2), family = "Hiragino Sans")
    draw_map_panel(rings, value_sets[[i]], limits, palette, titles[[i]])
  }
  graphics::par(mar = c(3.3, 0.1, 2.3, 3.9), family = "Hiragino Sans")
  draw_colour_legend(limits, palette, legend_label, digits, suffix, midpoint)
}

save_single_map <- function(path, rings, values, limits, palette, title, legend_label, digits = 1L, suffix = "", midpoint = NULL) {
  grDevices::png(path, width = 1800, height = 1050, res = 180)
  old <- graphics::par(no.readonly = TRUE)
  on.exit({ graphics::par(old); grDevices::dev.off() }, add = TRUE)
  graphics::layout(matrix(c(1, 2), nrow = 1L), widths = c(1, 0.16))
  graphics::par(mar = c(0.6, 0.6, 2.5, 0.2), family = "Hiragino Sans")
  draw_map_panel(rings, values, limits, palette, title)
  graphics::par(mar = c(3.4, 0.1, 2.5, 4.4), family = "Hiragino Sans")
  draw_colour_legend(limits, palette, legend_label, digits, suffix, midpoint)
}

save_patient_supply_scatter <- function(path, pooled) {
  group_levels <- c("患者側・供給側とも低い", "患者側高・供給側低い", "患者側低い・供給側高", "患者側・供給側とも高い")
  group_labels <- c("患者側・供給側とも低い", "患者側のみ高い", "供給側のみ高い", "患者側・供給側とも高い")
  group_colours <- c("#a6a6a6", "#ef8a62", "#67a9cf", "#1b7837")
  group <- factor(pooled$patient_supply_type, levels = group_levels)
  y <- pooled$supply_standardized_mean_pct
  x <- pooled$patient_online_rate_mean_pct

  grDevices::png(path, width = 1600, height = 1120, res = 180)
  old <- graphics::par(no.readonly = TRUE)
  on.exit({ graphics::par(old); grDevices::dev.off() }, add = TRUE)
  graphics::par(mar = c(5.2, 5.4, 3.9, 1.0), family = "Hiragino Sans")
  graphics::plot(
    x, y,
    log = "y", pch = 21, bg = group_colours[as.integer(group)], col = "white", cex = 1.35,
    xlab = "患者側：オンライン診療利用率（2022–2024年平均、%）",
    ylab = "供給側：NDB算定割合（2022–2024年度平均、医療機関所在地、%）",
    main = "患者居住地の利用経験と医療機関所在地の保険診療算定は一致しない",
    sub = "各点は都道府県。破線は各指標の中央値。患者側は需要そのものではなく、インターネット利用者の自己申告による利用経験。"
  )
  graphics::abline(v = stats::median(x), h = stats::median(y), lty = 2, col = "grey45", lwd = 1)
  # 全県名ではなく、分布の読み取りを左右する外れ値だけを示す。
  labelled_prefectures <- c("東京都", "島根県", "熊本県", "岡山県", "和歌山県", "広島県")
  labelled <- match(labelled_prefectures, pooled$prefecture_name)
  label_text <- sub("[都府県]$", "", pooled$prefecture_name[labelled])
  label_pos <- c(2, 2, 4, 2, 4, 4)
  graphics::text(x[labelled], y[labelled], labels = label_text, pos = label_pos, offset = 0.55, cex = 0.82, col = "#222222")
  graphics::legend("bottomright", legend = group_labels, pt.bg = group_colours, pch = 21, col = "white", bty = "n", cex = 0.82, title = "相対的位置")
}

rings <- read_prefecture_rings(geo_path)
patient <- read_utf8_csv(file.path(table_dir, "patient_survey_prefecture.csv"))
pooled <- read_utf8_csv(file.path(table_dir, "patient_supply_pooled_summary.csv"))
change <- read_utf8_csv(file.path(table_dir, "patient_location_change_2022_2024.csv"))

patient$prefecture_code <- sprintf("%02d", as.integer(patient$prefecture_code))
pooled$prefecture_code <- sprintf("%02d", as.integer(pooled$prefecture_code))
change$prefecture_code <- sprintf("%02d", as.integer(change$prefecture_code))

patient_values <- lapply(2022:2024, function(year) {
  d <- patient[patient$year == year & patient$level == "都道府県", ]
  stats::setNames(d$patient_online_rate_pct, d$prefecture_code)
})
rate_limit <- c(0, ceiling(max(patient$patient_online_rate_pct, na.rm = TRUE) * 2) / 2)
save_triptych_map(
  file.path(fig_dir, "figure4_patient_prefecture_map.png"), rings, patient_values, rate_limit,
  c("#fff7ec", "#f16913", "#7f2704"), c("2022年", "2023年", "2024年"),
  "患者側のオンライン診療利用率（%）", digits = 1L, suffix = "%"
)

# 患者所在地の集計レポートでも同じラベルなし地図を参照できるよう、同じ画像を保存する。
file.copy(
  file.path(fig_dir, "figure4_patient_prefecture_map.png"),
  file.path(fig_dir, "figure18_patient_location_rate_map.png"), overwrite = TRUE
)

rank_values <- list(
  stats::setNames(pooled$patient_mean_rank, pooled$prefecture_code),
  stats::setNames(pooled$supply_mean_rank, pooled$prefecture_code),
  stats::setNames(pooled$rank_gap_mean, pooled$prefecture_code)
)
save_double_map(
  file.path(fig_dir, "figure20_patient_provider_rank_maps.png"), rings, rank_values[1:2], c(1, 47),
  c("#f7fbff", "#6baed6", "#08306b"), c("患者側：利用率順位", "供給側：NDB算定割合順位"),
  "順位（高いほど濃色）", digits = 0L
)

# 3枚目の順位差地図は単独で読みやすくし、同一図の別ファイルとしても利用する。
gap_limit <- max(abs(pooled$rank_gap_mean), na.rm = TRUE)
save_single_map(
  file.path(fig_dir, "figure22_patient_provider_rank_gap_map.png"), rings, rank_values[[3L]], c(-gap_limit, gap_limit),
  c("#b2182b", "#f7f7f7", "#2166ac"), "供給側順位 − 患者側順位（2022–2024年平均）",
  "順位差（正＝供給側が相対的に高い）", digits = 0L, midpoint = 0
)

change_values <- stats::setNames(change$change_2022_2024_pct_points, change$prefecture_code)
change_limit <- ceiling(max(abs(change$change_2022_2024_pct_points), na.rm = TRUE) * 2) / 2
save_single_map(
  file.path(fig_dir, "figure19_patient_location_change_map.png"), rings, change_values, c(-change_limit, change_limit),
  c("#b2182b", "#f7f7f7", "#2166ac"), "患者側オンライン診療利用率の変化（2022年→2024年）",
  "変化（パーセントポイント）", digits = 1L, suffix = " pp", midpoint = 0
)
file.copy(
  file.path(fig_dir, "figure19_patient_location_change_map.png"),
  file.path(fig_dir, "figure18_patient_location_change_map.png"), overwrite = TRUE
)

save_patient_supply_scatter(file.path(fig_dir, "figure21_patient_provider_scatter.png"), pooled)

message("R標準描画による患者地理図を出力しました: ", fig_dir)
