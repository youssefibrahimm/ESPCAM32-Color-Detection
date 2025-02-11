import numpy as np
import cv2
import time

# color_bounds = {
#     'Green': {'lower': np.array([57, 64, 55]), 'upper': np.array([77, 255, 255])},
#     'Blue': {'lower': np.array([100, 150, 0], np.uint8), 'upper': np.array([140, 255, 255], np.uint8)}
# }

color_bounds = {
    'Green': {'lower': np.array([40, 100, 50]), 'upper': np.array([80, 255, 255])},
    'Blue': {'lower': np.array([90, 150, 50]), 'upper': np.array([120, 255, 255])}
}
def preprocess_image(img, color):
    """Preprocesses the image to detect edges within the color range."""
    lower_color = color_bounds[color]['lower']
    upper_color = color_bounds[color]['upper']
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) 
    blur = cv2.GaussianBlur(mask, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    confidence = (np.sum(mask > 0) / mask.size) * 100  # Calculate confidence as percentage
    return edges, min(confidence, 100.0)

def filter_contours(contours, min_area=500, max_area=20000, min_perimeter=100, max_perimeter=10000):

    filtered = []
    for c in contours:
        area = cv2.contourArea(c)
        perimeter = cv2.arcLength(c, True)
        if min_area <= area <= max_area and min_perimeter <= perimeter <= max_perimeter:
            approx = cv2.approxPolyDP(c, 0.02 * perimeter, True)
            if len(approx) >= 3:
                filtered.append((c, approx, area, perimeter))
    return filtered

def classify_shape(approx, area, perimeter):

    obj_corner = len(approx)
    if obj_corner == 3:
        return 'Triangle'
    elif obj_corner == 4:
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / h
        return 'Square' if 0.95 < aspect_ratio < 1.05 else 'Rectangle'
    elif obj_corner > 4:
        circularity = 4 * np.pi * (area / (perimeter ** 2))
        return 'Circle' if 0.8 <= circularity <= 1.2 else 'Polygon'
    return "None"

def process_shapes(frame, color, color_code):

    edges, confidence = preprocess_image(frame, color)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    filtered = filter_contours(contours)
    
    # This is just for visualization and identification of the masked shape
    for c, approx, area, perimeter in filtered:
        shape_type = classify_shape(approx, area, perimeter)
        x, y, w, h = cv2.boundingRect(approx)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color_code, 2)
        cv2.drawContours(frame, [c], -1, color_code, 2)
        cv2.putText(frame, f"{shape_type} (Conf: {confidence:.2f}%)", (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_code, 2)
    return bool(filtered)

def determine_dominant_color(accumulated_frames):
    color_votes = {'Green': 0, 'Blue': 0}

    for frame in accumulated_frames:
        for color in color_bounds:
            _, confidence = preprocess_image(frame, color)  # Use preprocessing function
            color_votes[color] += confidence  # Sum confidence values

    return max(color_votes, key=color_votes.get) if max(color_votes.values()) > 0 else None



def main():
    cam = cv2.VideoCapture(0)

    while True:
        ret, frame = cam.read()
        key = cv2.waitKey(1)

        if not ret:
            continue
        process_shapes(frame, 'Blue', (255, 0, 0))
        process_shapes(frame, 'Green', (0, 255, 0))
        cv2.imshow('frame', frame)
        if key == ord('1'):
            print('starting color detection')
            _, frame = cam.read()
            detected_green = process_shapes(frame, 'Green', (0, 255, 0))
            detected_blue = process_shapes(frame, 'Blue', (255, 0, 0))

            if detected_green or detected_blue:
                print("Stopping conveyor belt for 5 seconds...")
                # time.sleep(5)  # Simulated stop

                accumulated_frames = []
                start_time = time.time()
                while time.time() - start_time < 5:
                    _, frame = cam.read()
                    accumulated_frames.append(frame)

                dominant_color = determine_dominant_color(accumulated_frames)
                print(f"Most common color detected: {dominant_color}" if dominant_color else "No dominant color detected.")

        elif key == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
