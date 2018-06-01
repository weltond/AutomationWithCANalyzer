import time
import Tkinter as tk
import tkFileDialog
import ttk
import tkMessageBox as tkMsgBox
from test_canalyzer import *
import threading
import win32com
import pythoncom
import Queue
from test_run_script import *
import win32com.client
from Tkinter import Frame
import serial_port_frame
import tkMessageBox as mbox
from ttk import *
from result_tree import *


class AutomationGUI:
    def __init__(self, master):
        self.master = master
        # master.title("Automation GUI")

        # self.lb_serial_queue = Queue.Queue()
        # self.tdk_serial_queue = Queue.Queue()

        # self.master.pack(fill=BOTH, expand=True)
        self.script_label_frame = tk.LabelFrame()

        self.script_window = WindowView()
        self.log_window = WindowView()
        self.result_window = WindowView()
        self.phone_entry = None
        self.standby_entry = None
        self.vehicle_type_entry = None
        self.propulsion_entry = None
        self.res_tree = ResultTreeList()

        self.result_frame = tk.Frame()

        self.phone_info = "882396202952427"
        self._oecon_user = 'hongyuan'
        self._oecon_pw = 'mengchi'
        self._oecon_list = [self.phone_info, self._oecon_user, self._oecon_pw]

        self.make_widget()

        self.list_of_script_result = []

        self.log_queue = Queue.Queue()
        self.log_res = ""

        self.result_queue = Queue.Queue()
        self.automation_res = ""

        self.msd_queue = Queue.Queue()

        self.pass_count = 0
        self.fail_count = 0
        self.index = 0
        self.end_pos = '1.0'

        # CANalyzer class thread event
        self.event = threading.Event()

    # Serial Port
    LB_SERIAL = None
    TDK_SERIAL = None

    def make_widget(self):
        pw = tk.PanedWindow(self.master, orient=VERTICAL,showhandle=True, handlesize=5)
        pw1 = tk.PanedWindow(pw, orient=HORIZONTAL)
        # pw.paneconfigure(pw1,pady=2)
        pw.add(pw1)
        pw7 = tk.PanedWindow(pw1)
        pw1.add(pw7)
        pw2 = tk.PanedWindow(pw, orient=HORIZONTAL,showhandle=True, handlesize=5)
        pw.add(pw2)
        # pw3 = tk.PanedWindow(pw2,sashwidth=50, sashpad=10,sashrelief=GROOVE,showhandle=True,handlesize=10)
        pw3 = tk.PanedWindow(pw2, orient=VERTICAL, showhandle=True, handlesize=5)
        pw2.add(pw3)
        pw4 = tk.PanedWindow(pw2, orient=VERTICAL,showhandle=True, handlesize=5)
        pw2.add(pw4)
        pw5 = tk.PanedWindow(pw4)
        pw6 = tk.PanedWindow(pw4)
        pw4.add(pw5)
        pw4.add(pw6)
        # ===================== SETTINGS ============================
        setting_frame = tk.LabelFrame(pw7, text="SETTINGS")
        setting_frame.grid(row=0, column=0, columnspan=2, sticky='NW', padx=5, pady=5, ipadx=3,
                                     ipady=1)
        # ===== Serial Port =====
        global LB_SERIAL
        global TDK_SERIAL
        port_frame = tk.LabelFrame(setting_frame, text="Serial")
        port_frame.grid(row=0, column=0, rowspan=2, padx=5)
        loadbox_frame = tk.LabelFrame(port_frame)
        tdk_frame = tk.LabelFrame(port_frame)
        loadbox_frame.grid(row=0, column=0, sticky=W)
        tdk_frame.grid(row=1, column=0, sticky=W)

        # Global lb_serial and tdk_serial, in order to get its instance globally.
        LB_SERIAL = serial_port_frame.PortFrame(loadbox_frame, 'LoadBox:  ')
        TDK_SERIAL = serial_port_frame.PortFrame(tdk_frame, "TDK:         ")

        start_button = tk.Button(port_frame, text='start', width=4, command=self.start_scenario_from_script)
        start_button.grid(row=0, column=1, sticky=W)

        test_button = tk.Button(port_frame, text='test', width=4, anchor=CENTER, command=self.test_serial_port)
        test_button.grid(row=1, column=1, sticky=W)

        # ====== OECON ======
        oecon_frame = tk.LabelFrame(setting_frame, text="OECON ACCOUNT")
        oecon_frame.grid(row=0, column=1, padx=3, sticky=W)
        # 1. Phone Num
        self.phone_entry = make_entry(oecon_frame, width=20, hint=True, text='Enter Phone...')
        self.phone_entry.pack(side='left',fill='x')
        # 2. User Account
        self.oecon_user_entry = make_entry(oecon_frame, width=20, hint=True, text='Enter User Name...')
        self.oecon_user_entry.pack(side='left',fill='x')
        # 3. Password
        self.oecon_pw_entry = make_entry(oecon_frame, width=20, hint=True, text='Enter Password...', hide=True)
        self.oecon_pw_entry.pack(side='left',fill='x')

        save_oecon_button = tk.Button(oecon_frame, text="save", command=self.save_oecon)
        save_oecon_button.pack(side='left',fill='x')
        edit_oecon_button = tk.Button(oecon_frame, text="edit", command=self.edit_oecon)
        edit_oecon_button.pack(side='left',fill='x')
        test_oecon_button = tk.Button(oecon_frame, text="test", command=self.test_oecon)
        test_oecon_button.pack(side='left', fill='x')

        # ====== DID DE06 ======
        did_frame = tk.LabelFrame(setting_frame, text='DID DE06')
        did_frame.grid(row=1, column=1, padx=3, sticky=W, ipadx=2)
        self.standby_entry = make_entry(did_frame, 'Standby', width=9, hint=True, text='60 min', state='readonly')
        self.vehicle_type_entry = make_entry(did_frame, 'Vehicle Type', width=21, hint=True, text='Type 1', state='readonly')
        self.propulsion_entry = make_entry(did_frame, 'Propulsion', width=14, hint=True, text='Petrol', state='readonly')

        pw7.add(setting_frame)

        # Save for future
        pw8 = tk.PanedWindow(pw1)
        pw1.add(pw8)

        # ===================== SCRIPT ============================
        self.script_label_frame = tk.LabelFrame(pw3, text="Script")
        self.script_label_frame.grid(row=1, column=0, rowspan=2, sticky='NW', padx=5, pady=5, ipadx=1,
                             ipady=1)
        script_frame = tk.Frame(self.script_label_frame, borderwidth=2, relief='groove')
        script_frame.pack(fill='both', expand=True)
        self.script_window = WindowView(script_frame, height=19)
        self.script_window.pack(fill='both', expand=True)
        # self.script_window.grid(row=0, column=0, padx=2, pady=2)

        self.result_frame = tk.Frame(self.script_label_frame, borderwidth=2, relief='groove')
        self.result_frame.pack(side='top',fill='x')

        default_script = "AUTO ECALL STANDBY(PERIOD=1,WAIT=TRUE_0,VTYPE=3,PROP=petrol&other&diesel&hydro,TIMES=1)\n" + \
                         "#False: Stop after entering Standby\n" + \
                         "#True_0: Stop after Standby expires and do 3 ign cycles\n" + \
                         "#True_1: Stop after (Standby + 2 hours) expires\n"+ \
                         "#TEST VTYPE(STANDBY=1, PROP=petrol&diesel, WAIT=TRUE_0, RANGE=[2-1])\n" + \
                         "#SET FAULT BUTTON(FAULT=GROUND, TIMES=1)\n" + \
                         "TEST PROP(STANDBY=1, VTYPE=1, WAIT=TRUE_0, PROP=petrol)\n" + \
                         "#SET FAULT IND(FAULT=GROUND, TIMES=1)\n" + \
                         "#SET FAULT MIC(FAULT=GROUND, TIMES=1)\n" + \
                         "#SET FAULT BUTTON(FAULT=VBATT, TIMES=1)\n" + \
                         "#SET FAULT IND(FAULT=VBATT, TIMES=1)\n" + \
                         "#SET FAULT MIC(FAULT=VBATT, TIMES=1)\n" + \
                         "#SET FAULT BUTTON(FAULT=OPEN, TIMES=1)\n" + \
                         "#SET FAULT IND(FAULT=OPEN, TIMES=1)\n" + \
                         "#SET FAULT MIC(FAULT=OPEN, TIMES=1)\n"
        self.script_window.insert_text(default_script)

        pw3.add(self.script_label_frame)

        # ========== TREE =============

        self.res_tree = ResultTreeList(pw3)
        self.res_tree.pack(fill='both', expand=True)
        pw3.add(self.res_tree)

        # ===================== LOG ============================
        log_label_frame = tk.LabelFrame(pw5, text="Log")
        log_label_frame.grid(row=1, column=1, columnspan=10, rowspan=20, sticky='NW', padx=5, pady=5, ipadx=1,
                               ipady=1)
        self.log_window = WindowView(log_label_frame, width=70, height=14)
        self.log_window.pack(fill='both', expand=True)
        #self.log_window.grid(row=0,column=0, padx= 2, pady=2)

        self.log_window.insert_text("Default Phone Num is: 882396202952427, User is: hongyuan\n")

        pw5.add(log_label_frame)
        # ===================== RESULT ============================
        result_label_frame = tk.LabelFrame(pw6, text="Result")
        result_label_frame.grid(row=3, column=1, columnspan=10, rowspan=20, sticky='NW', padx=5, pady=5, ipadx=1,
                             ipady=1)
        self.result_window = WindowView(result_label_frame, width=70, height=14)
        self.result_window.pack(fill='both', expand=True)
        #self.result_window.grid(row=0, column=0, padx=2, pady=2)
        pw6.add(result_label_frame)

        pw.pack(fill='both', expand=True)

    # ======================= SERIAL PORT ==========================
    def tdk_test_thread(self, selected_tdk_port):
        '''
        Test TDK serial. If select the right serial port, send IGN stat back to the GUI.
        :param selected_tdk_port: COM port
        :return:
        '''
        import serial
        try:
            tdk_stat = serial.Serial(selected_tdk_port, 115200, timeout=1)
        except serial.serialutil.SerialException:
            self.log_window.insert_text("TDK SerialPort didn't open, please check Serial or conflict\n")
        else:
            self.log_window.insert_text('Test should receive IGN stat: ')
            tdk_stat.write("ign stat\r")
            lines = tdk_stat.readlines()
            if lines == []:
                self.log_window.insert_text("No output. Wrong TDK Serial Port.\n")
            else:
                for line in lines:
                    if line.find("Ignition_Status:") != -1:
                        if line.find("4") != -1:
                            self.log_window.insert_text(line.split("\n")[0].strip() + " = IGN ON ------ OK\n")
                        elif line.find("1") != -1:
                            self.log_window.insert_text(line.split("\n")[0].strip() + " = IGN OFF ------ OK\n")
                        if line.find("2") != -1:
                            self.log_window.insert_text(line.split("\n")[0].strip() + " = IGN ACC ------ OK\n")

                self.log_window.insert_text("Test finished. TDK is CLOSED\n")
            print "should close"
            tdk_stat.close()

    def get_value_from_combobox(self, serial_combobox):
        selected_port = serial_combobox.box.get()
        if selected_port.find("Arduino") != -1:
            selected_port = selected_port.split("(Arduino")[0].strip()
        elif selected_port.find("USB") != -1:
            selected_port = selected_port.split("(USB")[0].strip()
        self.log_window.insert_text("Select Port: " + str(selected_port) + "\n")
        return selected_port

    def test_serial_port(self):
        selected_tdk_port = self.get_value_from_combobox(TDK_SERIAL)
        threading.Thread(target=self.tdk_test_thread, args=(selected_tdk_port,)).start()
    # ==============================================================

    # =================== Start OECON and GET MSD ==================
    def get_latest_msd(self):
        import Oecon_Access
        threading.Thread(target=Oecon_Access.startOECON, args=(25, self.msd_queue, "882396861537948")).start()
        self.master.after(100, self.listen_for_msd_queue)

    def listen_for_msd_queue(self):
        try:
            logs = self.msd_queue.get(0)
            self.log_window.insert_text(logs)
            self.master.after(100, self.listen_for_msd_queue)
        except Queue.Empty:
            # print "queue empty"
            self.master.after(100, self.listen_for_msd_queue)

    def edit_oecon(self):
        self.phone_entry.config(state='normal')
        self.oecon_user_entry.config(state='normal')
        self.oecon_pw_entry.config(state='normal')

    def test_oecon(self):
        import Oecon_Access as oe
        threading.Thread(target=oe.test_oecon_thread, args=(self,)).start()

    def save_oecon(self):
        self.phone_info = self.phone_entry.get()
        self._oecon_user = self.oecon_user_entry.get()
        self._oecon_pw = self.oecon_pw_entry.get()

        if self.phone_info != "Enter Phone..." and \
                self._oecon_user != "Enter User Name..." and \
                self._oecon_pw != "Enter Password...":
            self._oecon_list = [self.phone_info, self._oecon_user, self._oecon_pw]
        print self._oecon_list
        if not self.phone_info.isdigit():
            mbox.showwarning(
                "WRONG",
                "Phone num should be DIGIT only!"
            )
        else:
            self.log_window.insert_text("Phone Number is: " + self.phone_info + '\n')
            self.phone_entry.config(state='readonly')
            self.oecon_pw_entry.config(state='readonly')
            self.oecon_user_entry.config(state='readonly')
    # =============================================================

    def get_script(self):
        """
        verify how many new lines are created. Then create corresponding numbers of Listbox.
        :return:
        """
        text = self.script_window.get_text()
        num = len(text.split("\n")) - 1  # has a null value at the end

        for row_num in range(num):
            self.list_of_script_result.append(OneListResult(self.result_frame, row_num))
        return num
        # self.list_of_script_result[0].insert_result("4/"+str(num))
        # self.list_of_script_result[1].insert_result("1/"+str(num))
        # self.list_of_script_result[2].insert_result("0/"+str(num))

    def script_thread(self):
        '''
        Start scripting thread!
        :return:
        '''
        selected_tdk_port = self.get_value_from_combobox(TDK_SERIAL)
        selected_lb_port = self.get_value_from_combobox(LB_SERIAL)
        text = self.script_window.get_text()
        if text.strip() == "":
            self.result_queue.put("Nothing...")
            self.log_queue.put("Nothing...")
        # scenario_num = len(text.split("\n")) - 1  # has a null value at the end
        # for row_num in range(scenario_num):
        #    self.list_of_script_result.append(OneListResult(self.result_frame, row_num))
        else:
            script_list = text.strip().split("\n")
            import help_utils
            help_utils.set_tree_view(script_list, self.res_tree)
            import script_bootup_from_gui
            #script_bootup_from_gui.run_script(selected_tdk_port, selected_lb_port, script_list,
            #                                  self.log_queue, self.result_queue, self._oecon_list)

    def start_scenario_from_script(self):
        self.log_window.insert_text("\nStart...\n")
        self.result_window.insert_text("Start...\n")
        # self.log_window.set_tag("Start...", tag="START", color='BLACK', justify=tk.CENTER)
        threading.Thread(target=self.script_thread).start()
        self.master.after(100, self.listen_for_log_result)
        self.master.after(100, self.listen_for_res_result)

    def stop_can(self, app):
        self.event.set()
        # listC = ic.get_log()
        # print("next to stop canalyzer: {}".format(time.ctime()))  # 1) 15:31:20
        app.Measurement.Stop()

    def listen_for_log_result(self):
        try:
            self.log_res = self.log_queue.get(0)
            self.log_window.insert_text(self.log_res + '\n')
            # ======= Update DE06 values in DE06 settings ==========
            if self.log_res.find("DE06:") != -1:
                for info in self.log_res.split("\n"):
                    if info.startswith("Propulsion"):
                        prop = info.split(":")[1].strip()
                        update_entry_text_when_readonly(self.propulsion_entry, prop)
                    elif info.startswith("Vehicle Type"):
                        v_type = info.split(":")[1].strip()
                        update_entry_text_when_readonly(self.vehicle_type_entry, v_type)
                    elif info.startswith("Standby"):
                        standby = info.split(":")[1].strip()
                        update_entry_text_when_readonly(self.standby_entry, standby)
            # ======================================================
            set_color(self.log_res, self.log_window)
            self.master.after(100, self.listen_for_log_result)
        except Queue.Empty:
            # print "queue empty"
            self.master.after(100, self.listen_for_log_result)

    def listen_for_res_result(self):
        try:
            self.automation_res = self.result_queue.get(0)
            self.result_window.insert_text(self.automation_res + '\n')
            if self.automation_res.find("RESULT") != -1:
                self.total_loops = self.automation_res.strip().split("(")[1].split(" ")[0]
                print self.total_loops
            # ============= count results=============
            set_color(self.automation_res, self.result_window)

            self.master.after(100, self.listen_for_res_result)
        except Queue.Empty:
            self.master.after(100, self.listen_for_res_result)

    # ************ TEST ONLY START**************
    def test_thread(self):
        listC = []
        app = win32com.client.DispatchEx('CANalyzer.Application')
        app.Measurement.Start()
        startTime = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        marshalled_app = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, app)
        ic = InitiateCanalyzer(marshalled_app, self.event, listC)
        threading.Thread(target=ic.get_all_signals, args=(self.log_queue, can_signals_enum.EmgcyCallFault, "EmgcyCallFalt_B_Dsply",
                                                          "TCU_Send_Signals_5")).start()

        self.master.after(100, self.listen_for_result)
        print "after master"
        # use this frame.after() to stop CANalyzer.
        # It's a replacement of time.sleep
        self.master.after(9000, self.stop_can, app)

    # WORKS!!!
    def test_can_thread(self, id):
        pythoncom.CoInitialize()
        self.app = win32com.client.Dispatch(
            pythoncom.CoGetInterfaceAndReleaseStream(
                id,
                pythoncom.IID_IDispatch
            )
        )
        print 'nothing happend'
        self.app.Measurement.Start()
    # ************ TEST ONLY END**************


# ============= SET COLOR===============
def set_color(queue_res, window):
    if queue_res.find(" PASS") != -1:
        target = " PASS"
        window.set_tag(target, tag="pass", color="lime green", length=5)
    if queue_res.find(" FAIL") != -1:
        target = " FAIL"
        window.set_tag(target, tag="fail", color="IndianRed1", length=5)
    if queue_res.find("======PASS") != -1:
        target = '======PASS'
        window.set_tag(target, tag="PASS", color='GREEN')
        # self.pass_count += 1
    if queue_res.find("======FAIL") != -1:
        target = '======FAIL'
        window.set_tag(target, tag="FAIL", color='RED')
        # self.fail_count += 1
    if queue_res.find("----TC") != -1:
        target = '----TC'
        window.set_tag(target, tag="TC", color='violet', length=11)
    if queue_res.find("======PARTIAL") != -1:
        target = '======PARTIAL'
        window.set_tag(target, tag="PARTIAL", color='ORANGE', length=19)
    if queue_res.find("AUTO ECALL: (") != -1:
        target = 'AUTO ECALL'
        window.set_tag(target, tag='AUTO ECALL', length=10, underline=1, font='Helvetica', color='goldenrod1')
    if queue_res.find("Vehicle Type Test (") != -1:
        target = 'Vehicle Type Test'
        window.set_tag(target, tag='Vehicle Type', length=17, underline=1, font='Helvetica', color='goldenrod1')
    # Propulsion Type Test
    if queue_res.find("Propulsion Type Test (") != -1:
        target = 'Propulsion Type Test'
        window.set_tag(target, tag='Prop Type', length=20, underline=1, font='Helvetica', color='goldenrod1')
    if queue_res.find("BUTTON DIAG RESULT (") != -1:
        target = 'BUTTON DIAG RESULT'
        window.set_tag(target, tag='Button Diag', length=18, underline=1, font='Helvetica', color='goldenrod1')
    if queue_res.find("IND DIAG RESULT (") != -1:
        target = 'IND DIAG RESULT'
        window.set_tag(target, tag='IND Diag', length=15, underline=1, font='Helvetica', color='goldenrod1')
    if queue_res.find("MIC DIAG RESULT (") != -1:
        target = 'MIC DIAG RESULT'
        window.set_tag(target, tag='IND Diag', length=15, underline=1, font='Helvetica', color='goldenrod1')
    if queue_res.find("Raw MSD:") != -1:
        target = "Raw MSD:"
        if queue_res.find("No MSD") != -1:
            window.set_tag(target, tag="Raw MSD", length=7, background='dark orange')
        elif queue_res.find("WRONG") != -1:
            window.set_tag(target, tag="Raw MSD", length=7, background='firebrick1')
        else:
            window.set_tag(target, tag="Raw MSD", length=7, background='SpringGreen2')
    if queue_res.find("About to open OECON!") != -1:
        print "find about to open OECON"
        target = "   About to open OECON!"
        window.set_tag(target, tag="OECON", length=3, fgstipple='warning')
    if queue_res.find("POSITIVE RESPONSE!") != -1:
        target = "POSITIVE RESPONSE!"
        window.set_tag(target, tag="positive", length=18, color='lime green')
    if queue_res.find("NEGATIVE RESPONSE!") != -1:
        target = "NEGATIVE RESPONSE!"
        window.set_tag(target, tag="negative", length=18, color='firebrick1')
    if queue_res.find("------NOK") != -1:
        target = "------NOK"
        window.set_tag(target, tag='nok', length=9, color='firebrick1')
    if queue_res.find("------OK") != -1:
        target = "------OK"
        window.set_tag(target, tag='ok', length=9, color='lime green')
    if queue_res.find("------PARTIAL") != -1:
        target = "------PARTIAL"
        window.set_tag(target, tag='partial', length=13, color='dark orange')
    if queue_res.find("Batch Result:") != -1:
        target = "Batch Result"
        window.set_tag(target, tag='batch result', length=12, underline=1)
        if queue_res.find("Successfully got hotkey") != -1:
            target = "Successfully got hotkey"
            window.set_tag(target, tag='batch success', length=23, color='lime green')
    if queue_res.find("Batch Error:") != -1:
        target = "Batch Error"
        window.set_tag(target, tag='batch error', length=12, underline=1)
        if queue_res.find("None") != -1:
            target = "None"
            window.set_tag(target, tag='none', length=4, color='lime green')
    if queue_res.find("Congratulation!") != -1:
        target = "Congratulation!"
        window.set_tag(target, tag='congrats', length=48, font='Times 11 bold')


def make_entry(parent, caption=None, width=None, hint=False, text='', hide=False, **options):
    if caption:
        tk.Label(parent, text=caption).pack(side=LEFT)

    # entry = art.AutoResizedText(parent, width=width, height=25, size=5)
    entry = tk.Entry(parent, **options)
    if width:
        entry.config(width=width)
    if hint:
        # ### Set entry hint ###
        entry.insert(0, text)
        # entry.insert('1.0', text)

        # === Make Entry widget detect mouse action ======
        entry.bind('<FocusIn>', lambda event, entry=entry, text=text,
                                                  hide=hide: on_entry_click(event, entry, text, hide))
        entry.bind('<FocusOut>', lambda event, entry=entry, text=text,
                                                  : on_focusout(event, entry, text))
        entry.config(fg='grey')
        # #######################
    entry.pack(side=LEFT)
    return entry

def update_entry_text_when_readonly(entry, str_value, color='RoyalBlue1'):
    s = StringVar()
    s.set(str_value)
    entry.config(textvariable=s, fg=color)

def on_entry_click(event, entry, text, hide=False):
    """function that gets called whenever entry is clicked"""
    if entry.get() == text:
        if hide:
            entry.config(show='*')
        entry.delete(0, "end") # delete all the text in the entry
        entry.insert(0, '') #Insert blank for user input
        entry.config(fg='black')

def on_focusout(event, entry, text):
    if entry.get() == '':
        entry.insert(0, text)
        entry.config(fg='grey')
        entry.config(show='')

class OneListResult(tk.Frame):

    def __init__(self, parent, row_num, height=1):
        tk.Frame.__init__(self, parent)
        self.result_list = tk.StringVar()
        self.listbox = tk.Listbox()
        self.result = ""
        self.create_ui(height)
        self.grid(row=row_num, column=0, padx=2, pady=1, sticky='n')
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

    def create_ui(self, height):
        self.listbox = tk.Listbox(self, height=height, width=25, listvariable=self.result_list)
        self.listbox.pack(side=tk.LEFT)

    def insert_result(self, result):
        self.listbox.insert(tk.END, result)
        pass_result, total_result = result.split("/")
        if pass_result == total_result:
            self.listbox.itemconfig(0, bg='green')
        elif pass_result == '0':
            self.listbox.itemconfig(0, bg='red')
        else:
            self.listbox.itemconfig(0, bg='yellow')


class WindowView(tk.Frame):
    def __init__(self, parent=None, width=40, height=30, wrap=tk.NONE, is_bar=True, **kw):
        tk.Frame.__init__(self, parent, kw)
        self.text_window = tk.Text(self, width=width, height=height, spacing1=3, wrap=wrap)
        self.is_bar = is_bar
        self.end_pos = '1.0'
        self.make_window()

    def make_window(self):
        self.xbar = tk.Scrollbar(self, orient='horizontal')
        self.text_window.grid(row=0,column=0,rowspan=2, sticky='nwse')
        self.text_window.config(xscrollcommand=self.xbar.set)
        self.xbar.grid(row=2, column=0, columnspan=2, sticky='WE')
        self.xbar.config(command=self.text_window.xview)
        self.grid_rowconfigure(0, weight=4)
        # self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        if self.is_bar:
            self.sbar = tk.Scrollbar(self)
            self.text_window.config(yscrollcommand=self.sbar.set)
            self.sbar.grid(row=0,column=2,rowspan=2,sticky='NS')
            self.sbar.config(command=self.text_window.yview)

    def insert_text(self, text):
        self.text_window.insert(tk.END, text)
        self.text_window.see('end')

    def get_text(self):
        return self.text_window.get(1.0, tk.END)

    def set_tag(self, target, tag, color='black', length=16, **kwargs):
        # target = '======PASS'
        start_pos = self.text_window.search(target, self.end_pos, stopindex=tk.END)
        self.end_pos = '{}+{}c'.format(start_pos, length)
        # self.text_window.tag_add("PASS", start_pos, end_pos)
        # self.text_window.tag_config("PASS", foreground='GREEN')
        self.text_window.tag_add(tag, start_pos, self.end_pos)
        self.text_window.tag_config(tag, foreground=color, **kwargs)


def main():
    root = tk.Tk()
    root.title("Automation GUI")
    #pw = PanedWindow(root, orient='vertical')
    #ag = AutomationGUI(pw)
    #pw.pack(fill='both', expand=True)
    AutomationGUI(root)

    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=0)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)

    root.mainloop()

from Tkinter import *
def example():
    window = Tk()

    ia_answers = "test\n"
    input_frame = LabelFrame(window, text="User :", borderwidth=4)
    input_frame.pack(fill=BOTH, side=BOTTOM)
    input_user = StringVar()
    input_field = Entry(input_frame, text=input_user)
    input_field.pack(fill=BOTH, side=BOTTOM)

    ia_frame = LabelFrame(window, text="Discussion", borderwidth=15, height=100, width=100)
    ia_frame.pack(fill=BOTH, side=TOP)

    text = Text(ia_frame, state='disabled')
    text.pack()
    text.tag_configure("right", justify='right')
    text.tag_add("right", 1.0, "end")

    # text.tag_configure("right", justify="right")
    text.tag_configure("left", justify="left")

    def Enter_pressed(event):
        """Took the current string in the Entry field."""
        input_get = input_field.get()
        input_user.set("")
        text.configure(state='normal')
        # text.insert("end", "this is right-justified\n", "right")
        # text.insert("end", "this is left-justified\n", "left")
        text.insert('end', input_get + '\n', 'right')
        text.insert('end', ia_answers + '\n', 'left')
        text.configure(state='disabled')

    input_field.bind("<Return>", Enter_pressed)
    window.mainloop()


if __name__ == '__main__':
    main()
    #end_pos = '{}+{}c'.format('1.6', 5)
    #print end_pos

    # txt = "BUTTON DIAG RESULT (" + str(5) + " TCs):"
    # print txt.strip().split("(")[1].split(" ")[0]



