import argparse
import shutil

# --- Argument Parsing ---
parser = argparse.ArgumentParser(
    description="Extract sequences from a proteome by matching UniProt IDs and append them to an existing base dataset."
)

parser.add_argument("-i", "--id-file", help="UniProt ID list", required=True)
parser.add_argument("-p", "--proteome-file", help="Proteome FASTA file", required=True)
parser.add_argument("-b", "--base-dataset", help="Base dataset FASTA file", required=True)
parser.add_argument("-o", "--output-file", help="Output merged FASTA file", required=True)

args = parser.parse_args()

id_file = args.id_file
proteome_file = args.proteome_file
base_dataset_file = args.base_dataset
output_file = args.output_file

# --- Step 1: Load all target UniProt IDs ---
with open(id_file, "r") as f:
    target_ids = {line.strip() for line in f if line.strip()}

print(f"Loaded {len(target_ids)} target IDs.")

# --- Step 2: Parse proteome and extract matches ---
matches = []
current_header = None
current_seq = []

with open(proteome_file, "r") as f:
    for line in f:
        if line.startswith(">"):
            if current_header:
                match = next((uid for uid in target_ids if uid in current_header), None)
                if match:
                    matches.append(current_header + "".join(current_seq))
            current_header = line
            current_seq = []
        else:
            current_seq.append(line)

if current_header:
    match = next((uid for uid in target_ids if uid in current_header), None)
    if match:
        matches.append(current_header + "".join(current_seq))

print(f"Found {len(matches)} matching sequences in the proteome.")

# --- Step 3: Copy base dataset to output file ---
shutil.copyfile(base_dataset_file, output_file)
print(f"Copied base dataset to '{output_file}'")

# --- Step 4: Append matches to the copied file ---
with open(output_file, "a") as out:
    for entry in matches:
        out.write(entry.strip()+"\n")

print(f"Merged dataset written to '{output_file}'")
