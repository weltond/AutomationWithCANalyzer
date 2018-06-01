import time
import threading
import help_utils
from Queue import Queue
import test_suite_1 as ts
from msd_decoder import *
import pythoncom
import win32com
import run_batch
import can_signals_enum
import canalyzer_final
import fd30_decoder as fd
import Queue as q_class


# Used to verify positive 75C response after setting DE06
def get_de06_response_from_75C(id, q, gui_queue):
    pythoncom.CoInitialize()
    app = win32com.client.Dispatch(
        pythoncom.CoGetInterfaceAndReleaseStream(
            id,
            pythoncom.IID_IDispatch
        )
    )
    tmp_list = []
    prev_time = time.time()
    temp_time = prev_time
    tmp = 0
    while True:
        time.sleep(0.01)

        c_75c = app.Bus.GetSignal(2, "TesterPhysicalResTCU4",
                                     "TesterPhysicalResTCU").RawValue
        if tmp != c_75c:
            tmp = c_75c
            tmp_list.append(c_75c)
            curr_time = time.time()
            delta_time, prev_time = curr_time - prev_time, curr_time
            gui_queue.put("Get response from 0x75C after setting DE06: " +
                          str(help_utils.decode_raw_signal_value_helper(c_75c)))
            if help_utils.decode_raw_signal_value_helper(c_75c) == "036ede0600000000L":
                gui_queue.put("Find positive response after setting DE06")
                break
        if time.time() - temp_time > 15:  # after 15s, force it break since 754 should be sent already.
            break

    decode_75c = help_utils.decode_raw_signal_values(tmp_list)
    print "decodedddddd: ", decode_75c
    q.put(decode_75c)
    pythoncom.CoUninitialize()


def verify_signal_not_null(gui_queue, verify_queue):
    gui_queue.put("Start verifying TCU is not NULL...")
    while True:
        # verify_queue is a tuple: (current_status, delta_time)
        can_signal = verify_queue.get()
        if can_signal[0] != 0:
            gui_queue.put("TCU is Not NULL. Continue...")
            break


def verify_standby_expire(gui_queue, verify_queue, standby_queue, standby_period):
    standby_period = int(standby_period) * 60
    standby_requirement = [standby_period - 1, standby_period, standby_period + 1]
    gui_queue.put("Start verifying Standby expires...")
    signal_list = []
    prev_time = time.time()
    while True:
        try:
            can_signal = verify_queue.get(timeout=(int(standby_period)*60-10))
        except q_class.Empty:
            gui_queue.put("Verify Standby Timeout.")
            break
        else:
            print "standby expire signal: ", can_signal
            signal_list.append(can_signal)
            # 1 is NoEvent, 14 is Standby
            if can_signal[0] == 1 and len(signal_list) > 1:
                print signal_list
                print signal_list[len(signal_list) - 1][0]
                if signal_list[len(signal_list) - 2][0] == 14:
                    if int(can_signal[1] + 10) in standby_requirement:
                        standby_queue.put("OK")
                        gui_queue.put("Actual standby timer is CORRECT: " + str(can_signal[1] + 10))
                    else:
                        standby_queue.put("Standby timer WRONG!")
                        gui_queue.put("Standby timer is WRONG: \n" +
                                      "Expected: " + str(standby_requirement) + "\t Actual: " + str(can_signal[1] + 10))
                    break


NOT_VERIFY_FD30 = 3
NO_MSD = 3
DEFAULT_RESULT = -1
FD30_SUCCESS = 1
MSD_SUCCESS = 1
FD30_FAIL = 0
MSD_FAIL = 0


def make_ecall(oecon_list, tdk_stat, wait, standby_period, result_queue, gui_queue,
               propulsion_byte_in_decimal, vehicle_type_byte_in_decimal, standby_byte1_in_decimal,
               standby_byte2_in_decimal, msd_vehicle_type, vehicle_propulsion_type, auto_ecall=True):
    event = threading.Event()
    list_suite_2 = []
    msd_result = DEFAULT_RESULT

    # ================= Determine when to stop current test =================
    # sleep starts when in Standby mode because msd_queue.get() will block the thread.
    # wait: 1. 'false': stop 60s after entering Standby, do not verify fd30 after standby expire
    #       2. 'true_0': stop 10s after quiting Standby, verify fd30 after standby expires
    #       3. 'true_1': stop 2h after quiting Standby, verify fd30 after standby expires
    if wait == 'false':
        # if user don't want to verify fd30, set to 3
        fd30_result_after = NOT_VERIFY_FD30
        fd30_result_before = NOT_VERIFY_FD30
    else:

        fd30_result_after = DEFAULT_RESULT
        fd30_result_before = DEFAULT_RESULT

    startTime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    id1 = help_utils.generate_app_marshal()
    ic = canalyzer_final.InitiateCanalyzer(event, list_suite_2, True, id1)
    ic.start()

    # ===== select CAPL function to set DE06 ======
    ic.select_capl_function('send_extension', 't2')
    help_utils.wait_and_pump_msg()
    try:
        capl_func_handler_id_1 = ic.marshal_handler_1()  # id for the first CAPL function
        capl_func_handler_id_2 = ic.marshal_handler_2()  # id for the second CAPL function
    except TypeError:
        result_queue.put("CANNOT MARSHAL CANalyzer!\nDon't blame me pls!\nRe-start should be fine!")
        ic.stop()
        event.set()
        return

    # ============verify positive response from 75C=================
    verify_queue = Queue()
    verify_ic_id = help_utils.generate_app_marshal()
    threading.Thread(target=get_de06_response_from_75C, name="Thread Get Response for DE06",
                     args=(verify_ic_id, verify_queue, gui_queue)).start()
    # =============================================================

    # (propulsion, vehicleType, standby1, standby2) in decimal
    ic.execute_capl_function2(capl_func_handler_id_1,
                              propulsion_byte_in_decimal,
                              vehicle_type_byte_in_decimal,
                              standby_byte1_in_decimal, standby_byte2_in_decimal)

    # ===========Verify positive response after setting DE06============
    verify_result = verify_queue.get()
    if '036ede0600000000L' in verify_result:
        gui_queue.put("POSITIVE RESPONSE! DE06 is being set successfully! Continue!")
    else:
        gui_queue.put("NEGATIVE RESPONSE! DE06 is not being set! Stop!\n======FAIL======")
        return

    # =============== Run eCall Test Case ===============
    signal_queue = Queue()  # signal_queue is used for ecall_ts
    msd_queue = Queue()
    verify_queue = Queue()  # verify signal is not null
    ecall_ts = ts.EcallTS(msd_queue)  # msd_queue is for getting msd
    threading.Thread(target=ic.get_a_signal, name="Thread run ecall test case",
                     args=(signal_queue, gui_queue, result_queue, oecon_list, ecall_ts,
                           2, "EmgcyCallHmi_D_Stat", "TCU_Send_Signals_5",
                           can_signals_enum.EmgcyCallHmi, verify_queue)).start()
    # Wait until signal is not null
    verify_signal_not_null(gui_queue, verify_queue)

    # ================ Trigger Auto/Manual eCall =====================
    temp_queue = Queue() # for trigger UTC time
    if auto_ecall:
        tdk_thread = threading.Thread(target=tdk_stat.auto_ecall, name="Thread tdk makes auto eCall", args=(temp_queue,))
        tdk_thread.start()
    # triggered utc ephoc
    triggered_utc = temp_queue.get()
    triggered_utc_epoch = time.mktime(triggered_utc.timetuple())
    if auto_ecall:
        result_queue.put("Trigger AUTO eCall at: " + str(triggered_utc))
        print("tdk auto ecall start!!!!!!!!!")
    else:
        result_queue.put("Trigger MANUAL eCall at: " + str(triggered_utc))
        print("tdk manual ecall start!!!!!!!!!")

    # ================== Get MSD =================
    # rawMSD values can be:
    #   - ""
    #   - NULL: IE search is end.
    #   - No MSD
    #   - TIMEOUT
    #   - Found n MSD(s), but something wrong with program
    #   - xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    raw_msd = msd_queue.get()
    gui_queue.put("Raw MSD: " + str(raw_msd)[:70] + '')
    if raw_msd == "NULL" or raw_msd == "" or raw_msd == "No MSD" or raw_msd == "TIMEOUT":
        decoded_msd = "MSD is NONE"

    elif raw_msd.find("but something wrong with program") != -1:
        decoded_msd = raw_msd

    elif len(raw_msd) == 280:
        decoded_msd = generateMSDdecoding(raw_msd)
    else:
        msd_result = NO_MSD
        decoded_msd = "WHAT is MSD? Maybe no internet..."
    result_queue.put(decoded_msd)

    if raw_msd == "NULL" or raw_msd == "" or raw_msd == "TIMEOUT":
        result_queue.put("eCall is Probably not made.\n======FAIL======")
    elif raw_msd == "No MSD":
        msd_result = NO_MSD
        result_queue.put("eCall is found but No MSD is received.\n======PARTIAL======")
    elif raw_msd.find("but something wrong with program") != -1:
        result_queue.put("Sorry my fault! Please use my MSD decoder tool to manually decode!\n======PARTIAL======")
    elif len(raw_msd) == 280:
        # ========= Verify MSD match ============
        # msd_dict =
        # {'Call Type': '',
        # 'Vehicle Type': '',
        # 'VIN': '',
        # 'Activation': '',
        # 'Msg Id': '',
        # 'Propulsion Type': '',
        # 'N2 Delta': '0.0, 0.0',
        # 'Number of Passenger': '',
        # 'N1 Delta': '0.0, 0.0',
        # 'Event Time (UTC)': '2017-06-28 13:09:36',
        # 'Position': '42.294444, -83.228633',
        # 'Position Confidence': '',
        # 'Vehicle Direction': ''}
        msd_dict = get_each_msd_value(decoded_msd)

        # status:    -1: default; 1: pass; 0: fail
        # ----- UTC -----
        utc_status = compare_utc(msd_dict, triggered_utc_epoch, result_queue)
        # ----- Activation -----
        if auto_ecall:
            activation_status = compare_activation(msd_dict, 'automatic', result_queue)
        else:
            activation_status = compare_activation(msd_dict, 'manual', result_queue)
        # ----- Vehicle Type -----
        v_type_status = compare_vehicle_type(msd_dict, msd_vehicle_type, result_queue)
        # ----- Propulsion -----
        prop_status = compare_propulsion(msd_dict, vehicle_propulsion_type, result_queue)

        # ################place it after ecall event result is cleared.
        if utc_status == 1 and activation_status == 1 and v_type_status == 1 and prop_status == 1:
            # result_queue.put("======PASS======")
            result_queue.put("MSD result ------OK")
            msd_result = MSD_SUCCESS
        else:
            # result_queue.put("======FAIL======")
            result_queue.put("MSD result ------NOK")
            msd_result = MSD_FAIL
        # ======================================

    # ================= Determine when to stop current test =================
    # After standby expires:
    #   0. read FD30 first. Make sure FD30 has values. Then put in default session. (operate in batch)
    #   1. do 3 ign cycles.
    #   2. use batch to read FD30 ecall event result. Then put in default session. (operate in batch)
    #   3. read 75C ecall event result.
    #   4. make sure ecall event result is 0.

    # sleep starts when in Standby mode because msd_queue.get() will block the thread.
    # wait: 1. 'false': stop 60s after entering Standby, do not verify fd30 after standby expire
    #       2. 'true_0': stop 10s after quiting Standby, verify fd30 after standby expires
    #       3. 'true_1': stop 2h after quiting Standby
    if wait == 'false':
        time.sleep(60)
    elif wait == 'true_0':
        gui_queue.put("Start reading FD30...")
        fd30_result_before = fd.read_fd30(gui_queue, result_queue, signal_queue, auto_ecall, after_ign_cycles=False)
        gui_queue.put("Finish reading FD30.\nPlease wait for TCU entering NoEvent...")
        # ======== Verify Standby expires and then do 3 ign cycles to clear FD30 ==========
        standby_result_queue = Queue()
        threading.Thread(target=verify_standby_expire, args=(gui_queue, verify_queue,
                                                             standby_result_queue, standby_period)).start()
        # verify_standby_expire(gui_queue, verify_queue, standby_period)
        try:
            print "going to get verify queue, ", time.time()
            standby_expire_result = standby_result_queue.get(timeout=(int(standby_period)*60))
            print "get standby_expire result: ", standby_expire_result
        except q_class.Empty:
            gui_queue.put("Timeout. Standby not EXPIRED. Quit...")
            fd30_result_after = NOT_VERIFY_FD30
        else:
            print "in eeeeelse: ", time.time()
            # time.sleep(int(standby_period) * 60)
            if standby_expire_result == "OK":
                gui_queue.put("Standby expires and Meet timer requirement.\nLet TCU have a rest...")
                time.sleep(15)
                gui_queue.put("Start doing 3 ign cycles...")
                three_ign_cycle(tdk_stat, gui_queue)
                gui_queue.put("Start reading FD30...")
                fd30_result_after = fd.read_fd30(gui_queue, result_queue, signal_queue, auto_ecall,
                                                 after_ign_cycles=True)
            else:
                time.sleep(3)
                event.set()
                gui_queue.put("TCU ISSUES: " + str(standby_expire_result) + ". Going to Stop current test case...")
                result_queue.put("TCU ISSUES: " + str(standby_expire_result) + "\n======FAIL======")
                ic.stop()
                time.sleep(1)  # to make sure ic.can_logs is updated
                can_log_suite_2 = ic.get_can_log()
                canalyzer_final.write_can_to_file(can_log_suite_2, startTime)
                # check_result.check_test_suite_2(can_log_suite_2, startTime, int(standby_period) * 60)
                print("over: {}".format(time.ctime()))  # 3) 15:31:20
                return

    elif wait == 'true_1':
        time.sleep(int(standby_period) * 60 + 7200)
    else:
        time.sleep(60)

    # ================ Verify Result ===============
    gui_queue.put("Result Status are: " + "MSD: " + str(msd_result) + " FD30 Before: " + str(fd30_result_before) +
                  " FD30 After: " + str(fd30_result_after))
    if fd30_result_after == NOT_VERIFY_FD30 and fd30_result_before == NOT_VERIFY_FD30:
        if msd_result == MSD_SUCCESS:
            result_queue.put("======PASS======")
        elif msd_result == MSD_FAIL:
            result_queue.put("======FAIL======")
        elif msd_result == NO_MSD:
            result_queue.put("No MSD\n======PARTIAL======")
    else:
        if msd_result == MSD_SUCCESS:
            if fd30_result_after == FD30_SUCCESS and fd30_result_before == FD30_SUCCESS:
                result_queue.put("======PASS======")
            elif fd30_result_before == FD30_SUCCESS and fd30_result_after == NOT_VERIFY_FD30:
                result_queue.put("MSD PASS, FD30 get PASS but Standby Timer FAIL\n======FAIL======")
            elif fd30_result_before == FD30_SUCCESS and fd30_result_after != FD30_SUCCESS:
                result_queue.put("MSD PASS, FD30 get PASS but FD30 not cleared FAIL\n======FAIL======")
            else:
                result_queue.put("MSD PASS but FD30 FAIL\n======FAIL======")
        elif msd_result == MSD_FAIL:
            if fd30_result_after == FD30_SUCCESS and fd30_result_before == FD30_SUCCESS:
                result_queue.put("MSD FAIL but FD30 PASS\n======FAIL======")
            else:
                result_queue.put("BOTH MSD and FD30 FAIL\n======FAIL======")
        elif msd_result == NO_MSD:
            if fd30_result_after == FD30_SUCCESS and fd30_result_after == FD30_SUCCESS:
                result_queue.put("No MSD but FD30 PASS\n======PARTIAL======")
            else:
                result_queue.put("No MSD and FD30 FAIL\n======FAIL======")
        else:
            if fd30_result_after == FD30_SUCCESS and fd30_result_after == FD30_SUCCESS:
                result_queue.put("Something wrong with MSD but FD30 PASS\n======PARTIAL======")
            else:
                result_queue.put("Something wrong with MSD and FD30 FAIL\n======FAIL======")

    time.sleep(3)
    event.set()
    gui_queue.put("Current Test Case finished. Stop everything.\nPrepare for the next test case...")
    ic.stop()
    time.sleep(1)  # to make sure ic.can_logs is updated
    can_log_suite_2 = ic.get_can_log()
    canalyzer_final.write_can_to_file(can_log_suite_2, startTime)
    # check_result.check_test_suite_2(can_log_suite_2, startTime, int(standby_period) * 60)
    print("over: {}".format(time.ctime()))  # 3) 15:31:20
    time.sleep(2)


def three_ign_cycle(tdk_stat, gui_queue):
    tdk_stat.ign_cycles(gui_queue)


# ==============Get PROPULSION TYPE parameters ==============
def get_prop_helper(prop_type):
    petrol, diesel, cn, lp, elec, hydro, other = 0, 0, 0, 0, 0, 0, 0
    if prop_type.lower() == "petrol" or prop_type.lower() == "gasoline":
        petrol = 1
    elif prop_type.lower() == "diesel":
        diesel = 1
    elif prop_type.lower() == "cn" or prop_type.lower() == "cngas" or prop_type.lower() == "cng":
        cn = 1
    elif prop_type.lower() == "lp" or prop_type.lower() == "lpgas" or prop_type.lower() == "lpg":
        lp = 1
    elif prop_type.lower() == "elect" or prop_type.lower() == "electic":
        elec = 1
    elif prop_type.lower() == "hydro" or prop_type.lower() == "hydrogen":
        hydro = 1
    elif prop_type.lower() == "other":
        other = 1
    print "in helper: petrol, diesel, cn, lp, elec, hydro, other", petrol, diesel, cn, lp, elec, hydro, other
    return petrol, diesel, cn, lp, elec, hydro, other


def get_prop(prop_type):
    petrol, diesel, cn, lp, elec, hydro, other = 0, 0, 0, 0, 0, 0, 0
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
            elif prop.lower() == "elect" or prop.lower() == "electic":
                elec = 1
            elif prop.lower() == "hydro" or prop.lower() == "hydrogen":
                hydro = 1
            elif prop.lower() == "other":
                other = 1
    elif isinstance(prop_type, str):
        print "in  get_prop:  pro_type is : ", prop_type
        petrol, diesel, cn, lp, elec, hydro, other = get_prop_helper(prop_type)
    else:
        print "type is wrong:", type(prop_type)
    return petrol, diesel, cn, lp, elec, hydro, other

# ==================================================================

if __name__ == "__main__":
    prop_type = "petrol"
    petrol, diesel, cn, lp, elec, hydro, other = get_prop(prop_type)
    print 'in for loop: prop_type: ', prop_type
    print "in for loop: petrol, diesel, cn, lp, elec, hydro, other", petrol, diesel, cn, lp, elec, hydro, other
