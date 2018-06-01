import help_utils

# ===================    FD30    ========================
_MSD_transmit_result_list = ['No event', 'Call not answered', 'START message not received',
                             'No acknowledgement', 'Link-level acknowledgement',
                             'Application-level acknowledgement', 'LL-ACK and AL-ACK']
_eCall_event_result_list = ['No event', 'Event in progress', 'eCall cancelled by user',
                            'No available cellular network',
                            'Could not register to available network',
                            'Call could not be connected', 'Call was not answered', 'Dropped call',
                            'Call ended by PSAP']
_eCall_trigger_source_list = ['No automatic eCall event', 'ENS', 'CAN']
_eCall_trigger_type_list = ['No event', 'Automatic trigger', 'Manual trigger']


def decode_fd30(hex_ecall_event):
    if hex_ecall_event == "":
        return "NULL"
    hex_ecall_event = hex_ecall_event.replace(" ", "").replace("\n", "")
    bin_ecall_event = help_utils.hex_to_bin(hex_ecall_event)
    # AL_ACK_Time
    AL_ACK_Time_bin = bin_ecall_event[5: 13]
    AL_ACK_Time = help_utils.bin_to_dec(AL_ACK_Time_bin) * 100
    # Call_established_time
    Call_established_time_bin = bin_ecall_event[13: 21]
    Call_established_time = help_utils.bin_to_dec(Call_established_time_bin) * 100
    # MSD_transmit_result
    MSD_transmit_result_bin = bin_ecall_event[21:24]
    MSD_transmit_result_index = help_utils.bin_to_dec(MSD_transmit_result_bin)
    MSD_transmit_result = _MSD_transmit_result_list[MSD_transmit_result_index]
    # eCall_event_result
    eCall_event_result_bin = bin_ecall_event[24:28]
    eCall_event_result_index = help_utils.bin_to_dec(eCall_event_result_bin)
    eCall_event_result = _eCall_event_result_list[eCall_event_result_index]
    # eCall_trigger_source
    eCall_trigger_source_bin = bin_ecall_event[28:30]
    eCall_trigger_source_index = help_utils.bin_to_dec(eCall_trigger_source_bin)
    eCall_trigger_source = _eCall_trigger_source_list[eCall_trigger_source_index]
    # eCall_trigger_type
    eCall_trigger_type_bin = bin_ecall_event[30:32]
    eCall_trigger_type_index = help_utils.bin_to_dec(eCall_trigger_type_bin)
    eCall_trigger_type = _eCall_trigger_type_list[eCall_trigger_type_index]
    fd30_ecall_event = "- - - - - - - - - - - - - - - - - - - -\n" \
                       + "AL_ACK_Time:" + '\t\t\t' + str(AL_ACK_Time) + '\n' \
                       + "Call_established_time:" + "\t\t\t" + str(Call_established_time) + '\n' \
                       + "MSD_transmit_result:" + "\t\t\t" + str(MSD_transmit_result) + "\n" \
                       + "eCall_event_result:" + "\t\t\t" + str(eCall_event_result) + "\n" \
                       + "eCall_trigger_source:" + "\t\t\t" + str(eCall_trigger_source) + "\n" \
                       + "eCall_trigger_type:" + "\t\t\t" + str(eCall_trigger_type) + '\n' \
                       + "- - - - - - - - - - - - - - - - - - - -"
    return fd30_ecall_event


def get_fd30_dict(fd30_text):
    from collections import OrderedDict
    fd30_dict = OrderedDict()
    for para in fd30_text.split("\n"):
        # remember there is a '-------------------' in fd30_text
        if len(para.split(":")) == 2:
            category = para.split(":")[0].replace("\t", "").strip()
            value = para.split(":")[1].replace("\t", "").strip()
            fd30_dict.update({category:value})
    return fd30_dict


def compare_ecall_event_result(fd30_dict, result_queue=None, automation=True):
    ecall_event_result = fd30_dict['eCall_event_result']
    if automation:
        should_report = 'Call ended by PSAP'
        if should_report == ecall_event_result:
            ecall_event_result_status = 1
            result_queue.put("  -eCall_event_result matches\n  ------OK")
        else:
            ecall_event_result_status = 0
            result_queue.put("  -eCall_event_result: " + ecall_event_result + " DOESN\'T matches\n  ------NOK")
    else:
        ecall_event_result_status = 2  # not implemented yet
    return ecall_event_result_status


def compare_ecall_trigger_source(fd30_dict, result_queue=None, trigger_source='CAN'):
    ecall_trigger_source = fd30_dict['eCall_trigger_source']
    if ecall_trigger_source == trigger_source:
        ecall_trigger_source_status = 1
        result_queue.put("  -eCall_trigger_source matches\n  ------OK")
    else:
        ecall_trigger_source_status = 0
        result_queue.put("  -eCall_trigger_source: " + ecall_trigger_source + " DOESN\'T matches\n  ------NOK")

    return ecall_trigger_source_status


# 'Automatic trigger', 'Manual trigger'
def compare_ecall_trigger_type(fd30_dict, auto_flag, result_queue=None):
    ecall_trigger_type = fd30_dict['eCall_trigger_type']
    if auto_flag:
        trigger_type = 'Automatic trigger'
    else:
        trigger_type = 'Manual trigger'
    if trigger_type == ecall_trigger_type:
        ecall_trigger_type_status = 1
        result_queue.put("  -eCall_trigger_type matches\n  ------OK")
    else:
        print ecall_trigger_type == trigger_type
        ecall_trigger_type_status = 0
        result_queue.put("  -eCall_trigger_type: " + ecall_trigger_type + " DOESN\'T matches\n  ------NOK")

    return ecall_trigger_type_status


def read_fd30(gui_queue, result_queue, signal_queue, auto_ecall_flag, after_ign_cycles=False):
    import threading
    from Queue import Queue
    import canalyzer_final
    import run_batch
    import test_suite_1 as ts
    event = threading.Event()
    event_result_queue = Queue()
    msg_760_ts = ts.ReadDid0x75C("0x760", event_result_queue)
    batch_queue = Queue()
    # !!HAVE TO!! initiate another CANalyzer marshal id
    id2 = help_utils.generate_app_marshal()
    ic2 = canalyzer_final.InitiateCanalyzer(event, app_id=id2)

    # Thread that will run batch to read FD30 or maybe FD34 in the future since FD34 is complicated.
    threading.Thread(target=run_batch.read_ecall_event_batch, name="Thread Run Batch",
                     args=(batch_queue, gui_queue, result_queue)).start()

    batch_result = batch_queue.get()

    # Thread that will keep reading 0x760 msg.
    # But this thread will only start after fd30 thread has completed because of batch_queue.get() will block.
    threading.Thread(target=ic2.get_a_signal, name="Thread Read 0x760 (one msg of 0x75C)",
                     args=(signal_queue, gui_queue, result_queue, None, msg_760_ts,
                           2, "TesterPhysicalResTCU_1", "TesterPhysicalResTCU4_Copy_1",
                           )).start()

    if batch_result == "OK":
        gui_queue.put("Batch result is OK")
    else:
        gui_queue.put("Batch result: " + batch_result)

    # print "about to get event_result"
    gui_queue.put("DET Batch Finished. About to decode FD30.")
    event_result_hex = event_result_queue.get()
    event_result_text = decode_fd30(event_result_hex)
    if event_result_text == "NULL":
        return -2
    fd30_status_before = -1
    fd30_status_after = -1
    if not after_ign_cycles:
        fd30_dict = get_fd30_dict(event_result_text)
        ecall_event_result_status = compare_ecall_event_result(fd30_dict, result_queue)
        ecall_trigger_source_status = compare_ecall_trigger_source(fd30_dict, result_queue)
        ecall_trigger_type_status = compare_ecall_trigger_type(fd30_dict, auto_ecall_flag, result_queue)
        if ecall_event_result_status == 1 and ecall_trigger_type_status == 1 and ecall_trigger_source_status == 1:
            result_queue.put("FD30 before clear result ------OK")
            fd30_status_before = 1
        elif ecall_event_result_status == 0 and ecall_trigger_source_status == 0 and ecall_trigger_type_status == 0:
            fd30_status_before = 0
            result_queue.put("FD30 before clear result ------NOK")
        else:
            fd30_status_before = 2  # Partial
            result_queue.put("FD30 before clear result ------PARTIAL")
        event.set()
        return fd30_status_before

    if after_ign_cycles:
        if event_result_hex == "00000000":
            fd30_status_after = 1
            result_queue.put("FD30 after clear result ------OK")
        else:
            gui_queue.put("Event result hex is: " + str(event_result_hex))
            fd30_status_after = 0
            result_queue.put("FD30 after clear result ------NOK")

        event.set()
        return fd30_status_after


if __name__ == "__main__":
    a = get_fd30_dict(decode_fd30("02 35 56 89 "))
    print a['eCall_trigger_type']
    print a
    # print compare_ecall_trigger_type(a, True)
    import script_bootup_from_gui as bbb
    p, w, v, prop, t = bbb.auto_standby_script_para("AUTO ECALL STANDBY(PERIOD=1,WAIT=TRUE_0,VTYPE=3,PROP=petrol&other&diesel&hydro,TIMES=1)")
    print prop, type(prop)
    petrol, diesel, cn, lp, elec, hydro, other = bbb.get_prop(prop)
    print bbb.get_prop(prop)

    p, w, v, prop= bbb.prop_type_script_para("TEST PROP(STANDBY=1, VTYPE=1, WAIT=TRUE_0, PROP=petrol)")
    print bbb.get_prop(prop), type(prop)
    period = 9.956
    print int(period + 10)