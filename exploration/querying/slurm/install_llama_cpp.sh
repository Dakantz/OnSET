#!/usr/bin/env bash
#SBATCH --gpus=1
#SBATCH --partition=hcc
#CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python==0.3.4 --upgrade --force-reinstall --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
#CMAKE_ARGS="-DGGML_CUDA=on -DGGML_CUDA_FORCE_CUBLAS=on -DLLAVA_BUILD=off -DCMAKE_CUDA_ARCHITECTURES=native" FORCE_CMAKE=1 pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
CMAKE_ARGS="-DGGML_CUDA=on -DGGML_CUDA_FORCE_CUBLAS=on -DLLAVA_BUILD=off -DCMAKE_CUDA_ARCHITECTURES=native" FORCE_CMAKE=1 pip install llama-cpp-python==0.3.4 --upgrade --force-reinstall --no-cache-dir
#pip install llama-cpp-agent
pip install git+https://github.com/Dakantz/llama-cpp-agent.git@add-literal-support
