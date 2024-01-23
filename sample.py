from tqdm import tqdm
import time

def execute_runner():
    # Replace this with the actual code from Runner.py
    for _ in tqdm(range(50), desc="Executing Runner.py"):
        time.sleep(0.1)  # Simulating some work

def execute_downloader():
    # Replace this with the actual code from DownloadNbaFromOneDrive.py
    for _ in tqdm(range(100), desc="Executing DownloadNbaFromOneDrive.py"):
        time.sleep(0.1)  # Simulating some work

# Record the start time
start_time = time.time()

# Execute Runner.py
execute_runner()

# Calculate the time taken for Runner.py
runner_time = time.time() - start_time

# Record the new start time
start_time = time.time()

# Execute DownloadNbaFromOneDrive.py
execute_downloader()

# Calculate the time taken for DownloadNbaFromOneDrive.py
downloader_time = time.time() - start_time

# Calculate the total time
total_time = runner_time + downloader_time

print(f"Total time taken: {total_time:.2f} seconds")
