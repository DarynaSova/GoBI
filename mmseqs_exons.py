from pathlib import Path
import argparse
import subprocess
import shutil
import sys
import logging

#!/usr/bin/env python3
"""
mmseqs_exons.py

Simple helper to run an MMseqs2 search of exon queries against genomic data.
Footprint / style follows pipelineMMSeqs.py in this folder (import not required).

Usage example:
    python mmseqs_exons.py --query exons.fasta --target genome.fasta --out out_mmseqs --threads 4

Creates mmseqs DBs as needed, runs `mmseqs search` and converts alignments to tabular output.
"""



