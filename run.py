# coding=utf-8

import argparse
from utils import mrchem_job, gaussian_job, orca_job



epilog = """
USAGE

REQUIREMENTS

AUTHOR
|==========================================|
|Anders Brakestad                          |
|PhD Candidate in Computational Chemistry  |
|UiT The Arctic University of Tromsø      |
|anders.m.brakestad@uit.no                 |
|==========================================|
"""

# Set up argument parser
description = "Script for generating SLURM job files for MRChem, ORCA, and Gaussian16 on Saga, Stallo, and Fram"
parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("-S", "--destination", metavar="", type=str, default=".", help="[str] Path to job directory")
parser.add_argument("-I", "--input", type=str, required=True, metavar="", help="[str] Name of input file")
parser.add_argument("-O", "--output", type=str, required=True, metavar="", help="[str] Name of output file")
parser.add_argument("-C", "--code", choices=["mrchem", "orca", "gaussian"], metavar="", type=str, required=True,
                    help="[str] Select code: {mrchem, orca, gaussian}")
parser.add_argument("-U", "--cluster", type=str, metavar="", choices=["saga", "stallo", "fram"], required=True,
                    help="[str] Select cluster: {saga, stallo, fram}")
parser.add_argument("-D", "--dev", action="store_true", help="Generate job suitable for development queue")

args = parser.parse_args()

print("DEV mode", args.dev)