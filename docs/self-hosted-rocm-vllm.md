# Self-Hosted ROCm vLLM Deployment Guide (AMD Instinct MI300X)

VitaLoop 360 supports two interchangeable OpenAI-compatible AMD inference backends through [`backend/gateway.py`](../backend/gateway.py) and [`config.json`](../config.json):

1. **Managed Cloud Endpoint (Default)**: **AMD Token Factory (Radeon Cloud)** at `https://developer.amd.com.cn/radeon/api/v1` serving `Gemma-4-31B-IT`.
2. **Self-Hosted Hardware Endpoint**: **ROCm vLLM** running on a single **AMD Instinct MI300X (192 GB HBM3)** instance on AMD Developer Cloud (`$1.99/hr` published single-GPU reference rate).

---

## 1. Quick Start with Docker Compose on AMD Instinct MI300X

```bash
docker compose -f deploy/vllm-rocm-mi300x.yaml up -d
```

Or launch the ROCm vLLM server directly on an MI300X host:

```bash
docker run -d --name vitaloop-rocm-gemma \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --ipc=host --shm-size 64G \
  -e HIP_VISIBLE_DEVICES=0 \
  -e HF_TOKEN=$HF_TOKEN \
  -p 8000:8000 \
  rocm/vllm:latest \
  python3 -m vllm.entrypoints.openai.api_server \
    --model google/gemma-3-27b-it \
    --served-model-name Gemma-4-31B-IT \
    --dtype bfloat16 \
    --max-model-len 16384 \
    --gpu-memory-utilization 0.90 \
    --port 8000
```

---

## 2. Pointing VitaLoop 360 at Your Self-Hosted Endpoint

Update `.env` (or environment variables):

```env
VITALOOP_BASE_URL=http://localhost:8000/v1
VITALOOP_API_KEY=vitaloop-rocm-local
VITALOOP_MODEL=Gemma-4-31B-IT
VITALOOP_PROVIDER=AMD Instinct MI300X (ROCm vLLM)
```

Then run the runtime, readiness suite, or metrics report:

```bash
python run.py --batch
python run.py --demo --metrics
python run.py
```

---

## 3. Unit Economics & Capacity Planning on MI300X

- **VRAM Footprint**: `Gemma-4-31B-IT` / `gemma-3-27b-it` in `BF16` requires ~54–62 GB of weights, leaving >120 GB of the MI300X's **192 GB HBM3** for KV cache and concurrent requests across all 5 capability packs.
- **Cost Formula**: `Gateway.status()` computes both token-based API spend and GPU-time cost using the published AMD Developer Cloud single-MI300X rate (`$1.99/hr`, or `$0.00055278/sec` of active inference latency).
