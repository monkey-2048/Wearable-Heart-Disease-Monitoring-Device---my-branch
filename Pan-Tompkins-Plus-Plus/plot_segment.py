# plot_segment.py
import numpy as np
import matplotlib.pyplot as plt
import wfdb

from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus

FS = 360  # MIT-BIH sampling rate

def plot_segment(rec_id='207', lead=0, start_s=120, dur_s=10):
    rec_path = f'./data/MIT-BIH/{rec_id}'
    # 讀檔
    rec = wfdb.rdrecord(rec_path)
    ann = wfdb.rdann(rec_path, 'atr')  # 參考標註（R-peak 位置 in samples）

    ecg = rec.p_signal.T[lead]  # 選導程（0=MLII, 1=V5 for MIT-BIH）
    n = ecg.shape[0]

    # 偵測 R-peaks（樣本索引）
    detector = Pan_Tompkins_Plus_Plus()
    r_all = np.asarray(detector.rpeak_detection(ecg, FS), dtype=int)

    # 時段轉樣本範圍
    start = int(start_s * FS)
    end   = start + int(dur_s * FS)
    start = max(0, min(start, n-1))
    end   = max(start+1, min(end, n))

    seg = ecg[start:end]

    # 篩出落在視窗內的偵測 R（樣本索引，轉成區段內相對索引）
    mask = (r_all >= start) & (r_all < end)
    r_win = r_all[mask]
    r_idx = (r_win - start).astype(int)           # 相對區段索引（整數）
    r_idx = r_idx[(r_idx >= 0) & (r_idx < len(seg))]  # 裁切保險

    # 參考標註（可選）：拿 PhysioNet 的 atr R-peaks 來對照
    ref_all = np.asarray(ann.sample, dtype=int)
    ref_mask = (ref_all >= start) & (ref_all < end)
    ref_win = ref_all[ref_mask]
    ref_idx = (ref_win - start).astype(int)
    ref_idx = ref_idx[(ref_idx >= 0) & (ref_idx < len(seg))]

    # 時間軸（秒）
    t = np.arange(len(seg)) / FS
    t_r = r_idx / FS
    t_ref = ref_idx / FS

    # 畫圖
    plt.figure(figsize=(10, 4))
    plt.plot(t, seg, label=f'ECG lead {lead}')
    if r_idx.size:
        plt.scatter(t_r, seg[r_idx], s=28, label='Detected R', zorder=3)
    if ref_idx.size:
        plt.scatter(t_ref, seg[ref_idx], s=20, marker='x', label='Ref R (atr)', zorder=3)
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (mV)')
    plt.title(f'MIT-BIH {rec_id} | {start_s}–{start_s+dur_s}s | lead={lead}')
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    # 範例：高噪聲的 207，取 120–130 秒，MLII（lead=0）
    plot_segment('207', lead=0, start_s=120, dur_s=10)
