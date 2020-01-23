# coding=utf-8

import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from socket import gethostname
import subprocess
import json

from utils import orca_job, vars


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

epilog = f"""
=====
USAGE
=====
...to be continued

============
REQUIREMENTS
============
...to be continued

====================
CONFIGURATION REPORT
====================
Current cluster: {cluster}
Extension for input file: {INPUT_EXTENSION}
Extension for output file: {OUTPUT_EXTENSION}
extension for job file: {JOB_EXTENSION}
Default accounts:
    - Stallo: {ACCOUNTS['stallo']}
    - Fram:   {ACCOUNTS['fram']}
    - Saga:   {ACCOUNTS['saga']}

{cluster}-specific variables defined in \"vars\" in utils.py:
{json.dumps(vars[cluster], indent=4)}

Current PATH:
{":".join(sys.path)}

======
AUTHOR
======
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

parser.add_argument("-d", "--destination", metavar="<>", type=str, default=".", help="[str] Path to job directory")
parser.add_argument("-i", "--input", metavar="<>", type=str, help="[str] Name of input file")
parser.add_argument("-o", "--output", metavar="<>", type=str, help="[str] Name of output file")
parser.add_argument("-c", "--code", metavar="<>",choices=["mrchem", "orca", "gaussian"], type=str, required=True, help="[str] Select code: {mrchem, orca, gaussian}")
parser.add_argument("-D", "--dev", action="store_true", help="Generate job suitable for development queue")
parser.add_argument("-v", "--verbose", action="store_true", help="Run in verbose mode")
parser.add_argument("-x", "--execute", action="store_true", help="Submit job to queue")

# SLURM specific arguments
parser.add_argument("-m", "--memory", metavar="<>",type=str, default="5GB", help="Total memory per node")
parser.add_argument("-a", "--account", metavar="<>",type=str, help="Use this account on cluster")
parser.add_argument("-n", "--nodes", metavar="<>",type=str, default="1", help="Specify number of nodes")
parser.add_argument("-T", "--ntasks_per_node", metavar="<>",type=str, default="10", help="SLURM variable $NTASKS_PER_NODE")
parser.add_argument("-p", "--cpus_per_task", metavar="<>",type=str, default="0", help="SLURM variable $CPUS_PER_TASK")
parser.add_argument("-t", "--time", type=str, metavar="<>",default="00-01:00:00", help="Specify time [dd-hh:mm:ss]")
parser.add_argument("-M", "--mail", type=str, metavar="<>",default="NONE", help="Specify the SLURM mail type")

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

    job = orca_job(destination=args.destination, inputfile=args.input, outputfile=args.output, is_dev=args.dev,
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

