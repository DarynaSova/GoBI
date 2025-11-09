import argparse

# --- Argument parsing ---
parser = argparse.ArgumentParser(
    description="Clean FASTA headers by keeping only the UniProt ID (the second element after '|')."
)

parser.add_argument(
    "-i", "--input-file",
    help="Path to the input FASTA file.",
    required=True
)
parser.add_argument(
    "-o", "--output-file",
    help="Path to the cleaned output FASTA file.",
    required=True
)

args = parser.parse_args()
input_file = args.input_file
output_file = args.output_file

# --- FASTA cleaning ---
with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    for line in infile:
        if line.startswith(">"):
            parts = line.strip().split("|")
            if len(parts) > 1:
                new_header = ">" + parts[1].strip()
            else:
                new_header = line.strip()
            outfile.write(new_header + "\n")
        else:
            outfile.write(line)

print(f"Cleaned FASTA saved to '{output_file}'")
