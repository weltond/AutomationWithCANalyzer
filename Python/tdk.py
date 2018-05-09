import serial
import threading
import time
import help_utils


class TDK:
    def __init__(self, com_port):
        try:
            serial_load_box = serial.Serial(com_port, 115200, timeout=1)
            self.ser = serial_load_box
            print('start at: {}'.format(time.ctime()))
        except serial.serialutil.SerialException:
            print("TDK SerialPort didn't open, please check Serial or conflict")
            # exit(0)

    def open_serial(self, com_port):
        self.ser = serial.Serial(com_port, 115200, timeout=1)

    def set_ign_on(self):
        ign_stat_command = "ign stat" + "\r"
        ign_on = "ign on" + "\r"
        ign_off = "ign off" + "\r"
        global ign_status_flag
        self.ser.write(ign_stat_command)
        time.sleep(1)
        lines = self.ser.readlines()
        for line in lines:
            if line.find("Ignition_Status: 4") != -1:
                ign_status_flag = True
        if ign_status_flag:
            pass
        else:
            print('IGN IS ON in TDK')
            self.ser.write(ign_on)
            ign_status_flag = True
            print('DONE: IGN IS ON in TDK')

    def set_ign_off(self):
        ign_stat_command = "ign stat" + "\r"
        ign_on = "ign on" + "\r"
        ign_off = "ign off" + "\r"
        global ign_status_flag
        self.ser.write(ign_stat_command)
        time.sleep(3)
        self.ser.write("doo ope 0" + "\r")  # open driver door
        time.sleep(1)
        lines = self.ser.readlines()
        for line in lines:
            if line.find("Ignition_Status: 4") != -1:
                ign_status_flag = True
        if ign_status_flag:
            print("About to set IGN OFF")
            self.ser.write(ign_off)
            ign_status_flag = False
        else:
            pass

    def close_serial(self):
        print("TDK serial is closed")
        self.ser.close()

def start_tdk():
    try:
        global ser
        ser = serial.Serial('COM30', 115200, timeout=0)
        turn_unsub = "tur unsub" + "\r"
        ser.write(turn_unsub)
        print("time before turn unsub: {}".format(time.ctime()))
        time.sleep(1)
        print("time after turn unsub and start ign cycle: {}".format(time.ctime()))
        # ign_cycle(ser, 3)
        auto_ecall(ser)
        print("time after 3 ign cycle: {}".format(time.ctime()))
    except serial.serialutil.SerialException:
        print("oops, wrong COM port")
    finally:
        ser.close()


def ign_cycle():
    try:
        global ser
        ser = serial.Serial('COM30', 115200, timeout=0)
        turn_unsub = "tur unsub" + "\r"
        ser.write(turn_unsub)
        print("time before turn unsub: {}".format(time.ctime()))
        time.sleep(1)
        print("time after turn unsub and start ign cycle: {}".format(time.ctime()))
        ign_on = "ign on" + "\r"
        ign_off = "ign off" + "\r"
        print("time after 3 ign cycle: {}".format(time.ctime()))
    except serial.serialutil.SerialException:
        print("oops, wrong COM port")
    finally:
        ser.close()


ign_status_flag = False


def ign_cycles(loops):
    try:
        print("start ign cycles")
        global ser
        ser = serial.Serial('COM30', 115200, timeout=0)
        turn_unsub = "tur unsub" + "\r"
        ser.write(turn_unsub)
        print("time before turn unsub: {}".format(time.ctime()))
        time.sleep(1)
        print("time after turn unsub and start ign cycle: {}".format(time.ctime()))
        time.sleep(3)
        # ign stat 1 = ign off
        # ign stat 4 = ign on
        ign_stat_command = "ign stat" + "\r"
        ign_on = "ign on" + "\r"
        ign_off = "ign off" + "\r"
        global ign_status_flag
        # print("time before read ign stat: {}".format(time.ctime()))
        ser.write(ign_stat_command)
        time.sleep(1)
        # print("time after read ign stat: {}".format(time.ctime()))
        lines = ser.readlines()
        for line in lines:
            if line.find("Ignition_Status: 4") != -1:
                ign_status_flag = True
        # print("time after getting flag: {}".format(time.ctime()))
        if ign_status_flag:
            for i in range(loops):
                ser.write(ign_off)
                # print("time after ign off: {}".format(time.ctime()))
                time.sleep(6)
                ser.write(ign_on)
                time.sleep(15)
        else:
            for i in range(loops):
                ser.write(ign_on)
                time.sleep(15)
                ser.write(ign_off)
                time.sleep(6)
            ser.write(ign_on)
            time.sleep(1)
    except serial.serialutil.SerialException:
        print("oops, wrong COM port")
    finally:
        print("serial is CLOSED after ign cycles")
        ser.close()


def auto_ecall():
    try:
        print("start auto ecall")
        global ser
        ser = serial.Serial('COM30', 115200, timeout=0)
        turn_unsub = "tur unsub" + "\r"
        ser.write(turn_unsub)
        print("time before turn unsub: {}".format(time.ctime()))
        time.sleep(1)
        print("time after turn unsub and start ign cycle: {}".format(time.ctime()))
        time.sleep(3)
        rcm_threashold_2 = "ies 5" + "\r"
        rcm_normal = "ies 0" + "\r"
        rcm_enable = "ecu rcm en" + "\r"
        ser.write("ign on" + "\r")
        time.sleep(1)
        ser.write(rcm_enable)
        time.sleep(1)
        ser.write(rcm_normal)
        time.sleep(2)
        ser.write(rcm_threashold_2)
        time.sleep(4)
        ser.write(rcm_normal)
    except serial.serialutil.SerialException:
        print("oops, wrong COM port")
    finally:
        print("serial is CLOSED!!!!!")
        ser.close()


# not used
component_list = ['Switch', 'StatusIndc', 'Mic', 'LSpeaker', 'RSpeaker', 'ENS', 'Power']
fault_list = ['Normal', 'Ground', 'VBATT', 'Open', 'LeadToLead']
from collections import namedtuple
import load_box
Switch = namedtuple('Switch', ['Normal', 'Open', 'VBATT', 'Ground'])
switch = Switch(load_box.switch['normal'], load_box.switch['open'],
                load_box.switch['vbatt'], load_box.switch['ground'])
Mic = namedtuple('Mic', ['Normal', 'Open', 'VBATT', 'Ground'])
mic = Mic(load_box.mic['normal'], load_box.mic['open'],
          load_box.mic['vbatt'], load_box.mic['ground'])
Indicator = namedtuple('Indicator', ['Normal', 'Open', 'VBATT', 'Ground'])
ind = Indicator(load_box.indicator['normal'], load_box.indicator['open'],
                load_box.indicator['vbatt'], load_box.indicator['ground'])


def get_dtc_from_queue(queue_to_tdk):
    q_list = help_utils.queue_get_all(queue_to_tdk)
    q_fault_list = help_utils.get_fault_from_queue(q_list)
    q_dtc_list = help_utils.get_dtc_from_queue(q_list)
    print('fault list', q_fault_list)     # can be written to a file later
    print('dtc list', q_dtc_list)       # can be written to a file later
    return q_dtc_list


# address is any DTC 6 bytes adress. can be set to 123456
# if you want to clear any dtc, just set data to 0000.
def simulate_loadbox(self, node, data, address=123456):
    write_format = 'diag ' + node + ' set ' + address + ' ' + data + '\r'
    self.write(str.encode(write_format))
    self.flush()
    time.sleep(1)
    buf = self.read(2048)
    return buf.decode("utf-8")


class Test():
    def __init__(self):
        try:
            serial_load_box = serial.Serial('COM30', 115200, timeout=1)
            self.ser = serial_load_box
            print(' serial start at: {}'.format(time.time()))
        except serial.serialutil.SerialException:
            print("SerialPort didn't open, please check Serial or conflict")
            exit(0)

    def easy_read_dtc(self, fault_flag):
        self.ser.write('diag tcu stat')
        self.ser.flush()
        time.sleep(1)
        buf = self.ser.read(2048)
        lines = buf.split(b'\n')
        # get all dtc to a list.
        if not fault_flag:
            return lines
        else:
            dtc_list = []
            for x in lines:
                if x.find('DTC:') != -1:
                    dtc_id = x.split('TCU')[1].split(":")[0].strip()
                    dtc_list.append(dtc_id)
                else:
                    dtc_list.append('no DTC!')
            return dtc_list

    def easy_clear_dtc(self):
        self.ser.write('clear dtc')

    def easy_monitor_fault(self, q_from_loadbox):
        while True:
            item = q_from_loadbox.get()
            if isinstance(item, list):
                pass
            elif isinstance(item, str):
                pass
            else:
                pass

    def monitor_fault(self, q_from_loadbox, q_to_loadbox):
        if q_from_loadbox.get().find("Set fault:") != -1:
            while True:
                ser.write('diag tcu stat')
                ser.flush()
                time.sleep(1)
                buf = ser.read(2048)
                lines = buf.split(b'\n')
                data_flag = True
                # get all dtc to a list.
                dtc_list = []
                for x in lines:
                    if x.find('DTC:') != -1:
                        dtc_id = x.split('TCU')[1].split(":")[0].strip()
                        dtc_list.append(dtc_id)
                # compare dtc_list from queue
                # q_from_loadbox.get() = ['Set fault: 0x123456', 'Set fault: 0x234567']
                dtc_from_queue = q_from_loadbox.get().split(":")[1].strip()
                if compare(dtc_from_queue, dtc_list) == "ok":
                    q_to_loadbox.put('OK')
                else:
                    q_to_loadbox.put('NOK')


def compare(l1, l2):
    return 'ok'

if __name__ == "__main__":
    """ Test Diag"""
    '''
    import Diagnostics as diag

    di = diag.DiagCode('COM30')
    di.WriteDtc('bcm', '123345', '50')
    di.ReadDtc('bcm', '123345')
    '''

    """Test QUEUE"""
    import multiprocessing as mp
    import load_box

    queue_tdk = mp.Queue()
    queue_can = mp.Queue()
    lb = load_box.LoadBox('COM21', queue_tdk, queue_can)
    lb.set_fault_easy(load_box.switch['normal'])
    print('end at: {}'.format(time.ctime()))
    lb.close_serial()
    queue_tdk_list = []
    queue_can_list = []
    print('get dtc', get_dtc_from_queue(queue_tdk))
    # hypo_set_diag(queue_tdk)
    # while True:
    #    queue_tdk_list.append(queue_tdk.get_nowait())
    #    if queue_tdk.empty():
    #        break
    # print('list is ', queue_tdk_list)
    # print(switch.Ground)
    '''
    try:
        global ser
        ser = serial.Serial('COM30', 115200, timeout=0)
        turn_unsub = "tur unsub" + "\r"
        ser.write(turn_unsub)
        print("time before turn unsub: {}".format(time.ctime()))
        time.sleep(1)
        print("time after turn unsub and start ign cycle: {}".format(time.ctime()))
        ign_cycle(ser, 3)
        print("time after 3 ign cycle: {}".format(time.ctime()))
    except serial.serialutil.SerialException:
        print("oops, wrong COM port")
    finally:
        ser.close()
    '''
