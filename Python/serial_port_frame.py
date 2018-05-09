import serial, serial.tools, serial.tools.list_ports
from Tkinter import *
import ttk


class PortFrame:
    def __init__(self, parent, label_str):
        self.parent = parent
        self.box_value = StringVar()
        self.label_value = StringVar()
        self.box = ttk.Combobox(self.parent, textvariable=self.box_value, stat='readonly')
        self.label = ttk.Label(self.parent, textvariable=self.label_value)
        self.make_combo(label_str)
        self.value_of_combo = ""

    def port_selection(self, event):
        self.value_of_combo = self.box.get()
        if self.value_of_combo.find("Arduino") != -1:
            self.value_of_combo = self.value_of_combo.split("(Arduino")[0].strip()
        if self.value_of_combo.find("USB") != -1:
            self.value_of_combo = self.value_of_combo.split("(USB")[0].strip()
        print(self.value_of_combo)


    def make_combo(self, label_str):
        self.label_value.set(label_str)
        self.box.pack(side=RIGHT)
        self.label.pack(side=LEFT)
        port_tuple = ()
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            port_str = port[0]
            if port[1].find("Arduino") != -1:
                port_str = port[0] + " (Arduino)"
            elif port[1].find("USB Serial Port") != -1:
                port_str = port[0] + " (USB)"
            port_tuple += (port_str,)
        self.box['values'] = port_tuple

        self.box.bind("<<ComboboxSelected>>", self.port_selection)
        # self.parent.after(1000, self.combo)  # can be updated but CANNOT bind event to ComboSelected


if __name__ == '__main__':
    ports = list(serial.tools.list_ports.comports())

    print ports
    root = Tk()
    l = LabelFrame(root)
    l1 = LabelFrame(root)
    l.pack(side=LEFT)
    l1.pack(side=LEFT)
    #app = PortFrame(l, 'Loadbox')
    #app1 = PortFrame(l1, 'TDK')
    root.mainloop()