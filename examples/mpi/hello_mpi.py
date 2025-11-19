from mpi4py import MPI


def main() -> None:
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    host = MPI.Get_processor_name()
    print(f"hello from rank {rank} of {size} on {host}")


if __name__ == "__main__":
    main()
