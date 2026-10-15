# Episode-clustered paired bootstrap intervals (test split)

Completion differences in percentage points, 95% percentile intervals, 2000 resamples, resampling unit = parent episode (n = 94). Recomputed by `scripts/export_intervals.py` from `episode_cell_outcomes.csv`.

## Pooled over the 12 timing cells

| a − b | difference [95% CI] |
|---|---|
| Reactive slip + squeeze − Nominal | +17.1 [+10.9, +23.4] |
| Future-loss + squeeze − Nominal | +26.5 [+17.8, +34.8] |
| Value, delay-agnostic − Nominal | +25.3 [+16.5, +33.4] |
| Value, delay-aware − Nominal | +24.9 [+16.2, +32.9] |
| Oracle (privileged) − Nominal | +31.9 [+22.3, +41.5] |
| Random @ budget (10-seed mean) − Nominal | +5.8 [+3.9, +7.7] |
| Value, delay-aware − Value, delay-agnostic | -0.4 [-1.8, +0.8] |
| Value, delay-aware − Future-loss + squeeze | -1.6 [-3.5, -0.2] |
| Value, delay-agnostic − Future-loss + squeeze | -1.2 [-2.9, +0.0] |
| Future-loss + squeeze − Reactive slip + squeeze | +9.4 [+4.8, +14.4] |
| Value, delay-agnostic − Reactive slip + squeeze | +8.2 [+3.0, +13.5] |
| Value, delay-aware − Reactive slip + squeeze | +7.8 [+3.1, +12.7] |
| Value, delay-aware − Random @ budget (10-seed mean) | +19.1 [+12.1, +25.6] |
| Oracle (privileged) − Value, delay-aware | +7.0 [+3.1, +11.9] |
| Oracle (privileged) − Future-loss + squeeze | +5.4 [+2.1, +9.6] |
| Future-loss + squeeze (per-cell thr.) − Future-loss + squeeze | -1.8 [-3.1, -0.7] |
| Value, delay-agnostic (per-cell thr.) − Value, delay-agnostic | -0.3 [-0.8, +0.0] |
| Value, delay-aware (per-cell thr.) − Value, delay-aware | -0.5 [-1.1, -0.1] |
| Value, delay-aware (per-cell thr.) − Value, delay-agnostic (per-cell thr.) | -0.6 [-1.9, +0.4] |
| Value, delay-aware (per-cell thr.) − Future-loss + squeeze (per-cell thr.) | -0.4 [-1.9, +1.2] |

## Per response delay (pooled over observation ages)

| a − b | delay 0 ms | delay 100 ms | delay 250 ms | delay 500 ms |
|---|---|---|---|---|
| Reactive slip + squeeze − Nominal | +25.5 [+17.4, +33.7] | +19.5 [+12.4, +27.0] | +14.9 [+8.5, +21.6] | +8.5 [+3.9, +13.8] |
| Future-loss + squeeze − Nominal | +29.4 [+20.2, +37.9] | +28.0 [+18.8, +36.5] | +26.6 [+17.4, +35.1] | +22.0 [+13.8, +30.1] |
| Value, delay-agnostic − Nominal | +27.0 [+17.7, +35.5] | +26.6 [+17.0, +35.1] | +25.9 [+16.7, +34.1] | +21.6 [+13.1, +29.4] |
| Value, delay-aware − Nominal | +28.4 [+19.1, +37.2] | +25.5 [+16.3, +34.0] | +24.5 [+15.6, +32.6] | +21.3 [+13.1, +29.1] |
| Oracle (privileged) − Nominal | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] |
| Random @ budget (10-seed mean) − Nominal | +8.1 [+5.3, +10.8] | +6.2 [+4.1, +8.5] | +5.2 [+3.4, +7.1] | +3.8 [+2.3, +5.4] |
| Value, delay-aware − Value, delay-agnostic | +1.4 [+0.0, +3.9] | -1.1 [-2.8, +0.0] | -1.4 [-3.9, +0.0] | -0.4 [-1.8, +0.7] |
| Value, delay-aware − Future-loss + squeeze | -1.1 [-3.2, +0.0] | -2.5 [-5.0, -0.4] | -2.1 [-5.0, -0.4] | -0.7 [-2.1, +0.7] |
| Value, delay-agnostic − Future-loss + squeeze | -2.5 [-5.7, +0.0] | -1.4 [-3.5, +0.0] | -0.7 [-1.8, +0.0] | -0.4 [-1.8, +0.7] |
| Future-loss + squeeze − Reactive slip + squeeze | +3.9 [+0.4, +7.8] | +8.5 [+3.5, +13.8] | +11.7 [+6.0, +17.7] | +13.5 [+7.8, +19.5] |
| Value, delay-agnostic − Reactive slip + squeeze | +1.4 [-3.5, +6.0] | +7.1 [+1.4, +12.8] | +11.0 [+5.0, +17.4] | +13.1 [+7.4, +19.5] |
| Value, delay-aware − Reactive slip + squeeze | +2.8 [-1.8, +7.1] | +6.0 [+0.7, +11.3] | +9.6 [+3.9, +15.6] | +12.8 [+7.1, +18.8] |
| Value, delay-aware − Random @ budget (10-seed mean) | +20.2 [+13.3, +27.0] | +19.3 [+11.9, +26.3] | +19.3 [+11.8, +26.3] | +17.5 [+10.0, +24.5] |
| Oracle (privileged) − Value, delay-aware | +3.5 [+0.7, +7.4] | +6.4 [+2.1, +11.3] | +7.4 [+2.8, +12.8] | +10.6 [+5.3, +16.7] |
| Oracle (privileged) − Future-loss + squeeze | +2.5 [+0.0, +5.7] | +3.9 [+0.7, +8.2] | +5.3 [+1.8, +9.6] | +9.9 [+4.6, +16.0] |
| Future-loss + squeeze (per-cell thr.) − Future-loss + squeeze | -3.2 [-5.3, -1.4] | -2.1 [-3.9, -0.7] | -0.7 [-1.8, +0.0] | -1.1 [-2.5, +0.0] |
| Value, delay-agnostic (per-cell thr.) − Value, delay-agnostic | -0.4 [-1.1, +0.0] | -0.4 [-1.1, +0.0] | -0.4 [-1.1, +0.0] | +0.0 [+0.0, +0.0] |
| Value, delay-aware (per-cell thr.) − Value, delay-aware | -2.8 [-5.3, -0.7] | -0.4 [-1.1, +0.0] | +0.7 [+0.0, +1.8] | +0.4 [+0.0, +1.1] |
| Value, delay-aware (per-cell thr.) − Value, delay-agnostic (per-cell thr.) | -1.1 [-3.5, +1.4] | -1.1 [-2.8, +0.0] | -0.4 [-1.1, +0.0] | +0.0 [-1.1, +1.1] |
| Value, delay-aware (per-cell thr.) − Future-loss + squeeze (per-cell thr.) | -0.7 [-2.8, +1.1] | -0.7 [-3.2, +1.8] | -0.7 [-2.1, +0.7] | +0.7 [-0.7, +2.5] |

## Per observation age (pooled over response delays)

| a − b | age 0 ms | age 100 ms | age 250 ms |
|---|---|---|---|
| Reactive slip + squeeze − Nominal | +22.3 [+14.9, +29.5] | +16.8 [+10.6, +23.1] | +12.2 [+6.6, +18.1] |
| Future-loss + squeeze − Nominal | +28.2 [+19.1, +36.4] | +26.3 [+17.6, +34.6] | +25.0 [+16.5, +33.0] |
| Value, delay-agnostic − Nominal | +26.3 [+17.3, +34.6] | +25.3 [+16.5, +33.5] | +24.2 [+15.4, +32.2] |
| Value, delay-aware − Nominal | +25.5 [+16.7, +33.8] | +25.3 [+16.5, +33.5] | +23.9 [+15.4, +31.9] |
| Oracle (privileged) − Nominal | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] |
| Random @ budget (10-seed mean) − Nominal | +6.4 [+4.2, +8.4] | +5.6 [+3.7, +7.5] | +5.5 [+3.6, +7.5] |
| Value, delay-aware − Value, delay-agnostic | -0.8 [-2.9, +0.8] | +0.0 [-1.6, +1.1] | -0.3 [-1.6, +0.8] |
| Value, delay-aware − Future-loss + squeeze | -2.7 [-5.6, -0.5] | -1.1 [-2.9, +0.3] | -1.1 [-2.4, +0.0] |
| Value, delay-agnostic − Future-loss + squeeze | -1.9 [-4.3, +0.0] | -1.1 [-2.9, +0.5] | -0.8 [-1.9, +0.0] |
| Future-loss + squeeze − Reactive slip + squeeze | +5.9 [+1.9, +10.1] | +9.6 [+4.8, +14.6] | +12.8 [+7.2, +18.6] |
| Value, delay-agnostic − Reactive slip + squeeze | +4.0 [-1.1, +8.8] | +8.5 [+3.2, +14.1] | +12.0 [+6.4, +17.8] |
| Value, delay-aware − Reactive slip + squeeze | +3.2 [-1.1, +7.4] | +8.5 [+3.5, +13.8] | +11.7 [+6.1, +17.6] |
| Value, delay-aware − Random @ budget (10-seed mean) | +19.2 [+12.1, +25.8] | +19.7 [+12.5, +26.3] | +18.4 [+11.4, +24.8] |
| Oracle (privileged) − Value, delay-aware | +6.4 [+2.7, +11.2] | +6.6 [+2.4, +11.7] | +8.0 [+3.7, +13.0] |
| Oracle (privileged) − Future-loss + squeeze | +3.7 [+1.1, +7.4] | +5.6 [+2.1, +9.8] | +6.9 [+2.9, +11.4] |
| Future-loss + squeeze (per-cell thr.) − Future-loss + squeeze | -5.3 [-9.3, -2.1] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |
| Value, delay-agnostic (per-cell thr.) − Value, delay-agnostic | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | -0.8 [-2.4, +0.0] |
| Value, delay-aware (per-cell thr.) − Value, delay-aware | -0.3 [-1.1, +0.5] | -1.3 [-2.7, -0.3] | +0.0 [+0.0, +0.0] |
| Value, delay-aware (per-cell thr.) − Value, delay-agnostic (per-cell thr.) | -1.1 [-3.2, +0.5] | -1.3 [-3.5, +0.3] | +0.5 [+0.0, +1.3] |
| Value, delay-aware (per-cell thr.) − Future-loss + squeeze (per-cell thr.) | +2.4 [+0.0, +5.6] | -2.4 [-4.8, -0.5] | -1.1 [-2.4, +0.0] |

## Per cell

### Reactive slip + squeeze − Nominal

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +31.9 [+22.3, +41.5] | +25.5 [+17.0, +34.0] | +19.1 [+11.7, +27.7] | +12.8 [+6.4, +19.1] |
| age 100 ms | +25.5 [+17.0, +34.0] | +20.2 [+12.8, +28.7] | +12.8 [+6.4, +19.1] | +8.5 [+3.2, +13.9] |
| age 250 ms | +19.1 [+11.7, +27.7] | +12.8 [+6.4, +19.1] | +12.8 [+6.4, +19.1] | +4.3 [+1.1, +8.5] |

### Future-loss + squeeze − Nominal

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +30.9 [+21.3, +39.4] | +28.7 [+19.1, +37.2] | +28.7 [+19.1, +37.2] | +24.5 [+16.0, +33.0] |
| age 100 ms | +28.7 [+19.1, +37.2] | +28.7 [+19.1, +37.2] | +26.6 [+17.0, +35.1] | +21.3 [+12.8, +29.8] |
| age 250 ms | +28.7 [+19.1, +37.2] | +26.6 [+17.0, +35.1] | +24.5 [+16.0, +33.0] | +20.2 [+11.7, +28.7] |

### Value, delay-agnostic − Nominal

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +27.7 [+18.1, +36.2] | +26.6 [+17.0, +35.1] | +26.6 [+17.0, +35.1] | +24.5 [+16.0, +33.0] |
| age 100 ms | +26.6 [+17.0, +35.1] | +26.6 [+17.0, +35.1] | +26.6 [+17.0, +35.1] | +21.3 [+12.8, +29.8] |
| age 250 ms | +26.6 [+17.0, +35.1] | +26.6 [+17.0, +35.1] | +24.5 [+16.0, +33.0] | +19.1 [+10.6, +26.6] |

### Value, delay-aware − Nominal

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +29.8 [+20.2, +38.3] | +25.5 [+17.0, +34.0] | +24.5 [+14.9, +33.0] | +22.3 [+13.8, +30.9] |
| age 100 ms | +27.7 [+18.1, +36.2] | +25.5 [+16.0, +34.0] | +25.5 [+16.0, +34.0] | +22.3 [+13.8, +30.9] |
| age 250 ms | +27.7 [+18.1, +36.2] | +25.5 [+16.0, +34.0] | +23.4 [+14.9, +31.9] | +19.1 [+10.6, +26.6] |

### Oracle (privileged) − Nominal

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] |
| age 100 ms | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] |
| age 250 ms | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] | +31.9 [+22.3, +41.5] |

### Random @ budget (10-seed mean) − Nominal

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +8.5 [+5.5, +11.4] | +6.6 [+4.1, +9.0] | +5.7 [+3.6, +8.1] | +4.6 [+2.6, +6.9] |
| age 100 ms | +8.7 [+5.4, +12.0] | +5.3 [+3.3, +7.4] | +4.9 [+2.9, +7.0] | +3.5 [+1.9, +5.2] |
| age 250 ms | +7.1 [+4.4, +10.0] | +6.8 [+4.4, +9.6] | +5.0 [+2.8, +7.3] | +3.2 [+1.6, +4.9] |

### Value, delay-aware − Value, delay-agnostic

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +2.1 [+0.0, +5.3] | -1.1 [-3.2, +0.0] | -2.1 [-5.3, +0.0] | -2.1 [-5.3, +0.0] |
| age 100 ms | +1.1 [+0.0, +3.2] | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | +1.1 [+0.0, +3.2] |
| age 250 ms | +1.1 [+0.0, +3.2] | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | +0.0 [+0.0, +0.0] |

### Value, delay-aware − Future-loss + squeeze

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | -1.1 [-3.2, +0.0] | -3.2 [-7.4, +0.0] | -4.3 [-8.5, -1.1] | -2.1 [-5.3, +0.0] |
| age 100 ms | -1.1 [-3.2, +0.0] | -3.2 [-7.4, +0.0] | -1.1 [-3.2, +0.0] | +1.1 [+0.0, +3.2] |
| age 250 ms | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] |

### Value, delay-agnostic − Future-loss + squeeze

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | -3.2 [-7.4, +0.0] | -2.1 [-5.3, +0.0] | -2.1 [-5.3, +0.0] | +0.0 [+0.0, +0.0] |
| age 100 ms | -2.1 [-5.3, +0.0] | -2.1 [-5.3, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [-3.2, +3.2] |
| age 250 ms | -2.1 [-5.3, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | -1.1 [-3.2, +0.0] |

### Future-loss + squeeze − Reactive slip + squeeze

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | -1.1 [-3.2, +0.0] | +3.2 [-2.1, +8.5] | +9.6 [+4.3, +16.0] | +11.7 [+5.3, +18.1] |
| age 100 ms | +3.2 [-2.1, +8.5] | +8.5 [+3.2, +14.9] | +13.8 [+6.4, +21.3] | +12.8 [+6.4, +20.2] |
| age 250 ms | +9.6 [+4.3, +16.0] | +13.8 [+6.4, +21.3] | +11.7 [+5.3, +18.1] | +16.0 [+8.5, +23.4] |

### Value, delay-agnostic − Reactive slip + squeeze

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | -4.3 [-8.5, -1.1] | +1.1 [-5.3, +7.4] | +7.4 [+1.1, +13.8] | +11.7 [+5.3, +18.1] |
| age 100 ms | +1.1 [-5.3, +7.4] | +6.4 [+0.0, +12.8] | +13.8 [+6.4, +21.3] | +12.8 [+6.4, +20.2] |
| age 250 ms | +7.4 [+1.1, +13.8] | +13.8 [+6.4, +21.3] | +11.7 [+5.3, +18.1] | +14.9 [+7.4, +22.3] |

### Value, delay-aware − Reactive slip + squeeze

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | -2.1 [-5.3, +0.0] | +0.0 [-6.4, +6.4] | +5.3 [-1.1, +11.7] | +9.6 [+4.3, +16.0] |
| age 100 ms | +2.1 [-3.2, +8.5] | +5.3 [-1.1, +11.7] | +12.8 [+6.4, +19.1] | +13.8 [+7.4, +21.3] |
| age 250 ms | +8.5 [+2.1, +14.9] | +12.8 [+6.4, +19.1] | +10.6 [+4.3, +17.0] | +14.9 [+7.4, +22.3] |

### Value, delay-aware − Random @ budget (10-seed mean)

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +21.3 [+14.3, +27.9] | +18.9 [+11.8, +26.2] | +18.7 [+11.3, +25.9] | +17.8 [+9.7, +25.4] |
| age 100 ms | +18.9 [+12.1, +25.9] | +20.2 [+12.3, +27.4] | +20.6 [+13.0, +27.9] | +18.8 [+11.0, +26.3] |
| age 250 ms | +20.5 [+13.1, +27.6] | +18.7 [+11.2, +25.7] | +18.4 [+10.6, +25.6] | +16.0 [+8.2, +23.5] |

### Oracle (privileged) − Value, delay-aware

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +2.1 [+0.0, +5.3] | +6.4 [+2.1, +11.7] | +7.4 [+3.2, +12.8] | +9.6 [+4.3, +16.0] |
| age 100 ms | +4.3 [+1.1, +8.5] | +6.4 [+2.1, +11.7] | +6.4 [+2.1, +11.7] | +9.6 [+4.3, +16.0] |
| age 250 ms | +4.3 [+1.1, +8.5] | +6.4 [+2.1, +11.7] | +8.5 [+3.2, +14.9] | +12.8 [+6.4, +20.2] |

### Oracle (privileged) − Future-loss + squeeze

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +1.1 [+0.0, +3.2] | +3.2 [+0.0, +7.4] | +3.2 [+0.0, +7.4] | +7.4 [+3.2, +12.8] |
| age 100 ms | +3.2 [+0.0, +7.4] | +3.2 [+0.0, +7.4] | +5.3 [+1.1, +9.6] | +10.6 [+5.3, +17.0] |
| age 250 ms | +3.2 [+0.0, +7.4] | +5.3 [+1.1, +9.6] | +7.4 [+3.2, +12.8] | +11.7 [+5.3, +18.1] |

### Future-loss + squeeze (per-cell thr.) − Future-loss + squeeze

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | -9.6 [-16.0, -4.3] | -6.4 [-11.7, -2.1] | -2.1 [-5.3, +0.0] | -3.2 [-7.4, +0.0] |
| age 100 ms | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |
| age 250 ms | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |

### Value, delay-agnostic (per-cell thr.) − Value, delay-agnostic

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |
| age 100 ms | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |
| age 250 ms | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | +0.0 [+0.0, +0.0] |

### Value, delay-aware (per-cell thr.) − Value, delay-aware

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | -3.2 [-7.4, +0.0] | -1.1 [-3.2, +0.0] | +2.1 [+0.0, +5.3] | +1.1 [+0.0, +3.2] |
| age 100 ms | -5.3 [-10.6, -1.1] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |
| age 250 ms | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |

### Value, delay-aware (per-cell thr.) − Value, delay-agnostic (per-cell thr.)

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | -1.1 [-4.3, +2.1] | -2.1 [-5.3, +0.0] | +0.0 [+0.0, +0.0] | -1.1 [-3.2, +0.0] |
| age 100 ms | -4.3 [-8.5, -1.1] | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | +1.1 [+0.0, +3.2] |
| age 250 ms | +2.1 [+0.0, +5.3] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |

### Value, delay-aware (per-cell thr.) − Future-loss + squeeze (per-cell thr.)

| | delay 0 | delay 100 | delay 250 | delay 500 |
|---|---|---|---|---|
| age 0 ms | +5.3 [+1.1, +9.6] | +2.1 [-2.1, +6.4] | +0.0 [-4.3, +4.3] | +2.1 [+0.0, +5.3] |
| age 100 ms | -6.4 [-11.7, -2.1] | -3.2 [-7.4, +0.0] | -1.1 [-3.2, +0.0] | +1.1 [+0.0, +3.2] |
| age 250 ms | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] | -1.1 [-3.2, +0.0] |
