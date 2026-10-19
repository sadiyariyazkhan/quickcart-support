from huggingface_hub import snapshot_download
import os

print("Downloading FLEURS test clips (en_us & hi_in)...")
# Using your folder name 'fleurus_clips'
local_dir = os.path.join(os.path.dirname(__file__), "..", "fleurus_clips")

for config in ["en_us", "hi_in"]:
    print(f"Downloading {config}...")
    snapshot_download(
        repo_id="google/fleurs",
        repo_type="dataset",
        allow_patterns=[f"data/{config}/test/*"],
        local_dir=local_dir
    )
print("Download complete! Check the 'fleurus_clips' folder.")