#!/usr/bin/env python3
"""Build the public corpus from its source-reviewed example ledger."""

import build_xml


def main() -> None:
    rows = build_xml.read_examples()
    build_xml.write_tree(build_xml.build_tree(rows))
    print(f"Built {len(rows)} source-adjudicated sentences from the reviewed ledger.")


if __name__ == "__main__":
    main()
