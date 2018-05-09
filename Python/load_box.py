import serial
import threading
import time
import abc


# abstract class to force its child class to implement the close function
class ILoadBox(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def close_serial(self):
        pass


'''
Switch-Press-0 Switch-Normal-0 Switch-Open-0 Switch-Ground-0 Switch-VBATT-0
StatusIndc-Open-0 StatusIndc-Ground-0 StatusIndc-VBATT-0 StatusIndc-Normal-0
Mic-Open-0 Mic-Ground-0 Mic-VBATT-0 Mic-Normal-0
LSpeaker-Open-0 LSpeaker-Ground-0 LSpeaker-VBATT-0 LSpeaker-LeadToLead-0 LSpeaker-Normal-0
RSpeaker-Open-0 RSpeaker-Ground-0 RSpeaker-VBATT-0 RSpeaker-LeadToLead-0 RSpeaker-Normal-0
ENS-Pass-0 ENS-Ground-0 ENS-Cutoff-0 ENS-Deploy-0 ENS-Normal-0
Power-Open-0 Power-Normal-0
Reset-0-0
'''
switch = {'press': 'Switch-Press-0', 'normal': 'Switch-Normal-0-1-2-3', 'ground': 'Switch-Ground-0',
          'vbatt': 'Switch-VBATT-0', 'open': 'Switch-Open-0-0-0'}
indicator = {'open': 'StatusIndc-Open-0', 'ground': 'StatusIndc-Ground-0',
             'vbatt': 'StatusIndc-VBATT-0', 'normal': 'StatusIndc-Normal-0'}
mic = {'open': 'Mic-Open-0', 'ground': 'Mic-Ground-0', 'vbatt': 'Mic-VBATT-0', 'normal': 'Mic-Normal-0'}
left_speaker = {'open': 'LSpeaker-Open-0', 'ground': 'LSpeaker-Ground-0',
                'vbatt': 'LSpeaker-VBATT-0', 'leadTolead': 'LSpeaker-LeadToLead-0', 'normal': 'LSpeaker-Normal-0'}
right_speaker = {'open': 'RSpeaker-Open-0', 'ground': 'RSpeaker-Ground-0',
                'vbatt': 'RSpeaker-VBATT-0', 'leadTolead': 'RSpeaker-LeadToLead-0', 'normal': 'RSpeaker-Normal-0'}
ens = {'pass': 'ENS-Pass-0', 'ground': 'ENS-Ground-0', 'cutoff': 'ENS-Cutoff-0',
       'deploy': 'ENS-Deploy-0', 'normal': 'ENS-Normal-0'}
power = {'open': 'Power-Open-0', 'normal': 'Power-Normal-0'}


class LoadBox(ILoadBox):
    def __init__(self, com_port, queue_tdk, queue_can):
        try:
            serial_load_box = serial.Serial(com_port, 9600, timeout=1)
            self.ser = serial_load_box
            self.queue_tdk = queue_tdk
            self.queue_can = queue_can
            print('start at: {}'.format(time.ctime()))
        except serial.serialutil.SerialException:
            print("Loadbox SerialPort didn't open, please check Serial or conflict")
            exit(0)

    # save for future usage
    def write_to_loadbox(self, component, fault, sequence='0', delta_1='0', delta_2='0', delta_3='0', delta_4='0'):
        valid_result = data_validation(component, fault, sequence)
        if valid_result == "OK":
            print(write_to_serial(self, component, fault, sequence, delta_1, delta_2, delta_3, delta_4))
        else:
            print(valid_result)

    def manual_ecall(self):
        """
        Trigger a manual eCall
        :return:
        """
        with self.ser as s:
            time.sleep(8)
            s.write(switch['press'])
            time.sleep(2)
            s.write(switch['normal'])

    def set_all_normal(self):
        """
        Used to set everything back to normal before starting a new test case.
        :return:
        """
        normal_list = [switch['normal'], mic['normal'], left_speaker['normal'],
                       right_speaker['normal'], indicator['normal'], ens['normal'], power['normal']]
        self.set_status_without_seq(normal_list)

    def set_one_normal(self, component, q, cdl, result):
        if component == "Switch":
            self.set_one_status(switch['normal'])
        elif component == "StatusIndc":
            self.set_one_status(indicator['normal'])
        elif component == "Mic":
            self.set_one_status(mic['normal'])
        elif component == "LSpeaker":
            self.set_one_status(left_speaker['normal'])
        elif component == "RSpeaker":
            self.set_one_status(right_speaker['normal'])
        elif component == "ENS":
            self.set_one_status(ens['normal'])
        elif component == "Power":
            self.set_one_status(power['normal'])
        if result == "OK":
            q.put("Set Normal")
        else:
            q.put("NOK")
        cdl.count_down()
        """
        # Save for later diagnostic that is not capable of coding process
        dtc_cleared = False
        while not dtc_cleared:
            while True:
                answer = raw_input("Did you clear the DTC? Yes or No?").lower()
                if answer in ('yes', 'no'):
                    break

            dtc_cleared = answer == 'yes'
        """
    def set_one_status(self, fault):
        # with self.ser as s:
        s = self.ser
        time.sleep(2)
        print('from loadbox: {}, fault is sent'.format(write_to_serial_easy(s, fault)))

        # ====== Add for test only, delete later =======
        # time.sleep(1)
        # write_to_serial_easy(s, switch['open'])
        # ==============================================

    def set_one_stat_to_queue(self, fault, queue_from_gui):
        self.set_one_status(fault)
        queue_from_gui.put('Set Fault: ' + fault + "at: {}".format(time.time()))
        self.queue_tdk.put('Set Fault: ' + fault + "at: {}".format(time.time()))

    def set_spk_stat_to_queue(self, spk_list):
        self.set_status_without_seq(spk_list)
        self.queue_tdk.put('Set Speaker Fault: ' + spk_list[0] + ' and ' + spk_list[1] + "at: {}".format(time.time()))

    def set_status_without_seq(self, *args):
        """
        Set no sequence fault (do not need sequence delta times).
        :param args: list/dict/str
        :return: None
        """
        # with self.ser as s:
        s = self.ser
        for para in args:
            if isinstance(para, list):
                for item in para:
                    time.sleep(2)
                    # s.write(item)
                    write_to_serial_easy(s, item)
                    print('item: {}'.format(item))
            elif isinstance(para, dict):
                for key, value in para.items():
                    time.sleep(2)
                    write_to_serial_easy(s, value)
                    print("key:{}, value:{}".format(key, value))
            elif isinstance(para, str):
                print('enter set_status_without_seq at:{}'.format(time.ctime()))
                time.sleep(2)
                print('from loadbox:'.format(write_to_serial_easy(s, para)))
                print('set fault at:{}'.format(time.ctime()))
                print("para str: {}".format(para))
                self.queue_tdk.put('Set fault: ' + para + "at: {}".format(time.time()))
                self.queue_can.put('Set fault: ' + para + "at: {}".format(time.time()))
            # print('para:{}'.format(para))

    # callback function
    def on_receive_fault_from_can(self, component, q, cdl, result):
        self.set_one_normal(component, q, cdl, result)
        print('receive fault status from CAN at: {}'.format(time.time()))
        return True

    def on_receive_spk_fault_from_can(self, q, cdl):
        self.set_one_status(left_speaker['normal'])
        self.set_one_status(right_speaker['normal'])
        print('receive speaker fault status from CAN at: {}'.format(time.time()))
        q.put("Set Speaker Normal")
        cdl.count_down()
        return True

    def on_receive_fault_from_tdk(self, component):
        print('receive fault status from CAN at: {}'.format(time.time()))
        return True

    def close_serial(self):
        print("loadbox serial is closed")
        self.ser.close()


########################################################################
# ======================Helper Function=================================#
########################################################################
component_list = ['Switch', 'StatusIndc', 'Mic', 'LSpeaker', 'RSpeaker', 'ENS', 'Power']
fault_list = ['Normal', 'Ground', 'VBATT', 'Open', 'LeadToLead']


def data_validation(component, fault, sequence):
    if component not in component_list.__str__():
        return "Not valid Component. List is: {}".format(component_list)
    elif fault not in fault_list.__str__():
        return "Not valid Fault. List is: {}".format(fault_list)
    elif sequence != '0' and sequence != '1':
        return "Not valid sequence. It has to be 0(no sequence) or 1(sequence)!"
    else:
        return "OK"


def write_to_serial_easy(self, simple_fault_command):
    self.write(str.encode(simple_fault_command))
    self.flush()
    time.sleep(1)
    buf = self.read(1024)
    return buf.decode("utf-8")


def write_to_serial(self, component, fault='Normal', sequence='0', delta_1='0', delta_2='0', delta_3='0', delta_4='0'):
    write_format = component + '-' + fault + '-' + sequence + '-' + \
        delta_1 + '-' + delta_2 + '-' + delta_3 + '-' + delta_4
    print('write format: {}'.format(write_format))
    with self.ser as s:
        s.write(str.encode(write_format))
        s.flush()
        time.sleep(1)
        buf = s.read(2048)
    return buf.decode("utf-8")


def queue_get_all(q, max_item_to_retrieve=10):
    items = []
    for num_of_items_retrieved in range(0, max_item_to_retrieve):
        try:
            if num_of_items_retrieved == max_item_to_retrieve:
                break
            items.append(q.get_nowait())
        except:
            break
    return items


def test(*args):
    # lb = LoadBox('COM21')
    # lb.set_fault(switch.values())
    # print(type(switch.values()))
    # list_fault = [switch['ground'], left_speaker['vbatt'], right_speaker['vbatt'], indicator['vbatt']]
    # list_normal = [switch['normal'], left_speaker['normal'], right_speaker['normal'], indicator['normal']]
    # lb.set_fault(switch)
    # lb.set_fault('s1', 's2', switch['normal'])
    # lb.set_fault(switch['normal'])
    # lb.set_fault(list_normal)
    # lb.set_fault(switch['normal'])

    # threading.Thread(target=lb.manual_ecall).start()

    # test([1,2,3])  # *args returns a tuple

    # print(data_validation('SwITch'))
    # print(type(component_list.__str__()))
    # print("write_to_serial_2: {}".format(write_to_serial("Switch", 'Normal')))
    print(args)


if __name__ == "__main__":
    # start_load_box()
    import multiprocessing as mp
    queue = mp.Queue()
    lb = LoadBox('COM21', queue)
    lb.set_fault_easy(switch['normal'], mic['normal'])
    print('end at: {}'.format(time.ctime()))
    lb.close_serial()
    l = []
    while True:
        l.append(queue.get_nowait())
        if queue.empty():
            break
    print('list is ', l)
    # print(write_to_serial(lb, 'Switch', 'Normal'))

    # lb.write_normal('switch', 'press')
    # lb.manual_ecall_old()
    # lb.close_serial()   # must be implemented if not using with statement in the function.
