# How we got these numbers

This is the path from "llama.cpp hangs the GPU" to "Qwen3-4B at 20 tok/s on a PS4 Pro", in order, with the
evidence for each step. Every result is from one PS4 Pro (CUH-7xxx, firmware 12.00, GoldHEN) running Arch Linux
on the Strawberry 7.3.4 kernel. Patches and tools are in [ps4-rocm](https://github.com/Scottcjn/ps4-rocm).

## 1. Stock llama.cpp + Vulkan hangs the GPU

`llama-bench -ngl 99` never finished. Each dispatch hung, and dmesg filled with `amdgpu: ring comp_1.0.0 timeout, but
soft recovered`. The same happened with the compute queue hidden (`RADV_DEBUG=nocompute` just moved the hang
to the gfx ring).

**Bisect.** `vkbisect` ran fill, copy and a trivial shader on both queue types and both memory types:
- Mesa's internal fill/copy shaders hung. They use `flat_store_dwordx2`.
- A plain SSBO shader worked. It uses `buffer_store_dword`.

So FLAT memory instructions hang this GPU. Garlic LLM, which runs natively on PS4, compiles with FLAT disabled for
the same reason.

**Fix.** Mesa's ACO compiler uses MUBUF addr64 (the GFX6 path) instead of FLAT on the PS4 PCI IDs, and splits
LDS accesses wider than 64 bits.

## 2. One matrix-multiply case still hung

After the FLAT fix, 2,359 MUL_MAT cases passed and then one hung, always on a compute ring and only in the full run.
It wasn't the shader. It went away when every submit was waited on, or when everything ran on the GFX ring.

**Fix.** RADV exposes no separate compute queue on these chips. After that, `test-backend-ops -o MUL_MAT` passed
2636/2636 and ADD passed 173/173.

## 3. Token generation was no faster than the CPU

With the GPU working, Qwen3-0.6B generated at 22.9 tok/s, exactly the CPU's rate. Qwen3-4B managed 6.6 tok/s.
6.6 tok/s × 2.3 GB of weights is about 15 GB/s, while GDDR5 on the Pro is ~218 GB/s.

**Measure the memory path directly.** We wrote a small KFD PM4 dispatch library (pm4bridge) and timed GPU
reads of a 256 MB buffer:
- **CPU-cached memory** (KFD userptr, cached GTT, Vulkan HOST_CACHED) reads at **~18 GB/s**. Adding waves,
  using 16-byte loads, pinning and setting CU masks didn't move it.
- **Write-combined GTT** (`AMDGPU_GEM_CREATE_CPU_GTT_USWC`, or Vulkan HOST_VISIBLE non-cached) reads at
  **~167 GB/s**, up to 176.
- **The VRAM carve-out** reads at ~161 GB/s.

So the slow path is the coherent (snooped) path that CPU-cached pages take. It isn't GTT vs VRAM, and a bigger
VRAM carve-out isn't needed.

**Fix.** `GGML_VK_PREFER_HOST_MEMORY=1` makes llama.cpp put its buffers in the host-visible, non-cached type,
which is write-combined and takes the fast path:
- Qwen3-4B generation went from 6.6 to **20.5 tok/s**.
- Qwen3-0.6B generation went from 22.9 to **73.3 tok/s**.

Output was checked for correctness: the 4B answers "Paris … the Seine".

## Measurement rules
- **Bench command:** `llama-bench -p 128 -n 32` (`-r 2` unless a row says otherwise). We report the mean ± stdev that llama-bench prints.
- **CPU baselines** hide the GPU completely (`GGML_VK_VISIBLE_DEVICES=`). Running the stock Mesa ICD at
  `-ngl 0` still touches the GPU and hangs it.
- **GPU runs always** use the patched Mesa ICD (`VK_ICD_FILENAMES=…/mesa-ps4/…`).
- **Health check:** before and after GPU runs we count `ring … timeout` lines in dmesg. Every number here comes from a run with 0 new timeouts.
- **Models** are pinned by repo revision and sha256 (see `MODELS.md`), with licenses saved at download.
- **Kernel versions are recorded per row.** 0.6B prompt processing dropped from 1164 to 790 tok/s when we moved
  from the stock kernel to our KFD kernel. That drop is not yet explained, and both rows are kept.
- **Background load:** from 2026-11-25 22:25 a RustChain miner runs on the console (CPU-only, nice 10). Rows taken
  after that note it.

## Known gaps
- **Prompt processing is likely compute-bound now.** The 4B uses ~47 GB/s of a possible ~165 GB/s during generation.
- **FP16:** the Pro's packed FP16 isn't exposed, because RADV treats the chip as gfx7.
- **Hardware coverage:** base PS4 (Liverpool) numbers are not measured yet.
