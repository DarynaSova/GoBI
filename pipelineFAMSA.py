import subprocess
import sys
import shutil
import json
from pathlib import Path

# FAMSA2 MSA

def famsa(config_path="config.json"):

    # Load JSON configuration
    with open(config_path, "r") as f:
        config = json.load(f)

    # Extract paths from JSON
    famsa = config["famsa"]["exe"]
    input_fasta = config["famsa"]["input_fasta"]
    output_fasta = config["famsa"]["output_fasta"]

      # Ensure paths are properly formatted for subprocess
    famsa = Path(famsa)
    input_fasta = Path(input_fasta)
    output_fasta = Path(output_fasta)


    # Check if famsa is installed in your environment
    if shutil.which("famsa") is None:
        print("FAMSA is not installed in your environment.")
        print("Can be installed with the following command: conda install -c bioconda famsa")
        sys.exit(1)

    # Perform a basic MSA using famsa
    try:
        subprocess.run([str(famsa), str(input_fasta), str(output_fasta)]) 
        print("Done!")

    except subprocess.CalledProcessError:
        print("FAMSA failed to run.")
        sys.exit(1)

if __name__ == "__main__":
    famsa()
