FROM ghcr.io/gem5/ubuntu-24.04_all-dependencies:v24-0

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu libc6-dev-riscv64-cross git && \
    rm -rf /var/lib/apt/lists/*

ENV GEM5_ROOT=/gem5
ENV PYTHONPATH=/gem5/src/python

RUN git clone --depth 1 https://github.com/gem5/gem5.git /gem5

WORKDIR /gem5

# Build gem5 for RISC-V (this may take 10-20 minutes)
RUN scons build/RISCV/gem5.opt -j$(nproc)

CMD ["bash"]