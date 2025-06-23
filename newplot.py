import matplotlib.pyplot as plt
import numpy as np
import cv2
import os
from matplotlib_scalebar.scalebar import ScaleBar

def get_image_path():
    while True:
        img_path = input("Enter the path to the image file: ")
        if os.path.exists(img_path):
            return img_path
        else:
            print("Invalid file path. Please try again.")

# input nozzle diameter
try:
    nozzle_diameter = float(input("Enter Nozzle Diameter (μm): "))
except ValueError:
    print("Invalid input. Please enter a new value.")
    exit()

# retrieve image for analyzing
image_path = get_image_path()
img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
if img is None:
    print("Error: Invalid image.")
    exit()

# Create axis and plot
fig, ax = plt.subplots()
ax.imshow(img, cmap="gray")
ax.set_xlabel('x position')
ax.set_ylabel('y position')

ax.set_title(f'Nozzle Diameter: {nozzle_diameter} μm')

# Add scalebar 
microns_per_pixel = nozzle_diameter / img.shape[1]
scalebar = ScaleBar(microns_per_pixel, "um", length_fraction=0.25)
ax.add_artist(scalebar)

# Function to calculate viscosity 
def calculate_viscosity(molecular_weight, K=1.5e-4, a=0.8):
    return K * (molecular_weight ** a)

molecular_weight = float(input("Enter Molecular Weight (g/mol): "))
viscosity = calculate_viscosity(molecular_weight)
formula_text = r"$\eta = K M^a$" + f"\nViscosity: {viscosity:.4f} Pa·s"
ax.text(0.05, 0.95, formula_text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.5))

# Get the two points for the diameter 
print("Please click on the two points for the diameter end points.")

# read in
points = plt.ginput(2)  

if len(points) == 2:
    # Extract the x-coordinates of the two points
    x1, y1 = points[0]
    x2, y2 = points[1]

    # Calculate the diameter by subtracting the x coordinates 
    diameter_pixels = abs(x2 - x1)  

    print(f"Detected Droplet Diameter: {diameter_pixels:.2f} pixels")

    # Plot new line 
    ax.plot([x1, x2], [y1, y2], color='blue', linewidth=2, label=f"Measured Diameter: {diameter_pixels:.2f} pixels")

    ax.annotate(f"{diameter_pixels:.2f} μm", xy=((x1 + x2) / 2, (y1 + y2) / 2),
                xytext=((x1 + x2) / 2, (y1 + y2) / 2 + 10),
                arrowprops=dict(facecolor='blue', arrowstyle='->'), color='blue', ha='center')

# Display the final image plot
plt.legend()
plt.show()
# input material, molecular weight, and pressure used
#frame by frame t1-t3 frames 
#analysize frame by frame
# angle and  angle of adhesion
# for analyzing video 'frame by frame
#plot over time 
# t1- t3 y axis viscocity and anglw of adhesion
# two graphs and detect contour and diameter through time 