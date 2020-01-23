import sys
import os
import datetime


# Set some variables
vars = {
    "stallo": {
        "mpi_version": "OpenMPI/3.1.3-GCC-8.2.0-2.31.1",
        "scratch": f"/global/work/ambr/${{SLURM_JOBID}}",
        "path_orca": f"/home/ambr/software/orca_4_1_2_linux_x86-64_openmpi313/orca",
        "path_mpi": "/global/hds/software/cpu/eb3/OpenMPI/3.1.3-GCC-8.2.0-2.31.1/bin/mpirun"
    },
    "fram": {
        "mpi_version": "OpenMPI/3.1.3-GCC-8.2.0-2.31.1",
        "path_orca": f"/cluster/home/ambr/software/orca_4_1_1_linux_x86-64_openmpi313/orca",
        "path_mpi": "/cluster/software/OpenMPI/3.1.3-GCC-8.2.0-2.31.1/bin/mpirun"
    },
    "saga": {
        "mpi_version": "OpenMPI/3.1.1-GCC-7.3.0-2.30",
        "path_orca": f"/cluster/home/ambr/software/orca_4_1_1_linux_x86-64_openmpi313/orca",
        "path_mpi": "/cluster/software/OpenMPI/3.1.1-GCC-7.3.0-2.30/bin"
    }
}


def get_orca_hessfile(inputfile):
    try:
        content = open(inputfile).readlines()
        for line in content:
            if line.lower().strip().startswith("inhessname"):
                return line.split()[1][1:-1]
        else:
            sys.exit("Error! Could not locate .hess file in input file.")
    except FileNotFoundError:
        sys.exit(f"Error! The input file ({inputfile}) was not found")


def get_orca_xyzfile(inputfile):
    try:
        content = open(inputfile).readlines()
        for line in content:
            if "".join(line.split()).strip().startswith("*xyzfile"):
                return line.split()[-1].strip()
        else:
            sys.exit("Error! Could not locate .xyz file in input file.")
    except FileNotFoundError:
        sys.exit(f"Error! The input file ({inputfile}) was not found")


def get_orca_compfile(inputfile):
    try:
        content = open(inputfile).readlines()
        for i, line in enumerate(content):
            # Catch the oneliner
            if "".join(line.lower().split()).strip().startswith("%compound") and line.strip().endswith("end"):
                return line.split()[-2][1:-1]
            # Catch the multiliner
            elif line.lower().strip().startswith("%") and "compound" in line and "end" not in line:
                return content[i+1].strip()[1:-1]
        else:
            sys.exit("Error! Could not locate .cmp file in input file.")
    except FileNotFoundError:
        sys.exit(f"Error! The input file ({inputfile}) was not found")


def get_orca_bgwfile(inputfile):
    try:
        content = open(inputfile).readlines()
        for line in content:
            if "".join(line.lower().split()).startswith("%moinp"):
                return line.split()[-1][1:-1]
        else:
            sys.exit("Error! Could not locate .bgw file in input file.")
    except FileNotFoundError:
        sys.exit(f"Error! The input file ({inputfile}) was not found")


def orca_job(inputfile=None, outputfile=None, is_dev=None, slurm_account=None, slurm_nodes=None,
             cluster=None, slurm_ntasks_per_node=None, slurm_memory=None, slurm_time=None,
             slurm_mail=None, extension_outputfile=None, extension_inputfile=None, chess=False, cxyz=False, ccomp=False,
             cbgw=False):

    assert slurm_memory.endswith("B"), "You must specify units of memory allocation (number must end with 'B')"

    timestamp = f"# File generated {datetime.datetime.now()}"

    jobfile = []
    jobfile.append("#! /bin/bash")
    jobfile.append("")
    jobfile.append(f"#{'-'*len(timestamp)}")
    jobfile.append(timestamp)
    jobfile.append(f"#{'-'*len(timestamp)}")
    jobfile.append("")
    jobfile.append(f"#SBATCH --account={slurm_account}")
    jobfile.append(f"#SBATCH --job-name={inputfile}")
    jobfile.append(f"#SBATCH --output={outputfile+'.log'}")
    jobfile.append(f"#SBATCH --error={outputfile+'.err'}")
    jobfile.append(f"#SBATCH --nodes={slurm_nodes}")
    jobfile.append(f"#SBATCH --ntasks-per-node={slurm_ntasks_per_node}")
    jobfile.append(f"#SBATCH --time={slurm_time}")
    jobfile.append(f"#SBATCH --mem={slurm_memory}")
    jobfile.append(f"#SBATCH --mail-type={slurm_mail}")
    if is_dev: jobfile.append("#SBATCH --qos=devel")
    jobfile.append("")
    jobfile.append("module purge")
    jobfile.append(f"module load {vars[cluster]['mpi_version']}")
    jobfile.append("")

    if cluster == "stallo":
        jobfile.append(f"SCRATCH={vars[cluster]['scratch']}")
        jobfile.append("mkdir $SCRATCH")
        jobfile.append("")

    # Define files for copying
    # Use arguments to specify which files to copy

    # Copy files to SCRATCH
    jobfile.append(f"cp {inputfile+extension_inputfile} $SCRATCH")

    # Determine which hess file to copy. Open the input file and look for a file name there,
    # if not file is found, then try to copy a hess file with the same base name as the input file.
    # If that also fails, then exit with error message.
    # The same approach is used for xyz, cmp, and bgw files.
    if chess:
        hessfile = get_orca_hessfile(inputfile+extension_inputfile)
        if not os.path.isfile(hessfile):
            sys.exit("Error! The .hess file specified does not exist.")
        jobfile.append(f"cp {hessfile} $SCRATCH")
    if cxyz:
        xyzfile = get_orca_xyzfile(inputfile+extension_inputfile)
        if not os.path.isfile(xyzfile):
            sys.exit("Error! The .xyz file specified does not exist.")
        jobfile.append(f"cp {xyzfile} $SCRATCH")
    if ccomp:
        compfile = get_orca_compfile(inputfile+extension_inputfile)
        if not os.path.isfile(compfile):
            sys.exit("Error! The .cmp file specified does not exist.")
        jobfile.append(f"cp {compfile} $SCRATCH")
    if cbgw:
        bgwfile = get_orca_bgwfile(inputfile+extension_inputfile)
        if not os.path.isfile(bgwfile):
            sys.exit("Error! The .bgw file specified does not exist.")
        jobfile.append(f"cp {bgwfile} $SCRATCH")

    # Export variables
    jobfile.append("")
    jobfile.append(f"ORCA={vars[cluster]['path_orca']}")
    jobfile.append(f"MPI={vars[cluster]['path_mpi']}")
    jobfile.append("")

    jobfile.append("export PATH=$ORCA:$PATH")
    jobfile.append(f"export PATH={'$MPI'}:$PATH")
    jobfile.append("export LD_LIBRARY_PATH=$ORCA:$LD_LIBRARY_PATH")
    jobfile.append(f"export LD_LIBRARY_PATH={'$MPI'}:$LD_LIBRARY_PATH")
    jobfile.append("export RSH_COMMAND=\"/usr/bin/ssh -x\"")

    # Execute ORCA
    jobfile.append("")
    jobfile.append("cd $SCRATCH")
    jobfile.append(f"time $ORCA {inputfile+extension_inputfile} >& {outputfile+extension_outputfile}")
    jobfile.append("")

    # Copy back files
    for ext in [".hess", ".xyz", "bgw", ".trj"]:
        jobfile.append(f"cp {inputfile + ext} $SLURM_SUBMIT_DIR")

    jobfile.append("")

    # Clean up (On Fram and Saga clean up is automatic)
    if cluster == "stallo":
        jobfile.append("rm $SCRATCH/*")
        jobfile.append("rmdir $SCRATCH")

    return jobfile


if __name__ == "__main__":
    print(f"You just executed {__file__}")