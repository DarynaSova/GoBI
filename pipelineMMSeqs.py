import subprocess
import sys
import shutil
import json
from pathlib import Path
import os

#This pipeline implementation calls mmseqs2 easy-search via WSL on Windows. It uses the default parameters
#It catches missing wsl installation and missing input files. 
# As of now it does not check for mmseqs2 installation inside WSL.
#The input and output paths are defined in the config.json file. So is the format of the output tsv file.
#sudo apt install mmseqs2 inside WSL to install mmseqs2 if not already installed.

# Converting a windows path to WSL path 
def windows_to_wsl(path: Path) -> str:
    drive, tail = path.drive[:-1].lower(), path.as_posix()[2:]
    wsl_path = f"/mnt/{drive}/{tail}"
    return wsl_path

def mmseqs_search(config_path="config.json"):
    #Reading json config
    with open(config_path, "r") as f:
        cfg = json.load(f)

    #Check if WSL is installed
    if shutil.which("wsl") is None:
        print("WSL is not installed or not in PATH.")
        print("wsl --install in the terminal for quick fix")
        sys.exit(1)

    mm = cfg["mmseqs"]
    exe = mm["exe"]                 
    query = Path(mm["query"]).resolve()
    target = Path(mm["target"]).resolve()
    result = Path(mm["result"]).resolve()
    fmt = mm.get("format", "query,target,evalue,pident,alnlen")
    tmp_dir = Path(mm.get("tmp_dir", "tmp")).resolve()
    result.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # use_wsl = exe.startswith("wsl:")
    exe_cmd = exe.replace("wsl:", "")

    if not query.exists():
        print(f"Query not found: {query}"); sys.exit(1)
    if not target.exists():
        print(f"Target not found: {target}"); sys.exit(1)

    q = windows_to_wsl(query); 
    t = windows_to_wsl(target)
    r = windows_to_wsl(result); 
    tmp = windows_to_wsl(tmp_dir)

    q_db = os.path.join(tmp, "queryDB")
    t_db = os.path.join(tmp, "targetDB")
    res_db = os.path.join(tmp, "searchRes")

    cmds = [
    ["wsl", exe_cmd, "createdb", q, q_db],                    # amino acids (proteins)
    ["wsl", exe_cmd, "createdb", t, t_db],                    # nucleotides (genome)
    # optional but speeds up repeated runs:
    ["wsl", exe_cmd, "createindex", t_db, tmp],               # index target genome
    # 2) Search: protein (query) vs nucleotide (target)  == TBLASTN
    ["wsl", exe_cmd, "search", q_db, t_db, res_db, tmp,
     "--search-type", "3",    # force protein->nucleotide (TBLASTN mode)
     "-a"],                   # keep alignment info for convertalis/custom fields
    # 3) Convert to TSV with your chosen columns
    ["wsl", exe_cmd, "convertalis", q_db, t_db, res_db, r,
     "--format-output", fmt,
     "--format-mode", "4"]    # add header row (nice for downstream parsing)
]
    

    try:
        for c in cmds:
            print("Running:", " ".join(c))
            subprocess.run(c, check=True)
    except subprocess.CalledProcessError:
        print("MMseqs2 easy-search failed.")
        sys.exit(1)

if __name__ == "__main__":
    mmseqs_search()