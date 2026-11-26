# PS4 AI Benchmarks

Measured LLM and image-generation performance on PlayStation 4 hardware running Linux, plus the exact setup
needed to reproduce it. The porting work behind these numbers (kernel KFD patches, Mesa fixes, PM4 bridge) is in
**[Scottcjn/ps4-rocm](https://github.com/Scottcjn/ps4-rocm)**.

## Headline (PS4 Pro, GPU via patched Mesa Vulkan, llama.cpp `244640b`)

| model | quant | prompt (pp128) | generation (tg32) | vs 8-core CPU (tg) |
|---|---|---|---|---|
| Qwen3-0.6B | Q8_0 | 853 tok/s | **73.3 tok/s** | 3.2× |
| Qwen3-4B | Q4_K_M | 142 tok/s | **20.5 tok/s** | 3.7× |
| Qwen3-8B | Q3_K_S (3.5 GiB) | 70 tok/s | **9.4 tok/s** | — |
| Qwen3-8B | Q4_K_M (4.7 GiB, partial offload ngl 30) | 22 tok/s | 7.7 tok/s | — |
| Phi-4 14B | Q3_K_S (6.1 GiB, ngl 18) | 19 tok/s | 2.1 tok/s | — |
| Qwen3-14B | Q4_K_M (8.4 GiB > RAM, HDD paging) | 1.1 tok/s | **0.01 tok/s** (unusable) | — |

## Round 2: current small models (PrismML llama.cpp fork `f702476`, Vulkan)

| model | quant | GiB | prompt (pp128) | generation (tg32) | CPU tg | 16k ctx | quality (3 prompts) |
|---|---|---|---|---|---|---|---|
| **Gemma-4-E2B-it** | IQ4_XS | 2.78 | 255 tok/s | **27.0 tok/s** | 7.5 | ✅ | **3/3** |
| Ternary-Bonsai-2-2B | PQ2_0 | 0.48 | 368 tok/s | **43.0 tok/s** | 10.7 | ✅ (988 MiB GTT) | 2/3 |
| Qwen3.5-4B | Q4_0 | 2.41 | 157 tok/s | 23.7 tok/s | 4.6 | ✅ | 2/3 |
| Spark-X2.6-4B | Q4_K_M | 3.30 | 137 tok/s | 20.2 tok/s | 5.0 | ✅ (mmap) | 2/3 |
| Qwen3-4B (round-1 model, this build) | Q4_K_M | 2.32 | 137 tok/s | 20.1 tok/s | — | — | 3/3 |
| **Ternary-Bonsai-2-9B** | PQ2_0 | 2.25 | 86 tok/s | **14.2 tok/s** | 2.8 | ✅ | 3/3 |
| Ternary-Bonsai-2-9B | Q2_0 | 2.38 | 85 tok/s | 14.1 tok/s | — | — | — |
| Ternary-Bonsai-2-9B | PTQ1_0 | 1.86 | 58 tok/s | 10.8 tok/s | 1.8 | — | same as PQ2_0 |
| Gemma-4-E4B-it | Q3_K_S | 3.60 | 114 tok/s | 11.1 tok/s | 3.6 | ✅ (mmap) | 2/3 |
| Qwen3.5-9B (ngl 28, partial) | Q3_K_S | 4.02 | 40 tok/s | 5.8 tok/s | — | — | 3/3 |

- **Best overall:** Gemma-4-E2B, `-ngl 99 -lm none`. It is the only fast model that passed all three prompts.
- **A 9B model fully on the GPU:** Ternary-Bonsai-2-9B PQ2_0 fits in 2.25 GiB and generates at 14.2 tok/s. That is 1.5× the best round-1 8B and 2.4× Qwen3.5-9B at Q3.
- **Ternary quants run on the GPU, not the CPU:** the PrismML fork ships Vulkan shaders for PQ2_0, PTQ1_0 and Q2_0, and they work on gfx7.
- **Quality is a smoke test, not a ranking.** There is one trial per prompt at temp 0:
  - (a) Paris / Seine
  - (b) a code-only `is_prime`
  - (c) "17 sheep, all but 9 run away"

  Every model passed (a) and (b). The 2/3 models answered "8" on (c).
- **Use `-lm mmap` near the GTT cap.** This fork loads without mmap by default, and Gemma-E4B and Qwen3.5-9B fail to load that way.

**Limits on an 8 GB PS4 Pro:**
- **Full GPU offload** works up to a ~3.5 GiB model file. Bigger fails cleanly with "device lost", not a hang.
- **8B at Q3** is the sweet spot.
- **Models larger than RAM** page from the 5400 rpm HDD at ~100 s/token.
- **Swap** takes the system down.
- **zram** doesn't help, because quantized weights don't compress (~1%).

## Image generation (512×512, stable-diffusion.cpp Vulkan)

| model | steps | seconds per image | vs CPU |
|---|---|---|---|
| SDXS-512 | 1 | **2.9 s** | — |
| SD1.5 + LCM-LoRA | 4 | **22 s** | 9.4× faster (CPU: 206 s) |
| SD1.5 | 20 | 75 s | — |
| Segmind-Vega (SDXL-class) | 20 | 104 s | — |

Every image was checked by eye and is coherent; the GPU and CPU LCM runs produce the same picture.
Fitting in ~3.9 GiB GTT needs `--auto-fit off`, `--batched-cfg off` (20-step runs) and
`--lora-apply-mode at_runtime` (LCM). Full rows: [`results/image_gen.csv`](results/image_gen.csv).

**LLM sanity check:** Qwen3-8B (Q3 and Q4), Granite-3.3-8B and Phi-4 all answer "Paris … the Seine" correctly at temp 0.
On the GPU, context above ~512 tokens pushes the 8B Q3 past the GTT cap; partial offload needs `-lm mmap`.

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
