import os

from fastcontext.agent.agent import Agent
from fastcontext.agent.llm import LLM
from fastcontext.agent.tool.tool import ToolSet

from fastcontext.agent.utils import load_system_prompt


def make_fastcontext_agent(
    trajectory_file: str,
    work_dir: str,
    **kwargs,
) -> Agent:
    name = "FastContext"
    system_prompt = kwargs.get("system_prompt", None)
    if system_prompt is None:
        system_prompt = load_system_prompt(work_dir)

    llm = LLM(
        model=os.getenv("MODEL"),
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        temperature=float(os.getenv("TEMPERATURE", "1.0")),
        top_p=float(os.getenv("TOP_P", "0.95")),
        max_tokens=int(os.getenv("MAX_TOKENS", "32000")),
    )

    from fastcontext.agent.tool.glob import GlobTool
    from fastcontext.agent.tool.grep import GrepTool
    from fastcontext.agent.tool.read import ReadTool

    toolset = ToolSet([ReadTool(), GlobTool(), GrepTool()], work_dir=work_dir)
    return Agent(
        name=name,
        system_prompt=system_prompt,
        llm=llm,
        toolset=toolset,
        trajectory_file=trajectory_file,
        work_dir=work_dir,
    )
