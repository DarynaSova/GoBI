import argparse
import subprocess
import sys
import os
from pathlib import Path
import json
import yaml
import re



#-------------------------------------- HELPER METHODS -------------------------------------


def exit_with_error(message: str):
    embed_print(f"(ERROR) {message}")
    sys.exit(1)

def embed_print(message: str):
    print(f"[EMBED]{message}")

def setup_yml_file(sequence_file: str, prefix: str, protocol: str, path_to_save: str):
    """Create YAML config for bio_embeddings."""
    config = {
        "global": {
            "sequences_file": sequence_file,
            "prefix": prefix,
            "simple_remapping": True,
        },
        "stage_0": {
            "type": "embed",
            "protocol": protocol,
            "reduce": True,
            "device": "cuda",
        },
    }
    with open(path_to_save, "w") as output:
        yaml.safe_dump(config, output, sort_keys=False)

def find_python_executable(path: Path) -> Path:
    """Finds Python executable in given virtual environment path."""
    return path / "bin" / "python"

def check_package_in_env(env_path: Path, package: str) -> bool:
    """Checks if a package is installed inside a specific virtual environment."""
    python_exec = find_python_executable(env_path)
    if not python_exec.exists():
        embed_print(f" Environment not found at {env_path}")
        return False
    try:
        subprocess.run(
            [str(python_exec), "-c", f"import {package}"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        embed_print(f"'{package}' is installed in environment: {env_path}")
        return True
    except subprocess.CalledProcessError:
        embed_print(f"'{package}' is NOT installed in environment: {env_path}")
        return False


def run_and_prefix(command, prefix="[EMBED]",rx = None):
    """Run a subprocess and prefix its stdout/stderr lines."""
    pattern = ''
    if rx is not None:
        pattern = re.compile(rx)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    for line in process.stdout:
        if rx is not None:
            if pattern.match(line):
                print(f"{prefix}{line.rstrip()}")
        else:
            print(f"{prefix}{line.rstrip()}")

    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)


#-------------------------------------- MAIN PIPELINE ----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Protein embedding pipeline.")
    parser.add_argument("-c", "--config", required=True, help="Path to the JSON configuration file.")
    parser.add_argument("-o", "--organism_name", required=True, help="Organism name.")
    args = parser.parse_args()

    config_path = Path(args.config)
    organism_name = str(args.organism_name)

    # ---------- CONFIG VALIDATION ----------
    if not config_path.name.lower().endswith(".json"):
        exit_with_error("Argument must be a JSON file.")
    if not os.path.isfile(config_path):
        exit_with_error("Configuration file not found.")

    print(f"File {config_path.name} exists and is being accessed.")

    try:
        with open(config_path, "r") as cf:
            config = json.load(cf)
    except json.JSONDecodeError:
        exit_with_error("Failed to decode JSON from the configuration file.")

    embedding_section = config.get("embedding")
    if not embedding_section:
        exit_with_error("Missing section: 'embedding'")

    required_keys = [
        "base_dataset_file",
        "hit_ids",
        "hit_organism_proteome",
        "workflow_file_location",
        "env_bio_embedding",
        "env_protspace",
        "workflow_file_name",
        "protspace_methods",
        "protspace_features"
    ]
    missing_or_empty = [
        key for key in required_keys
        if key not in embedding_section or embedding_section[key] in (None, "", [])
    ]
    if missing_or_empty:
        exit_with_error(f"Missing or empty required keys in 'embedding': {', '.join(missing_or_empty)}")

    embed_print(f"Configuration loaded successfully for organism_name '{organism_name}'.")

    # ---------- CHECK ENVIRONMENTS AND PACKAGES ----------
    embed_env = Path(embedding_section["env_bio_embedding"])
    if not check_package_in_env(embed_env, "bio_embeddings"):
        exit_with_error("Exiting Pipeline")
    protspace_env = Path(embedding_section["env_protspace"])
    if not check_package_in_env(protspace_env, "protspace"):
        exit_with_error("Exiting Pipeline")

    # ---------- CREATE WORKFLOW DIRECTORY ----------
    flow_dir_name = embedding_section["workflow_file_name"].lower() + "_embedding_dir"
    flow_dir_path = Path(embedding_section["workflow_file_location"]) / flow_dir_name


    if flow_dir_path.exists():
        exit_with_error("Cannot create new File for the work flow, the specified file already exists.")
    flow_dir_path.mkdir(parents=True, exist_ok=True)
    embed_print(f"Workflow directory created under: {flow_dir_path}")

    # ---------- STAGE 1: CLEAN HEADERS ----------
    cleaned_base_dataset_path = Path(flow_dir_path) /  "dataset_without_hits_cleaned.fasta"
    try:
        run_and_prefix(
            [sys.executable, "EMBEDsupplementary/keep_protein_ids.py",
             "-i", embedding_section["base_dataset_file"],
             "-o", str(cleaned_base_dataset_path)])
        embed_print("Successfully cleaned headers from the base dataset.")
    except subprocess.CalledProcessError as e:
        exit_with_error(f"Stage 1 failed: {e}")

    # ---------- STAGE 2: EXTRACT AND APPEND HITS ----------
    embed_ready_dataset_path = flow_dir_path / "embed_ready_dataset.fasta"
    try:
        run_and_prefix(
            [sys.executable, "EMBEDsupplementary/extract_hits_and_append.py",
             "-i", embedding_section["hit_ids"],
             "-p", embedding_section["hit_organism_proteome"],
             "-b", str(cleaned_base_dataset_path),
             "-o", str(embed_ready_dataset_path)]
        )
        embed_print("Successfully extracted and appended hit proteins.")
    except subprocess.CalledProcessError as e:
        exit_with_error(f"Stage 2 failed: {e}")

    # ---------- STAGE 3: BIO_EMBEDDINGS ----------
    prefix = flow_dir_path / "bio_embeddings_out"
    bio_embeddings_config = flow_dir_path / "bio_embedding_config.yml"
    setup_yml_file(str(embed_ready_dataset_path), str(prefix), "prottrans_t5_xl_u50", str(bio_embeddings_config))

    try:
        run_and_prefix(
            [str(embed_env/"bin"/"bio_embeddings"), str(bio_embeddings_config),
             "--overwrite"], rx = r'^\s*\d+%'
        )
        embed_print("Protein Embeddings produced via bio_embeddings successfully.")
    except subprocess.CalledProcessError as e:
        exit_with_error(f"Stage 3 failed: {e}")

    # ---------- STAGE 4: CORRECT H5 HEADERS ----------
    reduced_embeddings_path = prefix /"stage_0/reduced_embeddings_file.h5"
    plot_ready_embeddings = flow_dir_path / "reduced_embeddings_with_ids.h5"
    try:
        run_and_prefix(
            [sys.executable, "EMBEDsupplementary/h5_correction.py",
             "-i", str(reduced_embeddings_path),
             "-o", str(plot_ready_embeddings)]
        )
        embed_print("Final embeddings successfully corrected and saved.")
    except subprocess.CalledProcessError as e:
        exit_with_error(f"Stage 4 failed: {e}")

    #Unneccessary files from bio_embeddings such as config.yml and stage_0 gets deleted  (THIS PART CAN BE REMOVED IN THE FUTURE)
    #Removal is done because we will make use of Uniprot features in Protspace
    # TODO: add file removal functionality using shutil.rmtree on stage_0 file produced by bio_embeddings

    #------------ STAGE 5: PROTSPACE, GENERATION OF VISUALIZATIONS
    protspace_path = flow_dir_path / "protspace_output"
    protspace_output = protspace_path / f"{organism_name}_{embedding_section['protspace_methods'].replace(',', '_')}"

    if not protspace_path.exists():
        protspace_path.mkdir(parents=True, exist_ok=True)
    try:
        run_and_prefix([
            str(protspace_env / "bin" / "protspace-local"),
            "-i", str(plot_ready_embeddings),
            "-o", str(protspace_output),
            "-m", embedding_section["protspace_methods"],
            "-f", embedding_section["protspace_features"],
            "--bundled", "false"])
        embed_print("Protspace visualization produced successfully.")
    except subprocess.CalledProcessError as e:
        exit_with_error(f"Stage 5 failed: {e}")

    # here we add a custom visualization for better seperation of target organism_name hits from the base dataset proteins

    custom_style = {
        "feature_colors": {
            "species": {
                f"{organism_name}": "rgba(255, 64, 64, 0.9)"
            }
        },
        "marker_shape": {
            "species": {
                f"{organism_name}": "x"
            }
        }
    }
    with open(str(protspace_output / "visualization_state.json"), "w") as f:
        json.dump(custom_style, f, indent=2)

    embed_print("Pipeline completed successfully.")


#-------------------------------------- ENTRY POINT ------------------------------------------------------------

if __name__ == "__main__":
    main()
