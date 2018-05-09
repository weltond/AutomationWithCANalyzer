# WORKING!!!!!!
import sys
import win32com.client
import time
import threading
import pythoncom
import can_signals_enum
from win32gui import MessageBox as msgbox
from win32api import Sleep as wait


sys.coinit_flags = 0
# CANalyzer Event Class **************
class MeasEvents:

    def __init__(self):

        self.CAPL1 = None
        self.CAPL2 = None
        self.Appl = None
        self.CaplFunction1 = None
        self.CaplFunction2 = None
        self.init_flag = False


    def OnInit(self):
        print "parent MeasEvents:OnInit now called"
        print self.CAPL2, self.CAPL1
        if self.CAPL1 is not None and self.CAPL2 is not None:
            self.CaplFunction1 = self.Appl.CAPL.GetFunction(self.CAPL1)
            self.CaplFunction2 = self.Appl.CAPL.GetFunction(self.CAPL2)
            self.CaplFunction1 = win32com.client.Dispatch(self.CaplFunction1)
            self.CaplFunction2 = win32com.client.Dispatch(self.CaplFunction2)
            #self.CaplFunction1 = self.Appl.CAPL.GetFunction("testDiag")
            #self.CaplFunction2 = self.Appl.CAPL.GetFunction("t2")
            print "OnInit:Load CAPL Script = " + self.CAPL1 + self.CAPL2
            self.init_flag = True


# User Class **************
class InitiateCanalyzer:
    def __init__(self, event_thread, can_logs, delta_flag=False, app_id=None):
        # app = win32com.client.DispatchEx('CANalyzer.Application')
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
        self.delta_flag = delta_flag
        self.marshalled_app_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, self.app)
        # Used to call MeasEvent to call CAPL function, but time.sleep() will cause CANalyzer stuck
        # Besides, it has to be called before CANalyzer start?

        self.__MeasurementEvents = win32com.client.DispatchWithEvents(self.Measurement, MeasEvents)
        print self.__MeasurementEvents

        # transfer the application object to Event class for CAPL handling
        print 'which is first'
        self.__MeasurementEvents.Appl = self.app

    def start(self):
        if not self.Running():
            self.Measurement.Start() # when CANalyzer is down and has error, it will throw
            # com_error: (-2147352567, 'Exception occurred.', (0, u'Measurement::Start', u'User interface is busy',
            # u'C:\\Program Files\\Vector CANalyzer 10.0\\Help01\\CANoeCANalyzer.chm', 4270, -2147418113), None)

    def stop(self):
        if self.Running():
            self.Measurement.Stop()

    def get_can_log(self):
        return self.can_logs
	
    def get_a_signal(self):
        pythoncom.CoInitialize()
        self.app = win32com.client.Dispatch(
            pythoncom.CoGetInterfaceAndReleaseStream(
                self.marshalled_app_id,
                pythoncom.IID_IDispatch
            )
        )

        temp_status = -10.0

        prev_time = time.time()

        count_1 = 0
        while True:
            time.sleep(1)
            current_status = self.app.Bus.GetSignal(2, "Signal","Botschaft").RawValue

            if current_status >0:
                print current_status
		pythoncom.CoUnInitialize()
                break

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


def write_can_to_file(current_can_logs, start_time):
    with open('can_status_list.txt', 'a+') as f:
        print("write start!")
        f.write("\n" + start_time + ":\n ")
        for line in current_can_logs:
            f.write(line)
        # f.write('\n\n')
        print("write finish!")

	
def main(id1, id2):
    event = threading.Event()
    listC = []
    listD = []
    import Queue
    q = Queue.Queue()
    ic = InitiateCanalyzer(event, listC, app_id=id1)
    # id = InitiateCanalyzer(event, listD, app_id=id2)
    ic.start()
    t3 = threading.Thread(target=ic.select_capl_function, name="Select-Thread",args=("testDiag", 't2'))
    t3.start()
    # ic.select_capl_function("testDiag", 't2')
    print "selected"
    #t3.join()

    ############### USE MsgWaitForMultipleObject to pump message ################
    '''
    # !!!!!!!!!!!!!! IMPORTANT to make CANalyzer not FREEZE!!!!!
    # pythoncom.PumpWaitingMessages()
    
    from win32process import beginthreadex
    from win32event import MsgWaitForMultipleObjects, QS_ALLINPUT, WAIT_OBJECT_0,CreateEvent
    # handle, ids = beginthreadex(None, 0, sleep_thread, (), 0)
    # handles = list()
    # handles.append(handle)
    ic_event_handle = CreateEvent(None,0,0,None)
    rc = MsgWaitForMultipleObjects((ic_event_handle,), 0, 5000, QS_ALLINPUT)
    start_time = time.time()
    while True:
        if rc == WAIT_OBJECT_0 + 1:
            pythoncom.PumpWaitingMessages()
            # print 'pumping'
        else:
            break
        if ic.Running():
            if time.time() - start_time > 5:
                print ic.Running()
                break
    # msgbox(0, "Measurement Started" + chr(13) + "Now CAPL is called", "Info", 16) # Another not elegant way
    '''
    import help_utils
    help_utils.wait_and_pump_msg()
    ############### END ################

    capl_func_handler_id_1 = ic.marshal_handler_1()
    capl_func_handler_id_2 = ic.marshal_handler_2()

    threading.Thread(target=ic.execute_capl_function2, name="Execute-Thread1",
                     args=(capl_func_handler_id_1,)).start()

    # id.execute_capl_function()  # IT WORKS
    time.sleep(4)
    # cause com_error: 'The application called an interface that was marshalled for a different thread.'
    threading.Thread(target=ic.execute_capl_function2, name="Execute-Thread2", args=(capl_func_handler_id_2,)).start()
    print "before sleep", time.time()

    #id.execute_capl_function2()
    # wait(10000)
    print "after sleep", time.time()
    time.sleep(5)
    print("next to stop canalyzer: {}".format(time.ctime()))  # 1) 15:31:20
    ic.stop()


if __name__ == "__main__":

    import help_utils
    id1 = help_utils.generate_app_marshal()
    id2 = help_utils.generate_app_marshal()
    ''' # Test 1 for calling CAPL function.
    threading.Thread(target=main, args=(id1, id2)).start()
    l = [ '213']
    r = help_utils.get_dtc_msg_from_list(l)

    print r
    '''
	
    '''	# Test 2 for getting signal values from CANalyzer
    event = threading.Event()
    listC = []
    listD = []
    # app = win32com.client.DispatchEx('CANalyzer.Application')
    # app.Measurement.Start()
    startTime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    # marshalled_app = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, app)
    ic = InitiateCanalyzer(event, listC, app_id=id1)
    ic.start()
    threading.Thread(target=ic.get_a_signal).start()
    help_utils.wait_and_pump_msg()
    '''

