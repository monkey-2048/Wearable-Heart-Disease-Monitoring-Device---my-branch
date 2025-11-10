# -*- coding: utf-8 -*-
import numpy as np
import wfdb
import time
import tester_utils
import matplotlib.pyplot as plt

from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as Rpeak_detection_algo
from evaluation_methods.detection_evaluation_algo import Detection_evaluation as Detection_evaluator
import xlsxwriter

if __name__ == '__main__':
    m_detector = Rpeak_detection_algo()
    m_evaluator = Detection_evaluator()
    
    ecg_db_path = './data/MIT-BIH/'
    fs = 360
    
    total_files_db = 0
    total_beats_db = 0
    total_TP_db    = 0
    total_FP_db    = 0
    total_FN_db    = 0
    tolerance      = int(0.1*fs)  # 100 ms

    detection_results = []

    time_start = time.time()

    # =====================================================
    # 只跑指定的三筆紀錄（100、101、102）
    # =====================================================
    record_list = ['207.dat', '208.dat', '210.dat']

    for index, name in enumerate(record_list):
        name = name[:-4]  # 去掉 .dat
        print(f"file name: {name}  -->  {index + 1} of {len(record_list)}")

        # 讀資料與標註
        record = wfdb.rdrecord(ecg_db_path + name)
        ann = wfdb.rdann(ecg_db_path + name, 'atr')
        anno = tester_utils.sort_MIT_annotations(ann)  # 取 MIT-BIH 的 R-peak 參考位置

        # 選導程：MIT-BIH 常用 MLII 做為 channel 0，V5 為 channel 1
        sig = np.transpose(record.p_signal)
        ecg = sig[0]  # MLII；若想試 V5 改成 sig[1]

        # 偵測 R-peaks
        qrs_i_raw = m_detector.rpeak_detection(ecg, fs)

        # 200 ms 不應期去除過近的重複峰值
        corrected_peaks = []
        new_thresh = int(0.200 * fs)
        for i, pk in enumerate(qrs_i_raw):
            if i and (pk - qrs_i_raw[i-1]) < new_thresh:
                continue
            corrected_peaks.append(pk)

        # 評估
        TP, FP, FN = m_evaluator.evaluate_qrs_detector(corrected_peaks, anno, tol=tolerance)
        hr_mean_error, hr_std_error = m_evaluator.evaluate_hr_detector(corrected_peaks, ann.sample, tol=tolerance)

        total_beats = len(ann.sample)
        total_files_db += 1
        total_beats_db += total_beats
        total_TP_db += TP
        total_FP_db += FP
        total_FN_db += FN

        res = [name, total_beats, FP, FN, FP + FN, (FP + FN) / total_beats * 100, hr_mean_error, hr_std_error]
        detection_results.append(res)

            # 將峰值索引轉成合法整數索引
        peaks_idx = np.asarray(corrected_peaks, dtype=int)
        peaks_idx = peaks_idx[(peaks_idx >= 0) & (peaks_idx < len(ecg))]
        peaks_idx = np.unique(np.sort(peaks_idx))
        # 只取前 5 秒（或 10 秒）來看波形
        sec_to_show = 10
        samples_to_show = fs * sec_to_show
        plt.plot(ecg[:samples_to_show], label='ECG')

        # 過濾 R peaks 範圍
        show_peaks = peaks_idx[peaks_idx < samples_to_show]
        plt.plot(show_peaks, ecg[show_peaks], 'ro', label='R peaks')

        # 只有有峰值時才畫紅點
        plt.figure()
        plt.plot(ecg, label='ECG')
        if peaks_idx.size:
            plt.plot(peaks_idx, ecg[peaks_idx], 'o', label='R peaks')
        plt.title(f"Record {name} - Detected R peaks")
        plt.xlabel("Sample")
        plt.ylabel("Amplitude (mV)")
        plt.legend()
        plt.show()


    time_elapsed = time.time() - time_start

    # 總結指標
    se, ppv, f1 = m_evaluator.evaluate_detection_metrics(total_TP_db, total_FP_db, total_FN_db)
    print("\nSensitivity: %.2f%%" % se)
    print("PPV: %.2f%%" % ppv)
    print("F1 Score: %.2f%%\n" % f1)
    print("Elapsed time: %.2f s\n" % time_elapsed)

    print("================================================|=================")
    print("                              Failed    Failed  | mean hr  std hr ")
    print("File   Total     FP     FN   Detection Detection|det. err det. err")
    print("(No.) (Beats) (Beats) (Beats) (Beats)    (%)    |  (bpm)   (bpm)  ")
    print("------------------------------------------------|-----------------")
    for res in detection_results:
        print('{0[0]:1s}    {0[1]:5d}   {0[2]:5d} {0[3]:5d}   {0[4]:5d}   {0[5]:8.2f}   |  {0[6]:.2f}     {0[7]:.2f}'.format(res))
    print("------------------------------------------------|-----------------")
    print("%d      %5d   %5d    %5d    %5d  %2.2f  |" 
           % (total_files_db, total_beats_db, total_FP_db, total_FN_db, 
              total_FP_db + total_FN_db, (total_FP_db + total_FN_db)/total_beats_db*100))

    # 寫 Excel
    file_name = m_detector.get_name()
    workbook = xlsxwriter.Workbook("./results/" + file_name + '.xlsx')
    worksheet = workbook.add_worksheet()
    worksheet.set_column('A:H', 15)
    text_format = workbook.add_format({
        'bold': True, 'border': 6, 'align': 'center', 'valign': 'vcenter',
        'fg_color': '#D7E4BC', 'text_wrap': True,
    })

    worksheet.write(0, 0,     '\nFile \nNo.', text_format)
    worksheet.write(0, 1,     '\nTotal \n(Beats)', text_format)
    worksheet.write(0, 2,     '\nFP \n(Beats)', text_format)
    worksheet.write(0, 3,     '\nFN \n(Beats)', text_format)
    worksheet.write(0, 4,     'Failed \nDetection \n(Beats)', text_format)
    worksheet.write(0, 5,     'Failed \nDetection \n(%)', text_format)
    worksheet.write(0, 6,     'mean hr \ndetection error \n(bpm)', text_format)
    worksheet.write(0, 7,     'std hr \ndetection error \n(bpm)', text_format)

    for row, res in enumerate(detection_results, start=1):
        worksheet.write_row(row, 0, res)

    # 這裡改成動態顯示「幾筆紀錄」
    res_summary = [f'{total_files_db} records', total_beats_db, total_FP_db, total_FN_db,
                   total_FP_db + total_FN_db, (total_FP_db + total_FN_db)/total_beats_db*100, 0.0, 0.0]
    worksheet.write_row(len(detection_results) + 1, 0, res_summary)

    worksheet.write_row(len(detection_results) + 3, 0, ['Sensitivity: ', se])
    worksheet.write_row(len(detection_results) + 4, 0, ['PPV: ', ppv])
    worksheet.write_row(len(detection_results) + 5, 0, ['F1 Score: ', f1])
    worksheet.write_row(len(detection_results) + 7, 0, ['Time Elapsed (s): ', time_elapsed])
    workbook.close()
