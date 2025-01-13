import os
import subprocess
import itertools

# Change this to your own paths
arduino_cli_path = "U:\\Downloads\\ard\\arduino-cli.exe"
project_path = "U:\\Downloads\\2023_Firmware\\Marlin"
config_path = os.path.join(project_path, "Configuration.h")
config_path_temp = os.path.join(project_path, "ConfigurationTemp.h")

build_path = os.path.join(project_path, "build")

# Values to be used for SCARA_offset_x and SCARA_offset_y
#x_values = [0, 6.364, 6.44, 6.516, 8.216, 8.5095, 8.803, 9.916, 10.578, 11.24]
#y_values = [-245.6, -245.3, -245, -243.6, -243.2, -242.85, -242.13, -241.6, -241.1, -240.7]

x_values = [50, -11.875, -22.5]
y_values = [50, 71.875, 37.5]

#offset_values = list(itertools.product(x_values, y_values)) # All combinations of x and y values
offset_values = list(zip(x_values, y_values))  # Just simple pairs of x and y values matched in order.

print(offset_values[0])
id = 0

for i, (x_offset, y_offset) in enumerate(offset_values):
    # Read in the file
    with open(config_path_temp, 'r') as file :
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace('#define SCARA_offset_x 0', f'#define SCARA_offset_x {x_offset}')
    filedata = filedata.replace('#define SCARA_offset_y -242.13', f'#define SCARA_offset_y {y_offset}')
    filedata = filedata.replace('#define MACHINE_UUID "00000000-0000-0000-0000-000000000000"', f'#define MACHINE_UUID "00000000-0000-0000-0000-00000000000{id}"')

    id += 1
    # Write the file out again
    with open(config_path, 'w') as file:
        file.write(filedata)

    # Compile the project
    compile_command = [arduino_cli_path, "compile", "--fqbn", "arduino:avr:mega:cpu=atmega2560", "--build-path", build_path, project_path]
    subprocess.run(compile_command)

    # Change the name of the binary file
    binary_path = os.path.join(build_path, "Marlin.ino.hex")
    new_binary_path = os.path.join(project_path, f"Marlin_thesis{i}.ino.mega.hex")
    os.rename(binary_path, new_binary_path)