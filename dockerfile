FROM ghcr.io/gem5/ubuntu-24.04_all-dependencies:v24-0

RUN apt-get update && \
    apt-get install -y gcc-riscv64-linux-gnu && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /gem5

CMD ["bash"]