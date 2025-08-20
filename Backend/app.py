import cv2
from ultralytics import YOLO
from flask import Flask, Response, send_from_directory
import traceback

# --- Configuration ---
VIDEO_PATH = 0  # Use 0 for webcam, or provide a path like 'my_video.mp4'
MODEL_PATH = './yolov8n.pt'  # UPDATE with your custom model path.

# --- Initialize Flask app ---
app = Flask(__name__)

# --- Load YOLO model ---
try:
    model = YOLO(MODEL_PATH)
    print("✅ YOLO model loaded successfully!")
    print(f"📋 Available classes: {list(model.names.values())}")
except Exception as e:
    print(f"❌ Error loading YOLO model: {e}")
    traceback.print_exc()
    model = None

def generate_frames():
    print("🚀 Starting generate_frames...")
    
    if model is None:
        print("❌ Model is None, cannot generate frames")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"❌ Cannot open camera at {VIDEO_PATH}")
        return
    
    print("📹 Camera opened successfully!")
    
    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break

            frame_count += 1

            try:
                # Run YOLO detection
                results = model.predict(frame, conf=0.05, verbose=False)  # Even lower confidence
                
                # Debug: Check if we have results
                if results and len(results) > 0:
                    result = results[0]
                    
                    if result.boxes is not None and len(result.boxes) > 0:
                        if frame_count % 30 == 1:  # Print every 30 frames
                            print(f"🎯 Frame {frame_count}: Found {len(result.boxes)} detections")
                            for i, box in enumerate(result.boxes):
                                cls_id = int(box.cls[0])
                                conf = float(box.conf)
                                class_name = model.names[cls_id]
                                print(f"  Detection {i+1}: {class_name} ({conf:.3f})")
                    else:
                        if frame_count % 60 == 1:  # Print every 60 frames when no detections
                            print(f"📝 Frame {frame_count}: No detections (try pointing at person, phone, bottle, etc.)")
                    
                    # Use YOLO's built-in plotting
                    annotated_frame = result.plot()
                    annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
                else:
                    print(f"❌ No results from model prediction")
                    annotated_frame = frame

            except Exception as e:
                print(f"❌ Error during detection: {e}")
                annotated_frame = frame

            # Encode and yield frame
            try:
                (flag, encodedImage) = cv2.imencode(".jpg", annotated_frame)
                if flag:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' +
                           bytearray(encodedImage) + b'\r\n')
                else:
                    print("❌ Failed to encode frame")
            except Exception as e:
                print(f"❌ Error encoding frame: {e}")
                
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
        traceback.print_exc()
    finally:
        print("🧹 Cleaning up camera resources...")
        cap.release()

@app.route('/')
def index():
    print("📄 Serving index.html")
    return send_from_directory("../Frontend/static", "index.html")

@app.route('/video_feed')
def video_feed():
    print("📺 Video feed requested")
    """The main endpoint that streams the video feed."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("🚀 Starting Flask app on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
