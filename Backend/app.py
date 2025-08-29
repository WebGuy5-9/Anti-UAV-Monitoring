import cv2
from ultralytics import YOLO
from flask import Flask, Response, render_template, request, jsonify
import traceback

# Import the uploaded video blueprint
from uploaded_video import uploaded_video_bp

# --- Configuration ---
VIDEO_PATH = 0  # webcam
MODEL_PATH = './drone_detection.pt'
CONFIDENCE_THRESHOLD = 0.5  # default confidence

# --- Initialize Flask app ---
app = Flask(__name__,
            template_folder="./Frontend/templates",
            static_folder="./Frontend/static")

# --- Load YOLO model ---
try:
    model = YOLO(MODEL_PATH)
    print("✅ YOLO model loaded successfully!")
    print(f"📋 Available classes: {list(model.names.values())}")
except Exception as e:
    print(f"❌ Error loading YOLO model: {e}")
    traceback.print_exc()
    model = None

# --- Global camera instance (opened once) ---
camera = cv2.VideoCapture(VIDEO_PATH)
if not camera.isOpened():
    print(f"❌ Cannot open camera at {VIDEO_PATH}")
else:
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    print("📹 Camera opened successfully!")


def generate_frames():
    """Generator that captures frames, runs YOLO, and streams MJPEG"""
    global CONFIDENCE_THRESHOLD

    if model is None or not camera.isOpened():
        print("❌ No model or camera unavailable")
        return

    while True:
        ret, frame = camera.read()
        if not ret:
            print("❌ Failed to read frame from camera")
            break

        try:
            # Run YOLO detection
            results = model.predict(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

            if results and len(results) > 0:
                result = results[0]
                annotated_frame = result.plot()  # already BGR
            else:
                annotated_frame = frame
        except Exception as e:
            print(f"❌ Error during detection: {e}")
            annotated_frame = frame

        try:
            # Encode frame as JPEG
            flag, encodedImage = cv2.imencode(".jpg", annotated_frame)
            if flag:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       bytearray(encodedImage) + b'\r\n')
        except Exception as e:
            print(f"❌ Error encoding frame: {e}")

# def get_detections_info(results):
#     detections = []
#     if not results or len(results) == 0:
#         return detections

#     boxes = results[0].boxes  # Access detections in first result
#     for i, box in enumerate(boxes):
#         conf = box.conf.item()  # confidence as float
#         detections.append({
#             "id": i + 1,        # Simple numeric ID
#             "confidence": conf  # Confidence score
#         })
#     return detections



# --- Routes ---
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/update_confidence', methods=['POST'])
def update_confidence():
    global CONFIDENCE_THRESHOLD
    data = request.get_json()
    new_conf = data.get('confidence')

    if new_conf is not None:
        try:
            CONFIDENCE_THRESHOLD = float(new_conf)
            uploaded_video_bp.confidence_threshold = CONFIDENCE_THRESHOLD
            print(f"⚙️ Updated confidence to {CONFIDENCE_THRESHOLD}")
            return jsonify({"status": "success", "confidence": CONFIDENCE_THRESHOLD})
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid confidence"}), 400
    
    return jsonify({"status": "error", "message": "confidence not provided"}), 400  

# @app.route('/detections_info')
# def detections_info():
#     # Capture one frame for info (or use a frame buffer)
#     ret, frame = camera.read()
#     if not ret:
#         return jsonify({"detections": []})

#     results = model.predict(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
#     detections = get_detections_info(results)

#     return jsonify({"detections": detections})


# --- Register the uploaded_video blueprint ---
# Pass the YOLO model and confidence threshold to the blueprint by setting them as attributes or using current_app context
uploaded_video_bp.model = model
uploaded_video_bp.confidence_threshold = CONFIDENCE_THRESHOLD

app.register_blueprint(uploaded_video_bp)

if __name__ == '__main__':
    print("🚀 Starting Flask app on http://localhost:5000")
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        print("🧹 Cleaning up camera resources...")
        if camera.isOpened():
            camera.release()
