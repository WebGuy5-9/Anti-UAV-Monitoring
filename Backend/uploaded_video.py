import os
from flask import Blueprint, request, jsonify, Response
import cv2
from transformers import pipeline
from PIL import Image
import numpy as np
import cv2
import os

# Initialize your depth model once globally (do this once when blueprint loads)
depth_pipe = pipeline(task="depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")

# Assume `model` and `CONFIDENCE_THRESHOLD` are passed or accessed appropriately

uploaded_video_bp = Blueprint('uploaded_video_bp', __name__)
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

uploaded_video_path = None  # Global variable to store uploaded video path

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



def generate_frames_from_file(model, confidence_threshold):
    global uploaded_video_path
    if not uploaded_video_path or not os.path.exists(uploaded_video_path):
        print("No uploaded video available or file missing.")
        return

    cap = cv2.VideoCapture(uploaded_video_path)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            # 1. Run YOLO detection on original frame
            results = model.predict(frame, conf=confidence_threshold, verbose=False)
            boxes = results[0].boxes if results else None

            # 2. Run depth estimation on same frame
            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            depth_map = depth_pipe(pil_img)["depth"]
            depth_map = depth_map.resize((frame.shape[1], frame.shape[0]))
            depth_map_np = np.array(depth_map).astype(np.uint8)
            depth_colored = cv2.applyColorMap(depth_map_np, cv2.COLORMAP_MAGMA)

            # 3. Overlay YOLO bounding boxes on depth-colored frame
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0].item()
                    label = f"Drone {conf:.2f}"
                    cv2.rectangle(depth_colored, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(depth_colored, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            annotated_frame = depth_colored

        except Exception as e:
            print(f"Error during detection or depth estimation: {e}")
            # fallback to original frame
            annotated_frame = frame

        # Encode frame as JPEG and yield for streaming
        flag, encodedImage = cv2.imencode(".jpg", annotated_frame)
        if flag:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encodedImage) + b'\r\n')

    cap.release()


# def generate_frames_from_file(model, confidence_threshold):
#     global uploaded_video_path
#     if not uploaded_video_path or not os.path.exists(uploaded_video_path):
#         print("No uploaded video available or file missing.")
#         return

#     cap = cv2.VideoCapture(uploaded_video_path)
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         try:
#             results = model.predict(frame, conf=confidence_threshold, verbose=False)
#             annotated_frame = results[0].plot() if results else frame
#         except Exception as e:
#             print(f"Error during detection: {e}")
#             annotated_frame = frame

#         flag, encodedImage = cv2.imencode(".jpg", annotated_frame)
#         if flag:
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' +
#                    bytearray(encodedImage) + b'\r\n')

#     cap.release()

# @uploaded_video_bp.route('/detections_info_uploaded')
# def detections_info_uploaded():
#     global uploaded_video_path
#     if not uploaded_video_path or not os.path.exists(uploaded_video_path):
#         return jsonify({"detections": []})

#     cap = cv2.VideoCapture(uploaded_video_path)
#     ret, frame = cap.read()
#     cap.release()
#     if not ret:
#         return jsonify({"detections": []})

#     results = model.predict(frame, conf=confidence_threshold, verbose=False)
#     detections = get_detections_info(results)  # Use same detection extraction
#     return jsonify({"detections": detections})


@uploaded_video_bp.route('/video_feed_uploaded')
def video_feed_uploaded():
    model = getattr(uploaded_video_bp, 'model', None)
    confidence_threshold = getattr(uploaded_video_bp, 'confidence_threshold', 0.5)
    if model is None:
        return "Model not loaded", 500
    return Response(generate_frames_from_file(model, confidence_threshold),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

