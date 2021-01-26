#!/usr/bin/env python
# coding=utf-8

import argparse
import sys
import os
import subprocess
import json
from socket import gethostname

from utils import orca_job, gaussian_job, mrchem_job, vars, input_origin, make_test_inputs, header, maxbilling_okay, billing

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT)


#########################################################
####--U S E R    D E F I N E D    V A R I A B L E S--####
#########################################################
# Here you can set some defaults for choice of input,
# output, and job file extensions. Also, you can define
# your preferred default accounts to use for each cluster
#########################################################
INPUT_EXTENSION = ".inp"
OUTPUT_EXTENSION = ".out"
JOB_EXTENSION = ".job"
ACCOUNTS = dict(fram="nn4654k",
                saga="nn4654k",
                stallo="nn9330k",
                betzy="nn9330k")
#########################################################

AFFIRMATIVE = ["yes", "y", ""]
CLUSTERS = ["saga", "fram", "stallo", "betzy"]

# Determine cluster
if "stallo" in gethostname():
    cluster = "stallo"
elif "fram" in gethostname():
    cluster = "fram"
elif "saga" in gethostname():
    cluster = "saga"
elif "betzy" in gethostname():
    cluster = "betzy"
else:
    cluster = "saga"


epilog = f"""
{header("usage")}
Slurmify offers a universal interface for generating SLURM job script files for
Gaussian16, ORCA, and MRChem jobs. Slurmify detects whether you are logged in to
Stallo, Saga, or Fram, and adjusts the job script accordingly.

------------------------------------------
In order to print this help message, run

$ slurmify.py -h
------------------------------------------

Before starting, make sure to make the file slurmify.py executable.
Running the setup script 'setup.sh' will add the Slurmify directory
to your PATH in your .bashrc, as well as giving executable permissions
to slurmify.py. Run the setup with

$ bash setup.sh

You may have to source your .bashrc in order for the changes to take effect.

You need to edit the file named 'utils.py' in order to set up Slurmify.
Here you adjust Gaussian, ORCA, and MRChem versions, paths to executables,
etc. This step is absolutely necessary in order for Slurmify to work.

When you have Slurmify set up, you can generate some simple single-point 
jobs on the Hydrogen atom to check that everything works. Run

$ slurmify.py --test -d testdirectory

The files will be generated in ./testdirectory. Submit the job files with
(example showed for gaussian job)

$ sbatch gaussian_test.job

A full list of the possible command-line arguments for Slurmify is given
at the top of this help message. You can adjust the normal SLURM variables,
such as number of nodes, memory, tasks, etc.

Note that ORCA and Gaussian jobs are always generated by specifying the
number of nodes, and then the number of tasks per node. MRChem jobs, however,
are specified by simply requesting the number of tasks (MPI) and number of
CPUs per task (OpenMP).
The only memory specification supported is the '--mem'option, i.e. the total
memory per node. If you need to specify the memory per process, then simply
edit the generated .job file accordingly.

If you need to copy special files to the Scratch area, then Slurmify supports
a couple of arguments for this purpose. Examples of files you may want to copy
(but not always) include the .hess file for ORCA frequency calculations, the
.chk file for Gaussian calculations, the .cmp file for ORCA compound jobs, 
or a directory containing initial-guess orbitals for MRChem calculations.

These files are automatically copied back to the submit directory:

- ORCA: .hess, .out, .gbw, .trj, .xyz
- Gaussian: .out, .chk
- MRChem: .out, .json

In addition, the StdErr is directed to an .err file, and the .log file contains
some statistics generated by SLURM (e.g. memory usage).

Note that the meaning of the ' -T / --ntasks' option varies depending on whether
the '--loc' flag is activated or deactivated. For loc jobs, -T refers to the
SLURM variable '$NTASKS', while '$NTASKS-PER-NODE' for deloc jobs.

Instructions for obtaining the MRChem code is here: 
https://mrchem.readthedocs.io/en/latest/index.html


{header("bugs")}
Please report bugs and request new features at 
https://github.com/Andersmb/Slurmify/issues


{header("requirements")}
Tested with Python >= 3.6
(on Saga, Stallo, Fram, and betzy)


{header("configuration report")}
Current cluster: {cluster}
Extension for input file   :  {INPUT_EXTENSION}
Extension for output file  :  {OUTPUT_EXTENSION}
extension for job file     :  {JOB_EXTENSION}
Default accounts:
    - Stallo               :   {ACCOUNTS['stallo']}
    - Fram                 :   {ACCOUNTS['fram']}
    - Saga                 :   {ACCOUNTS['saga']}
    - betzy                :   {ACCOUNTS['betzy']}

{cluster.upper()}-specific variables defined in \"vars\" in utils.py:
{json.dumps(vars[cluster], indent=4)}

Root directory for Slurmify: {ROOT}

Current PATH:
{':'.join(sys.path)}


|===========================================|
|=============== A U T H O R ===============|
|===========================================|
|Anders Brakestad                           |
|PhD Candidate in Computational Chemistry   |
|UiT The Arctic University of Norway        |
|anders.m.brakestad@uit.no                  |
|===========================================|
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
parser.add_argument("-f", "--force", action="store_true", help="Overwrite job files without asking for permission")
parser.add_argument("-X", "--execute", action="store_true", help="Submit job to queue")
parser.add_argument("-I", "--identifier", type=str, metavar="<>", help="How job name is presented in the queue")
parser.add_argument("--test", action="store_true", help="Generate ORCA, Gaussian, and MRChem input files and submit to queue")
parser.add_argument("--loc", action="store_true", help="Specify number of nodes, which 'localizes' the requested tasks over specific nodes")
parser.add_argument("--checkbill", action="store_true", help="Check whether the job's billing exceeds the maximum allowed for the partition")

# SLURM specific arguments
parser.add_argument("-m", "--memory", metavar="<>",type=str, help="Total memory for calculation")
parser.add_argument("-mpc", "--memory_per_cpu", metavar="<>",type=str, help="Memory per CPU")
parser.add_argument("-a", "--account", metavar="<>",type=str, help="Use this account on cluster")
parser.add_argument("-n", "--nodes", metavar="<>",type=str, default="1", help="Specify number of nodes")
parser.add_argument("-T", "--ntasks", metavar="<>",type=str, default="10", help="SLURM variable $NTASKS(-PER-NODE)")
parser.add_argument("-p", "--cpus_per_task", metavar="<>",type=str, default="10", help="SLURM variable $CPUS_PER_TASK")
parser.add_argument("-t", "--time", type=str, metavar="<>",default="00-00:30:00", help="Specify time [dd-hh:mm:ss]")
parser.add_argument("-M", "--mail", type=str, metavar="<>",default="NONE", help="Specify the SLURM mail type")
parser.add_argument("-c", "--cmd", type=str, metavar="<>",help="Specify 'mpirun' or 'srun' to submit job.")
parser.add_argument("-P", "--partition", type=str, metavar="<>",default="normal", help="Specify the queueing partition.")
parser.add_argument("-C", "--cluster", type=str, metavar="<>",choices=CLUSTERS, help="Select custom cluster for the job")

# Arguments for copying files to scratch
parser.add_argument("--chess", action="store_true", help="Look for and copy .hess file to scratch (for ORCA jobs)")
parser.add_argument("--cxyz", action="store_true", help="Look for and copy .xyz file to scratch (for ORCA jobs)")
parser.add_argument("--ccomp", action="store_true", help="Look for and copy .cmp file to scratch (for ORCA jobs)")
parser.add_argument("--cgbw", action="store_true", help="Look for and copy .gbw file to scratch (for ORCA jobs)")
parser.add_argument("--cchk", action="store_true", help="Copy .chk file to scratch (for Gaussian jobs)")
parser.add_argument("--initorb", metavar="<>", type=str, help="Path to directory storing orbitals to be copied (for MRChem jobs)")
parser.add_argument("--initchk", metavar="<>", type=str, help="Path to directory storing checkpoint orbitals to be copied (for MRChem jobs)")

args = parser.parse_args()

# Now overwrite the automatically determined cluster, if specified
if args.cluster is not None:
    cluster = args.cluster

# Sort out some things
if args.output is None: args.output = args.input
if args.account is None: args.account = ACCOUNTS[cluster]
if args.identifier is None: args.identifier = args.input

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
                        loc=args.loc,
                        slurm_account=ACCOUNTS[cluster],
                        slurm_nodes="1",
                        slurm_ntasks_per_node="1",
                        slurm_memory="1GB",
                        slurm_time="00-00:05:00",
                        slurm_mail="None",
                        slurm_partition="normal")

    job_gaussian = gaussian_job(inputfile="gaussian_test", outputfile="gaussian_test", is_dev=False,
                                cluster=cluster, extension_inputfile=INPUT_EXTENSION, extension_outputfile=OUTPUT_EXTENSION,
                                loc=args.loc,
                                slurm_account=ACCOUNTS[cluster],
                                slurm_nodes="1",
                                slurm_ntasks_per_node="1",
                                slurm_memory="1GB",
                                slurm_time="00-00:05:00",
                                slurm_mail="None",
                                slurm_partition="normal")

    job_mrchem = mrchem_job(inputfile="mrchem_test", outputfile="mrchem_test", is_dev=False,
                            cluster=cluster, extension_inputfile=INPUT_EXTENSION, extension_outputfile=OUTPUT_EXTENSION,
                            loc=args.loc,
                            slurm_account=ACCOUNTS[cluster],
                            slurm_nodes="1",
                            slurm_ntasks_per_node="1",
                            slurm_cpus_per_task="1",
                            slurm_memory="1GB",
                            slurm_time="00-00:10:00",
                            slurm_mail="None",
                            slurm_partition="normal",
                            slurm_submit_cmd=args.cmd)

    # Create job files
    with open(os.path.join(args.destination, "orca_test"+JOB_EXTENSION), "w") as f:
        for line in job_orca:
            f.write(line + "\n")

    with open(os.path.join(args.destination, "gaussian_test"+JOB_EXTENSION), "w") as f:
        for line in job_gaussian:
            f.write(line + "\n")

    with open(os.path.join(args.destination, "mrchem_test"+JOB_EXTENSION), "w") as f:
        for line in job_mrchem:
            f.write(line + "\n")

    # Create test input files
    make_test_inputs(destination=args.destination)

    # Submit jobs
    if args.execute:
        os.chdir(args.destination)
        for job in ["orca_test", "gaussian_test", "mrchem_test"]:
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
if not args.force:
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
                   slurm_ntasks_per_node=args.ntasks,
                   slurm_memory=args.memory,
                   slurm_time=args.time,
                   slurm_mail=args.mail,
                   slurm_partition=args.partition,
                   chess=args.chess,
                   cxyz=args.cxyz,
                   ccomp=args.ccomp,
                   cgbw=args.cgbw,
                   loc=args.loc,
                   identifier=args.identifier)

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
                       cluster=cluster, extension_inputfile=INPUT_EXTENSION, extension_outputfile=OUTPUT_EXTENSION,
                       slurm_account=ACCOUNTS[cluster],
                       slurm_nodes=args.nodes,
                       slurm_ntasks_per_node=args.ntasks,
                       slurm_memory=args.memory,
                       slurm_time=args.time,
                       slurm_mail=args.mail,
                       slurm_partition=args.partition,
                       cchk=args.cchk,
                       loc=args.loc,
                       identifier=args.identifier)

    with open(jobname, "w") as f:
        for line in job:
            f.write(line + "\n")

    if not args.silent:
        print(f"Generated {jobname}")

    # Now submit to queue
    if args.execute:
        os.chdir(args.destination)
        subprocess.call(["sbatch", args.input+JOB_EXTENSION])

elif Mrcheminput:
    job = mrchem_job(inputfile=args.input, outputfile=args.output, is_dev=args.dev, cluster=cluster,
                     extension_inputfile=INPUT_EXTENSION, extension_outputfile=OUTPUT_EXTENSION,
                     slurm_account=ACCOUNTS[cluster],
                     slurm_nodes=args.nodes,
                     slurm_ntasks_per_node=args.ntasks,
                     slurm_cpus_per_task=args.cpus_per_task,
                     slurm_memory=args.memory,
                     slurm_mem_per_cpu=args.memory_per_cpu,
                     slurm_time=args.time,
                     slurm_mail=args.mail,
                     slurm_submit_cmd=args.cmd,
                     slurm_partition=args.partition,
                     initorb=args.initorb,
                     initchk=args.initchk,
                     loc=args.loc,
                     identifier=args.identifier)

    # Check that the job does not exceed maximum billing
    if args.checkbill:
        result, bill = maxbilling_okay(cluster=cluster,
                               ntasks=args.ntasks,
                               ncpus_per_task=args.cpus_per_task,
                               mem=args.memory,
                               mem_per_cpu=args.memory_per_cpu,
                               partition=args.partition)
        assert result, f"Your job ({bill}) exceeds the maximum number of billing units allowed on {cluster} ({billing[cluster]['max']})."

    with open(jobname, "w") as f:
        for line in job:
            f.write(line + "\n")

    if not args.silent:
        print(f"Generated {jobname}")

    # Now submit to queue
    if args.execute:
        os.chdir(args.destination)
        subprocess.call(["sbatch", args.input+JOB_EXTENSION])
