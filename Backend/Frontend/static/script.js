// Initialize the application controls
document.addEventListener("DOMContentLoaded", function () {
  initializeControls();

  // TODO: Implement WebSocket or SSE connection here to receive real-time data
  // from the Flask server and update the dashboard dynamically.
  // e.g., connectWebSocket();
});

function updateDetections(detections) {
    const tbody = document.getElementById('detectionsBody');
    tbody.innerHTML = ''; // clear existing
    detections.forEach(det => {
        const row = `<tr>
                       <td>${det.id}</td>
                       <td>${(det.confidence * 100).toFixed(2)}%</td>
                     </tr>`;
        tbody.innerHTML += row;
    });
}


// Function to update metrics
function updateMetrics(metrics) {
  document.getElementById("fpsValue").textContent = metrics.fps.toFixed(1);
  document.getElementById("dronesValue").textContent = metrics.totalDrones;
}

// Initialize user controls
function initializeControls() {
  // Tracking toggle
  document.getElementById("trackingBtn").addEventListener("click", function () {
    const isOff = this.classList.toggle("off");
    this.textContent = isOff ? "OFF" : "ON";
  });

  // Threshold slider
  const slider = document.getElementById("thresholdSlider");
  const valueDisplay = document.getElementById("thresholdValue");

  slider.addEventListener("input", function () {
    const newConfidence = parseFloat(this.value);
    valueDisplay.textContent = newConfidence.toFixed(2);
    sendConfidenceToServer(newConfidence);
    // TODO: Send this new threshold value to the backend
  });

  document.getElementById("uploadBtn").addEventListener("click", function () {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "video/*";
    input.onchange = async function (e) {
      const file = e.target.files[0];
      if (file) {
        try {
          const formData = new FormData();
          formData.append("file", file);

          const response = await fetch("/upload_video", {
            method: "POST",
            body: formData,
          });
          const data = await response.json();
          if (response.ok) {
            alert(
              `Uploaded ${file.name} successfully! Switching to uploaded video stream.`
            );
            // Switch video stream src to uploaded video detection
            document.querySelector(".video-stream").src =
              "/video_feed_uploaded";
          } else {
            alert(`Upload failed: ${data.error || "Unknown error"}`);
          }
        } catch (err) {
          alert("Error uploading video: " + err);
        }
      }
    };
    input.click();
  });

  // Download logs button
  document.getElementById("downloadBtn").addEventListener("click", function () {
    // This will still generate sample data until connected to the backend
    const logData = generateLogData();
    downloadFile("detection_logs.json", JSON.stringify(logData, null, 2));
  });
}

// Generate sample log data
function generateLogData() {
  return {
    timestamp: new Date().toISOString(),
    detections: [
      {
        id: 1,
        class: "Quad",
        confidence: 0.9408,
        timestamp: new Date().toISOString(),
      },
    ],
    metrics: {
      fps: parseFloat(document.getElementById("fpsValue").textContent),
      totalDrones: parseInt(document.getElementById("dronesValue").textContent),
    },
  };
}

// Download file utility
function downloadFile(filename, content) {
  const blob = new Blob([content], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// async function sendConfidenceToServer(confidenceValue) {
//   try {
//     const response = await fetch("/update_confidence", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify({ confidence: confidenceValue }),
//     });
//     const data = await response.json();
//     if (data.status === "success") {
//       console.log("Confidence updated successfully to:", data.confidence);
//       // Reload video stream to apply new confidence value
//       const videoElem = document.querySelector(".video-stream");
//       const currentSrc = videoElem.src;
//       videoElem.src = "";          // Clear current video src (stop stream)
//       setTimeout(() => {
//         videoElem.src = currentSrc;  // Restore src to restart stream with updated confidence
//       }, 100);
//     } else {
//       console.error("Failed to update confidence:", data.message);
//     }
//   } catch (error) {
//     console.error("Error sending confidence update:", error);
//   }
// }
let debounceTimeout = null;

async function sendConfidenceToServer(confidenceValue) {
  // Clear previous debounce timer
  if (debounceTimeout) clearTimeout(debounceTimeout);

  // Debounce: delay sending update until 300ms after last input change
  debounceTimeout = setTimeout(async () => {
    try {
      const response = await fetch("/update_confidence", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ confidence: confidenceValue }),
      });
      const data = await response.json();
      if (data.status === "success") {
        console.log("Confidence updated successfully to:", data.confidence);

        // Smooth reload of video stream to apply new confidence without abrupt stops
        const videoElem = document.querySelector(".video-stream");
        videoElem.style.visibility = "hidden";  // Hide video temporarily
        const currentSrc = videoElem.src;
        videoElem.src = "";  // Stop current stream
        setTimeout(() => {
          videoElem.src = currentSrc;  // Reload stream with new confidence
          videoElem.style.visibility = "visible";  // Show video again
        }, 200);  // 200ms delay for graceful reload
      } else {
        console.error("Failed to update confidence:", data.message);
      }
    } catch (error) {
      console.error("Error sending confidence update:", error);
    }
  }, 300);  // Wait 300ms after last slider change before sending
}

