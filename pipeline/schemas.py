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
                            "selection-policy",
                            "simulation-enhancement",
                            "parallelization",
                            "meta-optimization",
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
            "enum": ["game_tree", "random_tree", "adversarial_tree", "blokus_position"],
        },
        "visualization_type": {
            "type": "string",
            "enum": [
                "tree_expansion",
                "visit_heatmap",
                "convergence_curve",
                "win_rate_over_time",
            ],
        },
    },
    "additionalProperties": False,
}

CONTENT_BRIEF_SCHEMA = {
    "type": "object",
    "required": [
        "topic",
        "audience",
        "content_type",
        "technical_depth",
        "goals",
        "requested_artifacts",
        "raw_input_summary",
    ],
    "properties": {
        "topic": {"type": "string", "minLength": 3},
        "audience": {"type": "string", "minLength": 3},
        "content_type": {
            "type": "string",
            "enum": [
                "blog_post",
                "linkedin_post",
                "tutorial",
                "readme",
                "article",
                "slide_outline",
                "short_form_script",
            ],
        },
        "technical_depth": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"],
        },
        "goals": {
            "type": "array",
            "items": {"type": "string", "minLength": 3},
            "minItems": 1,
        },
        "requested_artifacts": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "raw_input_summary": {"type": "string", "minLength": 10},
        "key_terms": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


RESEARCH_NOTES_SCHEMA = {
    "type": "object",
    "required": ["notes", "assumptions", "open_questions"],
    "properties": {
        "notes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "claim",
                    "supporting_points",
                    "needs_verification",
                ],
                "properties": {
                    "claim": {"type": "string", "minLength": 5},
                    "supporting_points": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "needs_verification": {"type": "boolean"},
                    "source_hint": {"type": "string"},
                },
                "additionalProperties": False,
            },
            "minItems": 1,
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "open_questions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


CONTENT_OUTLINE_SCHEMA = {
    "type": "object",
    "required": [
        "title",
        "hook",
        "sections",
        "estimated_word_count",
        "target_format",
    ],
    "properties": {
        "title": {"type": "string", "minLength": 5},
        "hook": {"type": "string", "minLength": 10},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["heading", "purpose", "key_points", "section_type"],
                "properties": {
                    "heading": {"type": "string", "minLength": 3},
                    "purpose": {"type": "string", "minLength": 5},
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                    "section_type": {
                        "type": "string",
                        "enum": [
                            "intro",
                            "explanation",
                            "example",
                            "comparison",
                            "deep_dive",
                            "cta",
                            "conclusion",
                        ],
                    },
                },
                "additionalProperties": False,
            },
            "minItems": 3,
        },
        "estimated_word_count": {"type": "integer", "minimum": 100},
        "target_format": {"type": "string", "minLength": 3},
    },
    "additionalProperties": False,
}


DRAFT_SCHEMA = {
    "type": "object",
    "required": ["markdown", "word_count", "sections_covered"],
    "properties": {
        "markdown": {"type": "string", "minLength": 200},
        "word_count": {"type": "integer", "minimum": 50},
        "sections_covered": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "additionalProperties": False,
}


REVIEW_REPORT_SCHEMA = {
    "type": "object",
    "required": ["issues", "blocking_issues_count", "overall_assessment"],
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["severity", "location", "description"],
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "major", "minor", "nit"],
                    },
                    "location": {"type": "string"},
                    "description": {"type": "string", "minLength": 5},
                    "suggested_fix": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        "blocking_issues_count": {"type": "integer", "minimum": 0},
        "overall_assessment": {"type": "string", "minLength": 5},
        "requires_human": {"type": "boolean"},
    },
    "additionalProperties": False,
}


EDITED_DRAFT_SCHEMA = {
    "type": "object",
    "required": ["markdown", "word_count", "changes_made", "resolved_issues"],
    "properties": {
        "markdown": {"type": "string", "minLength": 200},
        "word_count": {"type": "integer", "minimum": 50},
        "changes_made": {
            "type": "array",
            "items": {"type": "string"},
        },
        "resolved_issues": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


REPURPOSED_ASSETS_SCHEMA = {
    "type": "object",
    "required": [
        "linkedin_post",
        "x_thread",
        "youtube_description",
        "short_form_script",
        "newsletter_blurb",
        "readme_excerpt",
    ],
    "properties": {
        "linkedin_post": {"type": "string", "minLength": 50},
        "x_thread": {
            "type": "array",
            "items": {"type": "string", "minLength": 5},
            "minItems": 2,
        },
        "youtube_description": {"type": "string", "minLength": 50},
        "short_form_script": {"type": "string", "minLength": 30},
        "newsletter_blurb": {"type": "string", "minLength": 30},
        "readme_excerpt": {"type": "string", "minLength": 30},
    },
    "additionalProperties": False,
}


PUBLISHING_QA_SCHEMA = {
    "type": "object",
    "required": ["findings", "qa_score", "publishable", "blocking_issues"],
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["category", "severity", "description"],
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "missing_section",
                            "format",
                            "overclaim",
                            "weak_hook",
                            "cta",
                            "terminology",
                            "completeness",
                        ],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "major", "minor", "nit"],
                    },
                    "description": {"type": "string", "minLength": 5},
                },
                "additionalProperties": False,
            },
        },
        "qa_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "publishable": {"type": "boolean"},
        "blocking_issues": {
            "type": "array",
            "items": {"type": "string"},
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
    "content_brief": CONTENT_BRIEF_SCHEMA,
    "research_notes": RESEARCH_NOTES_SCHEMA,
    "content_outline": CONTENT_OUTLINE_SCHEMA,
    "draft": DRAFT_SCHEMA,
    "review_report": REVIEW_REPORT_SCHEMA,
    "edited_draft": EDITED_DRAFT_SCHEMA,
    "repurposed_assets": REPURPOSED_ASSETS_SCHEMA,
    "publishing_qa": PUBLISHING_QA_SCHEMA,
}
