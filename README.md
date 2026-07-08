# FastContext: Training Efficient Repository Explorer for Coding Agents

<p align="center">
  <a href="https://arxiv.org/abs/2606.14066"><img src="https://img.shields.io/badge/arXiv-2606.14066-b31b1b.svg" alt="arXiv"></a>
  <a href="https://github.com/microsoft/fastcontext"><img src="https://img.shields.io/badge/Code-GitHub-181717.svg" alt="Code"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue.svg" alt="Python 3.12+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
</p>

<p align="center">
  <a href="#news">📰 News</a> |
  <a href="#overview">🔎 Overview</a> |
  <a href="#results">📊 Results</a> |
  <a href="#quick-start">⚡ Quick Start</a> |
  <a href="#reproduction">🧪 Reproduction</a> |
  <a href="#citation">📚 Citation</a>
</p>

> **About this mirror**: The original `microsoft/fastcontext` repository and official model listings were
> removed without explanation on 2026-06-30. This is a preserved copy (MIT license) with two small fixes for
> running against local OpenAI-compatible servers on macOS — see [Fixes in this mirror](#fixes-in-this-mirror).
> Surviving model weights: [ShaunGves/FastContext-1.0-4B-SFT](https://huggingface.co/ShaunGves/FastContext-1.0-4B-SFT).

FastContext is a lightweight repository-exploration subagent for coding agents. Instead of letting the main
coding agent spend its own context window on broad file reads and code searches, the main agent delegates
a natural-language context query to FastContext. FastContext explores the repository with read-only tools,
issues independent tool calls in parallel, and returns compact file-line citations as focused evidence for the
main agent.

<p align="center">
  <img src="figures/overview.png" alt="FastContext overview" width="95%">
</p>

## News

- 🚀 **2026-06-15**: We released the arXiv paper [[📄 arXiv](https://arxiv.org/abs/2606.14066)] and the model weights [[🤗 Model](https://huggingface.co/collections/microsoft/swe-fastcontext)].


## Overview

Modern coding agents often use the same model to explore a repository and solve the task. This makes
exploration expensive: exploratory reads and searches consume tokens, stay in the solver's history, and can
pollute later reasoning with irrelevant snippets.

FastContext separates repository exploration from solving:

- 🧭 **Delegated exploration**: the main agent asks FastContext for repository context before editing or answering.
- 🔒 **Read-only tools**: FastContext uses `Read`, `Glob`, and `Grep`; it does not modify files.
- ⚙️ **Parallel tool calling**: independent reads and searches can be issued in the same exploration turn.
- 📌 **Compact evidence**: the final response is a short `<final_answer>` block with file paths and line ranges.
- 🧠 **Trainable explorers**: the paper trains 4B-30B exploration models with SFT and task-grounded RL.

The intended contract is simple: FastContext finds the relevant code; the main coding agent uses that focused
evidence to edit, test, or answer.

```text
<final_answer>
/path/to/repo/src/router.py:42-58
/path/to/repo/tests/test_router.py:101-119
</final_answer>
```

## Results

Across SWE-bench Multilingual, SWE-bench Pro, and SWE-QA, FastContext improves the score-token tradeoff of
Mini-SWE-Agent style coding agents.

| Result | Finding |
| --- | --- |
| 📈 End-to-end success | Up to **+5.5** score improvement with delegated repository exploration. |
| 💸 Main-agent token use | Up to **60.3%** fewer main-agent tokens. |
| 🧠 Compact trained explorer | FC-4B-RL improves or ties FC-4B-SFT across all reported end-to-end settings. |
| 🎯 Standalone exploration | Trained FastContext models recover patch-relevant files and symbols more accurately than non-FastContext small-model baselines. |

<p align="center">
  <img src="figures/main-result.png" alt="FastContext main results" width="95%">
</p>

## Token Efficiency

FastContext reduces the main agent's context burden by moving broad repository exploration outside the
solver trajectory. The reduction is especially visible in file-reading and code-search tokens.

<p align="center">
  <img src="figures/breakdown.png" alt="FastContext token breakdown" width="95%">
</p>

## Installation

FastContext requires Python 3.12 or newer. The repository uses [`uv`](https://docs.astral.sh/uv/) for package
and environment management.

Install the CLI from the repository root:

```bash
uv tool install .
```

For development:

```bash
uv sync --all-groups
```

Build a local wheel:

```bash
uv build
```

The built wheel is written under `dist/`, for example:

```text
dist/fastcontext-0.1.0-py3-none-any.whl
```

## Model Configuration

FastContext expects an OpenAI-compatible chat completions endpoint. For direct CLI usage, configure:

```bash
export BASE_URL="https://your-endpoint.example/v1"
export MODEL="your-model-name"
export API_KEY="your-api-key"
```

Benchmark runners may also pass separate FastContext credentials through `FASTCONTEXT_*` variables in
`benchmark/evaluation/configs/example.env`.

### Choosing a model format

The explorer weights are available in several formats — pick whichever fits your setup:

| Format | Where | Size | Notes |
| --- | --- | --- | --- |
| BF16 safetensors | [ShaunGves/FastContext-1.0-4B-SFT](https://huggingface.co/ShaunGves/FastContext-1.0-4B-SFT) | ~8 GB | Original weights; serve with mlx-lm, vLLM, or SGLang. |
| MLX 8-bit | [mlx-community/FastContext-1.0-4B-SFT-8bit](https://huggingface.co/mlx-community/FastContext-1.0-4B-SFT-8bit) | ~4 GB | **Recommended local quant.** Tested accurate with LM Studio and mlx-lm on Apple Silicon. |
| MLX 4-bit | [mlx-community/FastContext-1.0-4B-SFT-4bit](https://huggingface.co/mlx-community/FastContext-1.0-4B-SFT-4bit) | ~2.1 GB | Degraded path grounding in testing (hallucinated citations); only for tight memory. |
| GGUF Q8 | [mitkox/FastContext-1.0-4B-RL-Q8_0-GGUF](https://huggingface.co/mitkox/FastContext-1.0-4B-RL-Q8_0-GGUF) | ~4.3 GB | For Ollama / llama.cpp: `ollama pull hf.co/mitkox/FastContext-1.0-4B-RL-Q8_0-GGUF`. |

**LM Studio**: download either MLX quant from the search tab (MLX runtime), load it, start the local
server, and point the CLI at `BASE_URL=http://localhost:1234/v1` with `MODEL` set to the LM Studio model
identifier (e.g. `fastcontext-1.0-4b-sft`).

**Ollama**: `ollama pull` the GGUF above — but don't use it directly: Ollama's auto-derived chat template
for this GGUF force-opens a `<think>` block, and FastContext's base model (Qwen3-4B-Instruct-2507) is the
non-thinking variant, so every response comes back empty (the model emits an immediate stop token). Create
a wrapper model with the bad line removed (reuses the already-pulled weights, no re-download):

```bash
{
  echo 'FROM hf.co/mitkox/FastContext-1.0-4B-RL-Q8_0-GGUF'
  echo 'TEMPLATE """'
  ollama show --template hf.co/mitkox/FastContext-1.0-4B-RL-Q8_0-GGUF | sed '/^<think>$/d'
  echo '"""'
} > Modelfile
ollama create fastcontext-ollama -f Modelfile
```

Then use `BASE_URL=http://localhost:11434/v1` with `MODEL=fastcontext-ollama`. Verified end to end:
citation accuracy comparable to the MLX 8-bit quant at ~11 s/query on an M4. (Note: Ollama's MLX engine
preview does not change this — the `hf.co/...` pull path still requires GGUF, so the mlx-community quants
above cannot be pulled via Ollama.)

For quantized models, lower the sampling temperature and cap generation length via the environment
overrides (defaults match the paper's serving setup):

```bash
export TEMPERATURE=0.6   # default 1.0
export TOP_P=0.95        # default 0.95
export MAX_TOKENS=4000   # default 32000; a missed stop token otherwise generates for minutes
```

### Local serving on Apple Silicon (mlx-lm)

The original BF16 safetensors run directly on Apple Silicon via [mlx-lm](https://github.com/ml-explore/mlx-lm)
— no GGUF conversion needed (a 4B model uses ~8 GB of RAM). Ripgrep (`rg`) must be installed for the
Glob/Grep tools (`brew install ripgrep`).

```bash
hf download ShaunGves/FastContext-1.0-4B-SFT --local-dir ./models/FastContext-1.0-4B-SFT

# Newer transformers/mlx releases break this mlx-lm version; the pins matter.
uv tool install "mlx-lm==0.29.1" --with "transformers<5" --with "mlx<0.31"

mlx_lm.server --model ./models/FastContext-1.0-4B-SFT --port 8080
```

Then configure the CLI (the mlx-lm server loads whatever the request's `model` field names, so `MODEL`
must be the local weights path):

```bash
export BASE_URL="http://127.0.0.1:8080/v1"
export MODEL="/absolute/path/to/models/FastContext-1.0-4B-SFT"
export API_KEY="local"
```

### Fixes in this mirror

- `src/fastcontext/agent/llm.py`: synthesize tool-call ids when the server omits them (mlx-lm returns
  `id: null`, which crashed the agent on the first tool call).
- `src/fastcontext/agent/tool/grep.py`: resolve `rg` from `PATH` instead of the hardcoded `/usr/bin/rg`
  (on macOS/Homebrew, ripgrep lives in `/opt/homebrew/bin`). Without this, every Grep call fails silently
  and the explorer hallucinates citations when forced to answer.
- Not a code fix, but documented above: Ollama's auto-derived chat template for the community GGUF breaks
  the model entirely (empty responses) — see the Modelfile workaround in
  [Choosing a model format](#choosing-a-model-format).

## Quick Start

Run FastContext from the repository you want to explore:

```bash
fastcontext \
  --query "Find the files that implement authentication and explain where to make a change" \
  --max-turns 6 \
  --traj .fastcontext/trajectory.jsonl
```

Return only the machine-readable citation block:

```bash
fastcontext \
  --query "Locate the request validation logic" \
  --citation
```

Useful CLI options:

| Option | Description |
| --- | --- |
| `--query`, `-q` | Natural-language exploration request. |
| `--traj`, `-t` | JSONL trajectory output path. |
| `--max-turns` | Maximum exploration turns before forcing a final answer. |
| `--verbose` | Print intermediate messages and runtime information. |
| `--citation` | Return only the `<final_answer>` block when present. |

## Programmatic Use

```python
import asyncio

from fastcontext.agent.agent_factory import make_fastcontext_agent


async def main() -> None:
    agent = make_fastcontext_agent(
        trajectory_file=".fastcontext/trajectory.jsonl",
        work_dir="/path/to/repo",
    )
    answer = await agent.run(
        prompt="Find where database migrations are defined",
        max_turns=6,
        citation=True,
    )
    print(answer)


asyncio.run(main())
```

## Reproduction

This repository contains scripts for end-to-end Mini-SWE-Agent runs and standalone exploration evaluation.
The exact paths, model names, and credentials should be adapted to your serving environment.

### End-to-End SWE-Bench Runs

```bash
git submodule update --init --recursive
uv build
cp benchmark/evaluation/configs/example.env .env
```

Edit `.env` with the main-agent and FastContext endpoint credentials, then run:

```bash
uv run --group benchmark python benchmark/evaluation/bench_mini_swe_agent.py \
  --bench swebench-multilingual \
  --agent-config prompts/gpt-multi-fc.yaml \
  --config .env \
  --output preds.json \
  --logs-dir logs \
  --workers 1
```

For SWE-bench Pro, use the Pro prompt:

```bash
uv run --group benchmark python benchmark/evaluation/bench_mini_swe_agent.py \
  --bench ScaleAI/SWE-bench_Pro \
  --agent-config prompts/gpt-pro-fc.yaml \
  --config .env \
  --output preds-pro.json \
  --logs-dir logs-pro
```

### Standalone Exploration

The standalone runner evaluates FastContext as a repository explorer on SWE-bench-style subagent queries.

```bash
cd benchmark/swebench
cp run.sh.sample run.sh
# Edit run.sh with BASE_URL, MODEL, and API_KEY.

uv run --group benchmark python bench_fastcontext.py \
  --bench swebench-multilingual \
  --experiment fastcontext-eval \
  --prediction-file predictions.jsonl \
  --local-mount-dir /absolute/path/to/output \
  --num-threads 1
```

After extracting the final FastContext responses into a JSONL file with `instance_id` and `finial_response`
fields, score citation quality from the repository root:

```bash
uv run --group benchmark python benchmark/evaluation/run_score.py \
  swebench-multilingual \
  result_finial_response.jsonl
```

## Training and Serving

The `training/` directory contains scripts used for the SFT and RL experiments described in the paper.
These scripts assume a research training environment with external model checkpoints, datasets, and cluster
settings; treat paths and launcher options as examples to adapt.

```text
training/
  fastcontext-sft/     Supervised fine-tuning scripts and data utilities
  fastcontext-rl/      Reinforcement-learning scripts and reward utilities
```

The `serving/` directory contains example manifests and API checks for serving FastContext-compatible
models behind an OpenAI-compatible endpoint.

## Repository Layout

```text
src/fastcontext/
  cli.py                         Command-line entry point
  agent/
    agent.py                     Agent loop
    agent_factory.py             Default FastContext agent construction
    context.py                   Conversation and trajectory storage
    llm.py                       OpenAI-compatible LLM wrapper
    system.md                    Explorer system prompt
    tool/
      read.py                    Read tool
      glob.py                    Glob tool
      grep.py                    Grep tool
      tool.py                    Tool base classes and ToolSet

benchmark/
  environment/                   Docker environment helpers
  evaluation/                    End-to-end Mini-SWE-Agent runners and scoring utilities
  swebench/                      SWE-bench-style standalone exploration runner

prompts/                         Mini-SWE-Agent prompt configs with FastContext integration
training/                        SFT and RL training scripts
serving/                         Example serving manifests and API checks
tests/                           Unit and integration-style tests
figures/                         README and paper figures
```

## Development

Run linting:

```bash
uv run ruff check .
```

Run tests:

```bash
uv run pytest -q
```

Build the package:

```bash
uv build
```

## Notes

- FastContext is intended for repository exploration, not code modification.
- Tool outputs are capped to keep interactions responsive.
- The default CLI records trajectories under `.fastcontext/` unless `--traj` is provided.
- For best results, write specific exploration queries that name the behavior, subsystem, error, or files you are trying to locate.

## Citation

If you find FastContext useful, please cite:

```bibtex
@misc{zhang2026fastcontexttrainingefficientrepository,
      title={FastContext: Training Efficient Repository Explorer for Coding Agents},
      author={Shaoqiu Zhang and Maoquan Wang and Yuling Shi and Yuhang Wang and Xiaodong Gu and Yongqiang Yao and Rao Fu and Shengyu Fu},
      year={2026},
      eprint={2606.14066},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2606.14066},
}
```

## Acknowledgements

FastContext builds on open research infrastructure and benchmarks for coding agents, including SWE-bench,
SWE-bench Multilingual, SWE-bench Pro, SWE-QA, Mini-SWE-Agent, and open model / serving ecosystems.
