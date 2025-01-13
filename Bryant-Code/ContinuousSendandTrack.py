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

filename1 = 'output/cross3_r10_t1.csv'
filename2 = 'output/cross3_r10_t2.csv'
ip_address = "192.168.1.9"
port = 5000
api_key = "C0CB1A0B37E748AFB8B99C84C4B4CF09"

app = FastAPI()

m400_completed_event = threading.Event()

@app.post("/m400completed")
async def m400_completed():
    print("Tracking toggled.")
    #Dex1.print_current_pose()
    #Dex1.append_to_matrix()
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

            start = time.time()
            try: 
                txt1 = ""
                txt2 = ""
                for each in v.devices["tracker_1"].get_pose_euler():
                    txt1 += "%.4f" % each
                    txt1 += " "
                for each in v.devices["tracker_2"].get_pose_euler():
                    txt2 += "%.4f" % each
                    txt2 += " "
                values1 = txt1.split()
                values2 = txt2.split()
                position1 = [float(values1) for values1 in values1[:3]]
                positionHistory1.append(position1) #x,z,y,pitch,yaw,roll
                timeHistory1.append(time.time())
                position2 = [float(values2) for values2 in values2[:3]]
                positionHistory2.append(position2) #x,z,y,pitch,yaw,roll
                timeHistory2.append(time.time())
        
                #if counter % 100000 == 0:
                #np.save(filename, np.array(positionHistory))
        
                #plt.clf()
                x1 = [p[0] for p in positionHistory1]
                y1 = [p[1] for p in positionHistory1]
                z1 = [p[2] for p in positionHistory1]
                x2 = [p[0] for p in positionHistory2]
                y2 = [p[1] for p in positionHistory2]
                z2 = [p[2] for p in positionHistory2]
                theta = 0#-30.45 #rotates all coordinates in matrix by this amount
                #New attempt at precise calibration theta = -30.44

                # Define a rotation matrix and a translation vector
                rot_matrix = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
                trans_vector = np.array([0,0])#np.array([-622.91805184, 434.53097522]) #shifts all coordinates by this amount
                #trans_vector = np.array([0, 0]) #shifts all coordinates by this amount
                x_values1 = np.array(x1)
                y_values1 = np.array(y1)
                x_values1 = x_values1*1000
                x_values1 = x_values1 * (-1)
                y_values1 = y_values1*1000
                x_values2 = np.array(x2)
                y_values2 = np.array(y2)
                x_values2 = x_values2*1000
                x_values2 = x_values2 * (-1)
                y_values2 = y_values2*1000
                values1 = np.stack((x_values1, y_values1), axis=-1)
                values2 = np.stack((x_values2, y_values2), axis=-1)
                # Rotate and translate the array using the function
                r_values1 = rotate_array(values1, theta, rot_matrix, trans_vector)
                r_values2 = rotate_array(values2, theta, rot_matrix, trans_vector)
               # plt.pause(0.001)
                Dex1.append_to_matrix()
                Dex2.append_to_matrix()
            
                if counter % 100 == 0:
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
    
def send_gcode():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    i1 = 0
    # open the gcode file for reading
    with open("test_cross.gcode", "r") as f:
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
            

    print("Experiment complete.")
    save_to_csv(Dex1, filename1)
    save_to_csv(Dex2, filename2)
    sys.exit(1)
    
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