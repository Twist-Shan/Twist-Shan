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
    remaining = {(x, y) for x, y, level in grid if level}
    route = [(0, 0)]
    remaining.discard(route[0])
    while remaining:
        x, y = route[-1]
        target_x, target_y = min(remaining, key=lambda p: (abs(x-p[0])+abs(y-p[1]), p))
        while (x, y) != (target_x, target_y):
            if x != target_x:
                x += 1 if target_x > x else -1
            else:
                y += 1 if target_y > y else -1
            route.append((x, y))
            remaining.discard((x, y))
    # Retrace the path so the chase also loops smoothly at the year boundary.
    route += route[-2::-1] or [route[0]]
    first_visit = {}
    for step, cell in enumerate(route):
        first_visit.setdefault(cell, step)
    svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg",
                     viewBox=f"0 0 {weeks * 16 + 24} 144", role="img")
    ET.SubElement(svg, "title").text = "Pac-Man eating dots on Liang Shan’s GitHub contribution calendar"
    ET.SubElement(svg, "style").text = """
    .tile{fill:#1b2940}.pac{fill:#ffda49;stroke:#fff3ac;stroke-width:.6}
    @media(prefers-reduced-motion:reduce){.player{display:none}.dot{opacity:1!important}}
    """
    width = weeks * 16 + 24
    ET.SubElement(svg, "rect", width=str(width), height="144", rx="13", fill="#10192b")
    ET.SubElement(svg, "rect", x="5", y="5", width=str(width-10), height="134",
                  rx="10", fill="none", stroke="#42618a")
    colors = ["", "#589c98", "#6ac6af", "#96e0be", "#d3ffca"]
    centers = [f"{x*16+20},{y*16+24}" for x, y in route]
    for col, row, level in grid:
        x, y = col * 16 + 20, row * 16 + 24
        ET.SubElement(svg, "rect", x=str(x-7), y=str(y-7), width="14", height="14",
                      rx="3", attrib={"class": "tile"})
        if level:
            dot = ET.SubElement(svg, "circle", cx=str(x), cy=str(y), r=str(2 + level / 2),
                                fill=colors[level], attrib={"class": "dot"})
            arrival = max(.00001, first_visit[col, row] / (len(route)-1))
            if level == 4:
                ET.SubElement(svg, "circle", cx=str(x), cy=str(y), r="5.5",
                              fill="none", stroke="#708a75", attrib={"stroke-width":".6"})
            ET.SubElement(dot, "animate", attributeName="opacity", values="1;0;0",
                          keyTimes=f"0;{arrival:.6f};1", calcMode="discrete",
                          dur="40s", repeatCount="indefinite")
    player = ET.SubElement(svg, "g", attrib={"class": "player"})
    course = "M"+" L".join(centers)
    ET.SubElement(player, "animateMotion", path=course,
                  rotate="auto", dur="40s", repeatCount="indefinite")
    mouth = "M0 0 L6 -4 A7.2 7.2 0 1 0 6 4 Z"
    closed = "M0 0 L7.2 -.4 A7.2 7.2 0 1 0 7.2 .4 Z"
    body = ET.SubElement(player, "path", d=mouth, attrib={"class": "pac"})
    ET.SubElement(body, "animate", attributeName="d", values=";".join([mouth, closed, mouth]),
                  dur=".29s", repeatCount="indefinite")
    for delay, color in [(3, "#79c9ea"), (6, "#ed98b4")]:
        ghost = ET.SubElement(svg, "g", attrib={"class":"player"})
        cycle = centers[:-1]
        offset = delay % len(cycle)
        chase = cycle[-offset:] + cycle[:-offset] if offset else cycle
        ET.SubElement(ghost, "animateMotion", path="M"+" L".join(chase+[chase[0]]),
                      dur="40s", repeatCount="indefinite")
        ET.SubElement(ghost, "path", fill=color,
                      d="M-6 6V-2h1v-3h2v-1h6v1h2v3h1v8H4V4H2v2h-4V4h-2v2Z")
        for eye in [-3, 2]:
            ET.SubElement(ghost, "rect", x=str(eye), y="-2", width="3", height="4", fill="white")
            ET.SubElement(ghost, "rect", x=str(eye+1), y="-1", width="2", height="2", fill="#233456")
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
