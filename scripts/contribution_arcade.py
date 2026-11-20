"""Render a looping Pac-Man animation from GitHub's public contribution calendar."""
import sys
from shortest_route import shortest_route
from ghost_patrol import patrol
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
    route = shortest_route((x, y) for x, y, level in grid if level)
    steps = len(route) - 1
    print(f'{steps} certified minimum steps')
    first_visit = {}
    for step, cell in enumerate(route):
        first_visit.setdefault(cell, step)
    svg = ET.Element("svg", xmlns="http://www.w3.org/2000/svg",
                     viewBox=f"0 0 {weeks * 16 + 24} 144", role="img")
    ET.SubElement(svg, "title").text = "Pac-Man eating dots on Liang Shan’s GitHub contribution calendar"
    ET.SubElement(svg, "style").text = """
    .tile{fill:#e8ecee}.pac{fill:#ffcf50;stroke:#b78830;stroke-width:.6}
    @media(prefers-color-scheme:dark){.tile{fill:#19222a}}
    @media(prefers-reduced-motion:reduce){.player{display:none}.dot{opacity:1!important}}
    """
    colors = ["", "#579991", "#45aba1", "#37c4b3", "#50ddc9"]
    for col, row, level in grid:
        x, y = col * 16 + 20, row * 16 + 24
        ET.SubElement(svg, "rect", x=str(x-7), y=str(y-7), width="14", height="14",
                      rx="3", attrib={"class": "tile"})
        if level:
            dot = ET.SubElement(svg, "circle", cx=str(x), cy=str(y), r=str(2 + level / 2),
                                fill=colors[level], attrib={"class": "dot"})
            arrival = max(.00001, first_visit[col, row] / (steps + 1))
            ET.SubElement(dot, "animate", attributeName="opacity", values="1;0;0",
                          keyTimes=f"0;{arrival:.6f};1", calcMode="discrete",
                          dur="40s", repeatCount="indefinite")
    player = ET.SubElement(svg, "g", attrib={"class": "player"})
    timeline = route + [route[-1]]
    def move(actor, path):
        values = ";".join(f"{16*x+20} {16*y+24}" for x,y in path)
        ET.SubElement(actor, "animateTransform", attributeName="transform", type="translate",
                      values=values, calcMode="linear", dur="40s", repeatCount="indefinite")
    move(player, timeline)
    facing = ET.SubElement(player, "g")
    angles = {(1,0):0, (0,1):90, (-1,0):180, (0,-1):270}
    headings = [angles[(b[0]-a[0], b[1]-a[1])] for a,b in zip(route,route[1:])]
    headings.extend([headings[-1] if headings else 0]*2)
    ET.SubElement(facing, "animateTransform", attributeName="transform", type="rotate",
                  values=";".join(map(str,headings)), calcMode="discrete",
                  keyTimes=";".join(str(i/(len(timeline)-1)) for i in range(len(timeline))),
                  dur="40s", repeatCount="indefinite")
    mouth = "M0 0 L6 -4 A7.2 7.2 0 1 0 6 4 Z"
    closed = "M0 0 L7.2 -.4 A7.2 7.2 0 1 0 7.2 .4 Z"
    body = ET.SubElement(facing, "path", d=mouth, attrib={"class": "pac"})
    ET.SubElement(body, "animate", attributeName="d", values=";".join([mouth, closed, mouth]),
                  dur=".29s", repeatCount="indefinite")
    occupied = [timeline]
    cells = {(x,y) for x,y,_ in grid}
    for lane, lag, color in [(1, 5, "#71b4d0"), (-1, 8, "#d992ac")]:
        ghost = ET.SubElement(svg, "g", attrib={"class":"player"})
        path = patrol(timeline, occupied, cells, lane, lag)
        move(ghost, path)
        occupied.append(path)
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
    ET.ElementTree(render(calendar.days)).write("contribution-patrol.svg", encoding="utf-8")
