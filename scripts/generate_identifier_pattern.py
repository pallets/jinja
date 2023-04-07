import os
import re
import sys


def get_characters():
    """Find every Unicode character that is valid in a Python `identifier`_ but
    is not matched by the regex ``\\w`` group.

    ``\\w`` matches some characters that aren't valid in identifiers, but
    :meth:`str.isidentifier` will catch that later in lexing.

    All start characters are valid continue characters, so we only test for
    continue characters.

    _identifier: https://docs.python.org/3/reference/lexical_analysis.html#identifiers
    """
    for codepage in range(sys.maxunicode + 1):
        character = chr(codepage)
        if ("a" + character).isidentifier() and not re.match(r"\w", character):
            yield character


def grouped_characters(characters):
    """Emit groups of contiguous (adjacent) Unicode characters"""
    character_group = next(characters)
    for character in characters:
        prev_character = chr(ord(character) - 1)
        if character_group.endswith(prev_character):
            character_group += character
        else:
            yield character_group
            character_group = character


def represent_groups(groups):
    """Provide regex-compatible string representations of character groups"""
    for group in groups:
        if len(group) > 2:
            yield f"{group[0]}-{group[-1]}"
        else:
            yield from group


def main():
    """Build the regex pattern and write it to
    ``jinja2/_identifier.py``.
    """
    pattern = "".join(represent_groups(grouped_characters(get_characters())))
    filename = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "src", "jinja2", "_identifier.py")
    )

    with open(filename, "w", encoding="utf8") as f:
        f.write("import re\n\n")
        f.write("# generated by scripts/generate_identifier_pattern.py\n")
        f.write("pattern = re.compile(\n")
        f.write(f'    r"[\\w{pattern}]+"  # noqa: B950\n')
        f.write(")\n")


if __name__ == "__main__":
    main()
