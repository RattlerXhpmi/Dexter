import asyncio
import datetime
import websockets
import uuid
import tracemalloc
import json
import tkinter as tk


async def read_output(textbox, websocket):
    while True:
        response = await websocket.recv()
        textbox.insert(tk.END, response + '\n')

async def extend_ping_timeout(websocket, timeout):
    message = {'action': 'extendPing', 'timeout': timeout}
    await websocket.send(json.dumps(message))

def send_command(entry, websocket):
    command = entry.get()
    message = {'action': 'send', 'data': command}
    websocket.send(json.dumps(message))

async def initialize_window():
    root = tk.Tk()
    root.title('Dexter Output')
    output_box = tk.Text(root, height=20, width=50)
    output_box.pack(side=tk.TOP)
    command_entry = tk.Entry(root)
    command_entry.pack(side=tk.TOP)
    return root, output_box, command_entry

async def open_websocket(root, output_box, command_entry):
    async with websockets.connect('ws://192.168.1.9:3344/socket/?apikey=16be457f-87d9-4120-8149-c5bb7fad5183') as websocket:
        while True:
            await extend_ping_timeout(websocket, 10) # Extend the ping timeout to 10 seconds
            response = await websocket.recv()
            output_box.insert(tk.END, response + '\n')
            await extend_ping_timeout(websocket, 0) # Set the ping timeout back to default

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    root, output_box, command_entry = loop.run_until_complete(initialize_window())
    websocket_task = asyncio.ensure_future(open_websocket(root, output_box, command_entry))
    loop.run_until_complete(read_output(output_box, websocket_task.result()))
    root.mainloop()

    root.mainloop()







#async def ping(websocket):
#    while True:
#        await websocket.send('ping')
#        await asyncio.sleep(3)

#async def send_gcode(websocket, gcode):
#    callback_id = str(uuid.uuid4())
#    message = {'action': 'send', 'data': gcode, 'callback': callback_id}
#    await websocket.send(json.dumps(message))
#    sent_time = datetime.datetime.now()
#    print(f'Sent at: {sent_time}, callback_id: {callback_id}')

#    while True:
#        response = await websocket.recv()
#        received_time = datetime.datetime.now()
#        print(f'Received at: {received_time}, callback_id: {callback_id}, response: {response}')

#        response_dict = json.loads(response)
#        if 'callback' in response_dict and response_dict['callback'] == callback_id:
#            if 'ok' in response_dict['result']:
#                executed_time = datetime.datetime.now()
#                print(f'Executed at: {executed_time}, callback_id: {callback_id}')
#                return executed_time
#            else:
#                raise Exception(f'Error executing GCODE {gcode}, callback_id: {callback_id}, response: {response}')



#def connect_to_websocket():
#    return websockets.connect('ws://192.168.1.9:3344/socket/?apikey=16be457f-87d9-4120-8149-c5bb7fad5183')

#async def connect_to_dexter():
#    async with websockets.connect('ws://192.168.1.9:3344/socket/?apikey=16be457f-87d9-4120-8149-c5bb7fad5183') as websocket:
#        ping_task = asyncio.create_task(ping(websocket))

#        await send_gcode(websocket, 'G1 X0 Y0 Z0')
#        await send_gcode(websocket, 'G1 X10 Y10 Z1')
#        await send_gcode(websocket, 'G1 X20 Y20 Z2')
#        await send_gcode(websocket, 'G1 X10 Y10 Z1')
#        await send_gcode(websocket, 'G1 X0 Y0 Z0')

#        ping_task.cancel()

#tracemalloc.start()
#asyncio.run(connect_to_dexter())
