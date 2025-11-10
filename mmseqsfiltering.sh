#!/usr/bin/env bash

# AI generated helper file to retrieve command lines for filtering the mmseqs results
# Those were basically the commands used, changing and altering the parameters as needed depending on use case
# Not automatized as depending on the search only certain filters or outputs made sense, all were then run manually as needed

# mmseqs_filters.sh
# A grab‑bag of AWK one‑liners to filter MMseqs2 convertalis TSV outputs.
# These assume your TSV has a HEADER (use: --format-mode 4) and the columns come from:
#   --format-output "query,target,evalue,pident,alnlen,qcov,tcov,qstart,qend,tstart,tend,qframe,tframe,qlen,tlen"
# Add or remove fields as needed. Everything here is header‑aware, so order doesn't matter as long as the names match.
#
# Usage examples (run in your shell):
#   bash mmseqs_filters.sh   # just prints this cheatsheet (no execution)
#   # Copy/paste any AWK line below and adapt thresholds/files to your case.
#
# NOTE on coverage units:
#   qcov/tcov can be either 0..1 fractions or 0..100 percentages depending on how you computed them.
#   This cheatsheet provides BOTH versions; uncomment the one that matches your data.
#
# ---------- COMMON THRESHOLD EXAMPLES (edit to taste) ----------
# E_VALUE_MAX=1e-5
# PIDENT_MIN=35
# ALNLEN_MIN=50
# QCOV_MIN_FRAC=0.6     # if coverage is in 0..1
# QCOV_MIN_PCT=60       # if coverage is in 0..100
#
# ---------- 0) Column resolver (used in every AWK) ----------
# Each AWK below starts with a header pass that maps column names to indices:
#   NR==1 { for (i=1;i<=NF;i++) h[$i]=i; next }
# After that, $h["pident"] refers to the pident column etc.
#
# ---------- 1) Basic high‑confidence filter (evalue + identity + length) ----------
# Fractions version for qcov (0..1):
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#             ($h[\"evalue\"]<=1e-5) && ($h[\"pident\"]>=35) && ($h[\"alnlen\"]>=50) && ($h[\"qcov\"]>=0.6)' \
#     mmseqs_results.tsv > mmseqs_hiconf.tsv
#
# Percent version for qcov (0..100):
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#             ($h[\"evalue\"]<=1e-5) && ($h[\"pident\"]>=35) && ($h[\"alnlen\"]>=50) && ($h[\"qcov\"]>=60)' \
#     mmseqs_results.tsv > mmseqs_hiconf.tsv
#
# ---------- 2) Add target coverage as a second guard ----------
# Fractions:
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#             ($h[\"evalue\"]<=1e-5) && ($h[\"pident\"]>=35) && ($h[\"alnlen\"]>=50) && ($h[\"qcov\"]>=0.6) && ($h[\"tcov\"]>=0.6)' \
#     mmseqs_results.tsv > mmseqs_hiconf.tsv
#
# Percent:
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#             ($h[\"evalue\"]<=1e-5) && ($h[\"pident\"]>=35) && ($h[\"alnlen\"]>=50) && ($h[\"qcov\"]>=60) && ($h[\"tcov\"]>=60)' \
#     mmseqs_results.tsv > mmseqs_hiconf.tsv
#
# ---------- 3) Keep the single best hit per QUERY (lowest evalue, break ties by highest pident) ----------
# awk -F'\t' 'BEGIN{OFS=\"\t\"} \
#   NR==1{for(i=1;i<=NF;i++)h[$i]=i; header=$0; next} \
#   {q=$h[\"query\"]; e=$h[\"evalue\"]; id=$h[\"pident\"]; key=q; \
#    if(!(key in best) || e<best_e[key] || (e==best_e[key] && id>best_id[key])){best[key]=$0; best_e[key]=e; best_id[key]=id}} \
#   END{print header; for(k in best) print best[k]}' \
#   mmseqs_results.tsv > best_per_query.tsv
#
# ---------- 4) Keep the single best hit per TARGET (lowest evalue) ----------
# awk -F'\t' 'BEGIN{OFS=\"\t\"} \
#   NR==1{for(i=1;i<=NF;i++)h[$i]=i; header=$0; next} \
#   {t=$h[\"target\"]; e=$h[\"evalue\"]; if(!(t in best) || e<best_e[t]){best[t]=$0; best_e[t]=e}} \
#   END{print header; for(k in best) print best[k]}' \
#   mmseqs_results.tsv > best_per_target.tsv
#
# ---------- 5) Require minimum aligned fraction of the QUERY or TARGET ----------
# Using lengths (robust when coverage columns are unavailable):
#   Require >=60% of query covered by the alignment length:
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#            (($h[\"alnlen\"]/$h[\"qlen\"])>=0.60)' \
#   mmseqs_results.tsv > alnlen_over_60pct_query.tsv
#
#   Require >=60% of target covered:
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#            (($h[\"alnlen\"]/$h[\"tlen\"])>=0.60)' \
#   mmseqs_results.tsv > alnlen_over_60pct_target.tsv
#
# ---------- 6) Enforce strand (only '+' or only '-') based on tstart/tend ----------
#   Keep only plus strand:
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#            ($h[\"tstart\"] <= $h[\"tend\"])' \
#   mmseqs_results.tsv > plus_strand.tsv
#
#   Keep only minus strand:
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#            ($h[\"tstart\"] > $h[\"tend\"])' \
#   mmseqs_results.tsv > minus_strand.tsv
#
# ---------- 7) Convert to 6‑column BED (chrom start end name score strand) ----------
# Assumes target holds the contig/chrom name and tstart/tend are 1‑based nucleotide coords.
# Score is pident mapped to 0..1000.
# awk -F'\t' 'BEGIN{OFS=\"\t\"} \
#   NR==1{for(i=1;i<=NF;i++)h[$i]=i; next} \
#   {chr=$h[\"target\"]; s=$h[\"tstart\"]; e=$h[\"tend\"]; name=$h[\"query\"]; pid=$h[\"pident\"]; \
#    strand=(s>e?\"-\":\"+\"); start0=(s>e?e:s)-1; end1=(s>e?s:e); score=int((pid/100)*1000); if(score>1000)score=1000; \
#    print chr, start0, end1, name, score, strand}' \
#   mmseqs_results.tsv > hits.bed
#
# ---------- 8) Filter by contig/chromosome name pattern ----------
# Keep only targets whose names start with 'chr' or 'scaffold_':
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#            ($h[\"target\"] ~ /^chr/ || $h[\"target\"] ~ /^scaffold_/)' \
#   mmseqs_results.tsv > filtered_by_chrom.tsv
#
# ---------- 9) Remove self‑hits (when query IDs and target IDs may match) ----------
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#            ($h[\"query\"] != $h[\"target\"])' \
#   mmseqs_results.tsv > no_self_hits.tsv
#
# ---------- 10) Compose multiple criteria in one pass ----------
# Example: evalue<=1e-10, pident>=40, qcov>=70% (percentage version), keep only plus strand:
# awk -F'\t' 'BEGIN{OFS=\"\t\"} NR==1{for(i=1;i<=NF;i++)h[$i]=i; print; next} \
#            ($h[\"evalue\"]<=1e-10) && ($h[\"pident\"]>=40) && ($h[\"qcov\"]>=70) && ($h[\"tstart\"] <= $h[\"tend\"])' \
#   mmseqs_results.tsv > strict_plus.tsv
#
# ---------- TIPS ----------
# • If your header names differ, adjust the strings in h[\"...\"] accordingly.
# • To keep the header in outputs, the examples explicitly print it (print; next) in NR==1.
# • For very large files, use LC_ALL=C for speed:  LC_ALL=C awk -F'\t' '...'
# • If you saved with Windows line endings, normalize first:  dos2unix mmseqs_results.tsv
#
# End of cheatsheet.
