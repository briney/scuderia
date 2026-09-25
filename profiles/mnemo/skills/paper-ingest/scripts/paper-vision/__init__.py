"""Native Hermes directory-plugin entry point; no network or credential read."""
from .client import MAX_IMAGES, MAX_LABEL, MAX_PATH, MAX_QUESTION, paper_vision_inspect


def bounded_text(limit):
    return {'type': 'string', 'minLength': 1, 'maxLength': limit}


SCHEMA = {
    'name': 'paper_vision_inspect',
    'description': (
        'Inspect ordered local PNG/JPEG original pages or crops with pinned qwen3.8-27b. '
        'Provide short labels and a visual question. Returns textual model observations, limitations, '
        'and evidence provenance; not human acceptance or a second-model verdict. '
        'Writes exact image copies to a NEW output directory whose parent already exists. '
        'No URLs or model/route overrides; no retries, even after failure. '
        'Up to 4 single-frame images, 20 MiB each, 12000 pixels per axis and 40 million pixels each. '
        'Image and question content is sent to the bundled HTTP endpoint.'
    ),
    'parameters': {
        'type': 'object', 'additionalProperties': False,
        'properties': {
            'images': {'type': 'array', 'minItems': 1, 'maxItems': MAX_IMAGES,
                       'items': {'type': 'object', 'additionalProperties': False,
                                 'properties': {'path': bounded_text(MAX_PATH), 'label': bounded_text(MAX_LABEL)},
                                 'required': ['path', 'label']}},
            'question': bounded_text(MAX_QUESTION),
            'output_dir': bounded_text(MAX_PATH),
        },
        'required': ['images', 'question', 'output_dir'],
    },
}


def register(ctx):
    ctx.register_tool(name='paper_vision_inspect', toolset='paper_vision',
                      schema=SCHEMA, handler=paper_vision_inspect)
