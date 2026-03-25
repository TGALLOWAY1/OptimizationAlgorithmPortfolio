"""JSON Schema definitions for all artifact types."""

PLAN_SCHEMA = {
    "type": "object",
    "required": [
        "technique_name",
        "slug",
        "aliases",
        "problem_type",
        "notation_conventions",
        "assumptions",
        "target_audience",
        "artifacts_required",
    ],
    "properties": {
        "technique_name": {"type": "string", "minLength": 1},
        "slug": {"type": "string", "minLength": 1},
        "aliases": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "problem_type": {"type": "string", "minLength": 1},
        "notation_conventions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "target_audience": {"type": "string", "minLength": 1},
        "artifacts_required": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "additionalProperties": False,
}

OVERVIEW_SCHEMA = {
    "type": "object",
    "required": [
        "technique_slug",
        "artifact_type",
        "title",
        "summary",
        "markdown",
        "use_cases",
        "strengths",
        "limitations",
        "comparisons",
    ],
    "properties": {
        "technique_slug": {"type": "string", "minLength": 1},
        "artifact_type": {"type": "string", "const": "overview"},
        "title": {"type": "string", "minLength": 1},
        "summary": {"type": "string", "minLength": 1},
        "markdown": {"type": "string", "minLength": 800},
        "use_cases": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "limitations": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "comparisons": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "additionalProperties": False,
}

MATH_DEEP_DIVE_SCHEMA = {
    "type": "object",
    "required": [
        "technique_slug",
        "artifact_type",
        "markdown",
        "key_equations",
        "worked_examples",
        "common_confusions",
    ],
    "properties": {
        "technique_slug": {"type": "string", "minLength": 1},
        "artifact_type": {"type": "string", "const": "math_deep_dive"},
        "markdown": {"type": "string", "minLength": 800},
        "key_equations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["equation", "label", "step_by_step_derivation"],
                "properties": {
                    "equation": {"type": "string", "minLength": 1},
                    "label": {"type": "string", "minLength": 1},
                    "step_by_step_derivation": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                    },
                },
                "additionalProperties": False,
            },
            "minItems": 1,
        },
        "worked_examples": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "common_confusions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "additionalProperties": False,
}

IMPLEMENTATION_SCHEMA = {
    "type": "object",
    "required": [
        "technique_slug",
        "artifact_type",
        "markdown",
        "python_examples",
        "libraries",
        "runtime_dependencies",
        "pseudo_code",
        "code_variations",
    ],
    "properties": {
        "technique_slug": {"type": "string", "minLength": 1},
        "artifact_type": {"type": "string", "const": "implementation"},
        "markdown": {"type": "string", "minLength": 800},
        "python_examples": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "libraries": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "runtime_dependencies": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "pseudo_code": {"type": "string", "minLength": 1},
        "code_variations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["framework", "label", "code"],
                "properties": {
                    "framework": {"type": "string", "minLength": 1},
                    "label": {"type": "string", "minLength": 1},
                    "code": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
            },
            "minItems": 3,
            "maxItems": 3,
        },
    },
    "additionalProperties": False,
}

INFOGRAPHIC_SPEC_SCHEMA = {
    "type": "object",
    "required": [
        "technique_slug",
        "artifact_type",
        "title",
        "panels",
        "visual_metaphors",
        "color_palette",
        "layout",
        "typography",
        "key_equations",
    ],
    "properties": {
        "technique_slug": {"type": "string", "minLength": 1},
        "artifact_type": {"type": "string", "const": "infographic_spec"},
        "title": {"type": "string", "minLength": 1},
        "panels": {
            "type": "array",
            "items": {"type": "object"},
            "minItems": 1,
        },
        "visual_metaphors": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "color_palette": {"type": "string", "minLength": 1},
        "layout": {"type": "string", "minLength": 1},
        "typography": {"type": "string", "minLength": 1},
        "key_equations": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "additionalProperties": False,
}

HOMEPAGE_SUMMARY_SCHEMA = {
    "type": "object",
    "required": ["bullets"],
    "properties": {
        "bullets": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 3,
            "maxItems": 5,
        },
    },
    "additionalProperties": False,
}

KNOWLEDGE_GRAPH_SCHEMA = {
    "type": "object",
    "required": ["nodes", "edges"],
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["slug", "label", "category", "summary"],
                "properties": {
                    "slug": {"type": "string", "minLength": 1},
                    "label": {"type": "string", "minLength": 1},
                    "category": {
                        "type": "string",
                        "enum": [
                            "evolutionary",
                            "gradient-based",
                            "probabilistic",
                            "direct-search",
                        ],
                    },
                    "summary": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
            },
            "minItems": 1,
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target", "relationship", "strength"],
                "properties": {
                    "source": {"type": "string", "minLength": 1},
                    "target": {"type": "string", "minLength": 1},
                    "relationship": {"type": "string", "minLength": 1},
                    "strength": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "additionalProperties": False,
            },
            "minItems": 1,
        },
    },
    "additionalProperties": False,
}

PLAYGROUND_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["parameters", "objective_function", "visualization_type"],
    "properties": {
        "parameters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "label", "min", "max", "default", "step"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "label": {"type": "string", "minLength": 1},
                    "min": {"type": "number"},
                    "max": {"type": "number"},
                    "default": {"type": "number"},
                    "step": {"type": "number"},
                    "description": {"type": "string"},
                },
                "additionalProperties": False,
            },
            "minItems": 1,
        },
        "objective_function": {
            "type": "string",
            "enum": ["rosenbrock", "rastrigin", "sphere", "ackley"],
        },
        "visualization_type": {
            "type": "string",
            "enum": [
                "contour_trajectory",
                "population_scatter",
                "convergence_curve",
            ],
        },
    },
    "additionalProperties": False,
}

SCHEMAS = {
    "plan": PLAN_SCHEMA,
    "overview": OVERVIEW_SCHEMA,
    "math_deep_dive": MATH_DEEP_DIVE_SCHEMA,
    "implementation": IMPLEMENTATION_SCHEMA,
    "infographic_spec": INFOGRAPHIC_SPEC_SCHEMA,
    "homepage_summary": HOMEPAGE_SUMMARY_SCHEMA,
    "knowledge_graph": KNOWLEDGE_GRAPH_SCHEMA,
    "playground_config": PLAYGROUND_CONFIG_SCHEMA,
}
