import sys
import os


def gaussian_job(destination=None, inputfile=None, outputfile=None, is_dev=None, slurm_account=None, slurm_nodes=None,
                 slurm_tasks_per_node=None, slurm_cpus_per_node=None, slurm_memory=None, slurm_time=None, mail=None):
    pass


def orca_job(destination=None, inputfile=None, outputfile=None, is_dev=None, slurm_account=None, slurm_nodes=None,
             slurm_tasks_per_node=None, slurm_cpus_per_node=None, slurm_memory=None, slurm_time=None, mail=None):
    pass


def mrchem_job(destination=None, inputfile=None, outputfile=None, is_dev=None, slurm_account=None, slurm_nodes=None,
               slurm_tasks_per_node=None, slurm_cpus_per_node=None, slurm_memory=None, slurm_time=None, mail=None):
    pass


if __name__ == "__main__":
    print(f"You just executed {__file__}")