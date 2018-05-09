import multiprocessing as mp
import threading
import time
import tdk
import Queue
import can_signals_enum
import load_box
import help_utils
import canalyzer_final
import canalyzer_diag_final
from countdown_latch import CountDownLatch
import win32com.client
import pythoncom
from win32gui import MessageBox as msgbox


# ============================ Diagnostic STEPS=================================
"""                         For Button, Indicator, Mic ONLY
    1. Start CANalyzer and IGN CYCLE (OFF -> ON to make sure CAN Fault signal starts from NO).
    2. Make sure there is no Fault by reading Fault Signal from CANalyzer.
    3. IGN OFF.
    4. Create a fault from loadbox.
    5. IGN ON.
    6. Monitor Fault Signal from CANalyzer. Once Fault.YES, CAPL program send 0x754 and read DTCs from 0x75C.
    7. IGN OFF. (Fault signal will change to NO immediately)
    8. Set Normal from loadbox.
    9. Clear DTC. (can be done at step 1)
    10. ING ON to make sure Fault.NO for 20s.
"""
# ============================       END       =================================


def generate_app_marshal():
    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx('CANalyzer.Application')
    app_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, app)
    return app_id


# sometimes even I close the tdk serial, it seems it's still open. So move the tdk object out of the func,
# instead, get an instance of tdk from test_run_script.py,
# so as to open and close before and after the script completed.
def button_indicator_mic_diagnostic_automation(lb_port, component, fault, tdk_stat, count, gui_queue, result_queue):
    # get fault command and send it to loadbox
    fault_command = help_utils.get_fault_command(component, fault)
    # For COM threading
    app_id1 = help_utils.generate_app_marshal()
    app_id2 = help_utils.generate_app_marshal()
    app_id3 = help_utils.generate_app_marshal()
    app_id4 = help_utils.generate_app_marshal()
    # CountDownLatch to make the third thread wait until the first two thread finish.
    cdl = CountDownLatch(2)

    # test_canalyzer_2.start_canalyzer("EmgcyCallFalt_B_Dsply", "TCU_Send_Signals_5", 50)
    # tdk.ign_cycles(int(cycle_times))

    # event is used to close the thread that is running in an infinite loop.
    event = threading.Event()
    event1 = threading.Event()
    event2 = threading.Event()

    listC = []
    dtc_list = []

    # Start time is used to indicate when the test case starts.
    startTime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    gui_queue.put(startTime + ": Log_" + str(count))
    result_queue.put(startTime + ": Log_" + str(count))

    # Set ign off at the beginning to make sure CAN fault signal stays at NO on start up.
    try:
        # Sometimes if you click the 'start' button again, tdk serial is not properly closed after the first test.
        tdk_stat.set_ign_off()
    except AttributeError:
        result_queue.put("TDK serial Issue. Please Try to Re-start the test or program.")
        event.set()
        return

    # =====step 1
    ic_start_up = canalyzer_final.InitiateCanalyzer(event, listC, True, app_id1)
    ic_start_up.start()
    # used to keep monitoring CAN signals
    ic = canalyzer_final.InitiateCanalyzer(event, listC, True, app_id2)
    # start initiation here to make select CAPL function able to use.
    ic2 = canalyzer_diag_final.InitiateCanalyzerDiagNoSpk(event1, dtc_list, app_id3)
    ic3 = canalyzer_diag_final.InitiateCanalyzerDiagNoSpk(event2, dtc_list, app_id4)
    ic2.select_capl_function("send_first_readDtcMsg", "t2")
    ic3.select_capl_function("send_first_readDtcMsg", "t2")
    print "selected"

    # ############## USE MsgWaitForMultipleObject to pump message ################
    help_utils.wait_and_pump_msg()
    # ############## END ################

    # Set ign back to ON.
    time.sleep(5)
    tdk_stat.set_ign_on()

    t = threading.Thread(target=ic.get_all_signals, args=(gui_queue, can_signals_enum.EmgcyCallFault,
                                                          "EmgcyCallFalt_B_Dsply",
                                                          "TCU_Send_Signals_5"))
    t.start()

    # Sometimes the marshal will fail due to unknown reason.
    # So it's neccessary to catch the error and should not do the following test.
    try:
        capl_func_handler_id_1 = ic2.marshal_handler_1()
        capl_func_handler_id_2 = ic2.marshal_handler_2()
    except TypeError:
        result_queue.put("CANNOT MARSHAL CANalyzer!\n")
        ic_start_up.stop()
        event.set()
        return

    # =====step 2
    result_queue.put("Going to Verify No Fault Before Test (15s)")
    no_fault = ic_start_up.verify_no_fault_on_start()
    # no_fault = 1
    print "fault on start?", no_fault
    result_queue.put("No Fault Before Test? -> " + str(no_fault))
    q = Queue.Queue()
    q2 = Queue.Queue()

    if no_fault:
        print('no fault')

        # ======step 3
        tdk_stat.set_ign_off()
        time.sleep(2)

        # ======step 4
        lb = load_box.LoadBox(lb_port, q, q2)
        # used to start a fault through loadbox, e.g. Para can be: help_utils.indicator['ground']
        t_lb = threading.Thread(target=lb.set_one_stat_to_queue, args=(fault_command, gui_queue))
        t_lb.start()
        print('fault created, about to set ign on')
        time.sleep(5)

        # ======step 5
        print('set ign on')
        tdk_stat.set_ign_on()
        time.sleep(2)
        print('ign is on')

        # marshal MeasurementEvent to COM thread. !!!!!!!!!! Should add EXCEPTIONS though. !!!!!!!!


        # ======step 6
        t2 = threading.Thread(target=ic2.get_754_from_loadbox, args=(capl_func_handler_id_1, capl_func_handler_id_2, gui_queue, result_queue, q, lb,
                                                                     tdk_stat, cdl, ic_start_up))
        t2.start()

        # this thread will happen after t_lb & t2 finish, usde to verify after loadbox sends normal
        t3 = threading.Thread(target=ic3.get_normal_from_loadbox, args=(gui_queue, result_queue, q, cdl, tdk_stat))
        t3.start()

        time.sleep(80)
        event.set()
        event1.set()

        # ic.stop()
        # ic2.stop()
        ic_start_up.stop()
        lb.close_serial()
        # tdk_stat.close_serial()

        time.sleep(1)  # to make sure ic.can_logs is updated

        can_log = ic.get_can_log()
        canalyzer_final.write_can_to_file(can_log, startTime)

        dtc_log = ic2.get_can_log()
        canalyzer_diag_final.write_can_to_file(dtc_log, startTime, count)

        # check(listC)
        print("over: {}".format(time.ctime()))  # 3) 15:31:20

    else:
        # ====== GET DTCs to GUI =======
        print "sleep 8s to wait and read DTCs"
        time.sleep(8)
        ic2.execute_capl_function(capl_func_handler_id_1)
        time.sleep(3)
        dtcs = help_utils.get_75c(ic2)
        result_queue.put("Before start: " + str(dtcs))
        # ==============================
        # result_queue.put(startTime + ": Log_" + str(count))
        result_queue.put("Please make sure no fault before testing\n======FAIL======\n")
        canalyzer_diag_final.write_can_to_file(["Please make sure create a NO FAULT system before testing\n"], startTime, count)
        ic_start_up.stop()
        event.set()
        # tdk_stat.close_serial()
        print("check to make sure ecall system has no fault!!!")


def current_button(fault):
    """
    Button as an example:
    1. Set fault in Loadbox.
    2. CAN (& TDK) will receive a signal from loadbox and then monitor its status.
       When its status change from NO->YES, callback loadbox and ask loadbox to set to normal.
    3. Users can manually clear DTC in DET tool and type in yes after it's done.
    4. CAN (&TDK) will keep monitoring its status and verify it stays at NO.
    :param fault: fault category. Available are:
            switch:     open, vbatt, ground
            indicator:  N/A
            mic:        open, vbatt, ground
    :return:
    """
    cdl = CountDownLatch(2)
    # test_canalyzer_2.start_canalyzer("EmgcyCallFalt_B_Dsply", "TCU_Send_Signals_5", 50)
    # tdk.ign_cycles(int(cycle_times))
    event = threading.Event()
    event1 = threading.Event()
    listC = []
    startTime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    q = Queue.Queue()
    q2 = Queue.Queue
    lb = load_box.LoadBox('COM21', q, q2)
    # used to start a fault through loadbox
    t_lb = threading.Thread(target=lb.set_one_stat_to_queue, args=(fault,))
    t_lb.start()
    ic = canalyzer_final.InitiateCanalyzer(event, listC, True)
    ic.start()
    ic2 = canalyzer_final.InitiateCanalyzer(event1, listC, True)
    ic3 = canalyzer_final.InitiateCanalyzer(event1, listC, True)
    # used to keep monitoring CAN signals
    t = threading.Thread(target=ic.get_all_signals, args=(can_signals_enum.EmgcyCallFault,
                                                          "EmgcyCallFalt_B_Dsply",
                                                          "TCU_Send_Signals_5"))
    # t2 = threading.Thread(target=ic2.get_emgcy_fault_signal, args=(q, lb))
    # used to verify fault from loadbox in CAN and callback to loadbox to set normal status
    # t2 = threading.Thread(target=ic2.get_emgcy_fault_from_loadbox, args=(q, lb, cdl))

    dtc_cleared = False
    while not dtc_cleared:
        while True:
            answer = raw_input("Did you clear the DTC? Yes or No?").lower()
            if answer in ('yes', 'no'):
                break

        dtc_cleared = answer == 'yes'
    # this thread will happen after t_lb & t2 finish, usde to verify after loadbox sends normal and dtc is cleared
    # t3 = threading.Thread(target=ic3.get_normal_from_loadbox, args=(q, cdl))

    t.start()
    # t2.start()
    # t3.start()

    time.sleep(40)
    event.set()
    event1.set()

    ic.stop()
    ic2.stop()
    lb.close_serial()

    time.sleep(1)  # to make sure ic.can_logs is updated

    can_log = ic.get_can_log()
    canalyzer_final.write_can_to_file(can_log, startTime)

    # check(listC)
    print("over: {}".format(time.ctime()))  # 3) 15:31:20

class A:
    x = 0
    def __init__(self, a):
        self.a = a
    def g(self):
        print "in A:", self.a

class B(A):
    def __init__(self,a):
        super.__init__(a)
        self.xx = 0
    def g(self):

        #print self.a
        print "in g"


if __name__ == '__main__':
    print(type(help_utils.switch['open']))
    # button_indicator_mic_diagnostic_automation("Switch", "open")
    # current_button(help_utils.switch['open'])
    # b = B()
    # print b.g()