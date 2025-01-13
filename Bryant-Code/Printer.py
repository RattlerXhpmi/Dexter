import numpy as np

class Tracker:
    def __init__(self):
        self.history = []
        
    def update_pose(self, x, y, z, yaw, pitch, roll):
        self.history.append([x, z, y, yaw, pitch, roll])

    def get_history(self):
        return self.history

class Printer:
    def __init__(self):
        self.extruder_history = []
        self.trackers = []
        self.mapped_history = []

    def update_extruder_position(self, x, y, z):
        self.extruder_history.append([x, y, z])

    def add_tracker(self):
        self.trackers.append(Tracker())
        return self.trackers[-1]

    def get_extruder_history(self):
        return self.extruder_history
    
    def updated_mapped_location(self, extruder_pos, tracker_pos):
        extruder_pos = np.array(extruder_pos)
        tracker_pos = np.array(tracker_pos[:3])  # Only use the first three elements (x, y, z)

        # Define transformation matrix to project tracker coordinates onto the same plane as the extruder
        normal = np.array([0, 0, 1])  # z-axis
        d = -extruder_pos.dot(normal)
        T = np.eye(4)
        T[3, :3] = -d * normal
        T[:3, 3] = extruder_pos

        # Apply transformation to tracker coordinates
        tracker_pos_homogeneous = np.concatenate([tracker_pos, np.ones((1, 1))], axis=1)
        mapped_pos_homogeneous = (T @ tracker_pos_homogeneous.T).T
        mapped_pos = mapped_pos_homogeneous[:, :3]

        self.mapped_history.append(mapped_pos.tolist())
        return mapped_pos.tolist()

