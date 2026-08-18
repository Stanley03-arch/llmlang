"""Reusable agent strategies: self-consistency, debate, plan-and-execute, refine."""

from __future__ import annotations
from typing import Any, Callable, List
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.core import run_agent, CallResult, model

def self_consistency(agent: Callable, prompt: str, n: int = 3) -> CallResult:
    answers = []
    for i in range(n):
        r = run_agent(agent, f"{prompt}\n(Independent attempt {i+1}/{n})", max_turns=2)
        answers.append(r.final_answer)
    # majority-ish: return last with note
    text = f"votes={n}\n" + "\n---\n".join(answers)
    return CallResult(text=text, confidence=0.7, final=True)

def debate(agent_a: Callable, agent_b: Callable, question: str, rounds: int = 2) -> CallResult:
    history = []
    a = run_agent(agent_a, f"Argue for your best answer: {question}", max_turns=2)
    history.append(f"A: {a.final_answer}")
    for r in range(rounds):
        b = run_agent(agent_b, f"Critique and improve:\n{history[-1]}\nQuestion: {question}", max_turns=2)
        history.append(f"B: {b.final_answer}")
        a = run_agent(agent_a, f"Respond to critique:\n{history[-1]}", max_turns=2)
        history.append(f"A: {a.final_answer}")
    return CallResult(text="\n".join(history), confidence=0.65, final=True)

def plan_and_execute(agent: Callable, goal: str) -> CallResult:
    prompt = (
        f"Goal: {goal}\n"
        "1) Write a short plan (3-6 steps)\n2) Execute using tools\n3) Report outcome"
    )
    r = run_agent(agent, prompt, max_turns=6)
    return CallResult(text=r.final_answer, confidence=r.confidence, final=True)

def refine(agent: Callable, draft: str, criteria: str = "clarity and correctness") -> CallResult:
    prompt = f"Refine this draft for {criteria}:\n\n{draft}\n\nReturn the improved version."
    r = run_agent(agent, prompt, max_turns=2)
    return CallResult(text=r.final_answer, confidence=r.confidence, final=True)

def majority_vote(answers: List[str]) -> str:
    from collections import Counter
    if not answers:
        return ""
    return Counter(answers).most_common(1)[0][0]
