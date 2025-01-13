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

poses = v.devices["tracker_1"].get_pose_euler()
origin_pose = poses

print("Recalibrating origin in 5 seconds.")
time.sleep(5)
print("Recalibrated.")

filename = "soltest1.txt"
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
       
    
#fig, ax = plt.subplots()
#fig.subplots_adjust(bottom=0.2)

#class Save:
#    def saveCSV(self, event):
#        print("test")
#        plt.draw()
        
#callback = Save()


if interval:
    

    while(True):
        start = time.time()
        txt = ""
        try:
            for each in v.devices["tracker_2"].get_pose_euler():
                txt += "%.4f" % each
                txt += " "
            print("\r" + txt, end="")
            values = txt.split()
            position = [float(value) for value in values[:3]]
            positionHistory.append(position) #x,z,y,pitch,yaw,roll
            timeHistory.append(time.time())
        
            #if counter % 100000 == 0:
            #np.save(filename, np.array(positionHistory))
        
            plt.clf()
            x = [p[0] for p in positionHistory]
            y = [p[1] for p in positionHistory]
            z = [p[2] for p in positionHistory]
            theta = 0#-30.45 #rotates all coordinates in matrix by this amount
            #New attempt at precise calibration theta = -30.44

            # Define a rotation matrix and a translation vector
            rot_matrix = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
            trans_vector = np.array([0,0])#np.array([-622.91805184, 434.53097522]) #shifts all coordinates by this amount
            #trans_vector = np.array([0, 0]) #shifts all coordinates by this amount
            x_values = np.array(x)
            y_values = np.array(z)
            x_values = x_values*1000
            y_values = y_values*1000
            values = np.stack((x_values, y_values), axis=-1)
            # Rotate and translate the array using the function
            r_values = rotate_array(values, theta, rot_matrix, trans_vector)
            ax = plt.axes()
            x_values = np.array(x)
            y_values = np.array(z)
            x_values = x_values*1000
            x_values = x_values * (-1)
            y_values = y_values*1000
            #ax.scatter(x, z, cmap='viridis')
            ax.scatter(x_values, y_values, cmap='viridis')
            """
            axSaveCSV = fig.add_axes([0.81, 0.05, 0.1, 0.075])
            bnext = Button(axSaveCSV, 'Save CSV')
            bnext.on_clicked(callback.saveCSV)
            """
            plt.draw()
            plt.pause(0.001)
            Dex1.append_to_matrix()
            Dex2.append_to_matrix()

            
            if counter % 50 == 0:
                save_to_csv(Dex1, "output/tracker1_pos4.csv")
                save_to_csv(Dex2, "output/tracker2_pos4.csv")

            print(counter)
            counter += 1
            sleep_time = interval-(time.time()-start)
            if sleep_time > 0:
                time.sleep(sleep_time)

        except:
            print("Tracking failed. Trying again.")
            time.sleep(1)
