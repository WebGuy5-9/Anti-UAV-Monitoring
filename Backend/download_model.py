# download_model.py (Final, Corrected, and Verified Version)
import torch
import os
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

print("🚀 Starting model download and conversion...")

# --- Configuration ---
# This is the correct, verified repository ID
REPO_ID = "depth-anything/Depth-Anything-V2-Small-hf"

# THIS WAS THE PROBLEM: The correct filename is 'model.safetensors'
FILENAME = "model.safetensors"

# This is the name we want for our final file for the Flask app
LOCAL_FILENAME_PT = "depth_anything_v2_small-hf.pt"

print(f"Repository: {REPO_ID}") 
print(f"Target file: {FILENAME}")

# --- Download and Convert ---
try:
    # 1. Download the .safetensors file from the Hub.
    #    This will now succeed because the file actually exists.
    print(f"Downloading '{FILENAME}'...")
    downloaded_model_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir='.',
        local_dir_use_symlinks=False
    )
    
    print(f"File downloaded successfully to: {downloaded_model_path}")

    # 2. Load the weights from the downloaded .safetensors file.
    #    We use `load_file` from the `safetensors` library for this.
    model_weights = load_file(downloaded_model_path)

    # 3. Save the weights into the standard PyTorch .pt format.
    #    This creates the file your Flask app is designed to use.
    torch.save(model_weights, LOCAL_FILENAME_PT)
    
    # # 4. (Optional) Clean up the original downloaded file
    # os.remove(downloaded_model_path)
    # print(f"Cleaned up temporary file: {downloaded_model_path}")

    print("-" * 50)
    print(f"✅ Success! Model has been converted and saved as '{LOCAL_FILENAME_PT}'")
    print(f"   File size: {os.path.getsize(LOCAL_FILENAME_PT) / 1e6:.2f} MB")
    print("   You can now run your Flask application.")
    print("-" * 50)

except Exception as e:
    print(f"\n❌ An error occurred: {e}")
    import traceback
    traceback.print_exc()