import os
from flask import Blueprint, request, jsonify, Response, current_app
import cv2
from transformers import pipeline
from PIL import Image
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort
import time
# Initialize depth model once
depth_pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")
# Initialize DeepSORT tracker
object_tracker = DeepSort(
    max_age=50,
    n_init=2,
    nms_max_overlap=1.0,
    max_cosine_distance=0.3,
    nn_budget=None,
    override_track_class=None,
    embedder="mobilenet",
    half=True,
    bgr=True,
    embedder_gpu=True
)

uploaded_video_bp = Blueprint('uploaded_video_bp', __name__)
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
uploaded_video_path = None  # Global variable for uploaded video path

@uploaded_video_bp.route('/upload_video', methods=['POST'])
def upload_video():
    global uploaded_video_path
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    uploaded_video_path = filepath
    print(f"Uploaded video saved to: {filepath}")
    return jsonify({"message": "File uploaded", "filepath": filepath}), 200

# At module level:
track_trails = {}  # Dictionary to store centroid trails for each track_id

def generate_frames_from_file(model, confidence_threshold):
    global uploaded_video_path, track_trails
    if not uploaded_video_path or not os.path.exists(uploaded_video_path):
        print("No uploaded video available or file missing.")
        return

    cap = cv2.VideoCapture(uploaded_video_path)
    desired_fps = 30
    frame_duration = 1 / desired_fps  # seconds per frame
    try:
        while True:
            start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            try:
                # 1. YOLO Detection
                results = model.predict(frame, conf=confidence_threshold, verbose=False)
                boxes = results[0].boxes if results else None

                # 2. Prepare DeepSORT detections
                detections = []
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf_score = box.conf[0].item()
                        bbox = [x1, y1, x2 - x1, y2 - y1]
                        detections.append((bbox, conf_score, "drone"))

                # 3. Update DeepSORT tracker
                tracks = object_tracker.update_tracks(detections, frame=frame)

                # 4. Depth estimation + colormap
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                depth_map = depth_pipe(pil_img)["depth"]
                depth_map = depth_map.resize((frame.shape[1], frame.shape[0]))
                depth_map_np = np.array(depth_map).astype(np.uint8)
                depth_colored = cv2.applyColorMap(depth_map_np, cv2.COLORMAP_MAGMA)

                # 5. Draw YOLO detection boxes (green)
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf_score = box.conf[0].item()
                        label = f"Det {conf_score:.2f}"
                        cv2.rectangle(depth_colored, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(depth_colored, label, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                # 6. Draw DeepSORT tracks with IDs (blue)
                for track in tracks:
                    if not track.is_confirmed() or track.time_since_update > 0:
                        continue
                    l, t, w, h = [int(i) for i in track.to_ltwh()]
                    track_id = track.track_id
                    # Compute centroid
                    cx = l + w // 2
                    cy = t + h // 2
                    # Update trail
                    if track_id not in track_trails:
                        track_trails[track_id] = []
                    track_trails[track_id].append((cx, cy))
                    max_trail_length = 600  # Only keep latest N points
                    track_trails[track_id] = track_trails[track_id][-max_trail_length:]

                    # Draw trail footprints
                    for pt in track_trails[track_id]:
                        cv2.circle(depth_colored, pt, 3, (255, 0, 0), -1)  # blue dot

                    # Draw current centroid larger
                    cv2.circle(depth_colored, (cx, cy), 5, (0, 0, 255), -1)  # red centroid
                    cv2.putText(depth_colored, f"ID:{track_id}", (cx + 6, cy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    # ---- FUTURE CENTROID ----
                    # Get Kalman filter state for velocity
                    state = track.mean  # [cx, cy, ra, h, vx, vy, vra, vh]
                    # Use predicted position n frames ahead (e.g. 10 frames)
                    n_future = 30
                    fx = int(state[0] + n_future * state[4])
                    fy = int(state[1] + n_future * state[5])
                    cv2.circle(depth_colored, (fx, fy), 7, (0, 255, 255), -1)  # Yellow for future
                    cv2.putText(depth_colored, "Future", (fx + 8, fy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                annotated_frame = depth_colored

            except Exception as e:
                print(f"Error during detection/tracking/depth estimation: {e}")
                annotated_frame = frame

            flag, encodedImage = cv2.imencode(".jpg", annotated_frame)
            if flag:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       bytearray(encodedImage) + b'\r\n')
            
            # Sleep to enforce FPS
            elapsed = time.time() - start_time
            to_wait = frame_duration - elapsed
            if to_wait > 0:
                time.sleep(to_wait)

    finally:
        cap.release()
        print("Released video capture resource")

@uploaded_video_bp.route('/video_feed_uploaded')
def video_feed_uploaded():
    model = getattr(uploaded_video_bp, 'model', None)
    if model is None:
        return "Model not loaded", 500
    confidence_threshold = current_app.config.get('CONFIDENCE_THRESHOLD', 0.5)
    return Response(generate_frames_from_file(model, confidence_threshold),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
