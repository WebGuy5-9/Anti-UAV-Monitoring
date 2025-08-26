import os
from flask import Blueprint, request, jsonify, Response
import cv2

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
            results = model.predict(frame, conf=confidence_threshold, verbose=False)
            annotated_frame = results[0].plot() if results else frame
        except Exception as e:
            print(f"Error during detection: {e}")
            annotated_frame = frame

        flag, encodedImage = cv2.imencode(".jpg", annotated_frame)
        if flag:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encodedImage) + b'\r\n')

    cap.release()

@uploaded_video_bp.route('/video_feed_uploaded')
def video_feed_uploaded():
    model = getattr(uploaded_video_bp, 'model', None)
    confidence_threshold = getattr(uploaded_video_bp, 'confidence_threshold', 0.5)
    if model is None:
        return "Model not loaded", 500
    return Response(generate_frames_from_file(model, confidence_threshold),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

