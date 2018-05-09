import win32com.client
import pythoncom


def generate_app_marshal():
    # ???????????????????? THAT"S ENOUGH????????????????????????????????
    # Only Call CoInitialize()???????????????????????????????????
    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx('CANalyzer.Application')
    app_id = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, app)
    return app_id


switch_dtc = {'GROUND': r'916D11', 'OPEN': r'916D13', 'VBATT': r'916D13', 'PRESS': r'916D9E'}
indicator_dtc = {'VBATT': r'92B712', 'GROUND': r'92B711', 'OPEN': r'92B712'}
mic_dtc = {'OPEN': r'9D7913', 'VBATT': r'9D7912', 'GROUND': r'9D7911'}
ens_dtc = {'Not Used 1': r'C45200', 'Not Used 2': r'C45200', 'Not Used 3': r'C45200',
           'Not Used 4': r'C45200', 'Not Used 5': r'C45200', 'DIS RCM': r'C15100',
           'PASS THROUGH': r'91D824', 'GROUND': r'91D823'}
power_off_dtc = {'POWER OFF': r'F00316'}
lspeaker_dtc = {'GROUND': r'9A0111', 'VBATT': r'9A0112', 'OPEN': r'9A0113', 'LeadToLead': r'9A011E'}
rspeaker_dtc = {'GROUND': r'9A0211', 'VBATT': r'9A0212', 'OPEN': r'9A0213', 'LeadToLead': r'9A021E'}

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

l = ['Set fault: Switch-Press-0-1-2-3 at: 6.3', 'Set fault: Mic-Open-0 at: 0.2']


def get_fault_command(component, fault):
    fault = fault.lower()
    if component.upper() == "SWITCH" or component.upper() == "BUTTON":
        print "switch"
        return switch[fault]
    elif component.upper() == "StatusIndc".upper() or component.upper() == "INDICATOR" or component.upper() == "IND":
        print "ind"
        return indicator[fault]
    elif component.upper() == "MIC":
        print "mic"
        return mic[fault]
    elif component.upper() == "LSpeaker".upper():
        print component
        return left_speaker[fault]
    elif component.upper() == "RSpeaker".upper():
        print component
        return right_speaker[fault]
    elif component.upper() == "ENS":
        print component
        return ens[fault]
    elif component.upper() == "Power".upper():
        print component
        return power[fault]

def append_dict_to_list(component):
    if component == "Switch":
        return "Switch DTC List: " + str(switch_dtc)
    elif component == "StatusIndc":
        return "Indicator DTC List: " + str(indicator_dtc)
    elif component == "Mic":
        return "Microphone DTC List: " + str(mic_dtc)
    elif component == "LSpeaker":
        return "Left Speaker DTC List: " + str(lspeaker_dtc)
    elif component == "RSpeaker":
        return "Right Speaker DTC List: " + str(rspeaker_dtc)
    elif component == "ENS":
        return "ENS DTC List: " + str(ens_dtc)
    elif component == "Power":
        return "Power DTC List: " + str(power_off_dtc)


def get_fault_from_queue(queue_list):
    return [fault.split("Set fault:")[1].split("at:")[0].strip().split("-")[0:2]
            for fault in queue_list if fault.find('Set fault:') != -1]


def append_dtc_to_list(fault, get_dtc_list, compo_dtc):
    if fault[1].upper() in compo_dtc.keys():
        get_dtc_list.append(compo_dtc[fault[1].upper()])
    elif fault[1] == "Normal":
        get_dtc_list.append(fault[0] + fault[1])
    else:
        print(fault[1].upper(), compo_dtc.keys())
        get_dtc_list.append(fault[0] + ' Wrong')


def get_dtc_id_from_queue(queue_list):
    get_dtc_list = list()
    fault_from_queue_list = get_fault_from_queue(queue_list)
    for fault in fault_from_queue_list:
        if fault[0] == "Switch":
            append_dtc_to_list(fault, get_dtc_list, switch_dtc)
        elif fault[0] == "Mic":
            append_dtc_to_list(fault, get_dtc_list, mic_dtc)
        elif fault[0] == "StatusIndc":
            append_dtc_to_list(fault, get_dtc_list, indicator_dtc)
        elif fault[0] == "ENS":
            append_dtc_to_list(fault, get_dtc_list, ens_dtc)
    return get_dtc_list


# =========== Help Function to verify 0x75C msg ======================

def get_dtc_id_from_one_fault(component, fault_stat):
    fault_stat = fault_stat.upper()
    if component == "Switch":
        return switch_dtc[fault_stat]
    elif component == "Mic":
        return mic_dtc[fault_stat]
    elif component == "StatusIndc":
        return indicator_dtc[fault_stat]
    elif component == "ENS":
        return ens_dtc[fault_stat]
    elif component == "LSpeaker":
        return lspeaker_dtc[fault_stat]
    elif component == "RSpeaker":
        return rspeaker_dtc[fault_stat]
    elif component == "Power":
        return power_off_dtc[fault_stat]


def get_key_from_value(component_dtc_dict, dtc_id):
    fault_list = []  # because one dtc_id will have different fault statuses
    if dtc_id in component_dtc_dict.values():
        print dtc_id.upper()
        for stat, _id in component_dtc_dict.iteritems():
            if dtc_id == _id:
                fault_list.append(stat)
    return fault_list


def get_fault_name_from_dtc_id(component, dtc_id):
    dtc_id = dtc_id.upper()
    result = ""
    if component == "Switch":
        result = get_key_from_value(switch_dtc, dtc_id)
    elif component == "StatusIndc":
        result = get_key_from_value(indicator_dtc, dtc_id)
    elif component == "Mic":
        result = get_key_from_value(mic_dtc, dtc_id)
    elif component == "LSpeaker":
        result = get_key_from_value(left_speaker, dtc_id)
    elif component == "RSpeaker":
        result = get_key_from_value(right_speaker, dtc_id)
    elif component == "ENS":
        result = get_key_from_value(ens_dtc, dtc_id)
    elif component == "Power":
        result = get_key_from_value(power_off_dtc, dtc_id)
    return result


# 0x75C: 1160619197504508160, count 1 at 1521826352.1
# 0x75C: 2398327631243681109, count 2 at 1521826352.12
# 0x75C: 2552717766254482760, count 3 at 1521826352.15
def decode_raw_signal_values(raw_value_dec_list):
    # Tradeoff for maximum of 4 DTCs
    raw_value_hex_list = []
    list_dtcs = []

    # 1160619197504508160 (DEC) -> 10 1B 59 02 CA C1 51 00 (HEX)
    # 2552717766254482760 (DEC) -> 23 6d 13 48 95 6d 55 48 (HEX)
    # 529457501042704394  (DEC) ->  7 59 02 ca c1 51 00 0a (HEX)
    for each in raw_value_dec_list:
        hex_num = decode_raw_signal_value(each)
        raw_value_hex_list.append(hex_num)

    head = raw_value_hex_list[0][:2]
    # print(hex_num)
    # print(head)
    # print(raw_value_hex_list)
    return raw_value_hex_list


def decode_raw_signal_value(raw_value):

    # 1160619197504508160 (DEC) -> 10 1B 59 02 CA C1 51 00 (HEX)
    # 2552717766254482760 (DEC) -> 23 6d 13 48 95 6d 55 48 (HEX)
    # 529457501042704394  (DEC) ->  7 59 02 ca c1 51 00 0a (HEX)

    hex_num = hex(raw_value).split('x')[-1].zfill(17)
    return hex_num


def get_dtc_status_in_det_tool(stat):
    """

    :param stat:
            1. 0x0A: Active
                    - Confirmed DTC
                    - Test Failed This Operation Cycle
            2. 0x08: In History but Actively Passing
                    - Confirmed DTC
            3. 0x48: In History but not Independently
                    - Confirmed DTC
                    - Test Not Completed This Operation Cycle
    :return: DTC status instruction
    """
    if stat == "0A".lower():
        return "Active DTC: "
    elif stat == "48".lower():
        return "In History but not Independently DTC: "
    elif stat == "08".lower():
        return "In History but Actively Passing DTC: "
    else:
        return "NOT KNOWN DTC: "


# first_dtc = "NULL"


def get_dtc_msg_from_list(hex_num_list):
    """
    Decode DTC Msg 0x75C

    :param hex_num:
                                        st - DTC status; xx - DTC Nums;
                - clear DTC: 01 | 54 00 00 00 00 00 00
                - 0     DTC: 03 | 59 02 CA 00 00 00 00   (03 = 3 data length  ===> (3 - 3) / 4 = 0 DTC)
                - 1     DTC: 07 | 59 02 CA xx xx xx st   (07 = 7 data length  ===> (7 - 3) / 4 = 1 DTC)
                - 2     DTC: 10   0B|59 02 CA xx xx xx   (0B = 11 data length ===> (11 - 3) / 4 = 2 DTCs)
                             21 | st xx xx xx st 00 00   (21 = Extra First Row)
                - 3     DTC: 10   0F|59 02 CA xx xx xx   (0F = 15 data length ===> (15 - 3) / 4 = 3 DTCs)
                             21 | st xx xx xx st xx xx   (21 = Extra First Row)
                             22 | xx st 00 00 00 00 00   (22 = Extra Second Row)
                - 4     DTC: 10   13|59 02 CA xx xx xx   (13 = 19 data length ===> (19 - 3) / 4 = 4 DTCs)
                             21 | st xx xx xx st xx xx   (21 = Extra First Row)
                             22 | xx st xx xx xx st 00   (22 = Extra Second Row)

                0x760 starts with 07; 0x761 starts with 10;
                0x762 starts with 21; 0x763 starts with 22; 0x764 starts with 23.
    :return:
    """
    global first_dtc
    third_dtc_half = "null"
    first_dtc_stat = "null"
    second_dtc_stat = "null"
    second_dtc = "null"
    num_of_dtc = 0
    count_list = 0
    for hex_num in hex_num_list:
        count_list += 1
        head = hex_num[:2]  # first bytes
        if head == "03":
            if hex_num[2:8].upper() == "5902CA":
                return "NO DTC"

        if head == "07":
            dtc = hex_num[8:14].upper()
            stat = hex_num[14:16]
            return "1 " + get_dtc_status_in_det_tool(stat) + dtc + " - "

        if head == "10":
            num_of_dtc = (int(hex_num[2:4], 16) - 3) / 4
            if hex_num[4:10].upper() == "5902CA":
                first_dtc = hex_num[10:16].upper()
            if count_list == len(hex_num_list):
                return "null, but get: " + hex_num
        if head == "21":
            first_dtc_stat = hex_num[2:4]
            second_dtc = hex_num[4:10].upper()
            second_dtc_stat = hex_num[10:12]
            if num_of_dtc == 2:
                return str(num_of_dtc) + " DTCs found. " + \
                       "1. " + get_dtc_status_in_det_tool(first_dtc_stat) + first_dtc + "\t" + \
                       "2. " + get_dtc_status_in_det_tool(second_dtc_stat) + str(second_dtc) + " - "
            # 10   13|59 02 CA xx xx xx   (13 = 19 data length ===> (19 - 3) / 4 = 4 DTCs)
            # 21 | st xx xx xx st xx xx   (21 = Extra First Row)
            # 22 | xx st xx xx xx st 00   (22 = Extra Second Row)
            elif num_of_dtc > 2:
                third_dtc_half = hex_num[12:16].upper()
            else:
                return "null, but get: " + hex_num
        if head == "22":
            third_dtc = third_dtc_half + hex_num[2:4].upper()
            third_dtc_stat = hex_num[4:6]
            if num_of_dtc == 3:
                return str(num_of_dtc) + "DTCs found. " + \
                       "1. " + get_dtc_status_in_det_tool(first_dtc_stat) + first_dtc + "\t" + \
                       "2. " + get_dtc_status_in_det_tool(second_dtc_stat) + second_dtc + "\t" + \
                       "3. " + get_dtc_status_in_det_tool(third_dtc_stat) + third_dtc + " - "
            elif num_of_dtc == 4:
                forth_dtc = hex_num[6:12].upper()
                forth_dtc_stat = hex_num[12:14]
                return str(num_of_dtc) + "DTCs found. " + \
                       "1. " + get_dtc_status_in_det_tool(first_dtc_stat) + first_dtc + "\t" + \
                       "2. " + get_dtc_status_in_det_tool(second_dtc_stat) + second_dtc + "\t" + \
                       "3. " + get_dtc_status_in_det_tool(third_dtc_stat) + third_dtc + "\t" + \
                       "4. " + get_dtc_status_in_det_tool(forth_dtc_stat) + forth_dtc + " - "
            elif num_of_dtc > 5:
                fifth_dtc_part = hex_num[14:16]
                # to be implemented later. But unlikely to be used.
            else:
                return "null, but get: " + hex_num

        if head == "01":
            if hex_num[2:4] == "54":
                print("DTC is cleared")
# =========== END of Help Function to verify 0x75C msg ===============

"""
# deprecated since it can only detect one msg.
def get_dtc_msg(hex_num):
    head = hex_num[:2]  # first bytes
    if head == "03":
        if hex_num[2:8] == "5902CA":
            return "NO DTC"

    if head == "07":
        dtc = hex_num[8:14]
        stat = hex_num[14:16]
        return "1 " + get_dtc_status_in_det_tool(stat) + dtc

    if head == "01":
        if hex_num[2:4] == "54":
            print("DTC is cleared")
"""

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


def get_75c(self):
    # 0x760 starts with 07; 0x761 starts with 10;
    # 0x762 starts with 21; 0x763 starts with 22; 0x764 starts with 23.
    list_decode_75c = []
    list_75c = []
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
    import time
    time.sleep(2)
    if len(list_75c) != 0:
        list_decode_75c = decode_raw_signal_values(list_75c)

    # ========== get dtc from 75C =======
    print list_decode_75c
    # queue_from_gui.put("DTCs: " + str(list_decode_75c))
    return_dtc_result = get_dtc_msg_from_list(list_decode_75c)
    return return_dtc_result


def wait_and_pump_msg(timeout=5, done_time=5000):
    """

    :param timeout:
    :param done_time:
    :return:
    """
    # timeout in seconds, dontime in milliseconds!
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
    import win32event, time
    event = win32event.CreateEvent(None, 0, 0, None)
    timeStart = time.time()
    timeTic = timeStart
    while True:
        rc = win32event.MsgWaitForMultipleObjects(
            (event,), 0, done_time, win32event.QS_ALLEVENTS)
        if rc == win32event.WAIT_OBJECT_0:
            pass
        elif rc == win32event.WAIT_OBJECT_0+1:
            pythoncom.PumpWaitingMessages()
        elif rc == win32event.WAIT_TIMEOUT:
            print( ' WaitMsg: got donetime' )
            return True
        else:
            print( 'Unrecognized event' )

        if time.time() - timeStart > timeout:
            print( ' ##### got timeout' )
            return False
        if time.time() - timeTic > 1:
            print( '.', )
            timeTic = time.time()


if __name__ == "__main__":
    '''
    #print(get_fault_from_queue(l))
    #print(get_dtc_id_from_queue(l))
    y = decode_raw_signal_values([1160619197504508160, 2398327631243681109, 2552717766254482760, 529457501042704394])
    # 754 msg: clear dtc, read dtc1, read dtc2, clear dtc
    x = decode_raw_signal_values([294141350645858304, 223212469735129088, 3458764513820540928, 294141350645858304])
    print x, y
    d = get_dtc_msg("075902ca916d130aL")
    print d
    o = get_fault_name_from_dtc_id("ENS", "C45200")
    print o

    ll = []
    print append_dict_to_list("Switch")

    list_decode_75c = ['0154000000000000L', '075902ca9d79130aL']
    for each_decode_75c in list_decode_75c:
        dtc_msg = get_dtc_msg(each_decode_75c)
        if dtc_msg is not None:
            ll.append(dtc_msg)
    print ll
    print int("10", 16)
    '''
    z = ['100b5902cac15100', '210a916d130a0000']
    print get_dtc_msg_from_list(z)
    x = ['0154000000000000L','100f5902cac15100L', '210a916d130a9d79L', '22110a0000000000L']
    print get_dtc_msg_from_list(x)

    st = "Simulate Fault: StatusIndc-Ground ---> 2 DTCs found. 1. Active DTC: 916d13"
    print st.split("\t")[0].split("DTC:")[1]

    print get_dtc_id_from_one_fault("Switch", 'open')

    print get_fault_command("ind", "open")

    x = decode_raw_signal_values([95701492081623040L, 1161745097408267795L, 2638398079388090368L, 2459821446727338650L, 1157241497780897299L])
    print x