FROM ubuntu:24.04 AS build-stage
WORKDIR /conda
RUN apt-get update && apt-get install -y  --no-install-recommends cmake build-essential wget ca-certificates git gcc g++ libssl-dev libxml2-dev libxslt-dev libffi-dev

RUN mkdir -p ./miniconda3
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ./miniconda3/miniconda.sh
RUN bash ./miniconda3/miniconda.sh -b -u -p ./miniconda3
RUN rm ./miniconda3/miniconda.sh
# RUN sh ~/miniconda3/bin/activate

ENV PATH="/conda/miniconda3/bin/:$PATH"
ENV CUDA_VERSION=12.8.1
RUN conda tos accept

RUN conda install \
    nvidia/label/cuda-${CUDA_VERSION}::cuda-nvcc \
    nvidia/label/cuda-${CUDA_VERSION}::libcublas-dev \
    nvidia/label/cuda-${CUDA_VERSION}::cuda-cudart-dev \
    nvidia/label/cuda-${CUDA_VERSION}::cuda-toolkit


WORKDIR /uv
# Download the latest installer
ADD https://astral.sh/uv/install.sh uv-installer.sh

# Run the installer then remove it
RUN sh uv-installer.sh && rm uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app
ADD pyproject.toml /app
ADD uv.lock /app
RUN CMAKE_ARGS="-DGGML_CUDA=on  -DLLAVA_BUILD=off" uv sync

WORKDIR /app

ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/src

CMD [ "python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000" ]