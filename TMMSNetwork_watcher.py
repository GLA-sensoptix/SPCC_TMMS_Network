# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 03:26:20 2022

@author: TMMS_User
"""

import sys
import os
import time
import win32gui, win32con

hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(hide, win32con.SW_HIDE)

time.sleep(5)

t0 = time.time()
run_file = os.getcwd()
# process_check_time = 10
# status_check_time = 1
process_1 = 'TMMS Network'
process_2 = 'Select TMMS Network'
# Check run arguments
redundancy = 'secondary'
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if arg == 'primary':
            redundancy = 'primary'
        elif arg == 'secondary':
            redundancy = 'secondary'
lagging = False
if os.path.exists('tmp/time.txt'):
    with open('tmp/time.txt', 'r') as conf:
        TMMS_Network_time = float(conf.read())
        if (t0 - TMMS_Network_time) > 30:
            lagging = True
print('lagging :' + str(lagging))
running = False
stopped = True
PID = None
# Check if software is stopped or not responding
# /fi "imagename eq cmd.exe"
os.system('tasklist /v /fi "imagename eq cmd.exe" /fi "status ne running" /fi "sessionname eq console" /fo "csv" > tmp/tasklist.txt')
with open('tmp/tasklist.txt', 'r') as task_file:
    do_read = True
    for line in task_file.readlines():
        if process_1 in line.split(',')[-1]:
            stopped = False
            PID = line.split(',')[1]
        elif process_2 in line.split(',')[-1]:
            stopped = False
            PID = line.split(',')[1]
# Check if software is running
os.system('tasklist /v /fi "imagename eq cmd.exe" /fi "status eq running" /fi "sessionname eq console" /fo "csv" > tmp/tasklist.txt')
with open('tmp/tasklist.txt', 'r') as task_file:
    do_read = True
    for line in task_file.readlines():
        if process_1 in line.split(',')[-1]:
            running = True
            stopped = False
            PID = line.split(',')[1]
        elif process_2 in line.split(',')[-1]:
            running = True
            stopped = False
            PID = line.split(',')[1]
print(PID)
# Else software is stopped
time_str = time.strftime('[%Y-%m-%d %H-%M-%S] ')
if stopped:
    print(time_str + 'Restarting TMMS Network Software')
    if redundancy == 'primary':
        os.startfile('TMMS_Network-P.bat')
    else:
        os.startfile('TMMS_Network-S.bat')
elif not running or lagging:
    print(time_str + 'Killing TMMS Network Software')
    os.system('taskkill /PID ' + PID)
    print(time_str + 'Restarting TMMS Network Software')
    if redundancy == 'primary':
        os.startfile('TMMS_Network-P.bat')
    else:
        os.startfile('TMMS_Network-S.bat')
else:
    print(time_str + 'TMMS Network Check OK')
    
# TMMS Display watcher
process = 'RTMC Run-time'
running = False
stopped = True
PID = None
# Check if software is stopped or not responding
# /fi "imagename eq cmd.exe"
os.system('tasklist /v /fi "imagename eq RTMC_Run-time.exe" /fi "status ne running" /fi "sessionname eq console" /fo "csv" > tmp/tasklist.txt')
with open('tmp/tasklist.txt', 'r') as task_file:
    do_read = True
    for line in task_file.readlines():
        if process in line.split(',')[-1]:
            stopped = False
            PID = line.split(',')[1]
# Check if software is running
os.system('tasklist /v /fi "imagename eq RTMC_Run-time.exe" /fi "status eq running" /fi "sessionname eq console" /fo "csv" > tmp/tasklist.txt')
with open('tmp/tasklist.txt', 'r') as task_file:
    do_read = True
    for line in task_file.readlines():
        if process in line.split(',')[-1]:
            running = True
            stopped = False
            PID = line.split(',')[1]
print(PID)
# Else software is stopped
time_str = time.strftime('[%Y-%m-%d %H-%M-%S] ')
if stopped:
    print(time_str + 'Restarting TMMS Display Software')
    os.startfile('RTMC\SPCC.rtmc2')
elif not running:
    print(time_str + 'Killing TMMS Display Software')
    os.system('taskkill /PID ' + PID)
    print(time_str + 'Restarting TMMS Display Software')
    os.startfile('RTMC\SPCC.rtmc2')
else:
    print(time_str + 'TMMS Display Check OK')
        
print(time.time() - t0)
             
# class Watcher:
#     def __init__(self):
#         pass

# if __name__ == "__main__":
#     watcher = Watcher()