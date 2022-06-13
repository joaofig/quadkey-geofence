import math
import numpy as np
from matplotlib import pyplot as plt
from dataclasses import dataclass
from operator import attrgetter


@dataclass
class PolyVertex:
    __slots__ = ["x", "y"]
    x: float
    y: float


@dataclass
class ActiveEdge:
    __slots__ = ["y_max", "x", "incr"]
    y_max: float
    x: float
    incr: float

    def __eq__(self, other):
        return self.x == other.x

    def __lt__(self, other):
        return self.x < other.x


@dataclass
class PolyEdge:
    __slots__ = ["y_min", "y_max", "x_min", "incr"]
    y_min: float
    y_max: float
    x_min: float
    incr: float

    def __eq__(self, other):
        return self.y_min == other.y_min and self.x_min == other.x_min

    def __lt__(self, other):
        return self.y_min < other.y_min and self.x_min < other.x_min

    def to_active(self):
        return ActiveEdge(self.y_max, self.x_min, self.incr)


def build_edge(v0: PolyVertex, v1: PolyVertex) -> PolyEdge:
    y_min = min(v0.y, v1.y)
    y_max = max(v0.y, v1.y)
    if v0.y < v1.y:
        x_min = v0.x
    else:
        x_min = v1.x
    if v0.x == v1.x:
        incr = 0.0
    else:
        incr = (v1.x - v0.x) / (v1.y - v0.y)    # 1/m
    return PolyEdge(y_min, y_max, x_min, incr)


def generate_edges(vertices):
    vx = vertices.copy()
    vx.append(vx[0])

    edges = []
    for i in range(len(vx)-1):
        v0 = vx[i]
        v1 = vx[i+1]
        if v0.y != v1.y:
            edges.append(build_edge(v0, v1))
    return sorted(edges)


def insert_edges(edges, y):
    result = []
    for edge in edges:
        if edge.y_min == y:
            result.append(edge.to_active())
    return result


def remove_edges(active, y):
    result = []
    for edge in active:
        if edge.y_max != y:
            result.append(edge)
    return result


def main():
    vertices = [PolyVertex(20, 30),
                PolyVertex(80, 10),
                PolyVertex(160, 60),
                PolyVertex(160, 180),
                PolyVertex(80, 120),
                PolyVertex(20, 150)
                ]
    edges = generate_edges(vertices)

    y_min = min(vertices, key=attrgetter("y")).y
    y_max = max(vertices, key=attrgetter("y")).y
    x_max = max(vertices, key=attrgetter("x")).x
    # print(edges)

    bmp = np.zeros((y_max+1, x_max+1, 3), dtype=np.uint8)

    y_line = y_min
    active_edges = []

    while y_line < y_max:
        active_edges.extend(insert_edges(edges, y_line))
        active_edges = sorted(remove_edges(active_edges, y_line))

        # Draw the scan line
        i = 0
        n = len(active_edges)
        while i < n:
            edge0 = active_edges[i]
            i += 1
            if i < n:
                edge1 = active_edges[i]
                i += 1

                for x in range(round(edge0.x), math.floor(edge1.x) + 1):
                    # print(f"({x}, {y_line})")
                    bmp[y_line, x] = [0, 0, 255]

        y_line += 1
        for edge in active_edges:
            edge.x += edge.incr

    plt.imshow(bmp, interpolation='nearest')
    plt.show()


if __name__ == "__main__":
    main()
