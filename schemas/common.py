"""
Reusable JSON schemas for structured generation.
"""

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "reasoning": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["answer", "confidence"],
    "additionalProperties": False,
}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "action": {"type": "string"},
                    "needs_tool": {"type": "boolean"},
                },
                "required": ["id", "action"],
            },
        },
    },
    "required": ["goal", "steps"],
    "additionalProperties": False,
}

CRITIQUE_SCHEMA = {
    "type": "object",
    "properties": {
        "critique": {"type": "string"},
        "score": {"type": "number", "minimum": 0, "maximum": 1},
        "issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["critique", "score"],
    "additionalProperties": False,
}

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "alternatives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
        },
    },
    "required": ["label", "confidence"],
    "additionalProperties": False,
}
