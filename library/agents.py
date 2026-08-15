"""
Higher-level agent helpers for LlmLang (usable from Python or via .ll wrappers).
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
import json

from .core import CallResult, ModelConfig, Memory, conf, backend as get_backend


def chat(
    config: ModelConfig,
    prompt: str,
    memory: Optional[Memory] = None,
    backend=None,
) -> CallResult:
    """Single- or multi-turn chat against a model."""
    b = backend or get_backend()
    if b is None:
        from library.core import LLMBackend
        b = LLMBackend(mock=True)

    if memory is not None:
        memory.add_user(prompt)
        result = b.complete(config, prompt, messages=memory.as_list())
        memory.add_assistant(result.text)
        return result

    return b.complete(config, prompt)


def plan(
    config: ModelConfig,
    goal: str,
    backend=None,
) -> CallResult:
    """Ask the model for a structured plan (prefers JSON mode)."""
    b = backend or get_backend()
    if b is None:
        from library.core import LLMBackend
        b = LLMBackend(mock=True)

    cfg = ModelConfig(
        name=config.name + "_planner",
        system=config.system + "\nRespond with JSON: {\"goal\": str, \"steps\": [{\"id\": int, \"action\": str}], \"confidence\": float}",
        temperature=config.temperature,
        mode="json",
        max_tokens=config.max_tokens,
    )
    prompt = f"Create a step-by-step plan for this goal:\n{goal}"
    return b.complete(cfg, prompt)


def critic(
    config: ModelConfig,
    content: str,
    criteria: str = "accuracy and clarity",
    backend=None,
) -> CallResult:
    """Critique content and return a score."""
    b = backend or get_backend()
    if b is None:
        from library.core import LLMBackend
        b = LLMBackend(mock=True)

    cfg = ModelConfig(
        name=config.name + "_critic",
        system=(
            "You are a strict critic. Respond with JSON: "
            '{"critique": str, "score": float (0-1), "issues": [str]}'
        ),
        temperature=0.1,
        mode="json",
        max_tokens=config.max_tokens,
    )
    prompt = f"Criteria: {criteria}\n\nContent to critique:\n{content}"
    return b.complete(cfg, prompt)


def run_agent(
    config: ModelConfig,
    goal: str,
    max_steps: int = 5,
    min_conf: float = 0.6,
    backend=None,
) -> Dict[str, Any]:
    """
    Minimal agent loop: plan -> execute steps via model -> optional critique.
    Returns {plan, steps, final, confidence}.
    """
    b = backend or get_backend()
    if b is None:
        from library.core import LLMBackend
        b = LLMBackend(mock=True)

    plan_result = plan(config, goal, backend=b)
    steps_out = []
    plan_data = plan_result.json() or {}
    steps = plan_data.get("steps") or [{"id": 1, "action": goal}]

    memory = Memory(system=config.system)
    memory.add_user(f"Goal: {goal}")

    for i, step in enumerate(steps[:max_steps]):
        action = step.get("action") if isinstance(step, dict) else str(step)
        r = chat(config, f"Step {i+1}: {action}\nDo this step. Be concise.", memory=memory, backend=b)
        steps_out.append({"action": action, "result": r.text, "confidence": r.confidence})
        if r.confidence < min_conf:
            break

    final = chat(config, f"Summarize the outcome for goal: {goal}", memory=memory, backend=b)
    return {
        "plan": plan_data,
        "steps": steps_out,
        "final": final.text,
        "confidence": final.confidence,
    }
