import re


def hex_to_rgba(hex_color, alpha=0.4) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def rgb_to_rgba(rgb_color, alpha=0.4) -> str:

    rgb = re.findall(r"([\d]+)", rgb_color)
    return f"rgba({', '.join(rgb)}, {alpha})"
