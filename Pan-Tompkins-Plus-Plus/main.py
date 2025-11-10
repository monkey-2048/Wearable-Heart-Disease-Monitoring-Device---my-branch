# -*- coding: utf-8 -*-
"""
Created on Mon Aug 01 16:48:43 2022

@author: Niaz
"""
import numpy as np
import wfdb
import glob
import time
import tester_utils

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
    tolerance      = int(0.1*fs) #Tolerance Window 100ms
    
    detection_results = [];

    db_length = len(glob.glob1('./data/MIT-BIH/',"*.dat"))
    
    time_start=time.time()
    temp_count=0
    
# =====================================================
# 只跑指定的三筆紀錄（100、101、102）
# =====================================================
    record_list = ['100.dat', '101.dat', '102.dat']

    for index, name in enumerate(record_list):
        name = name[:-4]  # 移除 .dat 副檔名
        print("file name: " + name + "  -->  " + str(index + 1) + " of " + str(len(record_list)))

        # === 讀取 MIT-BIH ECG 資料 ===
        record = wfdb.rdrecord(ecg_db_path + name)
        ann = wfdb.rdann(ecg_db_path + name, 'atr')
        anno = tester_utils.sort_MIT_annotations(ann)  # 擷取標準 R 波位置

        # === 選擇導程 (Lead II) ===
        record = np.transpose(record.p_signal)
        record = record[0]  # 改成 Lead II，AD8232 比較接近這個

        # === 啟動 R peak 偵測 ===
        qrs_i_raw = m_detector.rpeak_detection(record, fs)

        # === 修正過於接近的重複峰值 ===
        corrected_peaks = []
        len_orig_peaks = len(qrs_i_raw)
        flag = 0
        new_thresh = 0.200 * fs  # 200 ms refractory period
        for i in range(len_orig_peaks):
            if i > 0:
                if (qrs_i_raw[i] - qrs_i_raw[i - 1]) < new_thresh:
                    if flag == 0:
                        flag = 1
                        continue
            corrected_peaks.append(qrs_i_raw[i])
            flag = 0

        # === 評估準確率 ===
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
        temp_count += 1
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(record, label='ECG')
        plt.plot(corrected_peaks, record[corrected_peaks], 'ro', label='R peaks')
        plt.title(f"Record {name} - Detected R peaks")
        plt.xlabel("Sample")
        plt.ylabel("Amplitude (mV)")
        plt.legend()
        plt.show()


        
        
    time_elapsed = time.time() - time_start

    ###########################################################################
    # print results to the Console

    se, ppv, f1 = m_evaluator.evaluate_detection_metrics(total_TP_db,total_FP_db,total_FN_db)
            
    print("\nSensitivity: %.2f%%" % se)
    print("PPV: %.2f%%" % ppv)
    print("F1 Score: %.2f%%\n" % f1)
    print("Elapsed time: %.2f s\n" % time_elapsed)

    print("================================================|=================")
    print("                              Failed    Failed  | mean hr  std hr ")
    print("File   Total     FP     FN   Detection Detection|det. err det. err")
    print("(No.) (Beats) (Beats) (Beats) (Beats)    (%)    |  (bpm)   (bpm)  ")
    print("------------------------------------------------|-----------------")
    
    for i in range(len(detection_results)):
        res = detection_results[i]

        print('{0[0]:1s}    {0[1]:5d}   {0[2]:{2}d} {0[3]:{2}d}   {0[4]:{2}d}   {0[5]:8.2f}   |  {0[6]:{3}f}     {0[7]:{3}f}'.format(res, 10, 5, .2))

    print("------------------------------------------------|-----------------")
    print("%s      %5d   %5d    %5d    %5d  %2.2f  |" 
           % (total_files_db, total_beats_db, total_FP_db, total_FN_db, 
              total_FP_db+total_FN_db, (total_FP_db+total_FN_db)/total_beats_db*100))
    
    ###########################################################################
    # write results into a file
    file_name = m_detector.get_name()
    workbook = xlsxwriter.Workbook("./results/"+file_name+'.xlsx')
    worksheet = workbook.add_worksheet()

    # Widen the first column to make the text clearer.
    worksheet.set_column('A:H', 15)

    # Add a bold format to use to highlight cells.
    text_format = workbook.add_format({
            'bold':     True,
            'border':   6,
            'align':    'center',
            'valign':   'vcenter',
            'fg_color': '#D7E4BC',
            'text_wrap': True,
            })
    # write header
    worksheet.write(0, 0,     '\nFile \nNo.', text_format)
    worksheet.write(0, 1,     '\nTotal \n(Beats)', text_format)
    worksheet.write(0, 2,     '\nFP \n(Beats)', text_format)
    worksheet.write(0, 3,     '\nFN \n(Beats)',text_format)
    worksheet.write(0, 4,     'Failed \nDetection \n(Beats)',text_format)
    worksheet.write(0, 5,     'Failed \nDetection \n(%)', text_format)
    worksheet.write(0, 6,     'mean hr \ndetection error \n(bpm)', text_format)
    worksheet.write(0, 7,     'std hr \ndetection error \n(bpm)', text_format)

    for row in range(len(detection_results)):
        res = detection_results[row]
        worksheet.write_row(row + 1, 0, res)
        
    res = ['48 patients', total_beats_db, total_FP_db, total_FN_db,
           total_FP_db+total_FN_db, (total_FP_db+total_FN_db)/total_beats_db*100, 0.0, 0.0]
    worksheet.write_row(len(detection_results) + 1, 0, res)
    
    res2 = ['Sensitivity: ', se]
    worksheet.write_row(len(detection_results) + 3, 0, res2)
    
    res2 = ['PPV: ', ppv]
    worksheet.write_row(len(detection_results) + 4, 0, res2)
    
    res2 = ['F1 Score: ', f1]
    worksheet.write_row(len(detection_results) + 5, 0, res2)
    
    res3 = ['Time Elapsed (s): ', time_elapsed]
    worksheet.write_row(len(detection_results) + 7, 0, res3)
    
    workbook.close()
