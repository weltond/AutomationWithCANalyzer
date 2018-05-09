import threading
import pythoncom
import win32com.client
import time
import tdk
import Diagnostics
import check_result
import help_utils


def auto_standby_script_para(script):
    paras = script.split("(")[1]
    standby_period = ''
    loops = ''
    for para in paras.split(","):
        if para.find("PERIOD") != -1:
            standby_period = para.split("=")[1]
            print("standby period: {}".format(standby_period))
        elif para.find("TIMES") != -1:
            # TIMES is always the last parameter, so to remove the parenthesis
            loops = para.split("=")[1].strip(")\n")
            print("loops of standby: {}".format(loops))
    return standby_period, loops


def manual_standby_script_para(script):
    paras = script.split("(")[1]
    standby_period = ''
    loops = 0
    com_port = ''
    for para in paras.split(","):
        if para.find("PERIOD") != -1:
            standby_period = para.split("=")[1]
            print("standby period: {}".format(standby_period))
        elif para.find("TIMES") != -1:
            # TIMES is always the last parameter, so to remove the parenthesis
            loops = para.split("=")[1].strip(")\n")
            print("loops of standby: {}".format(loops))
        elif para.find("COM") != -1:
            com = para.split("=")[1]
            com_port = "COM" + com
    return standby_period, loops, com_port


def diag_script_para(script):
    fault_type = ''
    loops = 0
    # change to Regular Expression later
    paras = script.split("(")[1].split(")")[0]
    for para in paras.split(","):
        if para.find("FAULT") != -1:
            fault_type = para.split("=")[1]
        elif para.find("TIMES") != -1:
            loops = para.split("=")[1].strip()
    return fault_type, loops


def run_auto_ecall_script(script):
    standby_period, loops_standby = auto_standby_script_para(script)
    print('loops standby:{}'.format(loops_standby))
    for i in range(int(loops_standby)):
        import canalyzer_final
        # test_canalyzer_2.start_canalyzer("EmgcyCallFalt_B_Dsply", "TCU_Send_Signals_5", 50)
        # tdk.ign_cycles(int(cycle_times))
        event = threading.Event()
        list_suite_2 = []

        startTime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

        import can_signals_enum
        ic = canalyzer_final.InitiateCanalyzer(event, list_suite_2, True)
        ic.start()
        t = threading.Thread(target=ic.get_all_signals, args=(can_signals_enum.EmgcyCallHmi,
                                                              "EmgcyCallHmi_D_Stat",
                                                              "TCU_Send_Signals_5",
                                                              can_signals_enum.RstrnImpactEvntStatus,
                                                              "RstrnImpactEvntStatus",
                                                              "GWM_SendSignals_05_HS4"
                                                              ))
        t.start()
        print("canalyzer start!!!!!!!!")
        tdk_thread = threading.Thread(target=tdk.auto_ecall)
        tdk_thread.start()
        print("tdk auto ecall start!!!!!!!!!")
        time.sleep(int(standby_period) * 60 + 150)
        # time.sleep(20)
        event.set()
        print('going to stop')
        ic.stop()
        time.sleep(1)  # to make sure ic.can_logs is updated
        can_log_suite_2 = ic.get_can_log()
        canalyzer_final.write_can_to_file(can_log_suite_2, startTime)
        check_result.check_test_suite_2(can_log_suite_2, startTime, int(standby_period) * 60)
        print("over: {}".format(time.ctime()))  # 3) 15:31:20


def run_manual_ecall_script(script):
    standby_period, loops_standby, com_port = manual_standby_script_para(script)
    for i in range(int(loops_standby)):
        import canalyzer_final
        # test_canalyzer_2.start_canalyzer("EmgcyCallFalt_B_Dsply", "TCU_Send_Signals_5", 50)
        # tdk.ign_cycles(int(cycle_times))
        event = threading.Event()
        list_suite_2 = []
        startTime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        import can_signals_enum
        ic = canalyzer_final.InitiateCanalyzer(event, list_suite_2, True)
        ic.start()
        t = threading.Thread(target=ic.get_all_signals, args=(can_signals_enum.EmgcyCallHmi,
                                                              "EmgcyCallHmi_D_Stat",
                                                              "TCU_Send_Signals_5",
                                                              can_signals_enum.EmgcyCallCancl,
                                                              "EmgcyCallCancl_T_Actl",
                                                              "TCU_Send_Signals_5"
                                                              ))
        t.start()
        print("canalyzer start!!!!!!!!")
        import load_box
        load_box_thread = threading.Thread(target=load_box.start_load_box, args=(com_port,))
        load_box_thread.start()
        print("loadbox manual ecall start!!!!!!!!!")
        time.sleep(int(standby_period) * 60 + 150)
        event.set()

        ic.stop()
        time.sleep(1)  # to make sure ic.can_logs is updated
        can_log_suite_2 = ic.get_can_log()
        canalyzer_final.write_can_to_file(can_log_suite_2, startTime)
        check_result.check_test_suite_2(can_log_suite_2, startTime, int(standby_period) * 60)
        print("over: {}".format(time.ctime()))  # 3) 15:31:20


def run_diag_script(lb_port, script, tdk_stat, gui_queue, result_queue):
    import diag_automation
    if "button" in script.lower() or "switch" in script.lower():
        fault_type, loops = diag_script_para(script)

        gui_queue.put("BUTTON DIAG:")
        result_queue.put("BUTTON DIAG RESULT (" + str(loops) + " Cases):")
        result_queue.put(str(help_utils.append_dict_to_list("Switch")))

        count = 0
        for i in range(int(loops)):
            count += 1
            result_queue.put("----TC" + str(count) + "----")
            diag_automation.button_indicator_mic_diagnostic_automation(lb_port, "Switch", fault_type, tdk_stat, count,
                                                                       gui_queue, result_queue)
            time.sleep(2)
    if "ind" in script.lower() or "indicator" in script.lower():
        fault_type, loops = diag_script_para(script)

        gui_queue.put("IND DIAG:")
        result_queue.put("IND DIAG RESULT (" + str(loops) + " Cases):")
        result_queue.put(str(help_utils.append_dict_to_list("StatusIndc")))

        count = 0
        for i in range(int(loops)):
            count += 1
            result_queue.put("----TC" + str(count) + "----")
            diag_automation.button_indicator_mic_diagnostic_automation(lb_port, "ind", fault_type, tdk_stat, count,
                                                                       gui_queue, result_queue)
            time.sleep(2)
    if "mic" in script.lower():
        fault_type, loops = diag_script_para(script)

        gui_queue.put("MIC DIAG:")
        result_queue.put("MIC DIAG RESULT (" + str(loops) + " TCs):")
        result_queue.put(str(help_utils.append_dict_to_list("Mic")))

        count = 0
        for i in range(int(loops)):
            count += 1
            result_queue.put("----TC" + str(count) + "----")
            diag_automation.button_indicator_mic_diagnostic_automation(lb_port, "mic", fault_type, tdk_stat, count,
                                                                       gui_queue, result_queue)
            time.sleep(2)


def run_script(tdk_port, lb_port, script_list, gui_queue, result_queue):
    tdk_stat = tdk.TDK(tdk_port)
    for script in script_list:
        if script.find("SET FAULT") == 0:
            run_diag_script(lb_port, script, tdk_stat, gui_queue, result_queue)
        if script.find("AUTO ECALL STANDBY") == 0:
            run_auto_ecall_script(script)
        if script.find("MANUAL ECALL STANDBY") == 0:
            run_manual_ecall_script(script)
    tdk_stat.close_serial()
    result_queue.put("TDK serial is closed")


