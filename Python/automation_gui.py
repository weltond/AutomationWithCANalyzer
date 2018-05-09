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


class AutomationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Automation GUI")

        # self.lb_serial_queue = Queue.Queue()
        # self.tdk_serial_queue = Queue.Queue()

        # self.master.pack(fill=BOTH, expand=True)
        self.script_label_frame = tk.LabelFrame()

        self.script_window = WindowView()
        self.log_window = WindowView()
        self.result_window = WindowView()

        self.result_frame = tk.Frame()

        self.make_widget()

        self.list_of_script_result = []

        self.log_queue = Queue.Queue()
        self.log_res = ""

        self.result_queue = Queue.Queue()
        self.automation_res = ""

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
        # ===================== Serial Port ============================
        global LB_SERIAL
        global TDK_SERIAL
        port_frame = tk.LabelFrame(self.master, text="Serial")
        port_frame.grid(row=0, column=0, columnspan=2, sticky='NW', padx=5, pady=5, ipadx=1,
                                     ipady=1)
        loadbox_frame = tk.LabelFrame(port_frame)
        tdk_frame = tk.LabelFrame(port_frame)
        loadbox_frame.pack(side=LEFT)
        tdk_frame.pack(side=LEFT)

        # Global lb_serial and tdk_serial, in order to get its instance globally.
        LB_SERIAL = serial_port_frame.PortFrame(loadbox_frame, 'LoadBox:  ')
        TDK_SERIAL = serial_port_frame.PortFrame(tdk_frame, "TDK:  ")

        start_button = tk.Button(port_frame, text='start', command=self.start_scenario_from_script)
        start_button.pack(side='left', fill='x')

        test_button = tk.Button(port_frame, text='test', command=self.test_serial_port)
        test_button.pack(side='right', fill='x')

        # ===================== SCRIPT ============================
        self.script_label_frame = tk.LabelFrame(self.master, text="Script")
        self.script_label_frame.grid(row=1, column=0, rowspan=2, sticky='NW', padx=5, pady=5, ipadx=1,
                             ipady=1)
        script_frame = tk.Frame(self.script_label_frame, borderwidth=2, relief='groove')
        script_frame.pack(side='left')
        self.script_window = WindowView(script_frame)
        self.script_window.grid(row=0, column=0, padx=2, pady=2)

        self.result_frame = tk.Frame(self.script_label_frame, borderwidth=2, relief='groove')
        self.result_frame.pack(side='top',fill='x')

        # ===================== LOG ============================
        log_label_frame = tk.LabelFrame(self.master, text="Log")
        log_label_frame.grid(row=1, column=1, columnspan=10, rowspan=20, sticky='NW', padx=5, pady=5, ipadx=1,
                               ipady=1)
        self.log_window = WindowView(log_label_frame, width=70, height=14)
        self.log_window.grid(row=0,column=0, padx= 2, pady=2)

        # ===================== RESULT ============================
        result_label_frame = tk.LabelFrame(self.master, text="Result")
        result_label_frame.grid(row=2, column=1, columnspan=10, rowspan=20, sticky='NW', padx=5, pady=5, ipadx=1,
                             ipady=1)
        self.result_window = WindowView(result_label_frame, width=70, height=14)
        self.result_window.grid(row=0, column=0, padx=2, pady=2)

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
        self.log_window.insert_text("Select Port: " + selected_port + "\n")
        return selected_port

    def test_serial_port(self):
        selected_tdk_port = self.get_value_from_combobox(TDK_SERIAL)
        threading.Thread(target=self.tdk_test_thread, args=(selected_tdk_port,)).start()
    # ==============================================================

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
            import script_bootup_from_gui
            script_bootup_from_gui.run_script(selected_tdk_port, selected_lb_port, script_list,
                                              self.log_queue, self.result_queue)

    def start_scenario_from_script(self):
        self.log_window.insert_text("Start...\n")
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
            self.master.after(100, self.listen_for_log_result)
        except Queue.Empty:
            # print "queue empty"
            self.master.after(100, self.listen_for_log_result)

    def listen_for_res_result(self):
        try:
            self.automation_res = self.result_queue.get(0)
            self.result_window.insert_text(self.automation_res + '\n')
            # ============= count results=============
            if self.automation_res.find("RESULT") != -1:
                self.total_loops = self.automation_res.strip().split("(")[1].split(" ")[0]
                print self.total_loops
            # ============= SET COLOR===============
            if self.automation_res.find("PASS") != -1:
                target = '======PASS'
                self.result_window.set_tag(target, tag="PASS", color='GREEN')
                self.pass_count += 1
            if self.automation_res.find("FAIL") != -1:
                target = '======FAIL'
                self.result_window.set_tag(target, tag="FAIL", color='RED')
                self.fail_count += 1
            if self.automation_res.find("----TC") != -1:
                target = '----TC'
                self.result_window.set_tag(target, tag="TC", color='BLUE',length=10)

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
        self.text_window.grid(row=0,column=0,rowspan=2)
        self.text_window.config(xscrollcommand=self.xbar.set)
        self.xbar.grid(row=2, column=0, columnspan=2, sticky='WE')
        self.xbar.config(command=self.text_window.xview)
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

    def set_tag(self, target, tag, color, length=16, **kwargs):
        # target = '======PASS'
        start_pos = self.text_window.search(target, self.end_pos, stopindex=tk.END)
        self.end_pos = '{}+{}c'.format(start_pos, length)
        # self.text_window.tag_add("PASS", start_pos, end_pos)
        # self.text_window.tag_config("PASS", foreground='GREEN')
        self.text_window.tag_add(tag, start_pos, self.end_pos)
        self.text_window.tag_config(tag, foreground=color, **kwargs)


def main():
    root = tk.Tk()
    ag = AutomationGUI(root)
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



