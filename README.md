# Slurmify
Generate slurm job files for Gaussian16, ORCA, and MRChem on Stallo, Fram, and Saga.

### Installation
Clone this repository with

```bash
$ git clone https://github.com/Andersmb/Slurmify.git
```

### Configuration
Make `slurmify.py` executable by adding the Slurmify base directory to your `PATH` in your `~/.bashrc`

```bash
$ bash setup.sh
```

You need to define paths to executables by opening the `utils.py` file and editing the `vars` dictionary. 
This has to be done in order for Slurmify to work.

You should also check that the default file extensions are to your preference, by editing the top of the
`slurmify.py` file. These are the default extensions:

* Input files: `.inp`
* Output files: `.out`
* SLURM job script files: `.job`

Finally, set your default accounts to be charged on each cluster, by editing `slurmify.py`.

### Making sure it all works
To test that Slurmify has been configured correctly, run

```bash
$ slurmify.py --test -d slurmify_config_test
```
This generates simple Hydrogen atom single-point input files for Gaussian16, ORCA, and MRChem, with the corresponding
job script files, in the directory `./slurmify_config_test`. Submit these to the queue, and check that they 
terminated correctly. If they did, then Slurmify should work.


### Full User Manual
To get the full overview of all commend-line arguments, run

```bash
$ slurmify.py -h
```
