# WORKING!!!!!!

import win32com.client
import time
import threading
import pythoncom
import can_signals_enum
import help_utils
import canalyzer_final
from win32gui import MessageBox as msgbox

# ============================ Diagnostic STEPS=================================
"""
    1. Start CANalyzer and IGN ON.
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

class MeasEvents:
    def __init__(self):
        self.CAPL1 = None
        self.CAPL2 = None
        self.Appl = None
        self.CaplFunction1 = None
        self.CaplFunction2 = None

    def OnInit(self):
        print "diag MeasEvents:OnInit now called"
        if self.CAPL1 is not None and self.CAPL2 is not None:
            self.CaplFunction1 = self.Appl.CAPL.GetFunction(self.CAPL1)
            self.CaplFunction2 = self.Appl.CAPL.GetFunction(self.CAPL2)
            print "diag OnInit:Load CAPL Script = " + self.CAPL1 + " and " + self.CAPL2


class InitiateCanalyzerDiagNoSpk:
    # Remember to use Class.Variable_Name to change the class variable.
    dtc_result_final = ""

    def __init__(self, event_thread, can_logs, app_id):
        # canalyzer_final.InitiateCanalyzer.__init__(self, event_thread, can_logs, app_id)
        pythoncom.CoInitialize()
        self.app = win32com.client.Dispatch(
            pythoncom.CoGetInterfaceAndReleaseStream(
                app_id,
                pythoncom.IID_IDispatch
            )
        )
        self.Measurement = self.app.Measurement
        self.Running = lambda: self.Measurement.Running
        self.event = event_thread
        self.can_logs = can_logs  # It's a list
        self.dtc_result = ""
        self.marshalled_app = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, self.app)
        # Used to call MeasEvent to call CAPL function, but cause CANalyzer stuck
        self.__MeasurementEvents = win32com.client.DispatchWithEvents(self.Measurement, MeasEvents)
        # transfer the application object to Event class for CAPL handling
        self.__MeasurementEvents.Appl = self.app
        self.__MeasurementEvents_marshal = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch,
                                                                               self.__MeasurementEvents)

    def get_can_log(self):
        return self.can_logs

    # ========================= Interact with CAPL Function =============================
    def select_capl_function(self, function_name1, function_name2):
        '''
        Initialize which CAPL functions are being selected. At most 2 functions right now.
        :param function_name1:
        :param function_name2:
        :return:
        '''
        self.__MeasurementEvents.CAPL1 = function_name1
        self.__MeasurementEvents.CAPL2 = function_name2

    def marshal_handler_1(self):
        '''
        pass CaplFunction 1 to COM thread
        :return:
        '''
        call_marshal_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch,
                                                                          self.__MeasurementEvents.CaplFunction1)
        return call_marshal_id

    def marshal_handler_2(self):
        '''
        pass CaplFunction 2 to COM thread
        :return:
        '''
        call_marshal_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch,
                                                                          self.__MeasurementEvents.CaplFunction2)
        return call_marshal_id

    @staticmethod
    def execute_capl_function(call_marshal_id):
        '''
        Execute Capl Function based on call_marshal_id
        :param call_marshal_id: determine which Capl Function is called.
        :return:
        '''
        pythoncom.CoInitialize()
        measurement_event = pythoncom.CoGetInterfaceAndReleaseStream(
            call_marshal_id,
            pythoncom.IID_IDispatch
        )
        m = win32com.client.Dispatch(measurement_event)

        print "Now trying to call CAPL func now"
        while True:
            pythoncom.PumpWaitingMessages()
            ret = m.Call()
            print "ret is {}".format(ret)
            pythoncom.CoUninitialize()
            return ret
    # ========================= Interact with CAPL Function =============================
    # ===================================== END =========================================

    # ======8
    def get_normal_from_loadbox(self, log_queue, result_queue, q, cdl, tdk_instance,
                                signal_enum_1=can_signals_enum.EmgcyCallFault,
                                signal_1="EmgcyCallFalt_B_Dsply",
                                message_1="TCU_Send_Signals_5"):
        pythoncom.CoInitialize()
        self.app = win32com.client.Dispatch(
            pythoncom.CoGetInterfaceAndReleaseStream(
                self.marshalled_app,
                pythoncom.IID_IDispatch
            )
        )
        cdl.await()
        print("finally get normal!")
        print self.dtc_result
        get_normal_flag = False
        fault = q.get()  # if q is empty, this will stuck the thread
        print "fault?: ", fault
        if fault == "NOK":
            tdk_instance.set_ign_on()
            result_queue.put("======FAIL======\n")
            return
        else:
            # ======10
            tdk_instance.set_ign_on()
            prev_time = time.time()

            while True:
                # print('in while true of normal')
                time.sleep(0.01)
                current_status = self.app.Bus.GetSignal(2, message_1, signal_1).Value

                # Verify: if 15s later the status doesn't change, break loop and mark as FAIL.
                if time.time() - prev_time > 20:
                    print("NO CHANGE!! PASS!!")
                    # Remember to use Class.Variable_Name to change the class variable.
                    if InitiateCanalyzerDiagNoSpk.dtc_result_final == "OK":
                        result_queue.put("No Fault \n======PASS======\n")
                        self.can_logs.append("\n ======PASS======\n")
                        break
                    elif InitiateCanalyzerDiagNoSpk.dtc_result_final == "":
                        result_queue.put("\n ======NULL======\n")
                        self.can_logs.append("\n ======NULL======\n")
                        break
                    else:
                        result_queue.put("\n ======FAIL======\n")
                        self.can_logs.append("\n ======FAIL======\n")
                        break

                if current_status == 1.0:  # 1.0 is YES.
                    get_fault_flag = False
                    log_queue.put("FAULT STATUS DETECTED!!")
                    print('FAIL! STATUS CHANGED!! I am going to go out')
                    self.can_logs.append("FAULT NOT CLEARED. FAIL")
                    break

                if self.event.wait(timeout=0.01):
                    # print("received stop: {}".format(time.ctime()))         # 4) 15:31:20
                    break

    def get_754_from_loadbox(self, id1,id2, queue_from_gui, result_to_gui, q, loadbox_instance,
                             tdk_instance, cdl, initiate_instance):
        pythoncom.CoInitialize()
        self.app = win32com.client.Dispatch(
            pythoncom.CoGetInterfaceAndReleaseStream(
                self.marshalled_app,
                pythoncom.IID_IDispatch
            )
        )

        get_fault_flag = False
        # if q is empty, this will stuck the thread
        fault = q.get()
        # e.g. 'Switch-VBATT-0'
        component = ""
        should_report_dtc_id = "null"
        if fault.find("Set Fault:") != -1:
            component = fault.split("Fault: ")[1].split("-")[0]
            fault_category = fault.split("Fault: ")[1].split("-")[1]
            get_fault_flag = True
            # add corresponding dtc list to logs
            self.can_logs.append(help_utils.append_dict_to_list(component) + "\n ")

            # add simulated fault to logs
            self.can_logs.append("Simulate Fault: " + component + "-" + fault_category + " ---> ")

            # get corresponding dtc id from queue
            should_report_dtc_id = help_utils.get_dtc_id_from_one_fault(component, fault_category)
            result_to_gui.put("Simulate Fault: " + component + "-" + fault_category + " ---> Should receive: " + should_report_dtc_id)
        else:
            print('q not found in fault func', fault)
            get_fault_flag = False
        # since q.get() will make current thread stuck, so prev_time is the time when fault received.
        prev_time = time.time()
        temp_75c_status = -1

        list_75c = []  # used to store raw value of 75C

        print('get emgcy fault signal function starts')
        while True:
            # print('in while true of fault')
            time.sleep(0.01)
            if get_fault_flag:
                current_fault_status = self.app.Bus.GetSignal(2, "TCU_Send_Signals_5", "EmgcyCallFalt_B_Dsply").RawValue

                # Verify: if 15s later the status doesn't change, break loop and mark as FAIL.
                if time.time() - prev_time > 25:
                    print("TIMEOUT!!! QUIT!!!!")
                    result_to_gui.put("No DTCs received")
                    loadbox_instance.on_receive_fault_from_can(component, q, cdl, "NOK")
                    print('I am going to go out from fault func, but no fault found')
                    self.can_logs.append("No fault observed")
                    cdl.count_down()
                    break

                if current_fault_status == 1.0:
                    list_decode_75c = []
                    # ********************* SEND readDTC CAPL function************************
                    time.sleep(8)
                    self.execute_capl_function(id1)
                    self.execute_capl_function(id2)
                    time.sleep(2)
                    # *************************************************************

                    # ============ Following msgs represents all 0x75C ===============
                    current_760_status = self.app.Bus.GetSignal(2, "TesterPhysicalResTCU4_Copy_1",
                                                                "TesterPhysicalResTCU_1").RawValue
                    current_761_status = self.app.Bus.GetSignal(2, "TesterPhysicalResTCU4_Copy_2",
                                                                "TesterPhysicalResTCU_2").RawValue
                    current_762_status = self.app.Bus.GetSignal(2, "TesterPhysicalResTCU4_Copy_3",
                                                                "TesterPhysicalResTCU_3").RawValue
                    current_763_status = self.app.Bus.GetSignal(2, "TesterPhysicalResTCU4_Copy_4",
                                                                "TesterPhysicalResTCU_4").RawValue
                    current_764_status = self.app.Bus.GetSignal(2, "TesterPhysicalResTCU4_Copy_5",
                                                                "TesterPhysicalResTCU_5").RawValue
                    # ============ Above msgs represents all 0x75C ===============

                    if current_760_status > 0:
                        print "760:", current_760_status
                        list_75c.append(current_760_status)
                    if current_761_status > 0:
                        print "761:", current_761_status
                        list_75c.append(current_761_status)
                    if current_762_status > 0:
                        print "762:", current_762_status
                        list_75c.append(current_762_status)
                    if current_763_status > 0:
                        print "763:", current_763_status
                        list_75c.append(current_763_status)
                    if current_764_status > 0:
                        print "764:", current_764_status
                        list_75c.append(current_764_status)
                    time.sleep(2)
                    if len(list_75c) != 0:
                        list_decode_75c = help_utils.decode_raw_signal_values(list_75c)

                    fault_result_flag = False
                    # ========== get dtc from 75C =======
                    print list_decode_75c
                    queue_from_gui.put("DTCs: " + str(list_decode_75c))
                    return_dtc_result = help_utils.get_dtc_msg_from_list(list_decode_75c)
                    self.can_logs.append(return_dtc_result)
                    result_to_gui.put(str(return_dtc_result))
                    if should_report_dtc_id in return_dtc_result and return_dtc_result.find("DTCs found") == -1:
                        self.can_logs.append("OK")
                        result_to_gui.put("DTC MATCH")
                        InitiateCanalyzerDiagNoSpk.dtc_result_final = "OK"
                        fault_result_flag = True
                    elif should_report_dtc_id not in return_dtc_result and return_dtc_result.find("DTCs found") == -1:
                        self.can_logs.append("NOT FOUND DTC")
                        result_to_gui.put("DTC NOT FOUND")
                        InitiateCanalyzerDiagNoSpk.dtc_result_final = "DTC NOT FOUND"
                    else:
                        result_to_gui.put("SOMETHING WRONG")
                        self.can_logs.append("SOMETHING WRONG")
                        InitiateCanalyzerDiagNoSpk.dtc_result_final = "SOMETHING WRONG"
                    # ===================================

                    current_time = time.time()
                    delta_time = current_time - prev_time
                    print("GOT FAULT CHANGE! PASS!")
                    print('delta time after receiving fault:{} at {}'.format(delta_time, time.time()))

                    # ======step 7
                    print("\n about to set ign off")
                    time.sleep(3)
                    tdk_instance.set_ign_off()
                    print("\n ign is set to off completed")
                    time.sleep(4)

                    # ======step 8
                    result_to_gui.put("-About to Set Normal-")
                    if fault_result_flag:
                        loadbox_instance.on_receive_fault_from_can(component, q, cdl, "OK")
                        print('I am going to go out from fault func')
                    else:
                        loadbox_instance.on_receive_fault_from_can(component, q, cdl, "NOK")
                    cdl.count_down()
                    break
                else:
                    pass
                    # print('current 0x754 status: ', help_utils.decode_raw_signal_value(current_754_status))
            if self.event.wait(timeout=0.01):
                break


def write_can_to_file(current_can_logs, start_time, count):
    with open('diag_list.txt', 'a+') as f:
        print("write start!")
        f.write("\n" + start_time + ": Log_" + str(count) + "\n ")
        for line in current_can_logs:
            f.write(line)
        # f.write('\n\n')
        print("write finish!")


if __name__ == "__main__":
    event = threading.Event()
    listC = []
    listD = []
    # app = win32com.client.DispatchEx('CANalyzer.Application')
    # app.Measurement.Start()
    startTime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    # marshalled_app = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, app)
    ic = InitiateCanalyzerDiagNoSpk(event, listC)
    id = InitiateCanalyzerDiagNoSpk(event, listD)
    ic.start()

    t2 = threading.Thread(target=ic.get_all_signals, args=(can_signals_enum.EmgcyCallHmi,
                                                           "EmgcyCallHmi_D_Stat",
                                                           "TCU_Send_Signals_5"))
    t = threading.Thread(target=id.get_all_signals, args=(can_signals_enum.EmgcyCallFault,
                                                          "EmgcyCallFalt_B_Dsply",
                                                          "TCU_Send_Signals_5"))
    t.start()
    t2.start()
    time.sleep(10)
    event.set()

    print("next to stop canalyzer: {}".format(time.ctime()))  # 1) 15:31:20
    ic.stop()
    print("stopped canalyzer: {}".format(time.ctime()))  # 2) 15:31:20
    print("before sleep 1s")
    time.sleep(1)  # to make sure ic.can_logs is updated
    print("after sleep 1s")
    print("listC: {}".format(ic.get_can_log()))
    print("listD:{}".format(id.get_can_log()))
    # write_can_to_file(listC, startTime)
    # check(listC)
    print("over: {}".format(time.ctime()))  # 3) 15:31:20
