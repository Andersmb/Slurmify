# coding=utf-8

import argparse
import sys
import os
from socket import gethostname
import subprocess

from utils import orca_job


# Determine cluster
if "stallo" in gethostname():
    cluster = "stallo"
elif "fram" in gethostname():
    cluster = "fram"
elif "saga" in gethostname():
    cluster = "saga"
else:
    cluster = "stallo"

# Set some defaults
INPUT_EXTENSION = ".inp"
OUTPUT_EXTENSION = ".out"
JOB_EXTENSION = ".job"
ACCOUNTS = dict(fram="nn4654k",
                saga="nn4654k",
                stallo="nn9330k")

epilog = """
USAGE

REQUIREMENTS

AUTHOR
|==========================================|
|Anders Brakestad                          |
|PhD Candidate in Computational Chemistry  |
|UiT The Arctic University of Norway       |
|anders.m.brakestad@uit.no                 |
|==========================================|
"""

# Set up argument parser
description = "Script for generating SLURM job files for MRChem, ORCA, and Gaussian16 on Saga, Stallo, and Fram"
parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument("-S", "--destination", metavar="", type=str, default=".", help="[str] Path to job directory")
parser.add_argument("-I", "--input", type=str, required=True, metavar="", help="[str] Name of input file")
parser.add_argument("-O", "--output", type=str, metavar="", help="[str] Name of output file")
parser.add_argument("-C", "--code", choices=["mrchem", "orca", "gaussian"], metavar="", type=str, required=True,
                    help="[str] Select code: {mrchem, orca, gaussian}")
parser.add_argument("-D", "--dev", action="store_true", help="Generate job suitable for development queue")
parser.add_argument("-V", "--verbose", action="store_true", help="Run in verbose mode")
parser.add_argument("-X", "--execute", action="store_true", help="Submit job to queue")

# SLURM specific arguments
parser.add_argument("-M", "--memory", type=str, default="5GB", metavar="", help="Total memory per node")
parser.add_argument("-A", "--account", type=str, metavar="", help="Use this account on cluster")
parser.add_argument("-N", "--nodes", type=str, metavar="", default="1", help="Specify number of nodes")
parser.add_argument("-T", "--ntasks_per_node", type=str, default="10", metavar="", help="SLURM variable $NTASKS_PER_NODE")
parser.add_argument("-P", "--cpus_per_task", type=str, default="0", metavar="", help="SLURM variable $CPUS_PER_TASK")
parser.add_argument("-t", "--time", type=str, default="00-01:00:00", metavar="", help="Specify time [dd-hh:mm:ss]")
parser.add_argument("-m", "--mail", type=str, default="NONE", metavar="", help="Specify the SLURM mail type")

# Arguments for copying files to scratch
parser.add_argument("--chess", action="store_true", help="Look for and copy .hess file (for ORCA jobs)")
parser.add_argument("--cxyz", action="store_true", help="Look for and copy .xyz file (for ORCA jobs)")
parser.add_argument("--ccomp", action="store_true", help="Look for and copy .cmp file (for ORCA jobs)")
parser.add_argument("--cbgw", action="store_true", help="Look for and copy .bgw file (for ORCA jobs)")

args = parser.parse_args()

# Sort out some things
if args.output is None: args.output = args.input
if args.account is None: args.account = ACCOUNTS[cluster]

# Define name of job file
jobname = os.path.join(args.destination, args.input + JOB_EXTENSION)

if args.code == "orca":

    job = orca_job(inputfile=args.input, outputfile=args.output, is_dev=args.dev,
                   cluster=cluster, extension_inputfile=INPUT_EXTENSION, extension_outputfile=OUTPUT_EXTENSION,
                   slurm_account=ACCOUNTS[cluster],
                   slurm_nodes=args.nodes,
                   slurm_ntasks_per_node=args.ntasks_per_node,
                   slurm_memory=args.memory,
                   slurm_time=args.time,
                   slurm_mail=args.mail,
                   chess=args.chess,
                   cxyz=args.cxyz,
                   ccomp=args.ccomp,
                   cbgw=args.cbgw)

    with open(jobname, "w") as f:
        for line in job:
            f.write(line + "\n")

    if args.verbose:
        print(f"Generated {jobname}")

    # Now execute
    # if args.execute:
    #     os.chdir(args.destination)
    #     subprocess.call(["sbatch", args.input+JOB_EXTENSION])

