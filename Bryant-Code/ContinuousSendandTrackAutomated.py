from re import T
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
import csv
import paramiko
import itertools


ip_address = "192.168.1.9"
port = 5000
api_key = "C0CB1A0B37E748AFB8B99C84C4B4CF09"

shapes = ["square", "circle", "cross"]
shape_idx = 0
run_number = 44     
replicant_number = 1

x_values = [0, 6.364, 6.44, 6.516, 8.216, 8.5095, 8.803, 9.916, 10.578, 11.24]
y_values = [-245.6, -245.3, -245, -243.6, -243.2, -242.85, -242.13, -241.6, -241.1, -240.7]
offset_values = list(itertools.product(x_values, y_values)) # All combinations of x and y values

app = FastAPI()

m400_completed_event = threading.Event()
tracking = False

@app.post("/m400completed")
async def m400_completed():
    global tracking
    print("Tracking toggled.")
    tracking = not tracking

    if m400_completed_event.is_set():
        m400_completed_event.clear()
    else:
        m400_completed_event.set()

async def wait_for_m400_completed():
    m400_completed_event.wait()

def send_gcode_command(ip_address, port, api_key, gcode):
    # Build the URL for the OctoPrint API
    url = f"http://{ip_address}:{port}/api/printer/command"

    # Set the headers and data for the POST request
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    data = {"command": f"{gcode}"}
    print("Sending: " + str(data))
    while True:
        try:
            # Send the POST request to the OctoPrint API using httpx

            response = httpx.post(url, headers=headers, json=data)
            #logging.info(f"Sent {gcode}")
            # Check the response status code and raise an error if necessary
    
            response.raise_for_status()
            break
        except httpx.HTTPError as exc:
            time.sleep(10)
            
def rotate_array(arr, theta, rot_matrix, trans_vector):
    """
    Rotate an ndarray by a given angle and rotation matrix, and translate it by a given vector.

    Parameters:
    arr (numpy.ndarray): Input ndarray.
    theta (float): Rotation angle in radians.
    rot_matrix (numpy.ndarray): 2x2 rotation matrix.
    trans_vector (numpy.ndarray): 2x1 translation vector.

    Returns:
    numpy.ndarray: Rotated and translated ndarray.
    """
    # Construct the full 3x3 transformation matrix
    theta = np.radians(theta)
    transform_matrix = np.zeros((3, 3))
    transform_matrix[:2, :2] = rot_matrix
    transform_matrix[:2, 2] = trans_vector
    transform_matrix[2, 2] = 1

    # Add a column of ones to the array for homogeneous coordinates
    homog_arr = np.hstack([arr, np.ones((arr.shape[0], 1))])

    # Apply the transformation to the array
    transformed_arr = np.dot(homog_arr, transform_matrix.T)[:, :2]

    return transformed_arr

#recalibrate origin
Dex1 = PrinterTracker(1)
Dex2 = PrinterTracker(2)
v = triad_openvr.triad_openvr()
v.print_discovered_objects()

#poses = v.devices["tracker_1"].get_pose_euler()
#origin_pose = poses

#print("Recalibrating origin in 5 seconds.")
#time.sleep(5)
print("Program start...")

counter = 1
timeHistory = []
positionHistory = []

if len(sys.argv) == 1:
    interval = 1/10
elif len(sys.argv) == 2:
    interval = 1/float(sys.argv[1])
else:
    print("Invalid number of arguments")
    interval = False
   
    
def get_filenames():
    shape = shapes[shape_idx]
    filename1 = f'output/{offset_values[run_number-1]}_{shape}{replicant_number}_r{run_number}_t1.csv'
    filename2 = f'output/{offset_values[run_number-1]}_{shape}{replicant_number}_r{run_number}_t2.csv'
    gcode_file = f'test_{shape}.gcode'
    return filename1, filename2, gcode_file

# Update the state for the next run
def next_run():
    global shape_idx, run_number, replicant_number
    replicant_number += 1
    if replicant_number > 3:
        replicant_number = 1
        shape_idx += 1
        if shape_idx >= len(shapes):
            if run_number == 100:
                print("Finished!")
                sys.exit()
            # At the end of send_gcode():
            
            #input("Press enter to start the next run...")
            shape_idx = 0
            run_number += 1
            flash_firmware()
            send_gcode_command(ip_address, port, api_key, "M115")
            time.sleep(1)
            #print_printer_info()
    
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

def track_continuously():
    global tracking
    positionHistory1 = []
    positionHistory2 = []
    timeHistory1 = []
    timeHistory2 = []
    counter = 0
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(wait_for_m400_completed(loop))
    print("Tracking starting...")

    if interval:
        while(True):
            if not tracking:
                time.sleep(0.1)  # Sleep a bit to prevent busy-waiting
                continue

            start = time.time()
            try: 
                Dex1.append_to_matrix()
                Dex2.append_to_matrix()
            
                if counter % 100 == 0:
                    filename1, filename2, gcode_file = get_filenames()
                    save_to_csv(Dex1, filename1)
                    save_to_csv(Dex2, filename2)
                
                print(counter)
                counter += 1
                sleep_time = interval-(time.time()-start)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            except:
                print("Tracking failed. Trying again.")
                time.sleep(1)

async def wait_for_m400_completed(loop):
    m400_completed_event.wait()

def get_printer_info(ip_address, port, api_key):
    url = f"http://{ip_address}:{port}/api/connection"
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    response = httpx.get(url, headers=headers)
    response_data = response.json()
    return response_data

# Add this function to send the 'M115' command and print the results
def print_printer_info():
    while True:
        print("Printing Printer Info:")
        response = get_printer_info(ip_address, port, api_key)
        print(response)
        print("-" * 50)
        time.sleep(30)  # Adjust the sleep time as needed
    
def flash_firmware():

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Add host key automatically
    ssh.connect("192.168.1.9", username="pi", password="raspberry")
    sftp = ssh.open_sftp()
    print(f'firmware/Marlin_{run_number - 1}.ino.mega.hex')
    sftp.put(f'firmware/Marlin_{run_number - 1}.ino.mega.hex', f'/home/pi/firmware/Marlin_{run_number - 1}.ino.mega.hex') # Transfer file
    
    time.sleep(1)
    sftp.close()
    stdin, stdout, stderr = ssh.exec_command('sudo systemctl stop octoprint')
    time.sleep(1)
    stdin, stdout, stderr = ssh.exec_command(f'avrdude -p atmega2560 -c wiring -P /dev/ttyACM0 -b 115200 -D -U flash:w:/home/pi/firmware/Marlin_{run_number - 1}.ino.mega.hex:i')  # Flash Arduino
    time.sleep(30)
    print(stdout.read().decode())
    print(stderr.read().decode())
    stdin, stdout, stderr = ssh.exec_command('sudo systemctl start octoprint')
    time.sleep(50)
    ssh.close()
    time.sleep(1)

def send_gcode():
    while(True):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        i1 = 0
        # open the gcode file for reading
        filename1, filename2, gcode_file = get_filenames()
        with open(gcode_file, "r") as f:
            # iterate over the lines in the file
            for line in f:
                # strip any newline characters from the line
                line = line.strip()
                # send the gcode command to the Octoprint server
                send_gcode_command(ip_address, port, api_key, line)
                if "OCTO99" in line:
                    if m400_completed_event.is_set():
                        m400_completed_event.clear()
                    loop.run_until_complete(wait_for_m400_completed(loop))
                i1 += 1

        next_run()
        
        

        
        save_to_csv(Dex1, filename1)
        save_to_csv(Dex2, filename2)
        Dex1.clear_matrix()
        Dex2.clear_matrix()
        print("Experiment complete.")

    
def start_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=5001)
    
if __name__ == "__main__":
    #t1 = threading.Thread(target=run_send_gcode_command)
    t1 = threading.Thread(target=track_continuously)
    t2 = threading.Thread(target=start_uvicorn)
    t3 = threading.Thread(target=send_gcode)
    t1.start()
    t2.start()
    t3.start()
    
    t1.join()
    t2.join()
    t3.join()




