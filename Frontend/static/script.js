       
       
       // Initialize the application controls
        document.addEventListener('DOMContentLoaded', function() {
            initializeControls();
            
            // TODO: Implement WebSocket or SSE connection here to receive real-time data
            // from the Flask server and update the dashboard dynamically.
            // e.g., connectWebSocket();
        });

        // Function to update the detections table
        function updateDetections(detections) {
            const tbody = document.getElementById('detectionsBody');
            tbody.innerHTML = ''; // Clear existing rows
            detections.forEach(det => {
                const row = `<tr>
                                <td>${det.id}</td>
                                <td>${det.class}</td>
                                <td>${(det.confidence * 100).toFixed(2)}%</td>
                             </tr>`;
                tbody.innerHTML += row;
            });
        }
        
        // Function to update metrics
        function updateMetrics(metrics) {
            document.getElementById('fpsValue').textContent = metrics.fps.toFixed(1);
            document.getElementById('dronesValue').textContent = metrics.totalDrones;
        }

        // Initialize user controls
        function initializeControls() {
            // Tracking toggle
            document.getElementById('trackingBtn').addEventListener('click', function() {
                const isOff = this.classList.toggle('off');
                this.textContent = isOff ? 'OFF' : 'ON';
            });

            // Threshold slider
            const slider = document.getElementById('thresholdSlider');
            const valueDisplay = document.getElementById('thresholdValue');
            
            slider.addEventListener('input', function() {
                const newConfidence = parseFloat(this.value)
                valueDisplay.textContent = newConfidence.toFixed(2)
                sendConfidenceToServer(newConfidence)
                // TODO: Send this new threshold value to the backend
            });

            // Upload video button
            document.getElementById('uploadBtn').addEventListener('click', function() {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'video/*';
                input.onchange = function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        alert(`File selected: ${file.name}. Upload functionality to be implemented.`);
                        // TODO: Implement the logic to upload the video file to the server.
                    }
                };
                input.click();
            });

            // Download logs button
            document.getElementById('downloadBtn').addEventListener('click', function() {
                // This will still generate sample data until connected to the backend
                const logData = generateLogData();
                downloadFile('detection_logs.json', JSON.stringify(logData, null, 2));
            });
        }

        // Generate sample log data
        function generateLogData() {
            return {
                timestamp: new Date().toISOString(),
                detections: [
                    { id: 1, class: "Quad", confidence: 0.9408, timestamp: new Date().toISOString() },
                ],
                metrics: {
                    fps: parseFloat(document.getElementById('fpsValue').textContent),
                    totalDrones: parseInt(document.getElementById('dronesValue').textContent)
                }
            };
        }

        // Download file utility
        function downloadFile(filename, content) {
            const blob = new Blob([content], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
// code for implimenting confidnce slider
        async function sendConfidenceToServer(confidenceValue) {
    try {
        const response = await fetch('/update_confidence', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ confidence: confidenceValue })
        });
        const data = await response.json();
        if (data.status === 'success') {
            console.log('Confidence updated successfully to:', data.confidence);
        } else {
            console.error('Failed to update confidence:', data.message);
        }
    } catch (error) {
        console.error('Error sending confidence update:', error);
    }
}
