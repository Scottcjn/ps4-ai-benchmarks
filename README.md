# PS4 AI Benchmarks

Measured LLM and image-generation performance on PlayStation 4 hardware running Linux, plus the exact setup
needed to reproduce it. The porting work behind these numbers (kernel KFD patches, Mesa fixes, PM4 bridge) is in
**[Scottcjn/ps4-rocm](https://github.com/Scottcjn/ps4-rocm)**.

## Headline (PS4 Pro, GPU via patched Mesa Vulkan, llama.cpp `244640b`)

| model | quant | prompt (pp128) | generation (tg32) | vs 8-core CPU (tg) |
|---|---|---|---|---|
| Qwen3-0.6B | Q8_0 | 853 tok/s | **73.3 tok/s** | 3.2× |
| Qwen3-4B | Q4_K_M | 142 tok/s | **20.5 tok/s** | 3.7× |
| 8B / 14B models, image generation | | *in progress* | | |

All rows, including pre-fix and CPU-only baselines, are in [`results/llm.csv`](results/llm.csv). Memory
bandwidth measurements are in [`results/memory_bandwidth.csv`](results/memory_bandwidth.csv).

**The single most important setting:** `GGML_VK_PREFER_HOST_MEMORY=1`. On PS4 the GPU reads CPU-cached memory at
~18 GB/s but write-combined memory at ~167 GB/s. This setting moves llama.cpp's weights to the fast kind, for about 3×
the token generation. [`METHODOLOGY.md`](METHODOLOGY.md) explains how we found it.

## Test system

| | |
|---|---|
| Console | PS4 Pro, firmware 12.00 + GoldHEN, Linux via `linux-128mb.elf` payload |
| CPU | 8× AMD Jaguar @ 2.1 GHz (AVX, no AVX2) |
| GPU | Gladius (gfx7 / GCN2 ISA), 36 CUs, 4 shader engines |
| Memory | 8 GB GDDR5 unified; GPU can map ~3.9 GiB GTT + 128 MiB VRAM carve-out |
| Disk | stock 1 TB 2.5" 5400 rpm HDD |
| OS | Arch Linux, kernel 7.3.4 Strawberry (+ ps4-rocm KFD patches for later rows) |
| Driver | Mesa 26.3.1 RADV + ps4-rocm patch (no FLAT, no 128-bit LDS, GFX queue only) |

## Reproduce

```bash
# on the PS4, with ps4-rocm's patched Mesa installed to ~/mesa-ps4
export VK_ICD_FILENAMES=$HOME/mesa-ps4/share/vulkan/icd.d/radeon_icd.x86_64.json
export GGML_VK_PREFER_HOST_MEMORY=1
llama-bench -m Qwen3-4B-Q4_K_M.gguf -ngl 99 -p 128 -n 32 -r 2
```

⚠️ **Never run llama.cpp on PS4 with the stock Mesa driver**, even at `-ngl 0`: it hangs the GPU.
To get CPU-only numbers, hide the GPU with `GGML_VK_VISIBLE_DEVICES=`.

Models and their licenses: [`MODELS.md`](MODELS.md). No model weights are distributed here.

## License
Scripts: MIT. Docs and data: CC BY 4.0. Model licenses belong to their owners (see `MODELS.md`).
