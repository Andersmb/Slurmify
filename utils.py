import sys
import os
import datetime


#########################################################
#   --U S E R    D E F I N E D    V A R I A B L E S--   #
#########################################################
# You need to make sure to get the following paths and
# modules correct, in order for Slumify to run with
# problems.
# The variable 'orbdir' you can set freely, but it is
# recommended that this is limited to the work area,
# since orbital files can occupy many GBs worth of data
#########################################################
vars = {
    "stallo": {
        "mpi_version": "OpenMPI/3.1.3-GCC-8.2.0-2.31.1",
        "gaussian_version": "Gaussian/g16_B.01",
        "scratch": f"/global/work/ambr/${{SLURM_JOBID}}",
        "path_orca": f"/home/ambr/software/orca_4_2_1_linux_x86-64_openmpi314",
        "path_mpi": "/global/hds/software/cpu/eb3/OpenMPI/3.1.3-GCC-8.2.0-2.31.1/lib",
        "path_mrchem": "/home/ambr/mrchem_master200303/build/bin",
        "mrchem_venv": "/home/ambr/.local/share/virtualenvs/mrchem_master200303-X6sXxlx6/bin/activate",
        "modules_mrchem": ["intel/2018b", "Python/3.7.0-intel-2018b"],
        "orbdir": "/global/work/ambr/MWorbitals_${SLURM_JOBID}"
    },
    "fram": {
        "mpi_version": "OpenMPI/3.1.3-GCC-8.2.0-2.31.1",
        "gaussian_version": "Gaussian/g16_B.01",
        "path_orca": f"/cluster/home/ambr/software/orca_4_1_1_linux_x86-64_openmpi313",
        "path_mpi": "/cluster/software/OpenMPI/3.1.3-GCC-8.2.0-2.31.1/lib",
        "path_mrchem": "/cluster/home/ambr/mrchem022/build/bin",
        "modules_mrchem": ["intel/2017a", "Python/3.6.1-intel-2017a"],
        "mrchem_venv": "/cluster/home/ambr/.local/share/virtualenvs/mrchem022-RcvyK6hG/bin/activate",
        "orbdir": "/cluster/work/users/ambr/MWorbitals_${SLURM_JOBID}"
    },
    "saga": {
        "mpi_version": "OpenMPI/3.1.4-GCC-8.3.0",
        "gaussian_version": "Gaussian/g16_B.01",
        "path_orca": f"/cluster/home/ambr/software/orca_4_2_1_linux_x86-64_openmpi314",
        "path_mpi": "/cluster/software/OpenMPI/3.1.4-GCC-8.3.0/bin",
        "path_mrchem": "/cluster/home/ambr/mrchem_master200412/build/bin",
        "modules_mrchem": ["intel/2018b", "Python/3.6.6-intel-2018b"],
        "mrchem_venv": "/cluster/home/ambr/.local/share/virtualenvs/mrchem_master200412-LD0TdiUP/bin/activate",
        "orbdir": "/cluster/work/users/ambr/MWorbitals_${SLURM_JOBID}"
    }
}
#########################################################


def header(hdr):
    title = "="*20 + " "*5 + " ".join(hdr.upper()) + " "*5 + "="*20
    my_header = f"""
    {"="*len(title)}
    {title}
    {"="*len(title)}
    """
    return my_header


def make_test_inputs(destination=".", extension=".inp"):
    """
    Generate simple single-point calculations on H atom for testing if the job script works.
    :param destination: testing directory. current dir if not specified
    :param extension: input file extension for orca and mrchem
    :param gaussian_extension: gaussian input file extension
    :return:
    """
    with open(os.path.join(destination, "mrchem_test"+extension), "w") as f:
        f.write("world_prec = 1.0e-4\n")
        f.write("world_size = 4\n")
        f.write("\n")
        f.write("Basis {\n")
        f.write("order = 8\n")
        f.write("type = interpolating\n")
        f.write("}\n")
        f.write("\n")
        f.write("Molecule {\n")
        f.write("charge = 0\n")
        f.write("multiplicity = 2\n")
        f.write("angstrom = true\n")
        f.write("translate = true\n")
        f.write("$coords\n")
        f.write("H 0.0 0.0 0.0\n")
        f.write("$end\n")
        f.write("}\n")
        f.write("\n")
        f.write("WaveFunction {\n")
        f.write("method = pbe\n")
        f.write("restricted = false\n")
        f.write("}\n")
        f.write("\n")
        f.write("Properties {\n")
        f.write("scf_energy = true\n")
        f.write("}\n")
        f.write("\n")
        f.write("SCF {\n")
        f.write("kain = 4\n")
        f.write("initial_guess = sad_dz\n")
        f.write("}\n")

    with open(os.path.join(destination, "gaussian_test"+extension), "w") as f:
        f.write("#p pbepbe\n")
        f.write("\n")
        f.write("Comment\n")
        f.write("\n")
        f.write("0 2\n")
        f.write("H 0.0 0.0 0.0\n")
        f.write("\n")

    with open(os.path.join(destination, "orca_test"+extension), "w") as f:
        f.write("! pbe sto-3g\n")
        f.write("* xyz 0 2\n")
        f.write("H 0.0 0.0 0.0\n")
        f.write("*\n")


def input_origin(inputfile):
    G, O, M = False, False, False
    content = open(inputfile).readlines()
    if any(["".join(line.split()).startswith("*xyz") for line in content]):
        O = True
    elif any(["".join(line.split()).startswith("world_prec") for line in content]):
        M = True
    else:
        G = True
    return G, O, M


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
             cluster=None, slurm_ntasks_per_node=None, slurm_memory=None, slurm_time=None, slurm_partition=None,
             slurm_mail=None, extension_outputfile=None, extension_inputfile=None, chess=False, cxyz=False, ccomp=False,
             cbgw=False, deloc=None, identifier=None):
    """

    :param inputfile: name of input file without extension
    :param outputfile: name of output file without extension
    :param is_dev: prepare for development queue
    :param slurm_account: slurm account number to be charged
    :param slurm_nodes: number of nodes
    :param cluster: for which cluster will the job be made
    :param slurm_ntasks_per_node: number of tasks per node
    :param slurm_memory: total memory per node
    :param slurm_time: time limit for job
    :param slurm_mail: mail notification type
    :param extension_outputfile: extension used for output file
    :param extension_inputfile: extension used for input file
    :param chess: copy .hess file to scratch
    :param cxyz: copy .xyz file to scratch
    :param ccomp: copy .cmp file to scratcg
    :param cbgw: copy .bgw file to scratcg
    :param deloc: non-exclusive, use --ntasks instead of --ntasks-per-node
    :param identifier: how job name is presented in the queue. Does not affect name of input file
    :return:
    """

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
    jobfile.append(f"#SBATCH --job-name={identifier}")
    jobfile.append(f"#SBATCH --output={outputfile+'.log'}")
    jobfile.append(f"#SBATCH --error={outputfile+'.err'}")
    if not deloc:
        jobfile.append(f"#SBATCH --nodes={slurm_nodes}")
        jobfile.append(f"#SBATCH --ntasks-per-node={slurm_ntasks_per_node}")
    else:
        jobfile.append(f"#SBATCH --ntasks={slurm_ntasks_per_node}")
    jobfile.append(f"#SBATCH --time={slurm_time}")
    if cluster != "fram": jobfile.append(f"#SBATCH --mem={slurm_memory}")
    jobfile.append(f"#SBATCH --mail-type={slurm_mail}")
    if is_dev: 
        jobfile.append("#SBATCH --qos=devel")
    else:
        jobfile.append(f"#SBATCH --partition={slurm_partition}")
    jobfile.append("")
    jobfile.append("module purge")
    jobfile.append(f"module load {vars[cluster]['mpi_version']}")
    jobfile.append("")

    if cluster == "stallo":
        jobfile.append(f"SCRATCH={vars[cluster]['scratch']}")
        jobfile.append("mkdir $SCRATCH")
        jobfile.append("")

    # Copy files to SCRATCH
    jobfile.append(f"cp {inputfile+extension_inputfile} $SCRATCH")

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
    jobfile.append(f"time $ORCA/orca {inputfile+extension_inputfile} > {outputfile+extension_outputfile}")
    jobfile.append("")

    # Copy back files
    for ext in [".hess", ".xyz", ".bgw", ".trj", ".out"]:
        jobfile.append(f"cp {inputfile + ext} $SLURM_SUBMIT_DIR")
    if ccomp:
        jobfile.append("cp *.hess $SLURM_SUBMIT_DIR")

    jobfile.append("")

    # Clean up (On Fram and Saga clean up is automatic)
    if cluster == "stallo":
        jobfile.append("rm $SCRATCH/*")
        jobfile.append("rmdir $SCRATCH")

    jobfile.append("")
    jobfile.append("exit 0")

    return jobfile


def gaussian_job(inputfile=None, outputfile=None, is_dev=None, slurm_account=None, slurm_nodes=None,
                 cluster=None, slurm_ntasks_per_node=None, slurm_memory=None, slurm_time=None, slurm_partition=None,
                 slurm_mail=None, extension_outputfile=None, extension_inputfile=None, cchk=False, deloc=None,
                 identifier=None):

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
    jobfile.append(f"#SBATCH --job-name={identifier}")
    jobfile.append(f"#SBATCH --output={outputfile+'.log'}")
    jobfile.append(f"#SBATCH --error={outputfile+'.err'}")
    if not deloc: jobfile.append(f"#SBATCH --nodes={slurm_nodes}")
    jobfile.append(f"#SBATCH --ntasks-per-node={slurm_ntasks_per_node}")
    jobfile.append(f"#SBATCH --time={slurm_time}")
    if cluster != "fram": jobfile.append(f"#SBATCH --mem={slurm_memory}")
    jobfile.append(f"#SBATCH --mail-type={slurm_mail}")
    if is_dev: 
        jobfile.append("#SBATCH --qos=devel")
    else:
        jobfile.append(f"#SBATCH --partition={slurm_partition}")
    jobfile.append("")
    jobfile.append("module purge")
    jobfile.append(f"module load {vars[cluster]['gaussian_version']}")
    jobfile.append("")

    if cluster == "saga":
        jobfile.append("export GAUSS_LFLAGS2='--LindaOptions -s 20000000'")
        jobfile.append("")

    if cluster == "stallo":
        jobfile.append(f"SCRATCH={vars[cluster]['scratch']}")
        jobfile.append(f"mkdir -p $SCRATCH")
        jobfile.append("")

    # Copy files to SCRATCH
    jobfile.append(f"cp {inputfile+extension_inputfile} $SCRATCH")

    if cchk:
        if os.path.isfile(inputfile+'.chk'):
            jobfile.append(f"cp {inputfile+'.chk'} $SCRATCH")
        else:
            print(f"Warning: Copy of .chk file requested, but the file does not exist ({inputfile+'.chk'}). Continuing without copying file.")

    # Execute Gaussian
    jobfile.append("")
    jobfile.append(f"cd $SCRATCH")

    if cluster == "stallo":
        if extension_inputfile != ".com":
            jobfile.append(f"mv {inputfile+extension_inputfile} {inputfile+'.com'}")
        jobfile.append(f"G09.prep.slurm {inputfile}")
        if extension_inputfile != ".com":
            jobfile.append(f"mv {inputfile+'.com'} {inputfile+extension_inputfile}")
        jobfile.append("")

    jobfile.append(f"time g16.ib {inputfile+extension_inputfile} > {outputfile+extension_outputfile}")
    jobfile.append("")

    # Copy back files
    for ext in [".out", ".chk"]:
        jobfile.append(f"cp {inputfile + ext} $SLURM_SUBMIT_DIR")

    jobfile.append("")

    # Clean up (On Fram and Saga clean up is automatic)
    if cluster == "stallo":
        jobfile.append(f"rm $SCRATCH/*")
        jobfile.append(f"rmdir $SCRATCH")
        jobfile.append("")

    jobfile.append("exit 0")

    return jobfile


def mrchem_job(inputfile=None, outputfile=None, is_dev=None, slurm_account=None, slurm_nodes=None, slurm_partition=None,
               cluster=None, slurm_ntasks_per_node=None, slurm_cpus_per_task=None, slurm_memory=None, slurm_time=None,
               slurm_mail=None, extension_outputfile=None, extension_inputfile=None, initorb=None, deloc=None,
               identifier=None, slurm_submit_cmd="srun"):

    assert slurm_memory.endswith("B"), "You must specify units of memory allocation (number must end with 'B')"
    assert slurm_submit_cmd in ["mpirun", "srun"], "Invalid parallelization command used to submit MRChem job"

    timestamp = f"# File generated {datetime.datetime.now()}"

    jobfile = []
    jobfile.append("#! /bin/bash")
    jobfile.append("")
    jobfile.append(f"#{'-' * len(timestamp)}")
    jobfile.append(timestamp)
    jobfile.append(f"#{'-' * len(timestamp)}")
    jobfile.append("")
    jobfile.append(f"#SBATCH --account={slurm_account}")
    jobfile.append(f"#SBATCH --job-name={identifier}")
    jobfile.append(f"#SBATCH --output={outputfile + '.log'}")
    jobfile.append(f"#SBATCH --error={outputfile + '.err'}")
    if not deloc:
        jobfile.append(f"#SBATCH --nodes={slurm_nodes}")
        jobfile.append(f"#SBATCH --ntasks-per-node={slurm_ntasks_per_node}")
    else:
        jobfile.append(f"#SBATCH --ntasks={slurm_ntasks_per_node}")
    jobfile.append(f"#SBATCH --cpus-per-task={slurm_cpus_per_task}")
    jobfile.append(f"#SBATCH --time={slurm_time}")
    if cluster != "fram": jobfile.append(f"#SBATCH --mem={slurm_memory}")
    jobfile.append(f"#SBATCH --mail-type={slurm_mail}")
    if is_dev: 
        jobfile.append("#SBATCH --qos=devel")
    else:
        jobfile.append(f"#SBATCH --partition={slurm_partition}")
    jobfile.append("")
    jobfile.append("module purge")
    for module in vars[cluster]["modules_mrchem"]:
        jobfile.append(f"module load {module}")
    jobfile.append("")

    jobfile.append(f"export OMP_NUM_THREADS={slurm_cpus_per_task}")
    jobfile.append("")

    if cluster == "stallo":
        jobfile.append(f"SCRATCH={vars[cluster]['scratch']}")
        jobfile.append(f"mkdir -p $SCRATCH")
        jobfile.append("")

    jobfile.append(f"cp {os.path.join(inputfile+extension_inputfile)} $SCRATCH")

    if initorb is not None:
        jobfile.append(f"cp -r {initorb} $SCRATCH/initial_guess")

    jobfile.append("")
    jobfile.append(f"source {vars[cluster]['mrchem_venv']}")
    jobfile.append("")

    jobfile.append("cd $SCRATCH")
    jobfile.append(f"{vars[cluster]['path_mrchem']}/mrchem -D {inputfile+extension_inputfile}")
    jobfile.append(f"{slurm_submit_cmd} {vars[cluster]['path_mrchem']}/mrchem.x {inputfile+'.json'} > {inputfile+extension_outputfile}")
    jobfile.append("")

    if cluster == "stallo":
        jobfile.append(f"cp {inputfile+extension_outputfile} ${{SLURM_SUBMIT_DIR}}/")
    else:
        jobfile.append(f"savefile {inputfile+extension_outputfile}")

    jobfile.append(f"mkdir -p {vars[cluster]['orbdir']}")
    jobfile.append(f"cp orbitals/* {vars[cluster]['orbdir']}/")
    jobfile.append(f"echo {vars[cluster]['orbdir']} > ${{SLURM_SUBMIT_DIR}}/{inputfile}.orbitals")

    jobfile.append("")
    jobfile.append("exit 0")

    return jobfile


if __name__ == "__main__":
    print(f"Nothing happens when you execute {__file__}")
