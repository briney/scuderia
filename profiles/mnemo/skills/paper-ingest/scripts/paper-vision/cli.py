"""Standalone CLI: one bounded JSON request on stdin; same handler as the plugin."""
import argparse
import json
import sys

if __package__:
    from .client import MAX_INPUT_BYTES, paper_vision_inspect, parse_json
else:
    from client import MAX_INPUT_BYTES, paper_vision_inspect, parse_json


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default error can echo arbitrary command-line data.
        self.exit(2, 'paper-vision: invalid command-line arguments\n')


def main(argv=None):
    parser = SafeParser(description='Inspect local paper images using the pinned paper vision recipe. Read JSON from stdin.')
    parser.parse_args(argv)
    try:
        stream = getattr(sys.stdin, 'buffer', sys.stdin)
        raw = stream.read(MAX_INPUT_BYTES + 1)
        if isinstance(raw, str):
            raw = raw.encode('utf-8')
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError()
        args = parse_json(raw)
    except Exception:
        print('{"status":"error","error":"invalid-input-json"}')
        return 1
    result = paper_vision_inspect(args)
    print(result)
    return 0 if json.loads(result)['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
