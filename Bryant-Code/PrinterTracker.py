import triad_openvr
import time
import math

class PrinterTracker:
    def __init__(self, tracker_id):
        self.tracker_id = tracker_id
        self.pose_buffer = triad_openvr.pose_sample_buffer()
        self.v = triad_openvr.triad_openvr()
        
    def append_to_matrix(self):
        try:
            pose_mat = self.v.devices[f"tracker_{self.tracker_id}"].get_pose_matrix()
            self.pose_buffer.append(pose_mat, time.time())
        except:
            time.sleep(0.01)
        
    def print_current_pose(self):
        tTxt = 0
        try:
            for each in self.v.devices["tracker_{self.tracker_id}"].get_pose_euler():
                txt += "%.4f" % each
                txt += " "
            tTxt = txt
        except:
            txt = tTxt
        try:    
            print("\\r" + str(txt), end="")
        except:
            print("\\r" + str(tTxt), end="")
            time.sleep(0.01)
            
    def clear_matrix(self):
        self.pose_buffer.x = []
        self.pose_buffer.y = []
        self.pose_buffer.z = []
        self.pose_buffer.yaw = []
        self.pose_buffer.pitch = []
        self.pose_buffer.roll = []
        self.pose_buffer.time = []
        self.pose_buffer.r_x = []
        self.pose_buffer.r_y = []
        self.pose_buffer.r_z = []
        self.pose_buffer.r_w = []

