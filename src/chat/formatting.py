"""Lays out chat replies the same way every time, whatever spacing the AI used.

- each numbered step on its own line, with a blank line before and after the list
- a blank line between paragraphs
- bullets always as "- ", and menu paths such as **Settings > Plan > Change plan** always bold
- names of buttons, menus and forms (written in **bold** by the AI) are kept bold, so a name that ends in "?",
  such as the **Can't access your account?** form, reads as a name and not as a question
"""

import re

STEP = re.compile(r"^\s*(\d+)[.)]\s+")


# A menu path the AI forgot to bold, such as Settings > Plan > Change plan.
MENU_PATH = re.compile(r"(?<![*\w])((?:Settings|Products|Orders|Customers|Marketing|Analytics|Apps|Finances|"
                       r"Online Store)(?: > [A-Z][a-z]*(?: (?:and )?[a-z]+)*)+)(?![*\w])")


def format_chat_reply(text: str) -> str:
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"^\s*[*•]\s+", "- ", text, flags=re.M)  # one bullet style
    text = MENU_PATH.sub(r"**\1**", text)
    # A numbered step that follows other text on the same line moves to its own line ("...: 1. Go to 2. Click").
    text = re.sub(r"(?<=\S)\s+(\d{1,2})[.)]\s+(?=[A-Z*])", r"\n\1. ", text)
    blocks, current, in_list = [], [], ""
    for line in (l.strip() for l in text.split("\n")):
        if not line:
            continue
        kind = "table" if line.startswith("|") else "list" if STEP.match(line) or line.startswith("- ") else ""
        is_step = bool(kind)
        if current and kind != in_list:  # a list or table starts or ends: new block
            blocks.append(current)
            current = []
        if is_step:
            current.append(STEP.sub(lambda m: f"{m.group(1)}. ", line))
        else:
            if current:  # every plain line is its own paragraph
                blocks.append(current)
                current = []
            current.append(line)
        in_list = kind
    if current:
        blocks.append(current)
    return "\n\n".join("\n".join(b) for b in blocks)
