"""Render a looping Pac-Man animation from GitHub's public contribution calendar."""
import sys
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree as ET


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "td" and "data-date" in data and "data-level" in data:
            self.days[date.fromisoformat(data["data-date"])] = int(data["data-level"])


def render(days):
    first = min(days)
    sunday = first - timedelta(days=(first.weekday() + 1) % 7)
    weeks = (max(days) - sunday).days // 7 + 1
    grid = [((day - sunday).days // 7, (day.weekday() + 1) % 7, level)
            for day, level in days.items()]
    route = sorted(grid, key=lambda cell: (cell[1], cell[0] if cell[1] % 2 == 0 else -cell[0]))
    svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg",
                     viewBox=f"0 0 {weeks * 16 + 8} 120", role="img")
    ET.SubElement(svg, "title").text = "Pac-Man eating dots on Liang Shan’s GitHub contribution calendar"
    ET.SubElement(svg, "style").text = """
    .tile{fill:#eff2f4}.pac{fill:#ffce39;stroke:#987319;stroke-width:.7}
    @media(prefers-color-scheme:dark){.tile{fill:#21262d}}
    @media(prefers-reduced-motion:reduce){.player{display:none}.dot{opacity:1!important}}
    """
    colors = ["", "#88c99a", "#52ac73", "#288953", "#12633c"]
    centers = []
    for step, (col, row, level) in enumerate(route):
        x, y = col * 16 + 12, row * 16 + 12
        centers.append(f"{x},{y}")
        ET.SubElement(svg, "rect", x=str(x-7), y=str(y-7), width="14", height="14",
                      rx="3", attrib={"class": "tile"})
        if level:
            dot = ET.SubElement(svg, "circle", cx=str(x), cy=str(y), r=str(2 + level / 2),
                                fill=colors[level], attrib={"class": "dot"})
            arrival = max(.00001, step / len(route))
            ET.SubElement(dot, "animate", attributeName="opacity", values="1;0;0",
                          keyTimes=f"0;{arrival:.6f};1", calcMode="discrete",
                          dur="40s", repeatCount="indefinite")
    player = ET.SubElement(svg, "g", attrib={"class": "player"})
    ET.SubElement(player, "animateMotion", path="M"+" L".join(centers+[centers[-1]]),
                  rotate="auto", calcMode="linear", dur="40s", repeatCount="indefinite")
    mouth = "M0 0 L6 -4 A7.2 7.2 0 1 0 6 4 Z"
    closed = "M0 0 L7.2 -.4 A7.2 7.2 0 1 0 7.2 .4 Z"
    body = ET.SubElement(player, "path", d=mouth, attrib={"class": "pac"})
    ET.SubElement(body, "animate", attributeName="d", values=";".join([mouth, closed, mouth]),
                  dur=".29s", repeatCount="indefinite")
    return svg


if __name__ == "__main__":
    if len(sys.argv) > 1:
        html = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        with urlopen("https://github.com/users/Twist-Shan/contributions", timeout=30) as response:
            html = response.read().decode()
    calendar = Calendar()
    calendar.feed(html)
    if len(calendar.days) < 350:
        raise ValueError("Incomplete contribution calendar")
    ET.ElementTree(render(calendar.days)).write("pacman.svg", encoding="utf-8")
