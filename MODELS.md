# Models used

No weights are distributed here. Every model was downloaded at a pinned revision, with its license and model card,
by `fetch-model.sh` from [ps4-rocm](https://github.com/Scottcjn/ps4-rocm/blob/main/tools/fetch-model.sh). That
script writes a `LICENSE_RECEIPT.txt` next to the weights.

| model | repo @ revision | file | sha256 | license |
|---|---|---|---|---|
| Qwen3-0.6B | `Qwen/Qwen3-0.6B-GGUF` @ `23749fef` | Qwen3-0.6B-Q8_0.gguf | `9465e63a…3bb031` | Apache-2.0 |
| Qwen3-4B | `Qwen/Qwen3-4B-GGUF` @ `bc640142` | Qwen3-4B-Q4_K_M.gguf | `7485fe6f…34fdf5` | Apache-2.0 |
| Qwen3-8B | `Qwen/Qwen3-8B-GGUF` @ `7c41481f` | Qwen3-8B-Q4_K_M.gguf | `d98cdcbd…745785` | Apache-2.0 |
| Granite-3.3-8B-Instruct | `ibm-granite/granite-3.3-8b-instruct-GGUF` @ `e40e9dd7` | granite-3.3-8b-instruct-Q4_K_M.gguf | `77bcee06…215dca` | Apache-2.0 |
| Phi-4 (14B) | `microsoft/phi-4-gguf` @ `6edc2ef6` | phi-4-Q3_K_S.gguf | `df1d679c…65a745` | MIT |
| Qwen3-14B | `Qwen/Qwen3-14B-GGUF` @ `530227a7` | Qwen3-14B-Q4_K_M.gguf | (pending) | Apache-2.0 |
