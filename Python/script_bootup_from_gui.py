import threading
import pythoncom
import win32com.client
import time
import tdk
import Diagnostics
import check_result
import help_utils
from multiprocessing import Queue
import test_suite_1 as ts
from msd_decoder import *
from make_ecall import *


def auto_standby_script_para(script):
    # AUTO ECALL STANDBY(PERIOD=1,WAIT=TRUE_0,VTYPE=1,PROP=petrol,TIMES=1)
    paras = script.split("(")[1].split(")")[0]
    # if not specified, those are default values
    standby_period = '1'  # default 1 min
    loops = '1'  # default 1 loop
    wait = 'true_0'  # default true_0, which means check FD30
    v_type = 1    # default 1 - passenger
    prop_type = "petrol"  # default petrol
    for para in paras.split(","):
        if para.find("PERIOD") != -1:
            standby_period = para.split("=")[1].strip()
            print("standby period: {}".format(standby_period))
        elif para.find("WAIT") != -1:
            # if wait is set to True
            wait = para.split("=")[1].strip()
            print("wait: {}".format(wait))
        elif para.find("TIMES") != -1:
            # TIMES is always the last parameter, so to remove the parenthesis
            loops = para.split("=")[1].strip()
            print("loops of standby: {}".format(loops))
        elif para.find("VTYPE") != -1:
            v_type = para.split("=")[1].strip("").strip("\n")
        if para.find("PROP") != -1:
            # prop_type might be string or list
            prop_type = para.split("=")[1].strip("").strip("\n")
            if prop_type.find("&") != -1:
                prop_type = prop_type.split("&")
            else:
                prop_type = str(prop_type)  # otherwise, type(prop_type) is unicode. Maybe because of GUI?
    return standby_period, wait.lower(), v_type, prop_type, loops


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


def v_type_script_para(script):
    # TEST VTYPE(STANDBY=1, PROP=petrol&diesel, WAIT=TRUE_0, RANGE=[1-16])
    paras = script.split("(")[1].split(")")[0]
    standby_period = 1
    prop_type = 'petrol'
    wait = 'true_0'
    low_range, high_range = 0, 15
    for para in paras.split(","):
        if para.find("STANDBY") != -1:
            standby_period = para.split("=")[1].strip("").strip("\n")
        if para.find("PROP") != -1:
            prop_type = para.split("=")[1].strip("").strip("\n")
            if prop_type.find("&") != -1:
                prop_type = prop_type.split("&")
            else:
                prop_type = str(prop_type)  # otherwise, type(prop_type) is unicode. Maybe because of GUI?
        if para.find("WAIT") != -1:
            wait = para.split("=")[1].strip("").strip("\n")
        if para.find("RANGE") != -1:
            range = para.split("=")[1].strip("").strip("\n")  # [1-4] / [2]
            if range.find("-") == -1:
                low_range = range.strip("[").strip("]").strip()
                high_range = low_range
            else:
                low_range, high_range = range.split("-")[0].strip("[").strip(), range.split("-")[1].strip(
                    "]").strip()
    return standby_period, prop_type, wait.lower(), low_range, high_range


def prop_type_script_para(script):
    # TEST PROP(STANDBY=1, VTYPE=1, WAIT=TRUE_0, PROP=petrol)
    # if no PROP provided, then run all prop test cases
    paras = script.split("(")[1].split(")")[0]
    standby_period = 1
    v_type = "1"
    wait = 'true_0'
    prop_type = "each by each"
    for para in paras.split(","):
        if para.find("STANDBY") != -1:
            standby_period = para.split("=")[1].strip("").strip("\n")
        if para.find("WAIT") != -1:
            wait = para.split("=")[1].strip("").strip("\n")
        if para.find("VTYPE") != -1:
            v_type = para.split("=")[1].strip("").strip("\n")
        if para.find("PROP") != -1:
            prop_type = para.split("=")[1].strip("").strip("\n")
            print "type of prop_type in prop script:", type(prop_type)
            if prop_type.find("&") != -1:
                prop_type = prop_type.split("&")
            else:
                prop_type = str(prop_type)  # otherwise, type(prop_type) is unicode. Maybe because of GUI?
    return standby_period, wait.lower(), v_type, prop_type


WAIT_EXPLAIN = {'false': 'Stop after entering Standby',
                    'true_0': 'Stop after Standby expires and do 3 ign cycles',
                    'true_1': 'Stop after (Standby + 2 hours) expires'}

ONLY_AUTO = 0
ONLY_MANUAL = 1
V_TYPE = 2
PROP_TYPE = 3


def run_ecall_script(script, tdk_stat, gui_queue, result_queue, oecon_list, flag):
    # ===== default values =====
    standby_period = 1
    loops_auto = 1
    wait = 'true_0'
    v_type = "1"
    petrol, diesel, cn, lp, elec, hydro, other = 0, 0, 0, 0, 0, 0, 0
    low_v_type_range = 0
    high_v_type_range = 15
    prop_type = "petrol"
    # ==========================
    if flag == ONLY_AUTO:
        standby_period, wait, v_type, prop_type, loops_auto = auto_standby_script_para(script)
        result_queue.put("\nAUTO ECALL: (" + str(loops_auto) + " Cases): "+
                         "\nstandby period: " + str(standby_period) +
                         "\n" + WAIT_EXPLAIN[wait])
        gui_queue.put("\nAUTO ECALL: (" + str(loops_auto) + " Cases): " +
                         "\nstandby period: " + str(standby_period) +
                         "\n" + WAIT_EXPLAIN[wait])
        petrol, diesel, cn, lp, elec, hydro, other = get_prop(prop_type)
    elif flag == ONLY_MANUAL:
        pass
    elif flag == V_TYPE:
        standby_period, prop_type, wait, low_v_type_range, high_v_type_range = v_type_script_para(script)

        if isinstance(prop_type, list):
            for prop in prop_type:
                if prop.lower() == "petrol" or prop.lower() == "gasoline":
                    petrol = 1
                elif prop.lower() == "diesel":
                    diesel = 1
                elif prop.lower() == "cn" or prop.lower() == "cngas" or prop.lower() == "cng":
                    cn = 1
                elif prop.lower() == "lp" or prop.lower() == "lpgas" or prop.lower() == "lpg":
                    lp = 1
                elif prop.lower() == "elec" or prop.lower() == "electric" or prop.lower() == "elect":
                    elec = 1
                elif prop.lower() == "hydro" or prop.lower() == "hydrogen":
                    hydro = 1
                elif prop.lower() == "other":
                    other = 1
        elif isinstance(prop_type, str):
            petrol, diesel, cn, lp, elec, hydro, other = get_prop_helper(prop_type)
        else:
            pass
    elif flag == PROP_TYPE:
        standby_period, wait, v_type, prop_type = prop_type_script_para(script)
        # print 'script  prop_type :', prop_type

    else:
        pass
    # =============Get decimal bytes to send to CAPL function for DE06===========
    #    NOTICE!!!== propulsion type: reserved is the same as NONE ==

    import change_did
    if v_type.isdigit():
        v_type = int(v_type)
    else:
        result_queue.put("Wrong! Vehicle Type should be an integer. Please change your test cases!")
        return
    standby_byte1_in_decimal, standby_byte2_in_decimal = change_did.change_standby(int(standby_period))
    propulsion_byte_in_decimal, vehicle_propulsion_type = \
        change_propulsion(petrol=petrol, diesel=diesel, cngas=cn, lpgas=lp, elec=elec, hydro=hydro, other=other)# 8 bits
    # this will be rewritten in VTYPE test case.
    vehicle_type_byte_in_decimal, msd_vehicle_type = change_did.change_vehicle_type(v_type)  # first 4 bits
    if vehicle_type_byte_in_decimal == "ERROR":
        result_queue.put("Wrong Vehicle Type. Please change your test cases!")
        return

    # ============================================================================

    # ===== auto ecall only =====
    if flag == ONLY_AUTO:
        gui_queue.put("DE06: \n" + "Propulsion: " + vehicle_propulsion_type + "\n" +
                      "Vehicle Type: " + msd_vehicle_type + "\n" +
                      "Standby: " + str(standby_period) + " min(s)")
        count = 0
        for i in range(int(loops_auto)):
            count += 1
            result_queue.put("----TC" + str(count) + "----")
            gui_queue.put("----TC" + str(count) + "----")
            gui_queue.put("Verifying setting DE06... Please wait......")
            make_ecall(oecon_list, tdk_stat, wait, standby_period,result_queue, gui_queue,
                       propulsion_byte_in_decimal, vehicle_type_byte_in_decimal,
                       standby_byte1_in_decimal, standby_byte2_in_decimal,
                       msd_vehicle_type, vehicle_propulsion_type, auto_ecall=True)
    # ===== Vehicle Type automation =====
    elif flag == V_TYPE:
        count = 0
        # ----- Verify Typo of Vehicle Type Range -----
        if not low_v_type_range.isdigit() or not high_v_type_range.isdigit():
            low_v_type_range, high_v_type_range = 1, 1
            result_queue.put("Input Wrong Vehicle Type. Set to default: Passenger class.")
        else:
            low_v_type_range, high_v_type_range = int(low_v_type_range), int(high_v_type_range)
            if low_v_type_range > high_v_type_range:
                low_v_type_range, high_v_type_range = high_v_type_range, low_v_type_range
                gui_queue.put("Range of Vehicle Type is: " + str(low_v_type_range) + " - " + str(high_v_type_range))
        # ---------------------------------------------

        result_queue.put("\nVehicle Type Test (" + str(len(range(low_v_type_range,high_v_type_range+1))) + " Cases): " +
                         "\nVehicle types: " + str(vehicle_type) +
                         "\n" + WAIT_EXPLAIN[wait])
        gui_queue.put(
            "\nVehicle Type Test (" + str(len(range(low_v_type_range, high_v_type_range + 1))) + " Cases): " +
            "\nVehicle types: " + str(vehicle_type) +
            "\n" + WAIT_EXPLAIN[wait])
        # return
        for each_v_type in range(low_v_type_range, high_v_type_range+1):
            count += 1
            vehicle_type_byte_in_decimal, msd_vehicle_type = change_did.change_vehicle_type(each_v_type)
            gui_queue.put("----TC" + str(count) + "----: " + str(vehicle_type[each_v_type]))
            gui_queue.put("DE06: \n" + "Propulsion: " + vehicle_propulsion_type + "\n" +
                          "Vehicle Type: " + msd_vehicle_type + "\n" +
                          "Standby: " + str(standby_period) + " min(s)")
            result_queue.put("----TC" + str(count) + "----: " + str(vehicle_type[each_v_type]))
            gui_queue.put("Verifying setting DE06... Please wait......")
            make_ecall(oecon_list, tdk_stat, wait, standby_period, result_queue, gui_queue,
                       propulsion_byte_in_decimal, vehicle_type_byte_in_decimal,
                       standby_byte1_in_decimal, standby_byte2_in_decimal,
                       msd_vehicle_type, vehicle_propulsion_type, auto_ecall=True)

    # ===== Propulsion Type automation =====
    elif flag == PROP_TYPE:
        count = 0
        # return
        all_prop_flag = True
        for i in range(7):
            if prop_type != "each by each":
                result_queue.put(
                    "\nPropulsion Type Test (" + str(1) + " Cases): " +
                    "\nPropulsion types: " + str(vehicle_propulsion) +
                    "\n" + WAIT_EXPLAIN[wait])
                gui_queue.put(
                    "\nPropulsion Type Test (" + str(1) + " Cases): " +
                    "\nPropulsion types: " + str(vehicle_propulsion) +
                    "\n" + WAIT_EXPLAIN[wait])
                petrol, diesel, cn, lp, elec, hydro, other = get_prop(prop_type)
                all_prop_flag = False
            if prop_type == "each by each":
                result_queue.put(
                    "\nPropulsion Type Test (" + str(7) + " Cases): " +
                    "\nPropulsion types: " + str(vehicle_propulsion) +
                    "\n" + WAIT_EXPLAIN[wait])
                gui_queue.put(
                    "\nPropulsion Type Test (" + str(7) + " Cases): " +
                    "\nPropulsion types: " + str(vehicle_propulsion) +
                    "\n" + WAIT_EXPLAIN[wait])
                petrol, diesel, cn, lp, elec, hydro, other = 0, 0, 0, 0, 0, 0, 0
                if i == 0:
                    petrol = 1
                if i == 1:
                    diesel = 1
                if i == 2:
                    cn = 1
                if i == 3:
                    lp = 1
                if i == 4:
                    elec = 1
                if i == 5:
                    hydro = 1
                if i == 6:
                    other = 1
            count += 1
            print "prop?: petrol, diesel, cn, lp, elec, hydro, other", petrol, diesel, cn, lp, elec, hydro, other
            propulsion_byte_in_decimal, vehicle_propulsion_type = \
                change_propulsion(petrol=petrol, diesel=diesel, cngas=cn, lpgas=lp, elec=elec, hydro=hydro, other=other)
            gui_queue.put("----TC" + str(count) + "----: " + str(vehicle_propulsion_type))
            gui_queue.put("DE06: \n" + "Propulsion: " + vehicle_propulsion_type + "\n" +
                          "Vehicle Type: " + msd_vehicle_type + "\n" +
                          "Standby: " + str(standby_period) + " min(s)")
            result_queue.put("----TC" + str(count) + "----: " + str(vehicle_propulsion_type))
            gui_queue.put("Verifying setting DE06... Please wait......")
            make_ecall(oecon_list, tdk_stat, wait, standby_period, result_queue, gui_queue,
                       propulsion_byte_in_decimal, vehicle_type_byte_in_decimal,
                       standby_byte1_in_decimal, standby_byte2_in_decimal,
                       msd_vehicle_type, vehicle_propulsion_type, auto_ecall=True)
            if not all_prop_flag:
                break

def run_manual_ecall_script(script):
    #standby_period, loops_standby, com_port = manual_standby_script_para(script)
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
        #load_box_thread = threading.Thread(target=load_box.start_load_box, args=(com_port,))
        #load_box_thread.start()
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
        result_queue.put("\nBUTTON DIAG RESULT (" + str(loops) + " Cases):")
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
        result_queue.put("\nIND DIAG RESULT (" + str(loops) + " Cases):")
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
        result_queue.put("\nMIC DIAG RESULT (" + str(loops) + " TCs):")
        result_queue.put(str(help_utils.append_dict_to_list("Mic")))

        count = 0
        for i in range(int(loops)):
            count += 1
            result_queue.put("----TC" + str(count) + "----")
            diag_automation.button_indicator_mic_diagnostic_automation(lb_port, "mic", fault_type, tdk_stat, count,
                                                                       gui_queue, result_queue)
            time.sleep(2)


def run_script(tdk_port, lb_port, script_list, gui_queue, result_queue, oecon_list):
    import serial
    try:
        tdk_stat = tdk.TDK(tdk_port)
        for script in script_list:
            if script.find("SET FAULT") == 0:
                run_diag_script(lb_port, script, tdk_stat, gui_queue, result_queue)
            if script.find("AUTO ECALL STANDBY") == 0:
                run_ecall_script(script, tdk_stat, gui_queue, result_queue, oecon_list, flag=ONLY_AUTO)
            if script.find("MANUAL ECALL STANDBY") == 0:
                run_manual_ecall_script(script)
            if script.find("TEST VTYPE") == 0:
                run_ecall_script(script, tdk_stat, gui_queue, result_queue, oecon_list, flag=V_TYPE)
            if script.find("TEST PROP") == 0:
                run_ecall_script(script, tdk_stat, gui_queue, result_queue, oecon_list, flag=PROP_TYPE)
        tdk_stat.close_serial()
        result_queue.put("TDK serial is closed")
        gui_queue.put("No Test left.\nTDK serial is closed")
        result_queue.put("Congratulation! Finish all Test Cases! Good Job!\n")
    except serial.serialutil.SerialException:
        result_queue.put("TDK SerialPort didn't open, please check Serial or conflict")


if __name__ == '__main__':
    script = "AUTO ECALL STANDBY(PERIOD=1,WAIT=True_1,TIMES=3)\n"
    standby_period, wait, vtype, proptype, loops_standby = auto_standby_script_para(script)
    WAIT_EXPLAIN = {'false': 'Stop after entering Standby',
                    'true_0': 'Stop after Standby expires and do 3 ign cycles',
                    'true_1': 'Stop after standby + 2 hours expires'}
    print WAIT_EXPLAIN[wait]

    x = "DE06: \n" + "Propulsion: Petrol\n" + "Vehicle Type: passenger vehicle, Class M1\n" +\
        "Standby: " + str(5) + "\n"
    for info in x.split("\n"):
        if info.startswith("Propulsion"):
            print info.split(":")[1].strip()
        elif info.startswith("Vehicle Type"):
            print info.split(":")[1].strip()
        elif info.startswith("Standby"):
            print info.split(":")[1].strip()