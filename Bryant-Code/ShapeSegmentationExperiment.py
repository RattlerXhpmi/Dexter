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
import pandas as pd
import write2pyxl

ip_address = "192.168.1.9"
port = 5000
api_key = "C0CB1A0B37E748AFB8B99C84C4B4CF09"



app = FastAPI()

m400_completed_event = threading.Event()
# Configure logging
logging.basicConfig(filename="experiment_log" + ".log", level=logging.INFO, format='%(asctime)s %(message)s')
Dex1 = PrinterTracker(1)
Dex2 = PrinterTracker(2)

#def run_send_gcode_command():
  #  time.sleep(2)
  #  for i in range(10):
  #      send_gcode_command(ip_address, port, api_key, "OCTO99")

@app.post("/m400completed")
async def m400_completed():
    logging.info("Received OCTO99 acknowledgement.")
    print("Tracker position updated.")
    Dex1.print_current_pose()
    Dex1.append_to_matrix()
    m400_completed_event.set()


async def wait_for_m400_completed():
    m400_completed_event.wait()


def send_gcode_command(ip_address, port, api_key, gcode):
    # Build the URL for the OctoPrint API
    url = f"http://{ip_address}:{port}/api/printer/command"

    # Set the headers and data for the POST request
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    data = {"command": f"{gcode}"}

    while True:
        try:
            # Send the POST request to the OctoPrint API using httpx

            response = httpx.post(url, headers=headers, json=data)
            logging.info(f"Sent {gcode}")
            # Check the response status code and raise an error if necessary
    
            response.raise_for_status()
            break
        except httpx.HTTPError as exc:
            time.sleep(10)


def save_to_excel(filename, *Dex_objects):
    def save_data(Dex, sheetname, writer):
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
        
        # Convert the list of tuples to a DataFrame
        df = pd.DataFrame(data, columns=['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'time', 'r_x', 'r_y', 'r_z', 'r_w'])

        # Write the DataFrame to an Excel sheet
        df.to_excel(writer, sheet_name=sheetname, index=False)

    with pd.ExcelWriter(filename) as writer:
        for i, Dex in enumerate(Dex_objects, start=1):
            save_data(Dex, f'Sheet{i}', writer)
        
async def wait_for_m400_completed(loop):
    m400_completed_event.wait()
    
import sys

def run_experiment():
    shapes = ['square', 'circle', 'cross']
    segmentation_factors = [1, 4, 10]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for r in range(1, 10):
        for shape in shapes:
            for i in range(1, 4):
                for seg_factor in segmentation_factors:
                    gcode_file = f'test_{shape}.gcode'
                    bookname = f'output/{shape}{i}_r{r}_seg{seg_factor}.xlsx'
                    i1 = 0

                    with open(gcode_file, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith(('G0', 'G1')):
                                # Extract and modify X coordinate
                                x_match = re.search('X(-?[0-9.]+)', line)
                                if x_match:
                                    original_x = float(x_match.group(1))
                                    new_x = original_x / seg_factor
                                    line = line.replace(f'X{original_x}', f'X{new_x}', 1)

                                # Extract and modify Y coordinate
                                y_match = re.search('Y(-?[0-9.]+)', line)
                                if y_match:
                                    original_y = float(y_match.group(1))
                                    new_y = original_y / seg_factor
                                    line = line.replace(f'Y{original_y}', f'Y{new_y}', 1)
                                    
                                # Send the modified command the number of times equal to segmentation factor
                                for _ in range(seg_factor):
                                    send_gcode_command(ip_address, port, api_key, line)
                                    send_gcode_command(ip_address, port, api_key, "M400")
                                    send_gcode_command(ip_address, port, api_key, "OCTO99")
                                    loop.run_until_complete(wait_for_m400_completed(loop))
                                    m400_completed_event.clear()
                            else:
                                send_gcode_command(ip_address, port, api_key, line)

                            if i1 == 500:
                                save_to_excel(bookname, Dex1, Dex2)
                                i1 = 0

                            i1 += 1

                    print(f"Experiment {shape}{i}_r{r}_seg{seg_factor} complete.")
                    save_to_excel(bookname, Dex1, Dex2)

                    # Prompt user to continue or stop the program
                    answer = input(f"Press 'Enter' to continue to the next experiment or 'q' to quit: ")
                    if answer.strip().lower() == 'q':
                        print("Exiting program.")
                        sys.exit(0)

    print("All experiments complete.")
    
    
     
def start_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=5001)
    
if __name__ == "__main__":
    #t1 = threading.Thread(target=run_send_gcode_command)
    t1 = threading.Thread(target=run_experiment)
    t2 = threading.Thread(target=start_uvicorn)
 
    t1.start()
    t2.start()

    t1.join()
    t2.join()

