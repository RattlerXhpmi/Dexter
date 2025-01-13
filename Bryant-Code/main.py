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

ip_address = "192.168.1.9"
port = 5000
api_key = "C0CB1A0B37E748AFB8B99C84C4B4CF09"

app = FastAPI()

m400_completed_event = threading.Event()
# Configure logging
logging.basicConfig(filename="latency_3_24.log", level=logging.INFO, format='%(asctime)s %(message)s')
Dex1 = PrinterTracker(1)

#def run_send_gcode_command():
  #  time.sleep(2)
  #  for i in range(10):
  #      send_gcode_command(ip_address, port, api_key, "OCTO99")

@app.post("/m400completed")
async def m400_completed():
    logging.info("Received M400 completed event")
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

    # Send the POST request to the OctoPrint API using httpx

    response = httpx.post(url, headers=headers, json=data)
    logging.info(f"Sent {gcode}")
    # Check the response status code and raise an error if necessary
    response.raise_for_status()

    
async def wait_for_m400_completed(loop):
    m400_completed_event.wait()
    
def latency_study():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    run_length = 100
    time.sleep(2)
    with open("experiment_results_3_24.csv", "w", newline="") as csvfile:
        for run in range(1, 11):
            send_gcode_command(ip_address, port, api_key, "G91")  # switch to relative mode
            segments = run
            segment_length = run_length / segments
            send_gcode_command(ip_address, port, api_key, "M400")
            send_gcode_command(ip_address, port, api_key, "OCTO99") 
            loop.run_until_complete(wait_for_m400_completed(loop))
            m400_completed_event.clear()
            for segment in range(segments):
                send_gcode_command(ip_address, port, api_key, f"G1 X{segment_length}")
                send_gcode_command(ip_address, port, api_key, "M400")
                send_gcode_command(ip_address, port, api_key, "OCTO99")
                loop.run_until_complete(wait_for_m400_completed(loop))  # wait for m400completed event
                m400_completed_event.clear()  # reset the event for the next iteration
                send_gcode_command(ip_address, port, api_key, "OCTO99")
                loop.run_until_complete(wait_for_m400_completed(loop))  # wait for m400completed event
                #time.sleep(1)
                m400_completed_event.clear()  # reset the event for the next iteration
            send_gcode_command(ip_address, port, api_key, "G90")  # switch to absolute mode
            send_gcode_command(ip_address, port, api_key, "G1 X0 Y0 Z0")  # move to origin
            send_gcode_command(ip_address, port, api_key, "G91")  # switch to relative mode
           # time.sleep(0.1)
    print("Experiment complete.")
    save_to_csv(Dex1)
    
def save_to_csv(Dex):
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
    with open('pose_data_latency.csv', mode='w') as file:
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