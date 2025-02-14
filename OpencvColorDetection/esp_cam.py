import cv2
import argparse
import requests
import time
from opencv_module.color_detection import process_shapes, determine_dominant_color 


# Creating a single HTTP session
session = requests.Session()

# Argument parser setup
def parse_args():
    parser = argparse.ArgumentParser(description="Control ESP32 camera settings and detect objects.")
    parser.add_argument(
        "--url", 
        type=str, 
        required=True, 
        help="URL of the ESP32 camera, e.g., http://<ip_address>"
    )
    parser.add_argument(
        "--AWB",
        type=bool,
        required=False,
        default=True,
        help="Auto white balance"
    )
    return parser.parse_args()

# OpenCV setup
def initialize_camera(url):
    cam = cv2.VideoCapture(url+ ":81/stream")
    fps = cam.get(cv2.CAP_PROP_FPS)
    print(f"Camera frame rate: {fps} FPS")

    if not cam.isOpened():
        print("Error: Could not open video stream.")
        exit(1)

    return cam

def set_resolution(url: str, index: int = 1, verbose: bool = False):
    try:
        if verbose:
            resolutions = "10: UXGA(1600x1200)\n9: SXGA(1280x1024)\n8: XGA(1024x768)\n7: SVGA(800x600)\n6: VGA(640x480)\n5: CIF(400x296)\n4: QVGA(320x240)\n3: HQVGA(240x176)\n0: QQVGA(160x120)"
            print("Available resolutions:\n{}".format(resolutions))

        if index in [10, 9, 8, 7, 6, 5, 4, 3, 0]:
            session.get(url + "/control?var=framesize&val={}".format(index))
        else:
            print("Wrong index")
    except Exception as e:
        print(f"SET_RESOLUTION: Something went wrong: {e}")

def set_led_state(url: str, val: int = 0):
    try:
        response= session.get(url + "/control?var=led_intensity&val={}".format(val))
        response.raise_for_status()  # Raises HTTPError for bad responses
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")

def set_gpio_state(url: str, pin: int, val: int = 0):
    try:
        response= session.get(url + f"/control?var=gpio_{pin}&val={val}")
        response.raise_for_status()  # Raises HTTPError for bad responses
        print(f"GPIO pin {pin} state updated.")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")

def set_quality(url: str, value: int = 1):
    try:
        if 10 <= value <= 63:
            session.get(url + "/control?var=quality&val={}".format(value))
        else:
            print("Quality value must be between 10 and 63")
    except Exception as e:
        print(f"SET_QUALITY: Something went wrong: {e}")

def set_awb(url: str, awb: int = 1):
    try:
        awb = not awb
        session.get(url + "/control?var=awb&val={}".format(1 if awb else 0))
    except Exception as e:
        print(f"SET_AWB: Something went wrong: {e}")
    return awb

def get_gpio_state(url: str):
    try:
        response = session.get(url + "/gpio_read")
        response.raise_for_status()
        data = response.json()
        return data['gpio_state']
    
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")

def main():
    # Parse arguments
    args = parse_args()
    URL = args.url
    AWB = args.AWB

    # Initialize camera and set initial configurations
    cam = initialize_camera(URL)
    set_resolution(URL, index=9) 
    set_quality(URL, value=10)  
    set_gpio_state(URL, 13, 0) 
    set_gpio_state(URL, 14, 0)
    
    # Initialize flags before the loop
    object_printed = False
    color_printed = False

    while True: 
        key = cv2.waitKey(1)
        if key == ord('5'):
            val = int(input("Select val of led intensity: "))
            set_led_state(URL, val)
            print(f"Led set to {val}")

        elif key == ord('r'):
            idx = int(input("Select resolution index: "))
            set_resolution(URL, index=idx, verbose=True)

        elif key == ord('q'):
            val = int(input("Set quality (10 - 63): "))
            set_quality(URL, value=val)

        elif key == ord('a'):
            AWB = set_awb(URL, AWB)

        elif key == 27:  # ESC key to exit
            break
  
        detected=get_gpio_state(URL)

        if not detected:
            if not object_printed:
                print("No object detected")
                set_led_state(URL, 0)
                set_gpio_state(URL, 13, 0)  
                set_gpio_state(URL, 14, 0)  
                object_printed = True
            color_printed = False
            time.sleep(0.05)
            continue
        else:
            object_printed = False


        set_led_state(URL, 150)
        ret, frame = cam.read()
        if not ret:
            print("Warning: Failed to capture frame. Retrying...")
            time.sleep(0.01) 
            continue

        # for visualization
        #-------------------#
        detected_green = process_shapes(frame, 'Green', (0, 255, 0))
        detected_blue = process_shapes(frame, 'Blue', (255, 0, 0))
        cv2.imshow("ESP32-CAM Stream", frame)
        #-------------------#

        if detected_green or detected_blue:
            
            color_printed = False
            print("Object detected.... Stopping for 2 seconds")
            accumulated_frames = []
            start_time = time.time()

            while time.time() - start_time < 2:
                ret, frame = cam.read()
                if not ret: 
                    continue
                accumulated_frames.append(frame)

            dominant_color = determine_dominant_color(accumulated_frames)

            if dominant_color:
                print(f"Most common color detected: {dominant_color}")
            else:
                if not color_printed:
                    print("No dominant color detected.")
                    color_printed = True    

            if dominant_color == 'Green':
                set_gpio_state(URL, 14, 1)
                set_gpio_state(URL, 13, 0)

            elif dominant_color == 'Blue':
                set_gpio_state(URL, 13, 1)
                set_gpio_state(URL, 14, 0)
            time.sleep(2.0) 
        else:
            if not color_printed:
                print("No color detected")
                color_printed = True
            time.sleep(0.05)
            continue   
         
    set_gpio_state(URL, 13, 0)  
    set_gpio_state(URL, 14, 0)  
    cv2.destroyAllWindows()
    cam.release()

if __name__ == '__main__':
    main()
    