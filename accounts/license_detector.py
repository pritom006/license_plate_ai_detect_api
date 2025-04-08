from ultralytics import YOLO
import cv2
import time
import os
from django.conf import settings
from accounts.models import AIDetectedLicense

class LicensePlateDetector:
    def __init__(self):
        # Use absolute paths based on your project structure
        base_dir = settings.BASE_DIR
        model_path = os.path.join(base_dir, 'best.pt')
        
        # Check if file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
            
        # Print for debugging
        print(f"Loading model from: {model_path}")
        
        # For labels, check if file exists in project root or use hardcoded labels if needed
        labels_path = os.path.join(base_dir, 'labels.txt')
        if os.path.exists(labels_path):
            with open(labels_path, 'r') as file:
                self.class_labels = [line.strip() for line in file.readlines()]
        else:
            # Fallback to digits and letters if file not found
            self.class_labels = [str(i) for i in range(10)] + [chr(i) for i in range(65, 91)]
            print(f"Labels file not found at {labels_path}, using default labels")
        
        # Ensure directories exist
        self.snapshot_dir = os.path.join(base_dir, 'snapshots')
        self.detected_texts_dir = os.path.join(base_dir, 'detected_texts')
        
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
        
        if not os.path.exists(self.detected_texts_dir):
            os.makedirs(self.detected_texts_dir)
            
        # Load the YOLO model
        self.model = YOLO(model_path)
    
    # Rest of your methods remain the same
    def detect_from_camera(self, save_to_db=True):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise Exception("Unable to access the webcam")

        try:
            # Warm-up: Read and discard 10 frames
            for _ in range(10):
                cap.read()
                time.sleep(0.1)  # short delay to allow adjustment

            ret, frame = cap.read()
            if not ret:
                raise Exception("Failed to grab frame")

            license_plate_text = self._process_frame(frame)

            timestamp = int(time.time())
            snapshot_filename = f"license_plate_{timestamp}.jpg"
            snapshot_path = os.path.join(self.snapshot_dir, snapshot_filename)
            cv2.imwrite(snapshot_path, frame)

            text_filename = f"license_plate_{timestamp}.txt"
            text_path = os.path.join(self.detected_texts_dir, text_filename)
            with open(text_path, 'w') as text_file:
                text_file.write(license_plate_text)

            if save_to_db and license_plate_text:
                AIDetectedLicense.objects.create(
                    plate_number=license_plate_text,
                    snapshot_path=snapshot_path
                )

            return license_plate_text, snapshot_path

        finally:
            cap.release()
        
    def detect_from_image(self, image_path, save_to_db=True):
        """
        Detect license plate from an image file
        """
        # Read the image
        frame = cv2.imread(image_path)
        if frame is None:
            raise Exception(f"Could not read image from {image_path}")
        
        # Process the frame and get the text
        license_plate_text = self._process_frame(frame)
        
        # Generate timestamp for filenames
        timestamp = int(time.time())
        
        # Save snapshot (copy of the original)
        snapshot_filename = f"license_plate_{timestamp}.jpg"
        snapshot_path = os.path.join(self.snapshot_dir, snapshot_filename)
        cv2.imwrite(snapshot_path, frame)
        
        # Save text to file
        text_filename = f"license_plate_{timestamp}.txt"
        text_path = os.path.join(self.detected_texts_dir, text_filename)
        with open(text_path, 'w') as text_file:
            text_file.write(license_plate_text)
        
        # Save to database if requested
        if save_to_db and license_plate_text:
            AIDetectedLicense.objects.create(
                plate_number=license_plate_text,
                snapshot_path=snapshot_path
            )
        
        return license_plate_text, snapshot_path
    
    def _process_frame(self, frame):
        """
        Process a single frame to detect license plate text
        """
        # Perform detection
        results = self.model(frame)
        
        # Parse results
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Extract coordinates and class
                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])
                class_id = int(box.cls[0])
                
                # Add to detections list
                detections.append((x_min, self.class_labels[class_id], 
                                  (x_min, y_min, x_max, y_max)))
                
                # Draw bounding box (for visualization in saved image)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        # Sort detections by x-coordinate (left to right)
        sorted_detections = sorted(detections, key=lambda x: x[0])
        
        # Extract license plate text
        license_plate_text = ''.join([digit[1] for digit in sorted_detections])
        
        # Add text overlay to the frame
        cv2.putText(frame, license_plate_text, (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        
        return license_plate_text