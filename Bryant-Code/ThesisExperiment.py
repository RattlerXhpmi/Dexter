import triad_openvr
import openvr
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import sys
import asyncio
import json
import httpx
import threading
import logging
from fastapi import FastAPI
from PrinterTracker import PrinterTracker
import uvicorn
import time
import csv
import paramiko
import itertools                                    

ip_address = "192.168.1.9"
port = 5000
api_key = "C0CB1A0B37E748AFB8B99C84C4B4CF09"

segment_value = 1
dwell_value = 1
run_number = 0 

app = FastAPI()

m400_completed_event = threading.Event()
# Configure logging
#Change this in between sets
logging.basicConfig(filename="thesis-10-12-2023-05.log", level=logging.INFO, format='%(asctime)s %(message)s')
Dex1 = PrinterTracker(1)
Dex2 = PrinterTracker(2)

@app.post("/m400completed")
async def m400_completed():
    logging.info("Received OCTO99 acknowledgment event")
    print("Tracker position updated.")
    Dex1.print_current_pose()
    Dex1.append_to_matrix()
    Dex2.print_current_pose()
    Dex2.append_to_matrix()
    m400_completed_event.set()


async def wait_for_m400_completed():
    m400_completed_event.wait()


def send_gcode_command(ip_address, port, api_key, gcode):
    # Build the URL for the OctoPrint API
    url = f"http://{ip_address}:{port}/api/printer/command"

    # Set the headers and data for the POST request
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    data = {"command": f"{gcode}"}

    # Send the POST request to the OctoPrint API using httpx

    response = httpx.post(url, headers=headers, json=data)
    logging.info(f"Sent {gcode}")
    # Check the response status code and raise an error if necessary
    response.raise_for_status()

    
async def wait_for_m400_completed(loop):
    m400_completed_event.wait()
    # Update the state for the next run
   
#change # in front of "set" in between sets
def get_filenames():
    filename1 = f'output/set05_r{run_number}_d{dwell_value}_s{segment_value}_t1.csv'
    filename2 = f'output/set05_r{run_number}_d{dwell_value}_s{segment_value}_t2.csv'
    return filename1, filename2

def next_run():
    global run_number, dwell_value, segment_value
    run_number += 1
    dwell_value += 1
    
    if segment_value == 6:
        segment_value = 1
    if dwell_value == 5:
        dwell_value = 1
        segment_value += 1

    
    if run_number == 20:
        print("Experiment complete! Returning to home.")
            # At the end of send_gcode():
            
            #input("Press enter to start the next run...")

            #print_printer_info()
    
def latency_study():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    send_gcode_command(ip_address, port, api_key, "G90")
    send_gcode_command(ip_address, port, api_key, "G28")
    time.sleep(10)
    #send_gcode_command(ip_address, port, api_key, "M106 S200")
    #send_gcode_command(ip_address, port, api_key, "M109 S220")
    send_gcode_command(ip_address, port, api_key, "G0 Z20 F5000")
    #send_gcode_command(ip_address, port, api_key, "G0 X0 Y0 F5000 ") #default origin
    send_gcode_command(ip_address, port, api_key, "G0 X-6.4303 Y18.3489 F600")
    #send_gcode_command(ip_address, port, api_key, "M400")
    #send_gcode_command(ip_address, port, api_key, "OCTO99") 
    #loop.run_until_complete(wait_for_m400_completed(loop))
    #m400_completed_event.clear()
    #Alt Run 1 dy 50 #first run of this had to be redone; it is also run 3 (add one to run 3 onwards)
    #send_gcode_command(ip_address, port, api_key, "G0 X0 Y25 F600")
    #send_gcode_command(ip_address, port, api_key, "G0 X0 Y75 F600 E3.9")
    #Alt Run 2 Dx 50
    #send_gcode_command(ip_address, port, api_key, "G0 X25 Y0 F600")
    #send_gcode_command(ip_address, port, api_key, "G0 X75 Y0 F600 E3.9")
    #Alt Run 3 dx 35.3554 dy 35.3554
    #send_gcode_command(ip_address, port, api_key, "G0 X32.3223 Y32.3223 F600")
    #send_gcode_command(ip_address, port, api_key, "G0 X67.6777 Y67.6777 F600 E3.9")
    #Alt Run 4 dx 49.9696 dy 1.745
    #send_gcode_command(ip_address, port, api_key, "G0 X-36.8598 Y71.0025 F600")
    #send_gcode_command(ip_address, port, api_key, "G0 X13.1098 Y72.7475 F600 E3.9")
    #Alt Run 5 dx -32.1394 dy 38.3022
    #send_gcode_command(ip_address, port, api_key, "G0 X-6.4303 Y18.3489 F600")
    #send_gcode_command(ip_address, port, api_key, "G0 X-38.5697 Y56.6511 F600 E3.9")
    
    #send_gcode_command(ip_address, port, api_key, "G0 X-6.4303 Y18.3489 F5000")#starting pos
    #send_gcode_command(ip_address, port, api_key, "G0 Z16.6 F5000")
    send_gcode_command(ip_address, port, api_key, "G0 Z17 F5000")
    
    pause_times = [0.01, 0.1, 1, 10]
    run_length = 50
    time.sleep(20)
    #segment = 1

    with open("experiment-results10-18-23.csv", "w", newline="") as csvfile:
        for run in range(1, 6):
            send_gcode_command(ip_address, port, api_key, "G91")  # switch to relative mode
            segments = run
            segment_length = run_length / segments
            send_gcode_command(ip_address, port, api_key, "M106 S200")
           # send_gcode_command(ip_address, port, api_key, "M109 S220") #set temp

            for pause_time in pause_times:
                print("Run " + str(run_number) + " Segment Length " + str(segment_length) + " Pause Time " + str(pause_time))
                #print("Run " + str(run_number) + " Segment Length " + str(segment_length) + " Pause Time " + str(pause_time) + " Firmware Value " + str(firmware_number-1))
                send_gcode_command(ip_address, port, api_key, "M400")
                send_gcode_command(ip_address, port, api_key, "OCTO99") 
                loop.run_until_complete(wait_for_m400_completed(loop))
                m400_completed_event.clear()
                for segment in range(segments):
                    send_gcode_command(ip_address, port, api_key, f"G1 X{-32.1394/(segments)} Y{38.3022/(segments)} F600")
                    #send_gcode_command(ip_address, port, api_key, f"G1 X{DX/(segments)} Y{DY/(segments)} E{segment_length/3} F600") #old value
                    
                    #send_gcode_command(ip_address, port, api_key, f"G0 X{-32.1394/(segments)} Y{38.3022/(segments)} F600")
                    send_gcode_command(ip_address, port, api_key, "M400")
                    send_gcode_command(ip_address, port, api_key, "OCTO99")
                    loop.run_until_complete(wait_for_m400_completed(loop))  # wait for m400completed event
                    m400_completed_event.clear()  # reset the event for the next iteration
                    time.sleep(pause_time)
                        #send_gcode_command(ip_address, port, api_key, "OCTO99")
                        #loop.run_until_complete(wait_for_m400_completed(loop))  # wait for m400completed event
                        #time.sleep(1)
                        #m400_completed_event.clear()  # reset the event for the next iteration
                        #time.sleep(pause_time)
                send_gcode_command(ip_address, port, api_key, "G90")  # switch to absolute mode
                send_gcode_command(ip_address, port, api_key, "G0 Z30 F600")  # move to origin
                send_gcode_command(ip_address, port, api_key, "G0 X-6.4303 Y18.3489 F600")
                #send_gcode_command(ip_address, port, api_key, "G0 X-6.4303 Y18.3489 F600")  # move to next starting pos
                send_gcode_command(ip_address, port, api_key, "G0 Z17 F600") 
                #send_gcode_command(ip_address, port, api_key, "G0 Z31.7 F600")  # move to origin
                send_gcode_command(ip_address, port, api_key, "G91")  # switch to relative mode
                print("Run complete. Pausing for 15 seconds.")
                filename1, filename2= get_filenames()
                save_to_csv(Dex1, filename1)
                save_to_csv(Dex2, filename2)
                Dex1.clear_matrix()
                Dex2.clear_matrix()    
                next_run()
                
                time.sleep(20) #Pause in between runs
               # time.sleep(0.1)
    send_gcode_command(ip_address, port, api_key, "G90")            
    print("Experiment complete.")
    send_gcode_command(ip_address, port, api_key, "G0 Z25")
    send_gcode_command(ip_address, port, api_key, "G28 X Y")
    time.sleep(5)
    sys.exit()

def save_to_csv(Dex, filename):  
    # Get the lists from the pose_buffer object
    pose_buffer = Dex.pose_buffer
    x = pose_buffer.x
    y = pose_buffer.y
    z = pose_buffer.z
    yaw = pose_buffer.yaw
    pitch = pose_buffer.pitch
    roll = pose_buffer.roll
    time = pose_buffer.time
    r_x = pose_buffer.r_x
    r_y = pose_buffer.r_y
    r_z = pose_buffer.r_z
    r_w = pose_buffer.r_w
    
    # Create a list of tuples containing the data to be saved
    data = list(zip(x, y, z, yaw, pitch, roll, time, r_x, r_y, r_z, r_w))
    
    # Write the data to a CSV file
    with open(filename, mode='w') as file:
        writer = csv.writer(file)
        writer.writerow(['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'time', 'r_x', 'r_y', 'r_z', 'r_w'])
        writer.writerows(data)
        
def start_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=5001)
    
if __name__ == "__main__":
    #t1 = threading.Thread(target=run_send_gcode_command)
    t1 = threading.Thread(target=latency_study)
    t2 = threading.Thread(target=start_uvicorn)
 
    t1.start()
    t2.start()

    t1.join()
    t2.join()
    #