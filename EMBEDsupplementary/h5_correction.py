import argparse
import h5py

# --- Argument Parsing ---
parser = argparse.ArgumentParser(
    description="Rename datasets in an HDF5 file using their 'original_id' attribute."
)

parser.add_argument(
    "-i", "--input-file",
    help="Path to the input HDF5 file (e.g., reduced_embeddings_file.h5).",
    required=True
)
parser.add_argument(
    "-o", "--output-file",
    help="Path to the output HDF5 file (e.g., reduced_embeddings_with_ids.h5).",
    required=True
)

args = parser.parse_args()
embedding_file = args.input_file
output_file = args.output_file

# --- Core logic ---
with h5py.File(embedding_file, "r") as infile, h5py.File(output_file, "w") as outfile:
    for dataset_name in infile.keys():
        data = infile[dataset_name][:]
        attrs = dict(infile[dataset_name].attrs)

        protein_id = attrs.get("original_id", None)

        if protein_id is None:
            new_name = str(dataset_name)
        else:
            if isinstance(protein_id, bytes):
                protein_id = protein_id.decode("utf-8")
            elif isinstance(protein_id, (list, tuple)) and isinstance(protein_id[0], bytes):
                protein_id = protein_id[0].decode("utf-8")
            elif isinstance(protein_id, (list, tuple)):
                protein_id = protein_id[0]
            new_name = str(protein_id).strip()

        outfile.create_dataset(new_name, data=data)

        for key, value in attrs.items():
            outfile[new_name].attrs[key] = value

print(f"All datasets renamed using their 'original_id' attribute and saved to '{output_file}'.")

