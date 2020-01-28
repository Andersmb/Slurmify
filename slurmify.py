# coding=utf-8

import argparse
import sys
import os
import subprocess
import json
import shutil
from socket import gethostname

from utils import orca_job, gaussian_job, vars, input_origin, make_test_inputs

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT)


# Set some defaults
INPUT_EXTENSION = ".inp"
INPUT_EXTENSION_GAUSSIAN = ".com"
OUTPUT_EXTENSION = ".out"
JOB_EXTENSION = ".job"
ACCOUNTS = dict(fram="nn4654k",
                saga="nn4654k",
                stallo="nn9330k")
AFFIRMATIVE = ["yes", "y", ""]

# Determine cluster
if "stallo" in gethostname():
    cluster = "stallo"
elif "fram" in gethostname():
    cluster = "fram"
elif "saga" in gethostname():
    cluster = "saga"
else:
    cluster = "saga"


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

{cluster.upper()}-specific variables defined in \"vars\" defined in utils.py:
{json.dumps(vars[cluster], indent=4)}

Root directory for Slurmify: {ROOT}

Current PATH:
{':'.join(sys.path)}


|=================AUTHOR===================|
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
parser.add_argument("-D", "--dev", action="store_true", help="Generate job suitable for development queue")
parser.add_argument("-S", "--silent", action="store_true", help="Run in silent mode")
parser.add_argument("-X", "--execute", action="store_true", help="Submit job to queue")
parser.add_argument("--test", action="store_true", help="Generate ORCA, Gaussian, and MRChem input files and submit to queue")

# SLURM specific arguments
parser.add_argument("-m", "--memory", metavar="<>",type=str, default="5GB", help="Total memory per node")
parser.add_argument("-a", "--account", metavar="<>",type=str, help="Use this account on cluster")
parser.add_argument("-n", "--nodes", metavar="<>",type=str, default="1", help="Specify number of nodes")
parser.add_argument("-T", "--ntasks_per_node", metavar="<>",type=str, default="10", help="SLURM variable $NTASKS_PER_NODE")
parser.add_argument("-p", "--cpus_per_task", metavar="<>",type=str, default="0", help="SLURM variable $CPUS_PER_TASK")
parser.add_argument("-t", "--time", type=str, metavar="<>",default="00-00:30:00", help="Specify time [dd-hh:mm:ss]")
parser.add_argument("-M", "--mail", type=str, metavar="<>",default="NONE", help="Specify the SLURM mail type")

# Arguments for copying files to scratch
parser.add_argument("--chess", action="store_true", help="Look for and copy .hess file to scratch (for ORCA jobs)")
parser.add_argument("--cxyz", action="store_true", help="Look for and copy .xyz file to scratch (for ORCA jobs)")
parser.add_argument("--ccomp", action="store_true", help="Look for and copy .cmp file to scratch (for ORCA jobs)")
parser.add_argument("--cbgw", action="store_true", help="Look for and copy .bgw file to scratch (for ORCA jobs)")
parser.add_argument("--cchk", action="store_true", help="Copy .chk file to scratch (for Gaussian jobs)")

args = parser.parse_args()

# Sort out some things
if args.output is None: args.output = args.input
if args.account is None: args.account = ACCOUNTS[cluster]

# Evaluate whether the destination exists, and ask for permission to create if
if not os.path.isdir(args.destination):
    answer = input(f"The directory \"{args.destination}\" does not exist. Do you want to create it? (Y/n) ")
    if answer not in AFFIRMATIVE:
        sys.exit("Aborting")
    else:
        os.mkdir(args.destination)
        print(f"Created \"{args.destination}\"")

# Run testing module
if args.test:
    job_orca = orca_job(inputfile="orca_test", outputfile="orca_test", is_dev=False,
                   cluster=cluster, extension_inputfile=INPUT_EXTENSION, extension_outputfile=OUTPUT_EXTENSION,
                   slurm_account=ACCOUNTS[cluster],
                   slurm_nodes="1",
                   slurm_ntasks_per_node="1",
                   slurm_memory="1GB",
                   slurm_time="00-00:05:00",
                   slurm_mail="None")

    job_gauss = gaussian_job(inputfile="gaussian_test", outputfile="gaussian_test", is_dev=False,
                   cluster=cluster, extension_inputfile=INPUT_EXTENSION_GAUSSIAN, extension_outputfile=OUTPUT_EXTENSION,
                   slurm_account=ACCOUNTS[cluster],
                   slurm_nodes="1",
                   slurm_ntasks_per_node="1",
                   slurm_memory="1GB",
                   slurm_time="00-00:05:00",
                   slurm_mail="None")

    job_mrchem = ""

    # Create job files
    with open(os.path.join(args.destination, "orca_test"+JOB_EXTENSION), "w") as f:
        for line in job_orca:
            f.write(line + "\n")

    with open(os.path.join(args.destination, "gaussian_test"+JOB_EXTENSION), "w") as f:
        for line in job_gauss:
            f.write(line + "\n")

    with open(os.path.join(args.destination, "mrchem_test"+JOB_EXTENSION), "w") as f:
        for line in job_mrchem:
            f.write(line + "\n")

    # Create test input files
    make_test_inputs(destination=args.destination,
                     extension=INPUT_EXTENSION,
                     gaussian_extension=INPUT_EXTENSION_GAUSSIAN)

    # Make sure that the user does not request multiple dev jobs, since each user is limited to just one at a time
    if args.dev:
        print("Warning: You are limited to just one dev job at any given time. Therefore normal jobs are now created.")

    # Submit jobs
    if args.execute:
        jobs = [os.path.join(args.destination, f) for f in ["orca_test", "gaussian_test", "mrchem_test"]]
        os.chdir(args.destination)
        print("pwd", os.getcwd())
        print("Jobs:", "\n".join(jobs))
        for job in jobs:
            subprocess.call(["sbatch", job+JOB_EXTENSION])


    sys.exit("Testing done")

# Define name of job file
jobname = os.path.join(args.destination, args.input + JOB_EXTENSION)

# Determine origin of input file
GaussianInput, OrcaInput, Mrcheminput = input_origin(os.path.join(args.destination, args.input+INPUT_EXTENSION))
if not args.silent:
    if GaussianInput:
        print("Gaussian input file detected.")
    elif OrcaInput:
        print("ORCA input file detected.")
    else:
        print("MRChem input file detected.")

# Make sure not to silently overwrite existing files
if os.path.isfile(jobname):
    answer = input("The .job file exists. Do you want to overwrite it? (Y/n) ").lower()
    if answer not in AFFIRMATIVE:
        sys.exit("Aborted")

# Generate job files
if OrcaInput:
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

    if not args.silent:
        print(f"Generated {jobname}")

    # Now submit to queue
    if args.execute:
        os.chdir(args.destination)
        subprocess.call(["sbatch", args.input+JOB_EXTENSION])

elif GaussianInput:
    job = gaussian_job(inputfile=args.input, outputfile=args.output, is_dev=args.dev,
                   cluster=cluster, extension_inputfile=INPUT_EXTENSION_GAUSSIAN, extension_outputfile=OUTPUT_EXTENSION,
                   slurm_account=ACCOUNTS[cluster],
                   slurm_nodes=args.nodes,
                   slurm_ntasks_per_node=args.ntasks_per_node,
                   slurm_memory=args.memory,
                   slurm_time=args.time,
                   slurm_mail=args.mail,
                   cchk=args.cchk)

    with open(jobname, "w") as f:
        for line in job:
            f.write(line + "\n")

    if not args.silent:
        print(f"Generated {jobname}")

    # Now submit to queue
    if args.execute:
        os.chdir(args.destination)
        subprocess.call(["sbatch", args.input+JOB_EXTENSION])


# TODO gaussian test jobs terminating with segmentation error. why?
