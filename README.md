Data Collection & Labeling:
Collected a custom dataset of drone images by scraping Google using the BeautifulSoup library.
Labeled and annotated the dataset using Roboflow, ensuring accurate bounding boxes for model training.

Model Training & Testing:
Trained a YOLOv8 object detection model on the custom drone dataset for reliable drone identification.
Evaluated performance on multiple YouTube videos and real-time webcam feeds to validate accuracy and robustness.

Frontend Integration:
Built a JavaScript-based frontend to visualize real-time detection results from the trained model.

Future Work:
Integrating Depth-Anything v2 for depth estimation — aiming to convert colormap outputs into real-world distance values for precise spatial awareness.
Deploying the detection and depth estimation models on edge devices such as Raspberry Pi and NVIDIA Jetson Nano for efficient, on-device inference in real-time environments.

Demo: https://drive.google.com/file/d/1qKfXWvgYCwTD32tlNsUtYUIqKOFkZQAT/view?usp=sharing

<img width="1879" height="1055" alt="Screenshot 2025-11-11 120025" src="https://github.com/user-attachments/assets/83fe5a9b-8279-48bf-a76e-6501376cc296" />



