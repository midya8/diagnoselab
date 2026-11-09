import argparse
import json
from pathlib import Path
from .core import audit, parse


def main(argv=None):
    parser = argparse.ArgumentParser(description='Exact tiny CNF conflicts and minimal repairs')
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit(parse(args.input.read_text(encoding='utf-8')))
        text = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Invalid input: {exc}\n')
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')
    return 0
