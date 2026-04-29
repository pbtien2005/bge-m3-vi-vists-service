#!/usr/bin/env bash
set -euo pipefail

nvidia-smi
echo
nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu,utilization.memory,temperature.gpu,power.draw --format=csv
