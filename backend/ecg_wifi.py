import socket
import csv
import os
from datetime import datetime
from collections import deque

import numpy as np
import pan_tompkins_plus_plus.address_features as af

ESP32_IP = '192.168.0.102'
PORT = 80
BASE_DIR = "ecg_records"

WINDOW_SECONDS = 10.0
MICROS_WRAP = 2**32  # micros() on ESP32 is typically uint32 wrap (~71.6 min)

def mode_from_flag(flag: int) -> str:
    return "EXERCISE" if flag == 1 else "REST"

def start_receiver():
    os.makedirs(BASE_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = os.path.join(BASE_DIR, f"ecg_data_{timestamp}.csv")
    feat_path = os.path.join(BASE_DIR, f"ecg_features_{timestamp}.csv")

    print(f"Connecting to {ESP32_IP}:{PORT} ...")
    print(f"Saving raw data to: {raw_path}")
    print(f"Saving features  to: {feat_path}")

    # window buffers (ESP32 time base)
    win_t = deque()  # seconds (relative within window)
    win_v = deque()

    current_mode = "REST"

    # ESP32 time bookkeeping
    last_t_us_raw = None
    wrap_count = 0

    # window start (ESP32 extended time in seconds)
    window_start_s = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ESP32_IP, PORT))
        print("Connected! Receiving... (Press Ctrl+C to stop)")

        with open(raw_path, mode='w', newline='') as raw_f, \
             open(feat_path, mode='w', newline='') as feat_f:

            raw_writer = csv.writer(raw_f)
            raw_writer.writerow(["esp_time_us", "mode", "voltage"])

            feat_writer = csv.writer(feat_f)
            feat_fields = [
                "esp_time_s_start", "esp_time_s_end", "mode",
                "fs_hz", "max_hr", "avg_hr", "st_label", "oldpeak",
                "resting_ecg", "calc_time"
            ]
            feat_writer.writerow(feat_fields)

            buffer = ""

            try:
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        print("Connection closed by server.")
                        break

                    buffer += chunk.decode("utf-8", errors="replace")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        # expected: time_us,isExercise,voltage
                        parts = [p.strip().strip('"') for p in line.split(",")]
                        if len(parts) < 3:
                            continue

                        t_us_str, mode_str, v_str = parts[0], parts[1], parts[2]

                        # parse time_us
                        try:
                            t_us_raw = int(t_us_str)
                        except ValueError:
                            continue

                        # handle micros() wrap-around
                        if last_t_us_raw is not None and t_us_raw < last_t_us_raw:
                            # treat as wrap
                            wrap_count += 1
                        last_t_us_raw = t_us_raw

                        t_us_ext = t_us_raw + wrap_count * MICROS_WRAP  # monotone-ish
                        t_s_ext = t_us_ext * 1e-6

                        # parse mode 0/1 -> REST/EXERCISE
                        try:
                            mode_flag = int(mode_str)
                            current_mode = mode_from_flag(mode_flag)
                        except ValueError:
                            pass

                        # parse voltage (NaN allowed)
                        try:
                            v = float(v_str)
                        except ValueError:
                            continue

                        # raw write (ESP32 time)
                        raw_writer.writerow([t_us_ext, current_mode, v])

                        # init window start at first sample
                        if window_start_s is None:
                            window_start_s = t_s_ext

                        # push into window using ESP32-relative seconds
                        win_t.append(t_s_ext - window_start_s)
                        win_v.append(v)

                        # window complete?
                        if (t_s_ext - window_start_s) >= WINDOW_SECONDS:
                            ts = np.asarray(win_t, dtype=float)
                            ecg = np.asarray(win_v, dtype=float)

                            # compute fs from ESP32 timestamps (more reliable than assuming 160)
                            if len(ts) >= 2 and (ts[-1] - ts[0]) > 0:
                                fs_est = (len(ts) - 1) / (ts[-1] - ts[0])
                            else:
                                fs_est = np.nan

                            # reset for next window
                            window_end_s = t_s_ext
                            win_t.clear()
                            win_v.clear()
                            window_start_s = t_s_ext

                            try:
                                feat = af.calc_features(ts, ecg, base=current_mode)
                                if not isinstance(feat, dict):
                                    raise TypeError(f"calc_features returned {type(feat)}; expected dict")

                                # 若 calc_features 沒填 fs_hz，你可以用這個覆蓋/補上
                                if "fs_hz" not in feat or feat.get("fs_hz") in (None, "", 0):
                                    feat["fs_hz"] = fs_est

                                print(f"[FEATURE] mode={current_mode} avg_hr={feat.get('avg_hr')} max_hr={feat.get('max_hr')} fs={feat.get('fs_hz')}")

                                row = []
                                for k in feat_fields:
                                    if k == "esp_time_s_start":
                                        row.append(window_end_s - WINDOW_SECONDS)
                                    elif k == "esp_time_s_end":
                                        row.append(window_end_s)
                                    elif k == "mode":
                                        row.append(current_mode)
                                    else:
                                        row.append(feat.get(k, ""))
                                feat_writer.writerow(row)

                            except Exception as e:
                                print(f"[FEATURE] Error: {e}")

            except KeyboardInterrupt:
                print("\nStopped. Data saved.")

if __name__ == "__main__":
    start_receiver()