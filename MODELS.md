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
| Qwen3-14B | `Qwen/Qwen3-14B-GGUF` @ `530227a7` | Qwen3-14B-Q4_K_M.gguf | `500a8806…6b81f0` | Apache-2.0 |
| Qwen3-8B | `unsloth/Qwen3-8B-GGUF` @ `a6adef13` | Qwen3-8B-Q3_K_S.gguf | `d9ba9488…827f15` | Apache-2.0 |
| Granite-3.3-8B-Instruct | `ibm-granite/granite-3.3-8b-instruct-GGUF` @ `e40e9dd7` | granite-3.3-8b-instruct-Q3_K_S.gguf | `824abd81…a33c7d` | Apache-2.0 |
| Qwen3.5-4B | `unsloth/Qwen3.5-4B-GGUF` @ `e87f1764` | Qwen3.5-4B-Q4_0.gguf | `298fcb5f…72b8bb` | Apache-2.0 |
| Qwen3.5-9B | `unsloth/Qwen3.5-9B-GGUF` @ `3885219b` | Qwen3.5-9B-Q3_K_S.gguf | `162050d3…d0179e` | Apache-2.0 |
| Gemma-4-E2B-it | `unsloth/gemma-4-E2B-it-GGUF` @ `0314792d` | gemma-4-E2B-it-IQ4_XS.gguf | `c1496209…2fd1e3` | Apache-2.0 (card tag) |
| Gemma-4-E4B-it | `unsloth/gemma-4-E4B-it-GGUF` @ `bfc15c38` | gemma-4-E4B-it-Q3_K_S.gguf | `fe6e02cd…fe31aa` | Apache-2.0 (card tag) |
| Ternary-Bonsai-2-9B | `prism-ml/Ternary-Bonsai-2-9B-gguf` @ `82265ccc` | Ternary-Bonsai-2-9B-PQ2_0.gguf | `7a89ab48…de23f9` | Apache-2.0 |
| Ternary-Bonsai-2-9B | same | Ternary-Bonsai-2-9B-PTQ1_0.gguf | `3561df7a…8b4e8b` | Apache-2.0 |
| Ternary-Bonsai-2-9B | same | Ternary-Bonsai-2-9B-Q2_0.gguf | `1f884aa5…3a384d` | Apache-2.0 |
| Ternary-Bonsai-2-2B | `prism-ml/Ternary-Bonsai-2-2B-gguf` @ `a6032a50` | Ternary-Bonsai-2-2B-PQ2_0.gguf | `d5f01a4e…b45928` | Apache-2.0 |
| Spark-X2.6-4B | `XHToken/Spark-X2.6-4B-GGUF` @ `9d716770` | Spark-X2.6-4B-Q4_K_M.gguf | `91cb2811…f5cbd9` | Apache-2.0 |

Round-2 notes:
- The four Bonsai files match the publisher's `SHA256SUMS`.
- Bonsai's NOTICE asks for, but does not require, the attribution "Created using Bonsai by Prism ML."
- Neither the unsloth nor the Google Gemma-4 repos ship a LICENSE file. The licence evidence is the card tag plus the saved model card.

## Image models (all ungated)

| model | repo | file | license |
|---|---|---|---|
| SD1.5 | `Comfy-Org/stable-diffusion-v1-5-archive` | v1-5-pruned-emaonly-fp16.safetensors | CreativeML OpenRAIL-M |
| LCM-LoRA SD1.5 | `latent-consistency/lcm-lora-sdv1-5` | pytorch_lora_weights.safetensors | OpenRAIL++ |
| SDXS-512 | `akleine/sdxs-512` | sdxs.safetensors | OpenRAIL++ |
| Segmind-Vega | `segmind/Segmind-Vega` | segmind-vega.safetensors | Apache-2.0 |

These repos ship no LICENSE file; the license comes from the model card, saved with each download.
