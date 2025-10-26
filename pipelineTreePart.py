import subprocess
import json
import re
import sys
from pathlib import Path

def iqTree(config_path="config.json"):
    # Load JSON configuration
    with open(config_path, "r") as f:
        config = json.load(f)

    # Extract paths from JSON
    iqtree_exe = config["iqtree"]["exe"]
    alignment_fasta = config["famsa"]["output_fasta"]

    # Ensure paths are properly formatted for subprocess
    iqtree_exe = Path(iqtree_exe)
    alignment_fasta = Path(alignment_fasta)

    # Step 1: Run IQ-TREE to find the best-fit model
    print("Running model selection...")
    result = subprocess.run(
        [str(iqtree_exe), "-s", str(alignment_fasta), "-redo"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    stdout_str = result.stdout

    # Extract best-fit model
    match = re.search(r"Best-fit model:\s+(\S+)", stdout_str)
    if match:
        best_model = match.group(1)
        print(f"Best-fit model: {best_model}")
    else:
        print("No model found.")
        sys.exit(1)

    # Step 2: Run IQ-TREE with bootstrap analysis
    print("Running final IQ-TREE analysis...")
    subprocess.run(
        [str(iqtree_exe), "-s", str(alignment_fasta), "-m", best_model, "-bb", "1000", "-redo"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print("IQ-TREE analysis completed.")

if __name__ == "__main__":
    iqTree()
