import cv2
from ultralytics import YOLO
from flask import Flask, Response, render_template_string
from deep_sort_realtime.deepsort_tracker import DeepSort

# --- Configuration ---
VIDEO_PATH = 0  # Use 0 for webcam, or provide a path like 'my_video.mp4'
MODEL_PATH = 'yolov8n.pt'  # UPDATE with your custom model path.

# --- Initialize Flask app ---
app = Flask(__name__)

# --- Global Model and Tracker Initialization ---
try:
    model = YOLO(MODEL_PATH)
    tracker = DeepSort(max_age=30)
except Exception as e:
    print(f"Error loading model or tracker: {e}")
    model = None
    tracker = None

def generate_frames():
    """
    A generator function that yields video frames with object tracking.
    """
    if model is None or tracker is None:
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"Error: Could not open video source at {VIDEO_PATH}")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # --- YOLOv8, DeepSORT, and Drawing Logic (Identical to FastAPI version) ---
            results = model.predict(frame, conf=0.4, iou=0.5, verbose=False)
            yolo_detections = results[0]
            deepsort_detections = []
            for r in yolo_detections.boxes.data.tolist():
                x1, y1, x2, y2, conf, cls = r
                bbox = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
                class_name = model.names[int(cls)]
                deepsort_detections.append((bbox, conf, class_name))
            
            tracks = tracker.update_tracks(deepsort_detections, frame=frame)

            for track in tracks:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                # Get the class name from the tracker
                class_name = track.get_det_class() 
                l, t, r, b = track.to_ltrb()
                l, t, r, b = int(l), int(t), int(r), int(b)
                cv2.rectangle(frame, (l, t), (r, b), (0, 255, 0), 2)
                # Create a new label that includes both the class name and the ID
                label = f'{class_name} ID: {track_id}'
                cv2.putText(frame, label, (l, t - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        # --- End of processing logic ---

            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            if not flag:
                continue

            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encodedImage) + b'\r\n')
    finally:
        print("Cleaning up resources.")
        cap.release()

@app.route('/')
def index():
    """Serves the home page."""
    html_content = """
    <html>
        <head><title>YOLOv8 + DeepSORT Streaming</title></head>
        <body>
            <h1>Live Object Tracking Feed</h1>
            <p>Powered by Flask, YOLOv8, and DeepSORT.</p>
            <img src="{{ url_for('video_feed') }}" width="800" />
        </body>
    </html>
    """
    # This change processes the template, converting {{...}} into a real URL
    return render_template_string(html_content)

@app.route('/video_feed')
def video_feed():
    """The main endpoint that streams the video feed."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)