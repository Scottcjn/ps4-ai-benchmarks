# PS4 AI Benchmarks

Measured LLM and image-generation performance on PlayStation 4 hardware running Linux, plus the exact setup
needed to reproduce it. The porting work behind these numbers (kernel KFD patches, Mesa fixes, PM4 bridge) is in
**[Scottcjn/ps4-rocm](https://github.com/Scottcjn/ps4-rocm)**.

## Headline (PS4 Pro, GPU via patched Mesa Vulkan, llama.cpp `244640b`, `-fa 0`)

Re-measured 2026-11-27 with flash attention **off** (`-fa 0`), which is faster on this GPU (see Round 3). The
"fa on" column is the same session with `-fa 1` and matches the original 2026-11-25 numbers.

| model | quant | prompt (pp128) | generation (tg32) | tg with fa on | vs 8-core CPU (tg) |
|---|---|---|---|---|---|
| Qwen3-0.6B | Q8_0 | 1036 tok/s | **110.4 tok/s** | 73.2 | 4.8× |
| Qwen3-4B | Q4_K_M | 154 tok/s | **22.5 tok/s** | 20.5 | 4.0× |
| Qwen3-8B | Q3_K_S (3.5 GiB, `-lm none`) | 73 tok/s | **9.8 tok/s** | 9.4 | — |
| Qwen3-8B | Q4_K_M (4.7 GiB, partial offload ngl 30, `-lm mmap`) | 71 tok/s | 8.1 tok/s | 8.0 | — |
| Phi-4 14B | Q3_K_S (6.1 GiB, ngl 18, `-lm mmap`) | 30 tok/s | 2.1 tok/s | 2.1 | — |
| Qwen3-14B | Q4_K_M (8.4 GiB > RAM, HDD paging) | 1.1 tok/s | **0.01 tok/s** (unusable) | — | — |

- **Fa off gains the most on small, fully-offloaded models** (+51% on 0.6B, +10% on 4B). For partial offload the
  CPU layers dominate and fa makes no difference.
- **Partial-offload prompt numbers are warm-cache.** With `-lm mmap` the first run in a session reads weights from
  the HDD; Phi-4 pp128 measured 1.2 tok/s cold vs 30 warm. The original 22 / 19 tok/s prompt figures for these
  rows were cold-cache, not slower GPU work.
- **Set the load mode explicitly.** On this build `-lm auto` turns mmap off on the PS4's Vulkan device, so the
  partial-offload rows fail with "device lost" (out of GTT) unless you pass `-lm mmap`.
- The Qwen3-14B row was not re-run (it pages from disk at any setting).

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

## Round 3 (2026-11-27): coding test, flash attention, kernel v4

### Harder coding test

The round-2 coding prompt (`is_prime`) didn't separate the models: they all passed. Round 3 asks for three harder
functions and grades them with 32 hidden unit tests:
- merge intervals
- an arithmetic expression parser, with `eval`/`ast` banned
- an LRU cache

Settings: temp 0, thinking off, 1500-token cap, PrismML `f702476`. The grader is
[`scripts/codetest.py`](scripts/codetest.py). It was checked first against reference solutions (32/32) and against
planted bugs, all of which it caught.

| model | intervals | expr parser | LRU | total |
|---|---|---|---|---|
| **Ternary-Bonsai-2-9B** PQ2_0 | 9/9 | **4/14** | 9/9 | **22/32** |
| Qwen3-4B Q4_K_M | 9/9 | 2/14 | 9/9 | 20/32 |
| Qwen3.5-9B Q3_K_S (ngl 28) | 9/9 | 1/14 | 9/9 | 19/32 |
| Gemma-4-E2B-it IQ4_XS | 9/9 | 0 (truncated) | 9/9 | 18/32 |
| Gemma-4-E4B-it Q3_K_S | 9/9 | 0 (truncated) | 9/9 | 18/32 |
| Spark-X2.6-4B Q4_K_M | 9/9 | 0 | 9/9 | 18/32 |
| Qwen3.5-4B Q4_0 | 6/9 | 0 (infinite loop) | 9/9 | 15/32 |
| Ternary-Bonsai-2-2B PQ2_0 | 0/9 | 0 | 9/9 | 9/32 |

- **Best coder: Ternary-Bonsai-2-9B.** It is the only model that got part of the parser right, and it generates at 14 tok/s fully on the GPU.
- **Best speed-per-score: Qwen3-4B.**
- **Verbose models:** both Gemmas filled the 1500-token cap with comments before the parser was finished.
- **Qwen3-8B Q3_K_S** failed to load at `-c 4096` (out of GTT).
- Full rows: [`results/coder.csv`](results/coder.csv).

### Flash attention off is faster for generation

`-fa 0` vs `-fa 1`, tg64, `GGML_VK_PREFER_HOST_MEMORY=1`:

| model | depth 0: fa off / on | depth 1024: fa off / on |
|---|---|---|
| Qwen3-0.6B Q8_0 | **110.1** / 73.0 (+51%) | 79.4 / 66.0 (+20%) |
| Gemma-4-E2B-it IQ4_XS | **34.8** / 27.1 (+29%) | 32.1 / 20.5 (+57%) |
| Qwen3-4B Q4_K_M | 22.5 / 20.6 (+10%) | 20.4 / 19.5 (+5%) |
| Ternary-Bonsai-2-2B PQ2_0 | 44.6 / 43.5 | 44.4 / 42.1 |

Profiling with `GGML_VK_PERF_LOGGER` explains it:
- The GPU is busy for ~99% of each token, so there's no CPU or dispatch overhead to recover.
- The flash-attention decode shader is 43% of Qwen3-0.6B's token time.

**Use `-fa 0` on PS4 for small models.** The headline table at the top was re-measured with `-fa 0` (2026-11-27).
The Round 2 table above still uses the default setting, so its small-model tg numbers are not the ceiling.

### Kernel v4 and an env-var gotcha

- **Kernel v4 adds no slowdown.** Kernel v4 carries the KFD patches plus a fix for queues that come back dead after a
  memory-pressure eviction. On it, Qwen3-0.6B, Qwen3-4B, Bonsai-2-9B and Gemma-4-E4B match the v3 numbers to within
  noise (rows dated 2026-11-27 in `llm.csv`).
- **An empty variable still counts as set.** `GGML_VK_PREFER_HOST_MEMORY=` turns the setting **on**, because llama.cpp
  only checks `getenv() != NULL`. Use `env -u GGML_VK_PREFER_HOST_MEMORY` for a true "off" run.
- **The cost of leaving it off:** Qwen3-4B runs at 60.8 / 6.7 tok/s without it vs 142.0 / 20.5 with it.
- **Open:** prompt speed on the stock (non-KFD) kernel was higher (Qwen3-0.6B pp128 1164 vs 791, setting off). The
  planned stock-vs-KFD comparison with the setting on couldn't run today: the stock kernel image didn't boot on this
  attempt.

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
llama-bench -m Qwen3-4B-Q4_K_M.gguf -ngl 99 -fa 0 -p 128 -n 32 -r 2
```

⚠️ **Never run llama.cpp on PS4 with the stock Mesa driver**, even at `-ngl 0`: it hangs the GPU.
To get CPU-only numbers, hide the GPU with `GGML_VK_VISIBLE_DEVICES=`.

Models and their licenses: [`MODELS.md`](MODELS.md). No model weights are distributed here.

## License
Scripts: MIT. Docs and data: CC BY 4.0. Model licenses belong to their owners (see `MODELS.md`).
