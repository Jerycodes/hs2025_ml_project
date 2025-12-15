# Experiment-Timeline und Resultate (auto-generiert)

Stand: 2025-12-13

Dieses Dokument wurde aus folgenden Quellen rekonstruiert:
- `data/processed/experiments/*_config.json` (Label-Parameter)
- `notebooks/results/**/*.json` und `results/*.json` (Metriken + Modellkonfig)
- Git-Historie (Einführungsdatum je Datei)

## Glossar der Abkürzungen

- `EXP_ID`: Eindeutiger Name für ein Experiment; steuert welche Config/Labels/Datasets/Results zusammengehören.
- `h4 / h5 / h6`: Horizont in Tagen (label_params.horizon_days).
- `thr0p5pct`: Schwelle (threshold) in Prozent. '0p5' bedeutet 0.5% = 0.005.
- `strict`: strict_monotonic=True: Pfad muss streng steigen/fallen (sehr strikt).
- `relaxed`: strict_monotonic=False ohne zusätzliche Toleranz.
- `tolerant / tol0p3pct`: max_adverse_move_pct gesetzt (z.B. 0.3% = 0.003): Pfad darf nur begrenzt gegen die Richtung laufen.
- `hit`: hit_within_horizon=True: Schwelle muss irgendwo im Fenster [t..t+h] getroffen werden, nicht zwingend am Endtag.
- `p_pct_55p / 6p / 7p`: Signal-Probability-Threshold für Stufe 1: 55p = 0.55, 6p = 0.60, 7p = 0.70 (siehe config.signal_threshold).
- `spw1p0`: scale_pos_weight=1.0 für das Signal-Modell (Move/Neutral gleich gewichten statt automatisch).
- `sigdepth2 / sigdepth4`: max_depth des Signal-Modells (Baumtiefe) wurde verändert.
- `30dfeat`: 30-Tage-Preis-Historie-Features wurden hinzugefügt (z.B. price_close_ret_30d, price_range_pct_30d_std).
- `hp*`: Price-only Baseline (News werden nicht verwendet; im Final-Notebook wird feature_mode='price_only' gesetzt).
- `hp_long*`: Price-only Baseline mit längeren/weiteren Runs (mehr Vergleiche, oft mit kostenbasierten Thresholds).
- `*_eod*`: EODHD-Preisquelle statt Yahoo (price_source='eodhd', Datei EURUSDX_eodhd.csv).
- `v*/nv*/hv*/s*`: Experiment-Serien: v=frühe Baselines, nv=große Variantenserie, hv=hit-within-horizon Serie, s=up/down-only Analysen.

## Gesamt-Timeline (alle Experimente)

| Date | Series | EXP_ID | Label-Params | feature_mode | n_feat | thr_sig | thr_trade | thr_down/up | Test: F1(move) | Test: F1(up) | Test: macroF1(3c) | Δ vs prev (Serie) |
|---|---|---|---|---|---:|---:|---:|---|---:|---:|---:|---|
| 2025-11-15 | v | v0_h4_thr1pct_strict | h=4, up=1.00%, down=-1.00%, strict=True, tol=— | — | 35 | — | — | — | 0.242 | 0.889 | 0.464 | — |
| 2025-11-15 | v | v1_h4_thr0p5pct_strict | h=4, up=0.50%, down=-0.50%, strict=True, tol=— | — | 35 | — | — | — | 0.217 | 0.600 | 0.412 | Up-Schwelle: 1.00% → 0.50%; Down-Schwelle: -1.00% → -0.50%; Signal-scale_pos_weight: 10.63076923076923 → 7.689655172413793 |
| 2025-11-18 | v | v2_h4_thr0p5pct_strict_newfeat | h=4, up=0.50%, down=-0.50%, strict=True | — | 32 | — | — | — | 0.217 | 0.667 | 0.446 | Feature-Anzahl: 35 → 32 |
| 2025-11-18 | v | v3_h4_thr0p3pct_relaxed | h=4, up=0.30%, down=-0.30%, strict=False, tol=— | — | 35 | — | — | — | 0.747 | 0.690 | 0.457 | Up-Schwelle: 0.50% → 0.30%; Down-Schwelle: -0.50% → -0.30%; strict_monotonic: True → False; … |
| 2025-11-18 | v | v5_h4_thr0p5pct_tolerant0p3pct_spw1p0 | h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30% | — | 32 | — | — | — | 0.535 | 0.773 | 0.430 | Up-Schwelle: 0.30% → 0.50%; Down-Schwelle: -0.30% → -0.50%; max_adverse_move_pct: — → 0.30%; … |
| 2025-11-19 | v | v4_h4_thr0p5pct_tolerant0p3pct | h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30% | — | 35 | — | — | — | 0.602 | 0.750 | 0.477 | Feature-Anzahl: 32 → 35 |
| 2025-11-19 | v | v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2 | h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30% | — | 32 | — | — | — | 0.337 | 0.773 | 0.350 | Feature-Anzahl: 35 → 32; Signal-max_depth: 3 → 2; Signal-subsample: 0.9 → 0.8; … |
| 2025-11-19 | v | v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600 | h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30% | — | 32 | — | — | — | 0.537 | 0.773 | 0.437 | Signal-max_depth: 2 → 4; Signal-subsample: 0.8 → 0.9; Signal-colsample_bytree: 0.8 → 0.9; … |
| 2025-11-19 | v | v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain | h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30% | — | 32 | — | — | — | 0.592 | 0.773 | 0.416 | Signal-max_depth: 4 → 3; Signal-scale_pos_weight: 1.2366863905325445 → 0.25098039215686274 |
| 2025-11-19 | s | s1_h4_thr0p5pct_tol0p3 | h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30% | — | 32 | — | — | — | — | — | — | — |
| 2025-11-21 | v | v9_h4_thr0p5pct_tol0p3_30dfeat | h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30% | — | 32 | — | — | — | 0.535 | 0.773 | 0.430 | Signal-scale_pos_weight: 0.25098039215686274 → 1.2366863905325445 |
| 2025-11-21 | v | v10_h4_thr0p3pct_tol0p3_30dfeat | h=4, up=0.30%, down=-0.30%, strict=False, tol=0.30% | — | 32 | — | — | — | — | — | — | Up-Schwelle: 0.50% → 0.30%; Down-Schwelle: -0.50% → -0.30% |
| 2025-11-21 | s | s2_h4_thr0p5pct_tol0p3 | h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30% | — | 32 | — | — | — | — | — | — | — |
| 2025-11-21 | s | s3a_h4_thr0p3pct_tol0p3_30dfeat | h=4, up=0.30%, down=-0.30%, strict=False, tol=0.30% | — | 32 | — | — | — | — | — | — | Up-Schwelle: 0.50% → 0.30%; Down-Schwelle: -0.50% → -0.30% |
| 2025-11-21 | s | s3b_h4_thr0p3pct_tol0p3_30dfeat | h=4, up=0.30%, down=-0.30%, strict=False, tol=0.30% | — | 32 | — | — | — | — | — | — | — |
| 2025-11-22 | nv | nv1_h4_thr0p7pct_tolerant0p3pct | h=4, up=0.70%, down=-0.70%, strict=False, tol=0.30% | — | 35 | — | — | — | 0.430 | 0.716 | 0.408 | — |
| 2025-11-22 | nv | nv2_h4_thr0p_8pct_tolerant0p4pct | h=4, up=0.80%, down=-0.80%, strict=False, tol=0.40% | — | 35 | — | — | — | 0.450 | 0.721 | 0.427 | Up-Schwelle: 0.70% → 0.80%; Down-Schwelle: -0.70% → -0.80%; max_adverse_move_pct: 0.30% → 0.40%; … |
| 2025-11-22 | nv | nv3_h4_thr0p_65pct_tolerant0p35pct | h=4, up=0.65%, down=-0.65%, strict=False, tol=0.35% | — | 35 | — | — | — | 0.553 | 0.718 | 0.456 | Up-Schwelle: 0.80% → 0.65%; Down-Schwelle: -0.80% → -0.65%; max_adverse_move_pct: 0.40% → 0.35%; … |
| 2025-11-22 | nv | nv4_h4_thr0p_65pct_tolerant0p15pct | h=4, up=0.65%, down=-0.65%, strict=False, tol=0.15% | — | 35 | — | — | — | 0.405 | 0.783 | 0.436 | max_adverse_move_pct: 0.35% → 0.15%; Signal-scale_pos_weight: 1.5627118644067797 → 1.8854961832061068 |
| 2025-11-28 | nv | nv5_h4_thr0p_65pct_tolerant0p15pct_7p | h=4, up=0.65%, down=-0.65%, strict=False, tol=0.15% | — | 35 | 0.70 | — | — | 0.066 | 0.783 | 0.275 | Signal-Threshold: None → 0.7 |
| 2025-11-28 | nv | nv6_h4_thr0p_6pct_tolerant0p15pct_6p | h=4, up=0.60%, down=-0.60%, strict=False, tol=0.20% | — | 35 | 0.60 | — | — | 0.260 | 0.752 | 0.371 | Up-Schwelle: 0.65% → 0.60%; Down-Schwelle: -0.65% → -0.60%; max_adverse_move_pct: 0.15% → 0.20%; … |
| 2025-11-28 | nv | nv7_h4_thr0p_6pct_tolerant0p2pct_7p | h=4, up=0.60%, down=-0.60%, strict=False, tol=0.20% | — | 35 | 0.70 | — | — | 0.061 | 0.752 | 0.282 | Signal-Threshold: 0.6 → 0.7 |
| 2025-11-28 | nv | nv8_h4_thr0p_6pct_tolerant0p2pct_6p | h=4, up=0.60%, down=-0.60%, strict=False, tol=0.20% | — | 35 | 0.60 | — | — | 0.260 | 0.752 | 0.371 | Signal-Threshold: 0.7 → 0.6 |
| 2025-11-28 | nv | nv9_h4_thr0p_55pct_tolerant0p2pct_6p | h=4, up=0.55%, down=-0.55%, strict=False, tol=0.20% | — | 35 | 0.60 | — | — | 0.234 | 0.743 | 0.373 | Up-Schwelle: 0.60% → 0.55%; Down-Schwelle: -0.60% → -0.55%; Signal-scale_pos_weight: 1.6433566433566433 → 1.5116279069767442 |
| 2025-11-28 | nv | nv10_h4_thr0p_55pct_tolerant0p1pct_6p | h=4, up=0.55%, down=-0.55%, strict=False, tol=0.10% | — | 35 | 0.60 | — | — | 0.217 | 0.804 | 0.364 | max_adverse_move_pct: 0.20% → 0.10%; Signal-scale_pos_weight: 1.5116279069767442 → 1.7 |
| 2025-11-28 | nv | nv11_h4_thr0p_4pct_tolerant0p1pct_6p | h=4, up=0.40%, down=-0.40%, strict=False, tol=0.10% | — | 35 | 0.60 | — | — | 0.128 | 0.810 | 0.294 | Up-Schwelle: 0.55% → 0.40%; Down-Schwelle: -0.55% → -0.40%; Signal-scale_pos_weight: 1.7 → 1.166189111747851 |
| 2025-11-28 | nv | nv12_h4_thr0p_3pct_tolerant0p1pct_6p | h=4, up=0.30%, down=-0.30%, strict=False, tol=0.10% | — | 35 | 0.60 | — | — | 0.000 | 0.819 | 0.193 | Up-Schwelle: 0.40% → 0.30%; Down-Schwelle: -0.40% → -0.30%; Signal-scale_pos_weight: 1.166189111747851 → 0.9585492227979274 |
| 2025-11-28 | nv | nv13_h4_thr0p_3pct_tolerant0p1pct_4p | h=4, up=0.30%, down=-0.30%, strict=False, tol=0.10% | — | 35 | 0.40 | — | — | 0.744 | 0.819 | 0.394 | Signal-Threshold: 0.6 → 0.4 |
| 2025-11-28 | nv | nv14_h4_thr0p_3pct_tolerant0p1pct_51p | h=4, up=0.30%, down=-0.30%, strict=False, tol=0.10% | — | 35 | 0.51 | — | — | 0.111 | 0.819 | 0.255 | Signal-Threshold: 0.4 → 0.51 |
| 2025-11-28 | nv | nv15_h4_thr0p_3pct_tolerant0p1pct_5p | h=4, up=0.30%, down=-0.30%, strict=False, tol=0.10% | — | 35 | 0.50 | — | — | 0.200 | 0.819 | 0.283 | Signal-Threshold: 0.51 → 0.5 |
| 2025-11-28 | nv | nv16_h4_thr0p_3pct_tolerant0p1pct_5p | h=4, up=0.30%, down=-0.30%, strict=False, tol=— | — | 35 | 0.50 | — | — | 0.747 | 0.690 | 0.457 | max_adverse_move_pct: 0.10% → —; Signal-scale_pos_weight: 0.9585492227979274 → 0.37454545454545457 |
| 2025-11-28 | nv | nv17_h4_thr0p_3pct_tolerant0p1pct_6p | h=4, up=0.30%, down=-0.30%, strict=False, tol=— | — | 35 | 0.60 | — | — | 0.600 | 0.690 | 0.451 | Signal-Threshold: 0.5 → 0.6 |
| 2025-11-28 | nv | nv18_h4_thr0p_3pct_tolerant0p1pct_7p | h=4, up=0.30%, down=-0.30%, strict=False, tol=— | — | 35 | 0.70 | — | — | 0.220 | 0.690 | 0.231 | Signal-Threshold: 0.6 → 0.7 |
| 2025-11-28 | nv | nv19_h4_thr0p_3pct_tolerant0p1pct_55p | h=4, up=0.30%, down=-0.30%, strict=False, tol=— | — | 35 | 0.55 | — | — | 0.676 | 0.690 | 0.455 | Signal-Threshold: 0.7 → 0.55 |
| 2025-11-28 | nv | nv20_h4_thr0p_6pct_tolerant0p1pct_55p | h=4, up=0.60%, down=-0.60%, strict=False, tol=— | — | 35 | 0.55 | — | — | 0.546 | 0.690 | 0.446 | Up-Schwelle: 0.30% → 0.60%; Down-Schwelle: -0.30% → -0.60%; Signal-scale_pos_weight: 0.37454545454545457 → 1.16 |
| 2025-11-28 | nv | nv21_h4_thr0p_6pct_tolerant0p6pct_55p | h=4, up=0.60%, down=-0.60%, strict=False, tol=60.00% | — | 35 | 0.55 | — | — | 0.546 | 0.690 | 0.446 | max_adverse_move_pct: — → 60.00% |
| 2025-11-28 | nv | nv22_h4_thr0p_3pct_tolerant_p_pct_55p | h=4, up=0.30%, down=-0.30%, strict=False, tol=— | — | 35 | 0.55 | — | — | 0.676 | 0.690 | 0.455 | Up-Schwelle: 0.60% → 0.30%; Down-Schwelle: -0.60% → -0.30%; max_adverse_move_pct: 60.00% → —; … |
| 2025-11-28 | nv | nv23_h3_thr0p_3pct_tolerant_p_pct_55p | h=3, up=0.30%, down=-0.30%, strict=False, tol=— | — | 35 | 0.55 | — | — | 0.691 | 0.720 | 0.435 | Horizont (h): 4 → 3; Signal-scale_pos_weight: 0.37454545454545457 → 0.4482758620689655 |
| 2025-11-28 | nv | nv24_h6_thr0p_6pct_tolerant_p_pct_55p | h=6, up=0.60%, down=-0.60%, strict=False, tol=— | — | 35 | 0.55 | — | — | 0.000 | 0.602 | 0.207 | Horizont (h): 3 → 6; Up-Schwelle: 0.30% → 0.60%; Down-Schwelle: -0.30% → -0.60%; … |
| 2025-11-28 | nv | nv25_h6_thr1p_0pct_tolerant_p_pct_55p | h=6, up=1.00%, down=-1.00%, strict=False, tol=— | — | 35 | 0.55 | — | — | 0.359 | 0.667 | 0.402 | Up-Schwelle: 0.60% → 1.00%; Down-Schwelle: -0.60% → -1.00%; Signal-scale_pos_weight: 0.7704918032786885 → 2.0119521912350598 |
| 2025-11-28 | nv | nv26_h6_thr1p_0pct_strict_p_pct_55p | h=6, up=1.00%, down=-1.00%, strict=True, tol=— | — | 35 | 0.55 | — | — | 0.000 | 1.000 | 0.330 | strict_monotonic: False → True; Signal-scale_pos_weight: 2.0119521912350598 → 38.78947368421053 |
| 2025-11-28 | nv | nv26_h6_thr1p_0pct_tolerant_p_pct_55p | h=6, up=1.00%, down=-1.00%, strict=True, tol=— | — | 35 | 0.55 | — | — | 0.000 | 1.000 | 0.330 | — |
| 2025-11-28 | nv | nv27_h6_thr1p_0pct_tolerant_p_pct_5p | h=6, up=1.00%, down=-1.00%, strict=False, tol=0.50% | — | 35 | 0.50 | — | — | 0.365 | 0.819 | 0.432 | strict_monotonic: True → False; max_adverse_move_pct: — → 0.50%; Signal-Threshold: 0.55 → 0.5; … |
| 2025-11-28 | nv | nv28_h6_thr1p_5pct_tolerant_p_pct_5p | h=6, up=1.50%, down=-1.50%, strict=False, tol=— | — | 35 | 0.50 | — | — | 0.160 | 0.727 | 0.325 | Up-Schwelle: 1.00% → 1.50%; Down-Schwelle: -1.00% → -1.50%; max_adverse_move_pct: 0.50% → —; … |
| 2025-11-28 | nv | nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p | h=4, up=0.30%, down=-0.30%, strict=False, tol=1.55% | — | 35 | 0.50 | — | — | 0.747 | 0.690 | 0.457 | Horizont (h): 6 → 4; Up-Schwelle: 1.50% → 0.30%; Down-Schwelle: -1.50% → -0.30%; … |
| 2025-11-28 | nv | nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p | h=4, up=0.30%, down=-0.30%, strict=False, tol=1.55% | — | 35 | 0.55 | — | — | 0.676 | 0.690 | 0.455 | Signal-Threshold: 0.5 → 0.55 |
| 2025-11-28 | nv | nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p | h=4, up=0.30%, down=-0.30%, strict=False, tol=1.00% | — | 35 | 0.60 | — | — | 0.614 | 0.702 | 0.418 | max_adverse_move_pct: 1.55% → 1.00%; Signal-Threshold: 0.55 → 0.6; Signal-scale_pos_weight: 0.37454545454545457 → 0.3974121996303142 |
| 2025-11-28 | nv | nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p | h=4, up=0.30%, down=-0.30%, strict=False, tol=1.00% | — | 35 | 0.57 | — | — | 0.650 | 0.702 | 0.421 | Signal-Threshold: 0.6 → 0.575 |
| 2025-11-28 | nv | nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p | h=3, up=0.30%, down=-0.30%, strict=False, tol=1.00% | — | 35 | 0.55 | — | — | 0.000 | 0.720 | 0.154 | Horizont (h): 4 → 3; Signal-Threshold: 0.575 → 0.55; Signal-scale_pos_weight: 0.3974121996303142 → 0.45664739884393063 |
| 2025-11-28 | nv | nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p | h=5, up=0.30%, down=-0.30%, strict=False, tol=1.00% | — | 35 | 0.55 | — | — | 0.730 | 0.649 | 0.483 | Horizont (h): 3 → 5; Signal-scale_pos_weight: 0.45664739884393063 → 0.3820840950639854 |
| 2025-11-28 | nv | nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p | h=5, up=0.40%, down=-0.40%, strict=False, tol=1.00% | — | 35 | 0.55 | — | — | 0.000 | 0.628 | 0.176 | Up-Schwelle: 0.30% → 0.40%; Down-Schwelle: -0.30% → -0.40%; Signal-scale_pos_weight: 0.3820840950639854 → 0.5365853658536586 |
| 2025-11-28 | nv | nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p | h=5, up=0.35%, down=-0.35%, strict=False, tol=1.00% | — | 35 | 0.55 | — | — | 0.000 | 0.603 | 0.163 | Up-Schwelle: 0.40% → 0.35%; Down-Schwelle: -0.40% → -0.35%; Signal-scale_pos_weight: 0.5365853658536586 → 0.4594594594594595 |
| 2025-11-28 | hv | hv1_h4_thr0p3pct_hit | h=4, up=0.30%, down=-0.30%, strict=False, tol=1.00%, hit=True | — | 35 | 0.55 | — | — | 0.962 | 0.700 | 0.457 | — |
| 2025-11-28 | hv | hv2_h4_thr0p4pct_hit | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | — | 35 | 0.55 | — | — | 0.900 | 0.731 | 0.491 | Up-Schwelle: 0.30% → 0.40%; Down-Schwelle: -0.30% → -0.40%; Signal-scale_pos_weight: 0.07539118065433854 → 0.18309859154929578 |
| 2025-11-28 | hv | hv3_h4_thr0p5pct_hit | h=4, up=0.50%, down=-0.50%, strict=False, tol=1.00%, hit=True | — | 35 | 0.55 | — | — | 0.863 | 0.755 | 0.530 | Up-Schwelle: 0.40% → 0.50%; Down-Schwelle: -0.40% → -0.50%; Signal-scale_pos_weight: 0.18309859154929578 → 0.33568904593639576 |
| 2025-11-28 | hv | hv4_h4_thr0p4pct_hit | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | — | 35 | 0.50 | — | — | 0.914 | 0.731 | 0.501 | Up-Schwelle: 0.50% → 0.40%; Down-Schwelle: -0.50% → -0.40%; Signal-Threshold: 0.55 → 0.5; … |
| 2025-11-28 | hv | hv5_h4_thr0p4pct_hit | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | — | 35 | 0.50 | — | — | 0.914 | 0.756 | 0.494 | — |
| 2025-11-28 | hv | hv5_h4_thr0p4pct_hit_2 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | — | 35 | 0.50 | — | — | 0.914 | 0.756 | 0.494 | — |
| 2025-11-29 | hv | hv5_h4_thr0p4pct_hit_3 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | — | 35 | 0.50 | — | — | 0.914 | 0.756 | 0.494 | — |
| 2025-11-29 | hv | hv5_h4_thr0p4pct_hit_4 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | — | 35 | 0.50 | — | — | 0.914 | 0.756 | 0.494 | — |
| 2025-11-29 | hv | hv5_h4_thr0p4pct_hit_5 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | — | 35 | 0.50 | — | — | 0.914 | 0.756 | 0.494 | — |
| 2025-11-30 | hv | hv5_h4_thr0p4pct_hit_6 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | — | 35 | 0.50 | — | 0.3/0.625 | 0.914 | 0.756 | 0.451 | Direction-Thresholds: down None→0.3, up None→0.625 |
| 2025-11-30 | hv | hv5_h4_thr0p4pct_hit_6_2 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | news+price | 35 | 0.50 | 0.70 | 0.3/0.625 | 0.914 | 0.756 | 0.433 | Trade-Signal-Threshold: None → 0.7; feature_mode: None → news+price |
| 2025-11-30 | hp1 | hp1_h4_thr0p4pct_hit_1 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | price_only | 21 | 0.50 | — | 0.3/0.5249999999999999 | 0.920 | 0.760 | 0.475 | — |
| 2025-11-30 | hpL | hpL1_h4_thr0p4pct_hit_1 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | price_only | 21 | 0.50 | — | 0.3/0.5249999999999999 | 0.920 | 0.760 | 0.475 | — |
| 2025-11-30 | hp_long | hp_long1_h4_thr0p4pct_hit_1 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | price_only | 21 | 0.50 | — | 0.3/0.6749999999999999 | 0.920 | 0.763 | 0.413 | — |
| 2025-11-30 | hp_long | hp_long_h4_thr0p4pct_hit_1 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | price_only | 21 | 0.50 | — | 0.3/0.6749999999999999 | 0.920 | 0.763 | 0.413 | — |
| 2025-11-30 | hp_long | hp_long_h4_thr0p4pct_hit_1_2 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | price_only | 21 | 0.50 | 0.42 | 0.3/0.6749999999999999 | 0.920 | 0.763 | 0.412 | Trade-Signal-Threshold: None → 0.425 |
| 2025-11-30 | hp_long | hp_long_h4_thr0p4pct_hit_1_3 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | price_only | 16 | 0.50 | 0.50 | 0.3/0.7 | 0.914 | 0.750 | 0.428 | Trade-Signal-Threshold: 0.425 → 0.5; Direction-Thresholds: down 0.3→0.3, up 0.6749999999999999→0.7; Feature-Anzahl: 21 → 16 |
| 2025-11-30 | hp_long | hp_long_h4_thr0p4pct_hit_1_4 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True | price_only | 25 | 0.50 | 0.70 | 0.3/0.7 | 0.931 | 0.757 | 0.410 | Trade-Signal-Threshold: 0.5 → 0.7; Feature-Anzahl: 16 → 25 |
| 2025-12-12 | hp_long_eod | hp_long_eod_h4_thr0p3pct_hit_7 | h=4, up=0.30%, down=-0.30%, strict=False, tol=1.00%, hit=True, src=eodhd | price_only | 21 | 0.50 | 0.30 | 0.3/0.5499999999999999 | 0.922 | 0.682 | 0.074 | — |
| 2025-12-12 | hp_long_eod | hp_long_eod_h4_thr0p4pct_hit_1 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True, src=eodhd | price_only | 21 | 0.50 | 0.50 | 0.375/0.6 | 0.621 | 0.695 | 0.111 | Up-Schwelle: 0.30% → 0.40%; Down-Schwelle: -0.30% → -0.40%; Trade-Signal-Threshold: 0.3 → 0.5; … |
| 2025-12-12 | hp_long_eod | hp_long_eod_h4_thr0p4pct_hit_2 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True, src=eodhd | price_only | 21 | 0.50 | 0.70 | 0.3/0.7 | 0.621 | 0.695 | 0.111 | Trade-Signal-Threshold: 0.5 → 0.7; Direction-Thresholds: down 0.375→0.3, up 0.6→0.7 |
| 2025-12-12 | hp_long_eod | hp_long_eod_h4_thr0p4pct_hit_8 | h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True, src=eodhd | price_only | 21 | 0.50 | 0.50 | 0.375/0.6 | 0.621 | 0.695 | 0.111 | Trade-Signal-Threshold: 0.7 → 0.5; Direction-Thresholds: down 0.3→0.375, up 0.7→0.6 |
| 2025-12-12 | hp_long_eod | hp_long_eod_h4_thr0p5pct_hit_3 | h=4, up=0.50%, down=-0.50%, strict=False, tol=1.00%, hit=True, src=eodhd | price_only | 21 | 0.50 | 0.30 | 0.475/0.5249999999999999 | 0.753 | 0.715 | 0.157 | Up-Schwelle: 0.40% → 0.50%; Down-Schwelle: -0.40% → -0.50%; Trade-Signal-Threshold: 0.5 → 0.3; … |
| 2025-12-12 | hp_long_eod | hp_long_eod_h4_thr0p6pct_hit_6 | h=4, up=0.60%, down=-0.60%, strict=False, tol=1.00%, hit=True, src=eodhd | price_only | 21 | 0.50 | 0.30 | 0.475/0.5249999999999999 | 0.700 | 0.728 | 0.204 | Up-Schwelle: 0.50% → 0.60%; Down-Schwelle: -0.50% → -0.60%; Signal-scale_pos_weight: 0.34125533211456427 → 0.5413165266106442 |
| 2025-12-12 | hp_long_eod | hp_long_eod_h5_thr0p4pct_hit_5 | h=5, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True, src=eodhd | price_only | 21 | 0.50 | 0.30 | 0.3/0.5249999999999999 | 0.582 | 0.681 | 0.072 | Horizont (h): 4 → 5; Up-Schwelle: 0.60% → 0.40%; Down-Schwelle: -0.60% → -0.40%; … |
| 2025-12-12 | hp_long_eod | hp_long_eod_h5_thr0p5pct_hit_4 | h=5, up=0.50%, down=-0.50%, strict=False, tol=1.00%, hit=True, src=eodhd | price_only | 21 | 0.50 | 0.50 | 0.39999999999999997/0.5499999999999999 | 0.762 | 0.687 | 0.154 | Up-Schwelle: 0.40% → 0.50%; Down-Schwelle: -0.40% → -0.50%; Trade-Signal-Threshold: 0.3 → 0.5; … |
| — | nv | nv1_h6_thr2p_tolerant0p4pct | h=6, up=20.00%, down=-20.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Horizont (h): 5 → 6; Up-Schwelle: 0.35% → 20.00%; Down-Schwelle: -0.35% → -20.00%; … |
| — | nv | nv2_4_thr0p_5pct_tolerant0p3pct | h=4, up=50.00%, down=-50.00%, strict=False, tol=0.30% | — | 0 | — | — | — | — | — | — | Horizont (h): 6 → 4; Up-Schwelle: 20.00% → 50.00%; Down-Schwelle: -20.00% → -50.00%; … |
| — | nv | nv2_4_thr0p_5pct_tolerant0p4pct | h=4, up=50.00%, down=-50.00%, strict=False, tol=0.30% | — | 0 | — | — | — | — | — | — | — |
| — | nv | nv2_4_thr0p_65pct_tolerant0p4pct | h=4, up=65.00%, down=-65.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 50.00% → 65.00%; Down-Schwelle: -50.00% → -65.00%; max_adverse_move_pct: 0.30% → 0.40% |
| — | nv | nv2_4_thr0p_6pct_tolerant0p4pct | h=4, up=60.00%, down=-60.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 65.00% → 60.00%; Down-Schwelle: -65.00% → -60.00% |
| — | nv | nv2_4_thr0p_7pct_tolerant0p4pct | h=4, up=70.00%, down=-70.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 60.00% → 70.00%; Down-Schwelle: -60.00% → -70.00% |
| — | nv | nv2_4_thr0p_8pct_tolerant0p4pct | h=4, up=80.00%, down=-80.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 70.00% → 80.00%; Down-Schwelle: -70.00% → -80.00% |
| — | nv | nv2_5_thr0p_9pct_tolerant0p4pct | h=5, up=90.00%, down=-90.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Horizont (h): 4 → 5; Up-Schwelle: 80.00% → 90.00%; Down-Schwelle: -80.00% → -90.00% |
| — | nv | nv2_5_thr1p_0pct_tolerant0p4pct | h=5, up=10.00%, down=-10.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 90.00% → 10.00%; Down-Schwelle: -90.00% → -10.00% |
| — | nv | nv2_6_thr0p_8pct_tolerant0p4pct | h=6, up=8.00%, down=-8.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Horizont (h): 5 → 6; Up-Schwelle: 10.00% → 8.00%; Down-Schwelle: -10.00% → -8.00% |
| — | nv | nv2_6_thr1p_0pct_tolerant0p1pct | h=6, up=10.00%, down=-10.00%, strict=False, tol=0.10% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 8.00% → 10.00%; Down-Schwelle: -8.00% → -10.00%; max_adverse_move_pct: 0.40% → 0.10% |
| — | nv | nv2_6_thr1p_0pct_tolerant0p4pct | h=6, up=10.00%, down=-10.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | max_adverse_move_pct: 0.10% → 0.40% |
| — | nv | nv2_h4_thr0p_5pct_tolerant0p4pct | h=4, up=5.00%, down=-5.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Horizont (h): 6 → 4; Up-Schwelle: 10.00% → 5.00%; Down-Schwelle: -10.00% → -5.00% |
| — | nv | nv2_h4_thr0p_65pct_tolerant0p4pct | h=4, up=6.50%, down=-6.50%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 5.00% → 6.50%; Down-Schwelle: -5.00% → -6.50% |
| — | nv | nv2_h4_thr0p_7pct_tolerant0p4pct | h=4, up=7.00%, down=-7.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 6.50% → 7.00%; Down-Schwelle: -6.50% → -7.00% |
| — | nv | nv2_h5_thr1p_5pct_tolerant0p4pct | h=5, up=15.00%, down=-15.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Horizont (h): 4 → 5; Up-Schwelle: 7.00% → 15.00%; Down-Schwelle: -7.00% → -15.00% |
| — | nv | nv2_h5_thr2p_tolerant0p4pct | h=5, up=20.00%, down=-20.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 15.00% → 20.00%; Down-Schwelle: -15.00% → -20.00% |
| — | nv | nv2_h6_thr1p_5pct_tolerant0p4pct | h=6, up=15.00%, down=-15.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Horizont (h): 5 → 6; Up-Schwelle: 20.00% → 15.00%; Down-Schwelle: -20.00% → -15.00% |
| — | nv | nv2_h6_thr2p_tolerant0p4pct | h=6, up=20.00%, down=-20.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 15.00% → 20.00%; Down-Schwelle: -15.00% → -20.00% |
| — | nv | nv2_h8_thr1p_5pct_tolerant0p4pct | h=8, up=15.00%, down=-15.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Horizont (h): 6 → 8; Up-Schwelle: 20.00% → 15.00%; Down-Schwelle: -20.00% → -15.00% |
| — | nv | nv3_h4_thr1p_5pct_tolerant0p5pct | h=4, up=1.50%, down=-15.00%, strict=False, tol=0.50% | — | 0 | — | — | — | — | — | — | Horizont (h): 8 → 4; Up-Schwelle: 15.00% → 1.50%; max_adverse_move_pct: 0.40% → 0.50% |
| — | nv | nv3_h4_thr2p_0pct_tolerant0p4pct | h=4, up=2.00%, down=-2.00%, strict=False, tol=0.40% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 1.50% → 2.00%; Down-Schwelle: -15.00% → -2.00%; max_adverse_move_pct: 0.50% → 0.40% |
| — | nv | nv3_h5_thr0p_9pct_tolerant0p5pct | h=5, up=0.90%, down=-9.00%, strict=False, tol=0.50% | — | 0 | — | — | — | — | — | — | Horizont (h): 4 → 5; Up-Schwelle: 2.00% → 0.90%; Down-Schwelle: -2.00% → -9.00%; … |
| — | nv | nv3_h5_thr1p_0pct_tolerant0p5pct | h=5, up=1.00%, down=-10.00%, strict=False, tol=0.50% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 0.90% → 1.00%; Down-Schwelle: -9.00% → -10.00% |
| — | nv | nv22_h4_thr0p_25pct_tolerant_p_pct_55p | h=4, up=0.25%, down=-2.50%, strict=False, tol=— | — | 0 | — | — | — | — | — | — | Horizont (h): 5 → 4; Up-Schwelle: 1.00% → 0.25%; Down-Schwelle: -10.00% → -2.50%; … |
| — | nv | nv22_h4_thr0p_3pct_tolerant_p_pct_51p | h=4, up=0.30%, down=-3.00%, strict=False, tol=— | — | 0 | — | — | — | — | — | — | Up-Schwelle: 0.25% → 0.30%; Down-Schwelle: -2.50% → -3.00% |
| — | nv | nv22_h4_thr0p_3pct_tolerant_p_pct_5p | h=4, up=0.30%, down=-3.00%, strict=False, tol=— | — | 0 | — | — | — | — | — | — | — |
| — | nv | nv27_h6_thr1p_0pct_strict_p_pct_5p | h=6, up=1.00%, down=-1.00%, strict=False, tol=0.50% | — | 0 | — | — | — | — | — | — | Horizont (h): 4 → 6; Up-Schwelle: 0.30% → 1.00%; Down-Schwelle: -3.00% → -1.00%; … |
| — | nv | nv28_h6_thr2p_0pct_tolerant_1p_pct_5p | h=6, up=2.00%, down=-2.00%, strict=False, tol=1.00% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 1.00% → 2.00%; Down-Schwelle: -1.00% → -2.00%; max_adverse_move_pct: 0.50% → 1.00% |
| — | nv | nv28_h6_thr2p_0pct_tolerant_p_pct_5p | h=6, up=2.00%, down=-2.00%, strict=False, tol=— | — | 0 | — | — | — | — | — | — | max_adverse_move_pct: 1.00% → — |
| — | nv | nv28_h6_thr3p_0pct_tolerant_1p_pct_5p | h=6, up=3.00%, down=-3.00%, strict=False, tol=1.00% | — | 0 | — | — | — | — | — | — | Up-Schwelle: 2.00% → 3.00%; Down-Schwelle: -2.00% → -3.00%; max_adverse_move_pct: — → 1.00% |
| — | nv | nv28_h6_thr3p_0pct_tolerant_p_pct_5p | h=6, up=3.00%, down=-3.00%, strict=False, tol=0.50% | — | 0 | — | — | — | — | — | — | max_adverse_move_pct: 1.00% → 0.50% |

## Detail pro Serie (was wurde jeweils verändert?)

### Serie `v` (11 Experimente)

#### v0_h4_thr1pct_strict
- Erstes Auftreten (Git): `2025-11-15`
- Config: `data/processed/experiments/v0_h4_thr1pct_strict_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__v0_h4_thr1pct_strict.json`
- Base-Result: `results/two_stage_v0_h4_thr1pct_strict.json`
- Label-Params: h=4, up=1.00%, down=-1.00%, strict=True, tol=—
- Features: 35 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.24242424242424243`
  - Direction F1(up): `0.8888888888888888` (F1(down): `0.9`)
  - Combined (3 Klassen) accuracy: `0.8853211009174312`, macro-F1: `0.46417023836378674`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### v1_h4_thr0p5pct_strict
- Erstes Auftreten (Git): `2025-11-15`
- Config: `data/processed/experiments/v1_h4_thr0p5pct_strict_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__v1_h4_thr0p5pct_strict.json`
- Base-Result: `notebooks/results/two_stage__v1_h4_thr0p5pct_strict.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=True, tol=—
- Features: 35 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.21739130434782608`
  - Direction F1(up): `0.6` (F1(down): `0.7142857142857143`)
  - Combined (3 Klassen) accuracy: `0.8302752293577982`, macro-F1: `0.4115246760408051`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 1.00% → 0.50%
  - Down-Schwelle: -1.00% → -0.50%
  - Signal-scale_pos_weight: 10.63076923076923 → 7.689655172413793

#### v2_h4_thr0p5pct_strict_newfeat
- Erstes Auftreten (Git): `2025-11-18`
- Config: `data/processed/experiments/v2_h4_thr0p5pct_strict_newfeat_config.json`
- Base-Result: `notebooks/results/two_stage__v2_h4_thr0p5pct_strict_newfeat.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=True
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.21739130434782608`
  - Direction F1(up): `0.6666666666666666` (F1(down): `0.7407407407407407`)
  - Combined (3 Klassen) accuracy: `0.8348623853211009`, macro-F1: `0.4461538461538462`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Feature-Anzahl: 35 → 32

#### v3_h4_thr0p3pct_relaxed
- Erstes Auftreten (Git): `2025-11-18`
- Config: `data/processed/experiments/v3_h4_thr0p3pct_relaxed_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__v3_h4_thr0p3pct_relaxed.json`
- Base-Result: `notebooks/results/two_stage__v3_h4_thr0p3pct_relaxed.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=—
- Features: 35 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.7468354430379747`
  - Direction F1(up): `0.6900584795321637` (F1(down): `0.6666666666666666`)
  - Combined (3 Klassen) accuracy: `0.46788990825688076`, macro-F1: `0.4570097077007304`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.50% → 0.30%
  - Down-Schwelle: -0.50% → -0.30%
  - strict_monotonic: True → False
  - Feature-Anzahl: 32 → 35
  - Signal-scale_pos_weight: 7.689655172413793 → 0.37454545454545457

#### v5_h4_thr0p5pct_tolerant0p3pct_spw1p0
- Erstes Auftreten (Git): `2025-11-18`
- Config: `data/processed/experiments/v5_h4_thr0p5pct_tolerant0p3pct_spw1p0_config.json`
- Base-Result: `notebooks/results/two_stage__v5_h4_thr0p5pct_tolerant0p3pct_spw1p0.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.5350877192982456`
  - Direction F1(up): `0.7727272727272727` (F1(down): `0.7`)
  - Combined (3 Klassen) accuracy: `0.44954128440366975`, macro-F1: `0.42984631647422344`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.30% → 0.50%
  - Down-Schwelle: -0.30% → -0.50%
  - max_adverse_move_pct: — → 0.30%
  - Feature-Anzahl: 35 → 32
  - Signal-scale_pos_weight: 0.37454545454545457 → 1.2366863905325445

#### v4_h4_thr0p5pct_tolerant0p3pct
- Erstes Auftreten (Git): `2025-11-19`
- Config: `data/processed/experiments/v4_h4_thr0p5pct_tolerant0p3pct_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__v4_h4_thr0p5pct_tolerant0p3pct.json`
- Base-Result: `notebooks/results/up_only__v4_h4_thr0p5pct_tolerant0p3pct.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30%
- Features: 35 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6016260162601627`
  - Direction F1(up): `0.75` (F1(down): `0.6923076923076923`)
  - Combined (3 Klassen) accuracy: `0.481651376146789`, macro-F1: `0.47741274828863195`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Feature-Anzahl: 32 → 35

#### v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2
- Erstes Auftreten (Git): `2025-11-19`
- Config: `data/processed/experiments/v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2_config.json`
- Base-Result: `notebooks/results/two_stage__v6_h4_thr0p5pct_tolerant0p3pct_sigdepth2.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.3372093023255814`
  - Direction F1(up): `0.7727272727272727` (F1(down): `0.7`)
  - Combined (3 Klassen) accuracy: `0.44036697247706424`, macro-F1: `0.3498521295428512`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Feature-Anzahl: 35 → 32
  - Signal-max_depth: 3 → 2
  - Signal-subsample: 0.9 → 0.8
  - Signal-colsample_bytree: 0.9 → 0.8
  - Signal-gamma: None → 1.0
  - Signal-min_child_weight: None → 5
  - Signal-scale_pos_weight: 1.2366863905325445 → 1.0

#### v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600
- Erstes Auftreten (Git): `2025-11-19`
- Config: `data/processed/experiments/v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600_config.json`
- Base-Result: `notebooks/results/two_stage__v7_h4_thr0p5pct_tolerant0p3pct_sigdepth4_n600.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.5374449339207048`
  - Direction F1(up): `0.7727272727272727` (F1(down): `0.7`)
  - Combined (3 Klassen) accuracy: `0.4541284403669725`, macro-F1: `0.4369803296119085`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-max_depth: 2 → 4
  - Signal-subsample: 0.8 → 0.9
  - Signal-colsample_bytree: 0.8 → 0.9
  - Signal-gamma: 1.0 → None
  - Signal-min_child_weight: 5 → None
  - Signal-scale_pos_weight: 1.0 → 1.2366863905325445

#### v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain
- Erstes Auftreten (Git): `2025-11-19`
- Config: `data/processed/experiments/v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain_config.json`
- Base-Result: `notebooks/results/two_stage__v8_h4_thr0p5pct_tolerant0p3pct_sig_easytrain.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.592`
  - Direction F1(up): `0.7727272727272727` (F1(down): `0.7`)
  - Combined (3 Klassen) accuracy: `0.42201834862385323`, macro-F1: `0.41555916258802506`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-max_depth: 4 → 3
  - Signal-scale_pos_weight: 1.2366863905325445 → 0.25098039215686274

#### v9_h4_thr0p5pct_tol0p3_30dfeat
- Erstes Auftreten (Git): `2025-11-21`
- Config: `data/processed/experiments/v9_h4_thr0p5pct_tol0p3_30dfeat_config.json`
- Base-Result: `notebooks/results/two_stage__v9_h4_thr0p5pct_tol0p3_30dfeat.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.5350877192982456`
  - Direction F1(up): `0.7727272727272727` (F1(down): `0.7`)
  - Combined (3 Klassen) accuracy: `0.44954128440366975`, macro-F1: `0.42984631647422344`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-scale_pos_weight: 0.25098039215686274 → 1.2366863905325445

#### v10_h4_thr0p3pct_tol0p3_30dfeat
- Erstes Auftreten (Git): `2025-11-21`
- Config: `data/processed/experiments/v10_h4_thr0p3pct_tol0p3_30dfeat_config.json`
- Base-Result: `notebooks/results/up_only__v10_h4_thr0p3pct_tol0p3_30dfeat.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.50% → 0.30%
  - Down-Schwelle: -0.50% → -0.30%


### Serie `s` (4 Experimente)

#### s1_h4_thr0p5pct_tol0p3
- Erstes Auftreten (Git): `2025-11-19`
- Config: `data/processed/experiments/s1_h4_thr0p5pct_tol0p3_config.json`
- Base-Result: `notebooks/results/up_only__s1_h4_thr0p5pct_tol0p3.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### s2_h4_thr0p5pct_tol0p3
- Erstes Auftreten (Git): `2025-11-21`
- Config: `data/processed/experiments/s2_h4_thr0p5pct_tol0p3_config.json`
- Base-Result: `notebooks/results/up_only__s2_h4_thr0p5pct_tol0p3.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### s3a_h4_thr0p3pct_tol0p3_30dfeat
- Erstes Auftreten (Git): `2025-11-21`
- Config: `data/processed/experiments/s3a_h4_thr0p3pct_tol0p3_30dfeat_config.json`
- Base-Result: `notebooks/results/up_only__s3a_h4_thr0p3pct_tol0p3_30dfeat.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.50% → 0.30%
  - Down-Schwelle: -0.50% → -0.30%

#### s3b_h4_thr0p3pct_tol0p3_30dfeat
- Erstes Auftreten (Git): `2025-11-21`
- Config: `data/processed/experiments/s3b_h4_thr0p3pct_tol0p3_30dfeat_config.json`
- Base-Result: `notebooks/results/down_only__s3b_h4_thr0p3pct_tol0p3_30dfeat.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=0.30%
- Features: 32 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)


### Serie `nv` (69 Experimente)

#### nv1_h4_thr0p7pct_tolerant0p3pct
- Erstes Auftreten (Git): `2025-11-22`
- Config: `data/processed/experiments/nv1_h4_thr0p7pct_tolerant0p3pct_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv1_h4_thr0p7pct_tolerant0p3pct.json`
- Base-Result: `notebooks/results/two_stage__nv1_h4_thr0p7pct_tolerant0p3pct.json`
- Label-Params: h=4, up=0.70%, down=-0.70%, strict=False, tol=0.30%
- Features: 35 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.43023255813953487`
  - Direction F1(up): `0.7157894736842105` (F1(down): `0.6493506493506493`)
  - Combined (3 Klassen) accuracy: `0.5091743119266054`, macro-F1: `0.407898428731762`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### nv2_h4_thr0p_8pct_tolerant0p4pct
- Erstes Auftreten (Git): `2025-11-22`
- Config: `data/processed/experiments/nv2_h4_thr0p_8pct_tolerant0p4pct_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv2_h4_thr0p_8pct_tolerant0p4pct.json`
- Base-Result: `notebooks/results/two_stage__nv2_h4_thr0p_8pct_tolerant0p4pct.json`
- Label-Params: h=4, up=0.80%, down=-0.80%, strict=False, tol=0.40%
- Features: 35 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.44970414201183434`
  - Direction F1(up): `0.7209302325581395` (F1(down): `0.5862068965517241`)
  - Combined (3 Klassen) accuracy: `0.5275229357798165`, macro-F1: `0.4274848746758859`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.70% → 0.80%
  - Down-Schwelle: -0.70% → -0.80%
  - max_adverse_move_pct: 0.30% → 0.40%
  - Signal-scale_pos_weight: 1.8208955223880596 → 2.0483870967741935

#### nv3_h4_thr0p_65pct_tolerant0p35pct
- Erstes Auftreten (Git): `2025-11-22`
- Config: `data/processed/experiments/nv3_h4_thr0p_65pct_tolerant0p35pct_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv3_h4_thr0p_65pct_tolerant0p35pct.json`
- Base-Result: `notebooks/results/two_stage__nv3_h4_thr0p_65pct_tolerant0p35pct.json`
- Label-Params: h=4, up=0.65%, down=-0.65%, strict=False, tol=0.35%
- Features: 35 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.5533980582524272`
  - Direction F1(up): `0.7184466019417476` (F1(down): `0.6741573033707865`)
  - Combined (3 Klassen) accuracy: `0.5`, macro-F1: `0.4563465519987259`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.80% → 0.65%
  - Down-Schwelle: -0.80% → -0.65%
  - max_adverse_move_pct: 0.40% → 0.35%
  - Signal-scale_pos_weight: 2.0483870967741935 → 1.5627118644067797

#### nv4_h4_thr0p_65pct_tolerant0p15pct
- Erstes Auftreten (Git): `2025-11-22`
- Config: `data/processed/experiments/nv4_h4_thr0p_65pct_tolerant0p15pct_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv4_h4_thr0p_65pct_tolerant0p15pct.json`
- Base-Result: `notebooks/results/two_stage__nv4_h4_thr0p_65pct_tolerant0p15pct.json`
- Label-Params: h=4, up=0.65%, down=-0.65%, strict=False, tol=0.15%
- Features: 35 Spalten
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.40476190476190477`
  - Direction F1(up): `0.782608695652174` (F1(down): `0.7297297297297297`)
  - Combined (3 Klassen) accuracy: `0.518348623853211`, macro-F1: `0.43595294906330845`
- Änderung vs vorheriges Experiment in dieser Serie:
  - max_adverse_move_pct: 0.35% → 0.15%
  - Signal-scale_pos_weight: 1.5627118644067797 → 1.8854961832061068

#### nv5_h4_thr0p_65pct_tolerant0p15pct_7p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv5_h4_thr0p_65pct_tolerant0p15pct_7p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv5_h4_thr0p_65pct_tolerant0p15pct_7p.json`
- Base-Result: `notebooks/results/two_stage__nv5_h4_thr0p_65pct_tolerant0p15pct_7p.json`
- Label-Params: h=4, up=0.65%, down=-0.65%, strict=False, tol=0.15%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.7`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.06593406593406594`
  - Direction F1(up): `0.782608695652174` (F1(down): `0.7297297297297297`)
  - Combined (3 Klassen) accuracy: `0.6055045871559633`, macro-F1: `0.2750172532781228`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: None → 0.7

#### nv6_h4_thr0p_6pct_tolerant0p15pct_6p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv6_h4_thr0p_6pct_tolerant0p15pct_6p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv6_h4_thr0p_6pct_tolerant0p15pct_6p.json`
- Base-Result: `notebooks/results/two_stage__nv6_h4_thr0p_6pct_tolerant0p15pct_6p.json`
- Label-Params: h=4, up=0.60%, down=-0.60%, strict=False, tol=0.20%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.2595419847328244`
  - Direction F1(up): `0.7524752475247525` (F1(down): `0.6987951807228916`)
  - Combined (3 Klassen) accuracy: `0.5458715596330275`, macro-F1: `0.3711907171287863`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.65% → 0.60%
  - Down-Schwelle: -0.65% → -0.60%
  - max_adverse_move_pct: 0.15% → 0.20%
  - Signal-Threshold: 0.7 → 0.6
  - Signal-scale_pos_weight: 1.8854961832061068 → 1.6433566433566433

#### nv7_h4_thr0p_6pct_tolerant0p2pct_7p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv7_h4_thr0p_6pct_tolerant0p2pct_7p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv7_h4_thr0p_6pct_tolerant0p2pct_7p.json`
- Base-Result: `notebooks/results/two_stage__nv7_h4_thr0p_6pct_tolerant0p2pct_7p.json`
- Label-Params: h=4, up=0.60%, down=-0.60%, strict=False, tol=0.20%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.7`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.061224489795918366`
  - Direction F1(up): `0.7524752475247525` (F1(down): `0.6987951807228916`)
  - Combined (3 Klassen) accuracy: `0.5779816513761468`, macro-F1: `0.2822964374463723`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.6 → 0.7

#### nv8_h4_thr0p_6pct_tolerant0p2pct_6p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv8_h4_thr0p_6pct_tolerant0p2pct_6p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv8_h4_thr0p_6pct_tolerant0p2pct_6p.json`
- Base-Result: `notebooks/results/two_stage__nv8_h4_thr0p_6pct_tolerant0p2pct_6p.json`
- Label-Params: h=4, up=0.60%, down=-0.60%, strict=False, tol=0.20%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.2595419847328244`
  - Direction F1(up): `0.7524752475247525` (F1(down): `0.6987951807228916`)
  - Combined (3 Klassen) accuracy: `0.5458715596330275`, macro-F1: `0.3711907171287863`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.7 → 0.6

#### nv9_h4_thr0p_55pct_tolerant0p2pct_6p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv9_h4_thr0p_55pct_tolerant0p2pct_6p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv9_h4_thr0p_55pct_tolerant0p2pct_6p.json`
- Base-Result: `notebooks/results/two_stage__nv9_h4_thr0p_55pct_tolerant0p2pct_6p.json`
- Label-Params: h=4, up=0.55%, down=-0.55%, strict=False, tol=0.20%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.234375`
  - Direction F1(up): `0.7428571428571429` (F1(down): `0.7096774193548387`)
  - Combined (3 Klassen) accuracy: `0.5458715596330275`, macro-F1: `0.3730593607305936`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.60% → 0.55%
  - Down-Schwelle: -0.60% → -0.55%
  - Signal-scale_pos_weight: 1.6433566433566433 → 1.5116279069767442

#### nv10_h4_thr0p_55pct_tolerant0p1pct_6p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv10_h4_thr0p_55pct_tolerant0p1pct_6p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv10_h4_thr0p_55pct_tolerant0p1pct_6p.json`
- Base-Result: `notebooks/results/two_stage__nv10_h4_thr0p_55pct_tolerant0p1pct_6p.json`
- Label-Params: h=4, up=0.55%, down=-0.55%, strict=False, tol=0.10%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.21666666666666667`
  - Direction F1(up): `0.803921568627451` (F1(down): `0.7619047619047619`)
  - Combined (3 Klassen) accuracy: `0.5642201834862385`, macro-F1: `0.36370102471368293`
- Änderung vs vorheriges Experiment in dieser Serie:
  - max_adverse_move_pct: 0.20% → 0.10%
  - Signal-scale_pos_weight: 1.5116279069767442 → 1.7

#### nv11_h4_thr0p_4pct_tolerant0p1pct_6p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv11_h4_thr0p_4pct_tolerant0p1pct_6p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv11_h4_thr0p_4pct_tolerant0p1pct_6p.json`
- Base-Result: `notebooks/results/two_stage__nv11_h4_thr0p_4pct_tolerant0p1pct_6p.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=0.10%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.128`
  - Direction F1(up): `0.8099173553719008` (F1(down): `0.7526881720430108`)
  - Combined (3 Klassen) accuracy: `0.4954128440366973`, macro-F1: `0.29405762509637634`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.55% → 0.40%
  - Down-Schwelle: -0.55% → -0.40%
  - Signal-scale_pos_weight: 1.7 → 1.166189111747851

#### nv12_h4_thr0p_3pct_tolerant0p1pct_6p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv12_h4_thr0p_3pct_tolerant0p1pct_6p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv12_h4_thr0p_3pct_tolerant0p1pct_6p.json`
- Base-Result: `notebooks/results/two_stage__nv12_h4_thr0p_3pct_tolerant0p1pct_6p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=0.10%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.0`
  - Direction F1(up): `0.8194444444444444` (F1(down): `0.7719298245614035`)
  - Combined (3 Klassen) accuracy: `0.40825688073394495`, macro-F1: `0.19326818675352878`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.40% → 0.30%
  - Down-Schwelle: -0.40% → -0.30%
  - Signal-scale_pos_weight: 1.166189111747851 → 0.9585492227979274

#### nv13_h4_thr0p_3pct_tolerant0p1pct_4p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv13_h4_thr0p_3pct_tolerant0p1pct_4p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv13_h4_thr0p_3pct_tolerant0p1pct_4p.json`
- Base-Result: `notebooks/results/two_stage__nv13_h4_thr0p_3pct_tolerant0p1pct_4p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=0.10%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.4`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.7435158501440923`
  - Direction F1(up): `0.8194444444444444` (F1(down): `0.7719298245614035`)
  - Combined (3 Klassen) accuracy: `0.4724770642201835`, macro-F1: `0.39372721614652795`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.6 → 0.4

#### nv14_h4_thr0p_3pct_tolerant0p1pct_51p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv14_h4_thr0p_3pct_tolerant0p1pct_51p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv14_h4_thr0p_3pct_tolerant0p1pct_51p.json`
- Base-Result: `notebooks/results/two_stage__nv14_h4_thr0p_3pct_tolerant0p1pct_51p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=0.10%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.51`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.1111111111111111`
  - Direction F1(up): `0.8194444444444444` (F1(down): `0.7719298245614035`)
  - Combined (3 Klassen) accuracy: `0.40825688073394495`, macro-F1: `0.254847462113692`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.4 → 0.51

#### nv15_h4_thr0p_3pct_tolerant0p1pct_5p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv15_h4_thr0p_3pct_tolerant0p1pct_5p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv15_h4_thr0p_3pct_tolerant0p1pct_5p.json`
- Base-Result: `notebooks/results/two_stage__nv15_h4_thr0p_3pct_tolerant0p1pct_5p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=0.10%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.2`
  - Direction F1(up): `0.8194444444444444` (F1(down): `0.7719298245614035`)
  - Combined (3 Klassen) accuracy: `0.39908256880733944`, macro-F1: `0.28316163203538797`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.51 → 0.5

#### nv16_h4_thr0p_3pct_tolerant0p1pct_5p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv16_h4_thr0p_3pct_tolerant0p1pct_5p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv16_h4_thr0p_3pct_tolerant0p1pct_5p.json`
- Base-Result: `notebooks/results/two_stage__nv16_h4_thr0p_3pct_tolerant0p1pct_5p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.7468354430379747`
  - Direction F1(up): `0.6900584795321637` (F1(down): `0.6666666666666666`)
  - Combined (3 Klassen) accuracy: `0.46788990825688076`, macro-F1: `0.4570097077007304`
- Änderung vs vorheriges Experiment in dieser Serie:
  - max_adverse_move_pct: 0.10% → —
  - Signal-scale_pos_weight: 0.9585492227979274 → 0.37454545454545457

#### nv17_h4_thr0p_3pct_tolerant0p1pct_6p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv17_h4_thr0p_3pct_tolerant0p1pct_6p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv17_h4_thr0p_3pct_tolerant0p1pct_6p.json`
- Base-Result: `notebooks/results/two_stage__nv17_h4_thr0p_3pct_tolerant0p1pct_6p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6`
  - Direction F1(up): `0.6900584795321637` (F1(down): `0.6666666666666666`)
  - Combined (3 Klassen) accuracy: `0.44495412844036697`, macro-F1: `0.45063524130190796`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.5 → 0.6

#### nv18_h4_thr0p_3pct_tolerant0p1pct_7p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv18_h4_thr0p_3pct_tolerant0p1pct_7p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv18_h4_thr0p_3pct_tolerant0p1pct_7p.json`
- Base-Result: `notebooks/results/two_stage__nv18_h4_thr0p_3pct_tolerant0p1pct_7p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.7`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.2198952879581152`
  - Direction F1(up): `0.6900584795321637` (F1(down): `0.6666666666666666`)
  - Combined (3 Klassen) accuracy: `0.28440366972477066`, macro-F1: `0.23115652262670294`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.6 → 0.7

#### nv19_h4_thr0p_3pct_tolerant0p1pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv19_h4_thr0p_3pct_tolerant0p1pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv19_h4_thr0p_3pct_tolerant0p1pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv19_h4_thr0p_3pct_tolerant0p1pct_55p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6758620689655173`
  - Direction F1(up): `0.6900584795321637` (F1(down): `0.6666666666666666`)
  - Combined (3 Klassen) accuracy: `0.4541284403669725`, macro-F1: `0.4546077970735505`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.7 → 0.55

#### nv20_h4_thr0p_6pct_tolerant0p1pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv20_h4_thr0p_6pct_tolerant0p1pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv20_h4_thr0p_6pct_tolerant0p1pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv20_h4_thr0p_6pct_tolerant0p1pct_55p.json`
- Label-Params: h=4, up=0.60%, down=-0.60%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.5463414634146342`
  - Direction F1(up): `0.6896551724137931` (F1(down): `0.6326530612244898`)
  - Combined (3 Klassen) accuracy: `0.4954128440366973`, macro-F1: `0.4456283725491705`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.30% → 0.60%
  - Down-Schwelle: -0.30% → -0.60%
  - Signal-scale_pos_weight: 0.37454545454545457 → 1.16

#### nv21_h4_thr0p_6pct_tolerant0p6pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv21_h4_thr0p_6pct_tolerant0p6pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv21_h4_thr0p_6pct_tolerant0p6pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv21_h4_thr0p_6pct_tolerant0p6pct_55p.json`
- Label-Params: h=4, up=0.60%, down=-0.60%, strict=False, tol=60.00%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.5463414634146342`
  - Direction F1(up): `0.6896551724137931` (F1(down): `0.6326530612244898`)
  - Combined (3 Klassen) accuracy: `0.4954128440366973`, macro-F1: `0.4456283725491705`
- Änderung vs vorheriges Experiment in dieser Serie:
  - max_adverse_move_pct: — → 60.00%

#### nv22_h4_thr0p_3pct_tolerant_p_pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv22_h4_thr0p_3pct_tolerant_p_pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv22_h4_thr0p_3pct_tolerant_p_pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv22_h4_thr0p_3pct_tolerant_p_pct_55p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6758620689655173`
  - Direction F1(up): `0.6900584795321637` (F1(down): `0.6666666666666666`)
  - Combined (3 Klassen) accuracy: `0.4541284403669725`, macro-F1: `0.4546077970735505`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.60% → 0.30%
  - Down-Schwelle: -0.60% → -0.30%
  - max_adverse_move_pct: 60.00% → —
  - Signal-scale_pos_weight: 1.16 → 0.37454545454545457

#### nv23_h3_thr0p_3pct_tolerant_p_pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv23_h3_thr0p_3pct_tolerant_p_pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv23_h3_thr0p_3pct_tolerant_p_pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv23_h3_thr0p_3pct_tolerant_p_pct_55p.json`
- Label-Params: h=3, up=0.30%, down=-0.30%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6910299003322259`
  - Direction F1(up): `0.7204968944099379` (F1(down): `0.697986577181208`)
  - Combined (3 Klassen) accuracy: `0.4429223744292237`, macro-F1: `0.4349801736101568`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 4 → 3
  - Signal-scale_pos_weight: 0.37454545454545457 → 0.4482758620689655

#### nv24_h6_thr0p_6pct_tolerant_p_pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv24_h6_thr0p_6pct_tolerant_p_pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv24_h6_thr0p_6pct_tolerant_p_pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv24_h6_thr0p_6pct_tolerant_p_pct_55p.json`
- Label-Params: h=6, up=0.60%, down=-0.60%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.0`
  - Direction F1(up): `0.6017699115044248` (F1(down): `0.64`)
  - Combined (3 Klassen) accuracy: `0.44907407407407407`, macro-F1: `0.20660276890308837`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 3 → 6
  - Up-Schwelle: 0.30% → 0.60%
  - Down-Schwelle: -0.30% → -0.60%
  - Signal-scale_pos_weight: 0.4482758620689655 → 0.7704918032786885

#### nv25_h6_thr1p_0pct_tolerant_p_pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv25_h6_thr1p_0pct_tolerant_p_pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv25_h6_thr1p_0pct_tolerant_p_pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv25_h6_thr1p_0pct_tolerant_p_pct_55p.json`
- Label-Params: h=6, up=1.00%, down=-1.00%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.3586206896551724`
  - Direction F1(up): `0.6666666666666666` (F1(down): `0.5172413793103449`)
  - Combined (3 Klassen) accuracy: `0.5416666666666666`, macro-F1: `0.40178998428639745`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.60% → 1.00%
  - Down-Schwelle: -0.60% → -1.00%
  - Signal-scale_pos_weight: 0.7704918032786885 → 2.0119521912350598

#### nv26_h6_thr1p_0pct_strict_p_pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv26_h6_thr1p_0pct_strict_p_pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv26_h6_thr1p_0pct_strict_p_pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv26_h6_thr1p_0pct_strict_p_pct_55p.json`
- Label-Params: h=6, up=1.00%, down=-1.00%, strict=True, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.0`
  - Direction F1(up): `1.0` (F1(down): `1.0`)
  - Combined (3 Klassen) accuracy: `0.9814814814814815`, macro-F1: `0.3302180685358255`
- Änderung vs vorheriges Experiment in dieser Serie:
  - strict_monotonic: False → True
  - Signal-scale_pos_weight: 2.0119521912350598 → 38.78947368421053

#### nv26_h6_thr1p_0pct_tolerant_p_pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv26_h6_thr1p_0pct_tolerant_p_pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv26_h6_thr1p_0pct_tolerant_p_pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv26_h6_thr1p_0pct_tolerant_p_pct_55p.json`
- Label-Params: h=6, up=1.00%, down=-1.00%, strict=True, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.0`
  - Direction F1(up): `1.0` (F1(down): `1.0`)
  - Combined (3 Klassen) accuracy: `0.9814814814814815`, macro-F1: `0.3302180685358255`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### nv27_h6_thr1p_0pct_tolerant_p_pct_5p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv27_h6_thr1p_0pct_tolerant_p_pct_5p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv27_h6_thr1p_0pct_tolerant_p_pct_5p.json`
- Base-Result: `notebooks/results/two_stage__nv27_h6_thr1p_0pct_tolerant_p_pct_5p.json`
- Label-Params: h=6, up=1.00%, down=-1.00%, strict=False, tol=0.50%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.36496350364963503`
  - Direction F1(up): `0.8192771084337349` (F1(down): `0.6808510638297872`)
  - Combined (3 Klassen) accuracy: `0.5833333333333334`, macro-F1: `0.4318135170020525`
- Änderung vs vorheriges Experiment in dieser Serie:
  - strict_monotonic: True → False
  - max_adverse_move_pct: — → 0.50%
  - Signal-Threshold: 0.55 → 0.5
  - Signal-scale_pos_weight: 38.78947368421053 → 2.36

#### nv28_h6_thr1p_5pct_tolerant_p_pct_5p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv28_h6_thr1p_5pct_tolerant_p_pct_5p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv28_h6_thr1p_5pct_tolerant_p_pct_5p.json`
- Base-Result: `notebooks/results/two_stage__nv28_h6_thr1p_5pct_tolerant_p_pct_5p.json`
- Label-Params: h=6, up=1.50%, down=-1.50%, strict=False, tol=—
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.16`
  - Direction F1(up): `0.7272727272727273` (F1(down): `0.21052631578947367`)
  - Combined (3 Klassen) accuracy: `0.6990740740740741`, macro-F1: `0.3248242693303736`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 1.00% → 1.50%
  - Down-Schwelle: -1.00% → -1.50%
  - max_adverse_move_pct: 0.50% → —
  - Signal-scale_pos_weight: 2.36 → 4.8604651162790695

#### nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv29_h4_thr0p_3pct_tolerant_0p_1pct_55p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=1.55%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.7468354430379747`
  - Direction F1(up): `0.6900584795321637` (F1(down): `0.6666666666666666`)
  - Combined (3 Klassen) accuracy: `0.46788990825688076`, macro-F1: `0.4570097077007304`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 6 → 4
  - Up-Schwelle: 1.50% → 0.30%
  - Down-Schwelle: -1.50% → -0.30%
  - max_adverse_move_pct: — → 1.55%
  - Signal-scale_pos_weight: 4.8604651162790695 → 0.37454545454545457

#### nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv30_h4_thr0p_3pct_tolerant_0p_1pct_55p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=1.55%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6758620689655173`
  - Direction F1(up): `0.6900584795321637` (F1(down): `0.6666666666666666`)
  - Combined (3 Klassen) accuracy: `0.4541284403669725`, macro-F1: `0.4546077970735505`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.5 → 0.55

#### nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p.json`
- Base-Result: `notebooks/results/two_stage__nv31_h4_thr0p_3pct_tolerant_0p_1pct_6p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=1.00%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6142322097378277`
  - Direction F1(up): `0.7017543859649122` (F1(down): `0.6792452830188679`)
  - Combined (3 Klassen) accuracy: `0.41743119266055045`, macro-F1: `0.4179184842856937`
- Änderung vs vorheriges Experiment in dieser Serie:
  - max_adverse_move_pct: 1.55% → 1.00%
  - Signal-Threshold: 0.55 → 0.6
  - Signal-scale_pos_weight: 0.37454545454545457 → 0.3974121996303142

#### nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p.json`
- Base-Result: `notebooks/results/two_stage__nv32_h4_thr0p_3pct_tolerant_0p_1pct_5_75p.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=1.00%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.575`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.65`
  - Direction F1(up): `0.7017543859649122` (F1(down): `0.6792452830188679`)
  - Combined (3 Klassen) accuracy: `0.42201834862385323`, macro-F1: `0.42100788645462534`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Signal-Threshold: 0.6 → 0.575

#### nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv33_h3_thr0p_3pct_tolerant_0p_1pct_55p.json`
- Label-Params: h=3, up=0.30%, down=-0.30%, strict=False, tol=1.00%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.0`
  - Direction F1(up): `0.7204968944099379` (F1(down): `0.6896551724137931`)
  - Combined (3 Klassen) accuracy: `0.3013698630136986`, macro-F1: `0.1543859649122807`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 4 → 3
  - Signal-Threshold: 0.575 → 0.55
  - Signal-scale_pos_weight: 0.3974121996303142 → 0.45664739884393063

#### nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv34_h5_thr0p_3pct_tolerant_0p_1pct_55p.json`
- Label-Params: h=5, up=0.30%, down=-0.30%, strict=False, tol=1.00%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.7297297297297297`
  - Direction F1(up): `0.6490066225165563` (F1(down): `0.6580645161290323`)
  - Combined (3 Klassen) accuracy: `0.4838709677419355`, macro-F1: `0.48300253872819704`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 3 → 5
  - Signal-scale_pos_weight: 0.45664739884393063 → 0.3820840950639854

#### nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv35_h5_thr0p_4pct_tolerant_0p_1pct_55p.json`
- Label-Params: h=5, up=0.40%, down=-0.40%, strict=False, tol=1.00%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.0`
  - Direction F1(up): `0.6277372262773723` (F1(down): `0.6382978723404256`)
  - Combined (3 Klassen) accuracy: `0.35944700460829493`, macro-F1: `0.17627118644067796`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.30% → 0.40%
  - Down-Schwelle: -0.30% → -0.40%
  - Signal-scale_pos_weight: 0.3820840950639854 → 0.5365853658536586

#### nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p.json`
- Base-Result: `notebooks/results/two_stage__nv36_h5_thr0p_35pct_tolerant_0p_1pct_55p.json`
- Label-Params: h=5, up=0.35%, down=-0.35%, strict=False, tol=1.00%
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.0`
  - Direction F1(up): `0.6029411764705882` (F1(down): `0.6582278481012658`)
  - Combined (3 Klassen) accuracy: `0.3225806451612903`, macro-F1: `0.16260162601626016`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.40% → 0.35%
  - Down-Schwelle: -0.40% → -0.35%
  - Signal-scale_pos_weight: 0.5365853658536586 → 0.4594594594594595

#### nv1_h6_thr2p_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv1_h6_thr2p_tolerant0p4pct_config.json`
- Label-Params: h=6, up=20.00%, down=-20.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 5 → 6
  - Up-Schwelle: 0.35% → 20.00%
  - Down-Schwelle: -0.35% → -20.00%
  - max_adverse_move_pct: 1.00% → 0.40%
  - Signal-Threshold: 0.55 → None

#### nv2_4_thr0p_5pct_tolerant0p3pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_4_thr0p_5pct_tolerant0p3pct_config.json`
- Label-Params: h=4, up=50.00%, down=-50.00%, strict=False, tol=0.30%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 6 → 4
  - Up-Schwelle: 20.00% → 50.00%
  - Down-Schwelle: -20.00% → -50.00%
  - max_adverse_move_pct: 0.40% → 0.30%

#### nv2_4_thr0p_5pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_4_thr0p_5pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=50.00%, down=-50.00%, strict=False, tol=0.30%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### nv2_4_thr0p_65pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_4_thr0p_65pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=65.00%, down=-65.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 50.00% → 65.00%
  - Down-Schwelle: -50.00% → -65.00%
  - max_adverse_move_pct: 0.30% → 0.40%

#### nv2_4_thr0p_6pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_4_thr0p_6pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=60.00%, down=-60.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 65.00% → 60.00%
  - Down-Schwelle: -65.00% → -60.00%

#### nv2_4_thr0p_7pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_4_thr0p_7pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=70.00%, down=-70.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 60.00% → 70.00%
  - Down-Schwelle: -60.00% → -70.00%

#### nv2_4_thr0p_8pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_4_thr0p_8pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=80.00%, down=-80.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 70.00% → 80.00%
  - Down-Schwelle: -70.00% → -80.00%

#### nv2_5_thr0p_9pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_5_thr0p_9pct_tolerant0p4pct_config.json`
- Label-Params: h=5, up=90.00%, down=-90.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 4 → 5
  - Up-Schwelle: 80.00% → 90.00%
  - Down-Schwelle: -80.00% → -90.00%

#### nv2_5_thr1p_0pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_5_thr1p_0pct_tolerant0p4pct_config.json`
- Label-Params: h=5, up=10.00%, down=-10.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 90.00% → 10.00%
  - Down-Schwelle: -90.00% → -10.00%

#### nv2_6_thr0p_8pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_6_thr0p_8pct_tolerant0p4pct_config.json`
- Label-Params: h=6, up=8.00%, down=-8.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 5 → 6
  - Up-Schwelle: 10.00% → 8.00%
  - Down-Schwelle: -10.00% → -8.00%

#### nv2_6_thr1p_0pct_tolerant0p1pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_6_thr1p_0pct_tolerant0p1pct_config.json`
- Label-Params: h=6, up=10.00%, down=-10.00%, strict=False, tol=0.10%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 8.00% → 10.00%
  - Down-Schwelle: -8.00% → -10.00%
  - max_adverse_move_pct: 0.40% → 0.10%

#### nv2_6_thr1p_0pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_6_thr1p_0pct_tolerant0p4pct_config.json`
- Label-Params: h=6, up=10.00%, down=-10.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - max_adverse_move_pct: 0.10% → 0.40%

#### nv2_h4_thr0p_5pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_h4_thr0p_5pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=5.00%, down=-5.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 6 → 4
  - Up-Schwelle: 10.00% → 5.00%
  - Down-Schwelle: -10.00% → -5.00%

#### nv2_h4_thr0p_65pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_h4_thr0p_65pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=6.50%, down=-6.50%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 5.00% → 6.50%
  - Down-Schwelle: -5.00% → -6.50%

#### nv2_h4_thr0p_7pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_h4_thr0p_7pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=7.00%, down=-7.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 6.50% → 7.00%
  - Down-Schwelle: -6.50% → -7.00%

#### nv2_h5_thr1p_5pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_h5_thr1p_5pct_tolerant0p4pct_config.json`
- Label-Params: h=5, up=15.00%, down=-15.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 4 → 5
  - Up-Schwelle: 7.00% → 15.00%
  - Down-Schwelle: -7.00% → -15.00%

#### nv2_h5_thr2p_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_h5_thr2p_tolerant0p4pct_config.json`
- Label-Params: h=5, up=20.00%, down=-20.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 15.00% → 20.00%
  - Down-Schwelle: -15.00% → -20.00%

#### nv2_h6_thr1p_5pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_h6_thr1p_5pct_tolerant0p4pct_config.json`
- Label-Params: h=6, up=15.00%, down=-15.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 5 → 6
  - Up-Schwelle: 20.00% → 15.00%
  - Down-Schwelle: -20.00% → -15.00%

#### nv2_h6_thr2p_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_h6_thr2p_tolerant0p4pct_config.json`
- Label-Params: h=6, up=20.00%, down=-20.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 15.00% → 20.00%
  - Down-Schwelle: -15.00% → -20.00%

#### nv2_h8_thr1p_5pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv2_h8_thr1p_5pct_tolerant0p4pct_config.json`
- Label-Params: h=8, up=15.00%, down=-15.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 6 → 8
  - Up-Schwelle: 20.00% → 15.00%
  - Down-Schwelle: -20.00% → -15.00%

#### nv3_h4_thr1p_5pct_tolerant0p5pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv3_h4_thr1p_5pct_tolerant0p5pct_config.json`
- Label-Params: h=4, up=1.50%, down=-15.00%, strict=False, tol=0.50%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 8 → 4
  - Up-Schwelle: 15.00% → 1.50%
  - max_adverse_move_pct: 0.40% → 0.50%

#### nv3_h4_thr2p_0pct_tolerant0p4pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv3_h4_thr2p_0pct_tolerant0p4pct_config.json`
- Label-Params: h=4, up=2.00%, down=-2.00%, strict=False, tol=0.40%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 1.50% → 2.00%
  - Down-Schwelle: -15.00% → -2.00%
  - max_adverse_move_pct: 0.50% → 0.40%

#### nv3_h5_thr0p_9pct_tolerant0p5pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv3_h5_thr0p_9pct_tolerant0p5pct_config.json`
- Label-Params: h=5, up=0.90%, down=-9.00%, strict=False, tol=0.50%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 4 → 5
  - Up-Schwelle: 2.00% → 0.90%
  - Down-Schwelle: -2.00% → -9.00%
  - max_adverse_move_pct: 0.40% → 0.50%

#### nv3_h5_thr1p_0pct_tolerant0p5pct
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv3_h5_thr1p_0pct_tolerant0p5pct_config.json`
- Label-Params: h=5, up=1.00%, down=-10.00%, strict=False, tol=0.50%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.90% → 1.00%
  - Down-Schwelle: -9.00% → -10.00%

#### nv22_h4_thr0p_25pct_tolerant_p_pct_55p
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv22_h4_thr0p_25pct_tolerant_p_pct_55p_config.json`
- Label-Params: h=4, up=0.25%, down=-2.50%, strict=False, tol=—
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 5 → 4
  - Up-Schwelle: 1.00% → 0.25%
  - Down-Schwelle: -10.00% → -2.50%
  - max_adverse_move_pct: 0.50% → —

#### nv22_h4_thr0p_3pct_tolerant_p_pct_51p
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv22_h4_thr0p_3pct_tolerant_p_pct_51p_config.json`
- Label-Params: h=4, up=0.30%, down=-3.00%, strict=False, tol=—
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.25% → 0.30%
  - Down-Schwelle: -2.50% → -3.00%

#### nv22_h4_thr0p_3pct_tolerant_p_pct_5p
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv22_h4_thr0p_3pct_tolerant_p_pct_5p_config.json`
- Label-Params: h=4, up=0.30%, down=-3.00%, strict=False, tol=—
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### nv27_h6_thr1p_0pct_strict_p_pct_5p
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv27_h6_thr1p_0pct_strict_p_pct_5p_config.json`
- Label-Params: h=6, up=1.00%, down=-1.00%, strict=False, tol=0.50%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 4 → 6
  - Up-Schwelle: 0.30% → 1.00%
  - Down-Schwelle: -3.00% → -1.00%
  - max_adverse_move_pct: — → 0.50%

#### nv28_h6_thr2p_0pct_tolerant_1p_pct_5p
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv28_h6_thr2p_0pct_tolerant_1p_pct_5p_config.json`
- Label-Params: h=6, up=2.00%, down=-2.00%, strict=False, tol=1.00%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 1.00% → 2.00%
  - Down-Schwelle: -1.00% → -2.00%
  - max_adverse_move_pct: 0.50% → 1.00%

#### nv28_h6_thr2p_0pct_tolerant_p_pct_5p
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv28_h6_thr2p_0pct_tolerant_p_pct_5p_config.json`
- Label-Params: h=6, up=2.00%, down=-2.00%, strict=False, tol=—
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - max_adverse_move_pct: 1.00% → —

#### nv28_h6_thr3p_0pct_tolerant_1p_pct_5p
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv28_h6_thr3p_0pct_tolerant_1p_pct_5p_config.json`
- Label-Params: h=6, up=3.00%, down=-3.00%, strict=False, tol=1.00%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 2.00% → 3.00%
  - Down-Schwelle: -2.00% → -3.00%
  - max_adverse_move_pct: — → 1.00%

#### nv28_h6_thr3p_0pct_tolerant_p_pct_5p
- Erstes Auftreten (Git): `—`
- Config: `data/processed/experiments/nv28_h6_thr3p_0pct_tolerant_p_pct_5p_config.json`
- Label-Params: h=6, up=3.00%, down=-3.00%, strict=False, tol=0.50%
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `None`
  - Direction F1(up): `None` (F1(down): `None`)
  - Combined (3 Klassen) accuracy: `None`, macro-F1: `None`
- Änderung vs vorheriges Experiment in dieser Serie:
  - max_adverse_move_pct: 1.00% → 0.50%


### Serie `hv` (11 Experimente)

#### hv1_h4_thr0p3pct_hit
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/hv1_h4_thr0p3pct_hit_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv1_h4_thr0p3pct_hit.json`
- Base-Result: `notebooks/results/two_stage__hv1_h4_thr0p3pct_hit.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9619047619047619`
  - Direction F1(up): `0.6995073891625616` (F1(down): `0.7214611872146118`)
  - Combined (3 Klassen) accuracy: `0.6605504587155964`, macro-F1: `0.45659198050744215`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hv2_h4_thr0p4pct_hit
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/hv2_h4_thr0p4pct_hit_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv2_h4_thr0p4pct_hit.json`
- Base-Result: `notebooks/results/two_stage__hv2_h4_thr0p4pct_hit.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9002557544757033`
  - Direction F1(up): `0.7307692307692307` (F1(down): `0.7142857142857143`)
  - Combined (3 Klassen) accuracy: `0.6146788990825688`, macro-F1: `0.49130434782608695`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.30% → 0.40%
  - Down-Schwelle: -0.30% → -0.40%
  - Signal-scale_pos_weight: 0.07539118065433854 → 0.18309859154929578

#### hv3_h4_thr0p5pct_hit
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/hv3_h4_thr0p5pct_hit_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv3_h4_thr0p5pct_hit.json`
- Base-Result: `notebooks/results/two_stage__hv3_h4_thr0p5pct_hit.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.55`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.8626373626373627`
  - Direction F1(up): `0.7553191489361702` (F1(down): `0.7261904761904762`)
  - Combined (3 Klassen) accuracy: `0.5871559633027523`, macro-F1: `0.5296262605844171`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.40% → 0.50%
  - Down-Schwelle: -0.40% → -0.50%
  - Signal-scale_pos_weight: 0.18309859154929578 → 0.33568904593639576

#### hv4_h4_thr0p4pct_hit
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/hv4_h4_thr0p4pct_hit_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv4_h4_thr0p4pct_hit.json`
- Base-Result: `notebooks/results/two_stage__hv4_h4_thr0p4pct_hit.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.7307692307692307` (F1(down): `0.7142857142857143`)
  - Combined (3 Klassen) accuracy: `0.6284403669724771`, macro-F1: `0.5014991181657847`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.50% → 0.40%
  - Down-Schwelle: -0.50% → -0.40%
  - Signal-Threshold: 0.55 → 0.5
  - Signal-scale_pos_weight: 0.33568904593639576 → 0.18309859154929578

#### hv5_h4_thr0p4pct_hit
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/hv5_h4_thr0p4pct_hit_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit.json`
- Base-Result: `notebooks/results/two_stage__hv5_h4_thr0p4pct_hit.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.7555555555555555` (F1(down): `0.6927374301675978`)
  - Combined (3 Klassen) accuracy: `0.6192660550458715`, macro-F1: `0.49393939393939396`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hv5_h4_thr0p4pct_hit_2
- Erstes Auftreten (Git): `2025-11-28`
- Config: `data/processed/experiments/hv5_h4_thr0p4pct_hit_2_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_2.json`
- Base-Result: `notebooks/results/two_stage__hv5_h4_thr0p4pct_hit_2.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.7555555555555555` (F1(down): `0.6927374301675978`)
  - Combined (3 Klassen) accuracy: `0.6192660550458715`, macro-F1: `0.49393939393939396`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hv5_h4_thr0p4pct_hit_3
- Erstes Auftreten (Git): `2025-11-29`
- Config: `data/processed/experiments/hv5_h4_thr0p4pct_hit_3_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_3.json`
- Base-Result: `notebooks/results/two_stage__hv5_h4_thr0p4pct_hit_3.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.7555555555555555` (F1(down): `0.6927374301675978`)
  - Combined (3 Klassen) accuracy: `0.6192660550458715`, macro-F1: `0.49393939393939396`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hv5_h4_thr0p4pct_hit_4
- Erstes Auftreten (Git): `2025-11-29`
- Config: `data/processed/experiments/hv5_h4_thr0p4pct_hit_4_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_4.json`
- Base-Result: `notebooks/results/two_stage__hv5_h4_thr0p4pct_hit_4.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.7555555555555555` (F1(down): `0.6927374301675978`)
  - Combined (3 Klassen) accuracy: `0.6192660550458715`, macro-F1: `0.49393939393939396`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hv5_h4_thr0p4pct_hit_5
- Erstes Auftreten (Git): `2025-11-29`
- Config: `data/processed/experiments/hv5_h4_thr0p4pct_hit_5_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_5.json`
- Base-Result: `notebooks/results/two_stage__hv5_h4_thr0p4pct_hit_5.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.7555555555555555` (F1(down): `0.6927374301675978`)
  - Combined (3 Klassen) accuracy: `0.6192660550458715`, macro-F1: `0.49393939393939396`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hv5_h4_thr0p4pct_hit_6
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hv5_h4_thr0p4pct_hit_6_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_6.json`
- Base-Result: `notebooks/results/two_stage__hv5_h4_thr0p4pct_hit_6.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- Signal-Threshold (klassisch): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.625`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.7555555555555555` (F1(down): `0.6927374301675978`)
  - Combined (3 Klassen) accuracy: `0.5137614678899083`, macro-F1: `0.4511875564340972`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Direction-Thresholds: down None→0.3, up None→0.625

#### hv5_h4_thr0p4pct_hit_6_2
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hv5_h4_thr0p4pct_hit_6_2_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hv5_h4_thr0p4pct_hit_6_2.json`
- Base-Result: `notebooks/results/two_stage__hv5_h4_thr0p4pct_hit_6_2.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 35 Spalten
- feature_mode: `news+price`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.7`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.625`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.7555555555555555` (F1(down): `0.6927374301675978`)
  - Combined (3 Klassen) accuracy: `0.47706422018348627`, macro-F1: `0.43309044386400747`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Trade-Signal-Threshold: None → 0.7
  - feature_mode: None → news+price


### Serie `hp1` (1 Experimente)

#### hp1_h4_thr0p4pct_hit_1
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hp1_h4_thr0p4pct_hit_1_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp1_h4_thr0p4pct_hit_1.json`
- Base-Result: `notebooks/results/two_stage__hp1_h4_thr0p4pct_hit_1.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.5249999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9195979899497487`
  - Direction F1(up): `0.7601809954751131` (F1(down): `0.7103825136612022`)
  - Combined (3 Klassen) accuracy: `0.5504587155963303`, macro-F1: `0.4746954459978743`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)


### Serie `hpL` (1 Experimente)

#### hpL1_h4_thr0p4pct_hit_1
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hpL1_h4_thr0p4pct_hit_1_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hpL1_h4_thr0p4pct_hit_1.json`
- Base-Result: `notebooks/results/two_stage__hpL1_h4_thr0p4pct_hit_1.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.5249999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9195979899497487`
  - Direction F1(up): `0.7601809954751131` (F1(down): `0.7103825136612022`)
  - Combined (3 Klassen) accuracy: `0.5504587155963303`, macro-F1: `0.4746954459978743`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)


### Serie `hp_long` (5 Experimente)

#### hp_long1_h4_thr0p4pct_hit_1
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hp_long1_h4_thr0p4pct_hit_1_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long1_h4_thr0p4pct_hit_1.json`
- Base-Result: `notebooks/results/two_stage__hp_long1_h4_thr0p4pct_hit_1.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.6749999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.92`
  - Direction F1(up): `0.7631578947368421` (F1(down): `0.6931818181818182`)
  - Combined (3 Klassen) accuracy: `0.42660550458715596`, macro-F1: `0.41256569517439085`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hp_long_h4_thr0p4pct_hit_1
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hp_long_h4_thr0p4pct_hit_1_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1.json`
- Base-Result: `notebooks/results/two_stage__hp_long_h4_thr0p4pct_hit_1.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.6749999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.92`
  - Direction F1(up): `0.7631578947368421` (F1(down): `0.6931818181818182`)
  - Combined (3 Klassen) accuracy: `0.42660550458715596`, macro-F1: `0.41256569517439085`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hp_long_h4_thr0p4pct_hit_1_2
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hp_long_h4_thr0p4pct_hit_1_2_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_2.json`
- Base-Result: `notebooks/results/two_stage__hp_long_h4_thr0p4pct_hit_1_2.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.425`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.6749999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.92`
  - Direction F1(up): `0.7631578947368421` (F1(down): `0.6931818181818182`)
  - Combined (3 Klassen) accuracy: `0.42660550458715596`, macro-F1: `0.4118831139909152`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Trade-Signal-Threshold: None → 0.425

#### hp_long_h4_thr0p4pct_hit_1_3
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hp_long_h4_thr0p4pct_hit_1_3_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_3.json`
- Base-Result: `notebooks/results/two_stage__hp_long_h4_thr0p4pct_hit_1_3.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 16 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.7`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9141414141414141`
  - Direction F1(up): `0.75` (F1(down): `0.6888888888888889`)
  - Combined (3 Klassen) accuracy: `0.44036697247706424`, macro-F1: `0.4276994393451805`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Trade-Signal-Threshold: 0.425 → 0.5
  - Direction-Thresholds: down 0.3→0.3, up 0.6749999999999999→0.7
  - Feature-Anzahl: 21 → 16

#### hp_long_h4_thr0p4pct_hit_1_4
- Erstes Auftreten (Git): `2025-11-30`
- Config: `data/processed/experiments/hp_long_h4_thr0p4pct_hit_1_4_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_h4_thr0p4pct_hit_1_4.json`
- Base-Result: `notebooks/results/two_stage__hp_long_h4_thr0p4pct_hit_1_4.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True
- Features: 25 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.7`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.7`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9306930693069307`
  - Direction F1(up): `0.7567567567567568` (F1(down): `0.7032967032967034`)
  - Combined (3 Klassen) accuracy: `0.41743119266055045`, macro-F1: `0.4095660507040899`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Trade-Signal-Threshold: 0.5 → 0.7
  - Feature-Anzahl: 16 → 25


### Serie `hp_long_eod` (8 Experimente)

#### hp_long_eod_h4_thr0p3pct_hit_7
- Erstes Auftreten (Git): `2025-12-12`
- Config: `data/processed/experiments/hp_long_eod_h4_thr0p3pct_hit_7_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p3pct_hit_7.json`
- Base-Result: `notebooks/results/two_stage__hp_long_eod_h4_thr0p3pct_hit_7.json`
- Label-Params: h=4, up=0.30%, down=-0.30%, strict=False, tol=1.00%, hit=True, src=eodhd
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.3`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.5499999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.9217391304347826`
  - Direction F1(up): `0.681704260651629` (F1(down): `0.23030303030303031`)
  - Combined (3 Klassen) accuracy: `0.12422360248447205`, macro-F1: `0.07366482504604051`
- Änderung vs vorheriges Experiment in dieser Serie: (erstes Experiment der Serie)

#### hp_long_eod_h4_thr0p4pct_hit_1
- Erstes Auftreten (Git): `2025-12-12`
- Config: `data/processed/experiments/hp_long_eod_h4_thr0p4pct_hit_1_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_1.json`
- Base-Result: `notebooks/results/two_stage__hp_long_eod_h4_thr0p4pct_hit_1.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True, src=eodhd
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.375`, up `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6208530805687204`
  - Direction F1(up): `0.6945169712793734` (F1(down): `0.12030075187969924`)
  - Combined (3 Klassen) accuracy: `0.19875776397515527`, macro-F1: `0.11053540587219345`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.30% → 0.40%
  - Down-Schwelle: -0.30% → -0.40%
  - Trade-Signal-Threshold: 0.3 → 0.5
  - Direction-Thresholds: down 0.3→0.375, up 0.5499999999999999→0.6
  - Signal-scale_pos_weight: 0.0863770977295163 → 0.18333333333333332

#### hp_long_eod_h4_thr0p4pct_hit_2
- Erstes Auftreten (Git): `2025-12-12`
- Config: `data/processed/experiments/hp_long_eod_h4_thr0p4pct_hit_2_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_2.json`
- Base-Result: `notebooks/results/two_stage__hp_long_eod_h4_thr0p4pct_hit_2.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True, src=eodhd
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.7`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.7`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6208530805687204`
  - Direction F1(up): `0.6945169712793734` (F1(down): `0.12030075187969924`)
  - Combined (3 Klassen) accuracy: `0.19875776397515527`, macro-F1: `0.11053540587219345`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Trade-Signal-Threshold: 0.5 → 0.7
  - Direction-Thresholds: down 0.375→0.3, up 0.6→0.7

#### hp_long_eod_h4_thr0p4pct_hit_8
- Erstes Auftreten (Git): `2025-12-12`
- Config: `data/processed/experiments/hp_long_eod_h4_thr0p4pct_hit_8_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p4pct_hit_8.json`
- Base-Result: `notebooks/results/two_stage__hp_long_eod_h4_thr0p4pct_hit_8.json`
- Label-Params: h=4, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True, src=eodhd
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.375`, up `0.6`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6208530805687204`
  - Direction F1(up): `0.6945169712793734` (F1(down): `0.12030075187969924`)
  - Combined (3 Klassen) accuracy: `0.19875776397515527`, macro-F1: `0.11053540587219345`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Trade-Signal-Threshold: 0.7 → 0.5
  - Direction-Thresholds: down 0.3→0.375, up 0.7→0.6

#### hp_long_eod_h4_thr0p5pct_hit_3
- Erstes Auftreten (Git): `2025-12-12`
- Config: `data/processed/experiments/hp_long_eod_h4_thr0p5pct_hit_3_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p5pct_hit_3.json`
- Base-Result: `notebooks/results/two_stage__hp_long_eod_h4_thr0p5pct_hit_3.json`
- Label-Params: h=4, up=0.50%, down=-0.50%, strict=False, tol=1.00%, hit=True, src=eodhd
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.3`
- Direction-Thresholds (Trade/kostenbasiert): down `0.475`, up `0.5249999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.7533039647577092`
  - Direction F1(up): `0.7146974063400576` (F1(down): `0.0`)
  - Combined (3 Klassen) accuracy: `0.30745341614906835`, macro-F1: `0.15676959619952494`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.40% → 0.50%
  - Down-Schwelle: -0.40% → -0.50%
  - Trade-Signal-Threshold: 0.5 → 0.3
  - Direction-Thresholds: down 0.375→0.475, up 0.6→0.5249999999999999
  - Signal-scale_pos_weight: 0.18333333333333332 → 0.34125533211456427

#### hp_long_eod_h4_thr0p6pct_hit_6
- Erstes Auftreten (Git): `2025-12-12`
- Config: `data/processed/experiments/hp_long_eod_h4_thr0p6pct_hit_6_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h4_thr0p6pct_hit_6.json`
- Base-Result: `notebooks/results/two_stage__hp_long_eod_h4_thr0p6pct_hit_6.json`
- Label-Params: h=4, up=0.60%, down=-0.60%, strict=False, tol=1.00%, hit=True, src=eodhd
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.3`
- Direction-Thresholds (Trade/kostenbasiert): down `0.475`, up `0.5249999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.6997518610421837`
  - Direction F1(up): `0.7284768211920529` (F1(down): `0.0`)
  - Combined (3 Klassen) accuracy: `0.39751552795031053`, macro-F1: `0.20374531835205992`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.50% → 0.60%
  - Down-Schwelle: -0.50% → -0.60%
  - Signal-scale_pos_weight: 0.34125533211456427 → 0.5413165266106442

#### hp_long_eod_h5_thr0p4pct_hit_5
- Erstes Auftreten (Git): `2025-12-12`
- Config: `data/processed/experiments/hp_long_eod_h5_thr0p4pct_hit_5_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p4pct_hit_5.json`
- Base-Result: `notebooks/results/two_stage__hp_long_eod_h5_thr0p4pct_hit_5.json`
- Label-Params: h=5, up=0.40%, down=-0.40%, strict=False, tol=1.00%, hit=True, src=eodhd
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.3`
- Direction-Thresholds (Trade/kostenbasiert): down `0.3`, up `0.5249999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.5823389021479713`
  - Direction F1(up): `0.680952380952381` (F1(down): `0.06944444444444445`)
  - Combined (3 Klassen) accuracy: `0.12149532710280374`, macro-F1: `0.07222222222222223`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Horizont (h): 4 → 5
  - Up-Schwelle: 0.60% → 0.40%
  - Down-Schwelle: -0.60% → -0.40%
  - Direction-Thresholds: down 0.475→0.3, up 0.5249999999999999→0.5249999999999999
  - Signal-scale_pos_weight: 0.5413165266106442 → 0.11386639676113361

#### hp_long_eod_h5_thr0p5pct_hit_4
- Erstes Auftreten (Git): `2025-12-12`
- Config: `data/processed/experiments/hp_long_eod_h5_thr0p5pct_hit_4_config.json`
- Final-Result: `notebooks/results/final_two_stage/two_stage_final__hp_long_eod_h5_thr0p5pct_hit_4.json`
- Base-Result: `notebooks/results/two_stage__hp_long_eod_h5_thr0p5pct_hit_4.json`
- Label-Params: h=5, up=0.50%, down=-0.50%, strict=False, tol=1.00%, hit=True, src=eodhd
- Features: 21 Spalten
- feature_mode: `price_only`
- Signal-Threshold (klassisch): `0.5`
- Signal-Threshold (Trade/kostenbasiert): `0.5`
- Direction-Thresholds (Trade/kostenbasiert): down `0.39999999999999997`, up `0.5499999999999999`
- Test-Metriken (falls vorhanden):
  - Signal F1(move): `0.7619047619047619`
  - Direction F1(up): `0.6869806094182825` (F1(down): `0.2206896551724138`)
  - Combined (3 Klassen) accuracy: `0.22741433021806853`, macro-F1: `0.15368610204757174`
- Änderung vs vorheriges Experiment in dieser Serie:
  - Up-Schwelle: 0.40% → 0.50%
  - Down-Schwelle: -0.40% → -0.50%
  - Trade-Signal-Threshold: 0.3 → 0.5
  - Direction-Thresholds: down 0.3→0.39999999999999997, up 0.5249999999999999→0.5499999999999999
  - Signal-scale_pos_weight: 0.11386639676113361 → 0.23236282194848823

