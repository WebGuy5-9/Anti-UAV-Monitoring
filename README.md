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

Demo Video:
[![Watch the demo](<img width="1879" height="1055" alt="image" src="https://github.com/user-attachments/assets/508d41db-e2c6-40e3-85ae-6851c26c49e3" />
)](https://drive.google.com/file/d/1qKfXWvgYCwTD32tlNsUtYUIqKOFkZQAT/view?usp=sharing)
