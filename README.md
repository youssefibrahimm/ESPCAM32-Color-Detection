# **ESPCAM32-Color-Detection**  

This repository contains code for an **ESP-CAM32-based color detection system** integrated into a **production line**. The system detects specific colors in objects using an **ESP-CAM32** and **OpenCV**, then triggers corresponding **GPIO pins** to control a **robot arm** for sorting.  

## **Repository Structure**  

```
├── .gitignore
├── EspCamWebServer
    ├── CameraWebServer
        ├── CameraWebServer.ino
        ├── app_httpd.cpp
        ├── camera_index.h
        ├── camera_pins.h
        ├── ci.json
        └── partitions.csv
├── OpencvColorDetection
    ├── esp_cam.py
    └── opencv_module
    │   ├── __init__.py
    │   └── color_detection.py
└── README.md
```

---

## **How It Works**  

1. **ESP-CAM32 Setup**  
   - The ESP-CAM32 runs a **modified web server** that streams video frames.  
   - A **new URI handler** allows retrieving GPIO states.  
   - The **command handler** can set specific GPIO pins **HIGH**.  

2. **Color Detection on Laptop**  
   - The laptop **fetches frames** from the ESP-CAM32 web server.  
   - **OpenCV processes the frames** to detect colors.  
   - If an object is **blue or green**, the system sends a command back to the ESP-CAM32, setting a **corresponding GPIO pin HIGH**.  
   - The **robot arm sorts objects** based on the pin state.  

---

## **Installation & Setup**  

### **ESP-CAM32 Setup**  

1. Install **Arduino IDE** and add the ESP32 board support package.  
2. Connect the ESP-CAM32 and **flash the code** inside `EspCamWebServer/CameraWebServer.ino`.  
3. Change the Access Point's **SSID & Password** inside the Arduino code to your liking.  
4. After flashing, the ESP-CAM32 will start streaming video and listen for GPIO commands.  

### **Laptop Setup (Color Detection)**  

1. Install **Python 3** and required dependencies:  

   ```bash
   pip install opencv-python numpy requests
   ```

2. Run the **color detection script**:  

   ```bash
   python OpencvColorDetection/esp_cam.py --esp_url "http://<ESP-IP>"
   ```

3. The script will:  
   - Fetch frames from the ESP-CAM32.  
   - Detect blue/green objects.  
   - Send a command to the ESP-CAM32 to set a **specific GPIO pin HIGH** when a color is detected.  

---

## **Adding More Colors**  

You can **add new colors** by modifying the dictionary inside `color_detection.py`.  

### **Steps to Add a New Color**  

1. Open `OpencvColorDetection/opencv_module/detect_color.py`.  
2. Locate the dictionary that stores HSV ranges, which looks like this:  

   ```python
   color_bounds = {
    'Green': {'lower': np.array([40, 100, 50]), 'upper': np.array([80, 255, 255])},
    'Blue': {'lower': np.array([90, 150, 50]), 'upper': np.array([120, 255, 255])}
    }
   ```

3. Add a new color by inserting another key-value pair. Example for red:  

   ```python
    color_bounds['Red'] = {'lower': np.array([0, 100, 100]), 'upper': np.array([10, 255, 255])}
   ```

4. Save the file and restart the detection script.  

---

## **Future Improvements**  

- Optimize **frame processing speed** for real-time performance.  
- Implement a **fail-safe** to prevent false detections.  
- Expand to support **more colors** dynamically.  
