#!/usr/bin/env python3
import subprocess
import sys
import shutil

# FAMSA2 MSA

def famsa():
    # Check arguments
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input.fasta> <output.fasta>")
        sys.exit(1)

    input_fasta = sys.argv[1]
    output_fasta = sys.argv[2]

    # Check if famsa is installed in your environment
    if shutil.which("famsa") is None:
        print("FAMSA is not installed in your environment.")
        print("Can be installed with the following command: conda install -c bioconda famsa")
        sys.exit(1)

    # Perform a basic MSA using famsa
    try:
        subprocess.run(["famsa", input_fasta, output_fasta], check=True)
        print("Done!")

    except subprocess.CalledProcessError:
        print("FAMSA failed to run.")
        sys.exit(1)

if __name__ == "__main__":
    famsa()
