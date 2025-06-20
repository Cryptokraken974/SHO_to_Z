from PIL import Image, ImageChops

img1_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/PRGL1260C9597_2014/lidar/png_outputs/boosted_hillshade.png"
img2_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/PRGL1260C9597_2014/lidar/png_outputs/boosted_hillshade_stretch_stddev.png"
output_path = "/Users/samuelhoareau/Desktop/VS_Projects/SHO_to_Z/output/PRGL1260C9597_2014/lidar/png_outputs/pixel_diff.png"

try:
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    if img1.mode != img2.mode or img1.size != img2.size:
        print("Images have different modes or sizes and cannot be compared.")
    else:
        diff = ImageChops.difference(img1, img2)
        
        if diff.getbbox():
            diff.save(output_path)
            print(f"Pixel differences found. An image highlighting the differences has been saved to: {output_path}")
        else:
            print("The images are identical.")

except FileNotFoundError as e:
    print(f"Error: {e}. Please check the file paths.")
except Exception as e:
    print(f"An error occurred: {e}")
