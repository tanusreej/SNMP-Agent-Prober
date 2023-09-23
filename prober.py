#!/usr/bin/python3
import sys
import time
import math
import easysnmp
from easysnmp import Session, EasySNMPUnknownObjectIDError, EasySNMPTimeoutError

input_values = sys.argv[1]
split_values = input_values.split(':')
target_address = split_values[0]
target_port_num = split_values[1]
comm_string = split_values[2]
sampling_freq = float(sys.argv[2])
num_samples = int(sys.argv[3])
sampling_interval = 1 / sampling_freq
oid_collection = []

for idx in range(4, len(sys.argv)):
    oid_collection.append(sys.argv[idx])
oid_collection.insert(0, '1.3.6.1.2.1.1.3.0')

snmp_sess = Session(hostname=target_address, remote_port=target_port_num, community=comm_string, version=2, timeout=1, retries=3)

def calculate_rate(counter, prev_counter, time_difference):
    calculated_rate = (counter - prev_counter) / time_difference
    return round(calculated_rate)

def handle_negative_rate(sub_oid, snmp_data_type):
    if snmp_data_type == 'COUNTER64':
        return sub_oid + (2 ** 64)
    elif snmp_data_type == 'COUNTER32':
        return sub_oid + (2 ** 32)
    else:
        return sub_oid

def fetch_and_display_data():
    global previous_data, last_log_time, current_time
    try:
        fetched_data = snmp_sess.get(oid_collection)
    except EasySNMPUnknownObjectIDError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except EasySNMPTimeoutError:
        print("SNMP request timed out.", file=sys.stderr)
        return
    
    current_log_time = int(fetched_data[0].value) / 100
    current_data = []
    separator = ""
    
    for idx in range(1, len(fetched_data)):
        if fetched_data[idx].value != 'NOSUCHOBJECT' and fetched_data[idx].value != 'NOSUCHINSTANCE':
            if fetched_data[idx].snmp_type in ['COUNTER64', 'GAUGE', 'COUNTER32', 'COUNTER']:
                current_data.append(int(fetched_data[idx].value))
            else:
                current_data.append(fetched_data[idx].value)
                
            if num != 0 and len(previous_data) > 0:
                if current_log_time > last_log_time:
                    if fetched_data[idx].snmp_type in ['COUNTER', 'COUNTER32', 'COUNTER64']:
                        sub_oid = int(current_data[idx - 1]) - int(previous_data[idx - 1])
                        sub_time = (current_log_time - last_log_time)
                        rate = calculate_rate(sub_oid, 0, sub_time)
                        
                        if rate < 0:
                            if current_log_time > last_log_time:
                                sub_oid = handle_negative_rate(sub_oid, fetched_data[idx].snmp_type)
                                if separator != str(q1):
                                    print(q1, "|", round(sub_oid / sub_time), end="|")
                                    separator = str(q1)
                                else:
                                    print(round(sub_oid / sub_time), end="|")
                            else:
                                print(" System may have been reset ")
                                break
                        else:
                            if separator != str(q1):
                                print(q1, "|", round(rate), end="|")
                                separator = str(q1)
                            else:
                                print(round(rate), end="|")
                    elif fetched_data[idx].snmp_type == 'GAUGE':
                        sub_oid = int(current_data[idx - 1]) - int(previous_data[idx - 1])
                        if separator != str(q1):
                            print(q1, "|", current_data[len(current_data) - 1], "(", sub_oid, ")", end="|")
                            separator = str(q1)
                        else:
                            print(current_data[len(current_data) - 1], "(", sub_oid, ")", end="|")
                    else:
                        if separator != str(q1):
                            print(q1, "|", fetched_data[idx].value, end="|")
                            separator = str(q1)
                        else:
                            print(fetched_data[idx].value, end="|")
                else:
                    print("The system may have been reset ")
                    break

    previous_data = current_data
    last_log_time = current_log_time

if num_samples == -1:
    num = 0
    previous_data = []
    while True:
        q1 = time.time()
        fetch_and_display_data()
        if num != 0:
            print(end="\n")
        function_time = time.time()
        num += 1
        if sampling_interval >= function_time - q1:
            time.sleep((sampling_interval - function_time + q1))
        else:
            max_iter = math.ceil((function_time - q1) / sampling_interval)
            time.sleep(((max_iter * sampling_interval) - function_time + q1))
else:
    previous_data = []
    for num in range(0, num_samples + 1):
        q1 = time.time()
        fetch_and_display_data()
        if num != 0:
            print(end="\n")
        function_time = time.time()
        if sampling_interval >= function_time - q1:
            time.sleep((sampling_interval - function_time + q1))
        else:
            max_iter = math.ceil((function_time - q1) / sampling_interval)
            time.sleep(((max_iter * sampling_interval) - function_time + q1))
