#!/usr/bin/env python3

import argparse
import re
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Clean/filter a .bib file based on citations found in a .aux file"
    )
    parser.add_argument(
        "files",
        type=str,
        nargs=2,
        metavar=("FILE", "FILE"),
        help="Paths to the .aux and .bib files (any order)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="references_clean.bib",
        help="Path to the cleaned .bib output file (default: references_clean.bib)"
    )
    parser.add_argument(
        "--generate-clean-bib",
        dest="generate_clean_bib",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate a cleaned .bib file with only used entries (default: True)"
    )
    parser.add_argument(
        "--remove-unused",
        dest="remove_unused_from_original",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Overwrite the original .bib file removing unused entries (default: False)"
    )
    return parser.parse_args()


def detect_aux_bib(files):
    aux_file = None
    bib_file = None

    for f in files:
        suffix = Path(f).suffix.lower()

        if suffix == ".aux":
            aux_file = f
        elif suffix == ".bib":
            bib_file = f

    if aux_file is None or bib_file is None:
        raise ValueError(
            "Could not identify both a .aux and a .bib file among the arguments: "
            f"{files}"
        )

    return aux_file, bib_file


args = parse_args()

AUX_FILE, BIB_FILE = detect_aux_bib(args.files)
CLEAN_BIB_FILE = args.output
GENERATE_CLEAN_BIB = args.generate_clean_bib
REMOVE_UNUSED_FROM_ORIGINAL = args.remove_unused_from_original

if not Path(AUX_FILE).exists():
    raise FileNotFoundError(
        f"AUX file not found: {AUX_FILE}"
    )

if not Path(BIB_FILE).exists():
    raise FileNotFoundError(
        f"BIB file not found: {BIB_FILE}"
    )
    
###############################################################################
# AUX PARSER
###############################################################################

def extract_used_keys(aux_path):

    content = Path(aux_path).read_text(
        encoding="utf-8",
        errors="ignore"
    )

    used = set()

    patterns = [
        r'\\citation\{([^}]*)\}',
        r'\\abx@aux@cite\{([^}]*)\}',
        r'\\abx@aux@segm\{[^}]*\}\{[^}]*\}\{([^}]*)\}'
    ]

    for pattern in patterns:

        for match in re.findall(pattern, content):

            for key in match.split(","):
                key = key.strip()

                if key:
                    used.add(key)

    return used

###############################################################################
# BIB PARSER
###############################################################################

def parse_bib_entries(bib_content):

    entries = {}

    entry_start = re.compile(
        r'@(\w+)\s*\{\s*([^,]+)\s*,',
        re.IGNORECASE
    )

    matches = list(entry_start.finditer(bib_content))

    for i, match in enumerate(matches):

        key = match.group(2).strip()

        start = match.start()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(bib_content)

        entries[key] = bib_content[start:end].strip()

    return entries

###############################################################################
# MAIN
###############################################################################

used_keys = extract_used_keys(AUX_FILE)

bib_content = Path(BIB_FILE).read_text(
    encoding="utf-8",
    errors="ignore"
)

entries = parse_bib_entries(bib_content)

bib_keys = set(entries.keys())

unused_keys = bib_keys - used_keys
missing_keys = used_keys - bib_keys

print("\n==========================")
print("BIBLIOGRAPHY ANALYSIS")
print("==========================")

print(f"\nUsed citations:      {len(used_keys)}")
print(f"Bib entries:         {len(bib_keys)}")
print(f"Unused entries:      {len(unused_keys)}")
print(f"Missing entries:     {len(missing_keys)}")

if unused_keys:
    print("\n--- UNUSED ENTRIES ---")

    for key in sorted(unused_keys):
        print(key)

if missing_keys:
    print("\n--- CITED BUT NOT FOUND ---")

    for key in sorted(missing_keys):
        print(key)


###############################################################################
# GENERATE CLEAN FILE
###############################################################################

if GENERATE_CLEAN_BIB:

    with open(CLEAN_BIB_FILE, "w", encoding="utf-8") as f:

        for key in sorted(used_keys, reverse=True):

            if key in entries:
                f.write(entries[key])
                f.write("\n\n")

    print(f"\nGenerated: {CLEAN_BIB_FILE}")

###############################################################################
# OVERWRITE ORIGINAL FILE
###############################################################################



if REMOVE_UNUSED_FROM_ORIGINAL:

    with open(BIB_FILE, "w", encoding="utf-8") as f:

        for key in sorted(used_keys):

            if key in entries:
                f.write(entries[key])
                f.write("\n\n")

    print(f"\nUpdated original file: {BIB_FILE}")