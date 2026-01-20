# -*- coding: utf-8 -*-
import os
from pathlib import Path
import glob
import numpy as np
import time
import matplotlib.pyplot as plt
import csv
import argparse
from scipy import signal

from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection

def compute_ecg_features(
    sig: np.ndarray, 
    fs: float,
    use_st_filter: bool = True,
):
    sig = np.asarray(sig, dtype=float)
    n = sig.size

    if(use_st_filter):
        sig = filter_for_st(sig, fs)

    # 1) R-peak detection
    peaks = np.asarray(RpeakDetection().rpeak_detection(sig, fs), dtype=int)
    peaks = np.asarray(peaks, dtype=int)
    if peaks.size:
        refractory = int(0.200 * fs)
        keep = [peaks[0]]
        for k in range(1, len(peaks)):
            if peaks[k] - keep[-1] >= refractory:
                keep.append(peaks[k])
        peaks = np.asarray(keep, dtype=int)
    beats_count = int(peaks.size)

    # 2) Instantaneous HR from RR
    if beats_count >= 2:
        rr = np.diff(peaks) / float(fs) # s
        hr_inst = 60.0 / rr             # bpm
        max_hr = float(np.max(hr_inst))
    else:
        hr_inst = np.array([])
        max_hr = np.nan

    # 3) ST metrics per beat (baseline referenced)
    st_vals, slopes = [], []
    pre_w1 = int(0.20 * fs)
    pre_w2 = int(0.12 * fs)
    j_off  = int(0.04 * fs)
    st_s   = int(0.10 * fs)
    st_e   = int(0.16 * fs)
    slope_win = int(0.06 * fs)

    for r in peaks:
        pre_start = r - pre_w1
        pre_end   = r - pre_w2
        j         = r + j_off
        st_start  = r + st_s
        st_end    = r + st_e

        # Edge detection
        if pre_start < 0 or pre_end <= pre_start or st_end >= n or j >= n:
            continue

        baseline = float(np.median(sig[pre_start:pre_end]))

        # (A) ST offset (signed): +elevation / -depression
        st_seg = sig[st_start:st_end] - baseline
        if st_seg.size:
            st_vals.append(float(np.mean(st_seg)))

        # (B) ST slope (J -> J+80 ms linear fit slope，unit mV/s)
        j_end = min(j + slope_win, n)
        x = np.arange(j, j_end) / float(fs)
        y = sig[j:j_end] - baseline
        if x.size >= 3:
            k, _ = np.polyfit(x, y, 1)
            slopes.append(float(k))

    # 4) Compute aggregate statistics
    st_median = float(np.median(st_vals)) if st_vals else np.nan
    st_slope = float(np.median(slopes)) if slopes else np.nan

    # 5) determine slope label (threshold can be adjusted based on data calibration)
    thr_slope = 0.5  # mV/s
    if np.isfinite(st_slope):
        if st_slope >  thr_slope:   st_label = "Up"
        elif st_slope < -thr_slope: st_label = "Down"
        else:                       st_label = "Flat"
    else:
        st_label = None

    return {
        "HR": max_hr,
        "ST": st_median,
        "ST_Slope": st_slope,
        "ST_Label": st_label,         # Up/Flat/Down
        "n_beats": beats_count,
    }

def filter_for_st(sig, fs): #for st slope hp 0.5HZ lp 35Hz
    sig = np.asarray(sig, dtype=float)

    # 1) High-pass 0.5 Hz
    hp_cut = 0.5          # Hz
    hp_N   = 3            # 3rd-order
    Wn_hp  = hp_cut * 2.0 / fs
    bhp, ahp = signal.butter(hp_N, Wn_hp, btype='highpass')
    sig_hp = signal.filtfilt(bhp, ahp, sig)

    # 2) Low-pass 35 Hz
    lp_cut = 35.0         # or try 40 Hz 
    lp_N   = 3
    Wn_lp  = lp_cut * 2.0 / fs
    blp, alp = signal.butter(lp_N, Wn_lp, btype='lowpass')
    sig_bp = signal.filtfilt(blp, alp, sig_hp)

    return sig_bp

# ===== 可調參數 =====
TIMESTAMP_COL = "timestamp" # CSV column name (seconds)
VALUE_COL     = "ecg_value" # CSV column name (ADC counts or mV)

# 讀CSV
def read_csv_one(path):

    ts, val = [], []
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = [h.strip() for h in reader.fieldnames] if reader.fieldnames else [] # Remove leading and trailing whitespace
        name_map = {h.strip(): h for h in reader.fieldnames} if reader.fieldnames else {}
        # Check required columns
        if TIMESTAMP_COL not in fields or VALUE_COL not in fields:
            raise ValueError(f"{path} 缺少必要欄位 {TIMESTAMP_COL},{VALUE_COL} (header={reader.fieldnames})")
        for row in reader:
            try:
                ts.append(float(row[name_map[TIMESTAMP_COL]].strip()))
                val.append(float(row[name_map[VALUE_COL]].strip()))
            except Exception:
                continue
    ts = np.asarray(ts, dtype=float)
    val = np.asarray(val, dtype=float)
    if ts.size < 3:
        raise ValueError(f"{path} 太短，無法估計取樣率")
    return ts, val

def estimate_fs(timestamps):
    """
    以 median Δt 估計取樣率，返回 (fs_float, dt_stats)
    """
    dt = np.diff(timestamps)
    dt = dt[(dt > 0) & np.isfinite(dt)] # Keep positive and finite time differences
    if dt.size == 0:
        raise ValueError("timestamp 無法估計 dt")
    fs = 1.0 / np.median(dt)
    stats = dict(dt_ms_mean=np.mean(dt)*1000.0,
                 dt_ms_std=np.std(dt)*1000.0,
                 dt_ms_min=np.min(dt)*1000.0,
                 dt_ms_max=np.max(dt)*1000.0)
    return float(fs), stats

def linear_resample(ts, x, fs_target):

    t0, t1 = ts[0], ts[-1]
    n = int(np.floor((t1 - t0) * fs_target)) + 1
    if n <= 1:
        # 太短則不重採樣
        return x.copy(), fs_target, ts.copy()
    t_new = t0 + np.arange(n) / fs_target
    x_new = np.interp(t_new, ts, x)
    return x_new, fs_target, t_new

if __name__ == "__main__":
    det = RpeakDetection()

    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_dir", type=str, default=None, help="CSV directory", required=True)
    parser.add_argument("--out_dir", type=str, default=None, help="Output directory", required=True)
    parser.add_argument("--draw_every", type=int, default=1, help="Draw every N datas (avoids a bunch of windows)")
    parser.add_argument("--save_peaks", type=bool, default=True, help="Save R-peaks")
    parser.add_argument("--max_files", type=int, default=None, help="Maximum number of files to process")
    parser.add_argument("--resample_to", type=int, default=None, help="Example: 250 means resample to 250 Hz; set to None to not resample")
    args = parser.parse_args()

    files = sorted(glob.glob(args.csv_dir + "/*.csv"))
    if args.max_files:
        files = files[:args.max_files]
    print(f"[INFO] 使用的 CSV 目錄：{args.csv_dir}")
    print(f"[INFO] 找到 {len(files)} 個 CSV：", [Path(f).name for f in files][:5], "..." if len(files) > 5 else "")
    if not files:
        raise FileNotFoundError(f"找不到任何 CSV：{args.csv_dir}/*.csv")
    # ---- end locator ----

    # 2) 輸出資料夾
    os.makedirs(args.out_dir, exist_ok=True)

    t0 = time.time()
    for i, csv_path in enumerate(files, 1):
        base = Path(csv_path).stem

        # 3) 讀 CSV + 估 fs
        ts, ecg = read_csv_one(csv_path)
        fs_est, dt_stats = estimate_fs(ts)

        # 4) 是否重採樣
        if args.resample_to is not None and args.resample_to > 0:
            ecg_use, fs_float, ts_rs = linear_resample(ts, ecg, float(args.resample_to))
            t_axis = np.arange(ecg_use.size)  # sample index
        else:
            ecg_use, fs_float, ts_rs = ecg, fs_est, ts
            t_axis = np.arange(ecg_use.size)

        # 5) R-peak 偵測 + 不應期去重 (200 ms)
        fs_i = int(round(fs_float))  # 轉整數，避免報錯
        qrs = np.asarray(det.rpeak_detection(ecg_use, fs_i), dtype=int)

        #過濾假的 R-peak (200ms內不應有另一個peak)
        if qrs.size:
            refractory = int(round(0.200 * fs_i)) #應有幾個樣本
            keep = [qrs[0]]
            for k in range(1, len(qrs)):
                if qrs[k] - keep[-1] >= refractory:
                    keep.append(qrs[k])
            qrs = np.asarray(keep, dtype=int)

        # 6) 顯示/輸出
        print(f"[{i}/{len(files)}] {base:>20s} | fs≈{fs_est:.2f} Hz"
              f" (dt_mean={dt_stats['dt_ms_mean']:.3f} ms, std={dt_stats['dt_ms_std']:.3f} ms)"
              f" | peaks={len(qrs)} ")

        if args.save_peaks:
            if qrs.size:
                peak_ts = ts_rs[qrs]   # 與 sample index 對齊的 timestamp
                out_np = np.column_stack([qrs, peak_ts])
            else:
                out_np = np.empty((0, 2), dtype=float)
            np.savetxt(args.out_dir + f"/{base}.peaks.csv",
                       out_np,
                       fmt=["%d", "%.9f"],
                       delimiter=",",
                       header="sample_index,timestamp_s",
                       comments="")
            
            # === (A) 計算兩種版本的 feature ===
            # 建議都用 ecg_use (跟 R-peak 偵測同一個訊號 & fs)
            features = compute_ecg_features(ecg_use, fs_i, use_st_filter=False)
            features_stfilt = compute_ecg_features(ecg_use, fs_i, use_st_filter=True)

            print("Original: ")
            print(f"  HR={features['HR']:.1f} bpm")
            print(f"  ST={features['ST']:.3f} mV")
            print(f"  ST_label={features['ST_Label']}")
            print(f"  ST_slope={features['ST_Slope']:.3f} mV/s")

            print("="*20)

            print("ST filtered: ")
            print(f"  HR={features_stfilt['HR']:.1f} bpm")
            print(f"  ST={features_stfilt['ST']:.3f} mV")
            print(f"  ST_label={features_stfilt['ST_Label']}")
            print(f"  ST_slope={features_stfilt['ST_Slope']:.3f} mV/s")


            # === (B) 專門給 ST 用的濾波波形 (用來畫圖比較) ===
            ecg_stfilt_full = filter_for_st(ecg_use, fs_i)   # 跟 ecg_use 對齊
           
            # === 只取前 N 秒，看得比較清楚 ===
            max_t = 10.0  # 秒 (你剛才寫 2.0 但註解寫 10 秒，看你要哪一個)
            time_axis_sec = (ts_rs - ts_rs[0])
            mask = time_axis_sec <= max_t

            ecg_show_raw    = ecg_use[mask]
            ecg_show_stfilt = ecg_stfilt_full[mask]
            t_show          = time_axis_sec[mask]

            plt.figure()
            # 原始波形
            plt.plot(t_show, ecg_show_raw, label="ECG raw")
            # ST 濾波後波形 (0.5–35 Hz)
            plt.plot(t_show, ecg_show_stfilt, label="ECG ST-filtered (0.5–35 Hz)", linewidth=2)

            # 如果 R-peak 在這段範圍內，就畫出來 (還是用原始 ecg_use 的 peak)
            if qrs.size:
                qrs_mask = qrs[(qrs >= 0) & (qrs < len(ecg_use))]
                peak_times  = time_axis_sec[qrs_mask]
                peak_values = ecg_use[qrs_mask]
                valid = (peak_times >= 0.0) & (peak_times <= max_t)
                plt.plot(peak_times[valid], peak_values[valid], 'o', label="R peaks (raw)")

                # === 標示每拍的 ST 段 (R+60ms ~ R+80ms)，兩條波形都看得到 ===
                st_s = int(round(0.06 * fs_i))  # 60 ms
                st_e = int(round(0.08 * fs_i))  # 80 ms

                first_span = True
                for r in qrs_mask:
                    s_idx = r + st_s
                    e_idx = r + st_e
                    if s_idx < 0 or e_idx >= len(ecg_use):
                        continue

                    t_s = time_axis_sec[s_idx]
                    t_e = time_axis_sec[e_idx]

                    if t_e < 0.0 or t_s > max_t:
                        continue

                    # 半透明色塊：ST 量測窗
                    plt.axvspan(max(t_s, 0.0), min(t_e, max_t),
                                alpha=0.2,
                                label="ST 60–80 ms window" if first_span else None)

                    # 在 ST 段畫水平線：可以選擇畫 raw 或 ST-filtered 的平均
                    y_mean_raw    = float(np.mean(ecg_use[s_idx:e_idx]))
                    y_mean_stfilt = float(np.mean(ecg_stfilt_full[s_idx:e_idx]))

                    plt.plot([t_s, t_e], [y_mean_raw,    y_mean_raw],    linewidth=1, linestyle="--")
                    plt.plot([t_s, t_e], [y_mean_stfilt, y_mean_stfilt], linewidth=2)

                    first_span = False

            title_suffix = f" (fs≈{fs_est:.2f} Hz" + ("" if not args.resample_to else f" -> {fs_i} Hz") + ")"
            plt.title(f"{base} first {max_t:.0f} sec ECG{title_suffix}")
            plt.xlabel("Time (s)")
            plt.ylabel("ECG units")
            plt.legend()
            plt.tight_layout()
            plt.show()
