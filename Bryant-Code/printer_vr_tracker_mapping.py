import numpy as np

class VRTracker:
    def __init__(self):
        self.position = np.array([0, 0, 0, 0, 0, 0])
        # other attributes and methods for accessing tracker position

class Printer:
    def __init__(self):
        self.extruder_position = np.array([0, 0, 0])
        self.mapped_coordinates = np.array([0, 0, 0])
        # other attributes and methods for accessing printer and mapped positions
        
        self.transformation_matrix = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ]) # default transformation matrix
        
    def update_mapped_coordinates(self, tracker_position):
        homogenous_tracker_position = np.array([*tracker_position, 1])
        homogenous_mapped_position = self.transformation_matrix @ homogenous_tracker_position
        self.mapped_coordinates = homogenous_mapped_position[:3]

def update_printer_position(printer, tracker):
    # Extract the x, z, y, yaw, pitch, roll components of the tracker pose
    x_t, z_t, y_t, yaw_t, pitch_t, roll_t = tracker.pose()

    # Define the transformation matrix that converts tracker coordinates to extruder coordinates
    # In this case, we apply the translation (x_t, y_t, z_t) followed by the rotations around
    # the x, y, and z axes, in that order.
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(pitch_t), -np.sin(pitch_t)],
                    [0, np.sin(pitch_t), np.cos(pitch_t)]])
    R_y = np.array([[np.cos(roll_t), 0, np.sin(roll_t)],
                    [0, 1, 0],
                    [-np.sin(roll_t), 0, np.cos(roll_t)]])
    R_z = np.array([[np.cos(yaw_t), -np.sin(yaw_t), 0],
                    [np.sin(yaw_t), np.cos(yaw_t), 0],
                    [0, 0, 1]])
    T = np.array([[1, 0, 0, x_t],
                  [0, 1, 0, y_t],
                  [0, 0, 1, z_t],
                  [0, 0, 0, 1]])
    M = np.dot(T, np.dot(R_z, np.dot(R_y, R_x)))

    # Update the mapped_coordinates of the Printer object
    extruder_pos = np.array([printer.x, printer.y, printer.z, 1])
    mapped_pos = np.dot(M, extruder_pos)
    printer.mapped_coordinates = mapped_pos[:3]

