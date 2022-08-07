import math
import numpy as np
from matplotlib import pyplot as plt
from dataclasses import dataclass
from operator import attrgetter

# Algorithm based on https://www.cs.rit.edu/~icss571/filling/how_to.html


@dataclass
class PolyVertex:
    __slots__ = ["x", "y"]
    x: int
    y: int


@dataclass
class ActiveEdge:
    __slots__ = ["y_max", "x", "incr"]
    y_max: int
    x: float
    incr: float

    def __eq__(self, other):
        return self.x == other.x

    def __lt__(self, other):
        return self.x < other.x


@dataclass
class PolyEdge:
    __slots__ = ["y_min", "y_max", "x_min", "incr"]
    y_min: int
    y_max: int
    x_min: int
    incr: float

    def __eq__(self, other):
        return self.y_min == other.y_min and self.x_min == other.x_min

    def __lt__(self, other):
        return self.y_min < other.y_min and self.x_min < other.x_min

    def to_active(self):
        return ActiveEdge(self.y_max, self.x_min, self.incr)


def build_edge(v0, v1):
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


def edges_from_ring(ring):
    vx = ring.copy()
    vx.append(vx[0])

    edges = []
    for i in range(len(vx)-1):
        v0 = vx[i]
        v1 = vx[i+1]
        if v0.y != v1.y:
            edges.append(build_edge(v0, v1))
    return sorted(edges)


def insert_edges(edges, y):
    return [edge.to_active() for edge in edges if edge.y_min == y]


def remove_edges(active_edges, y):
    return [edge for edge in active_edges if edge.y_max != y]


def fill_polygon(polygon):
    edges = edges_from_ring(polygon)

    y_min = min(polygon, key=attrgetter("y")).y
    y_max = max(polygon, key=attrgetter("y")).y
    x_max = max(polygon, key=attrgetter("x")).x

    bmp = np.full((y_max+1, x_max+1, 3), fill_value=[255, 255, 255], dtype=np.uint8)

    active_edges = []

    for y_line in range(y_min, y_max):
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
                    bmp[y_line, x] = [0, 0, 255]

        for edge in active_edges:
            edge.x += edge.incr
    return bmp


def main():
    polygon = [PolyVertex(20, 30),
               PolyVertex(80, 10),
               PolyVertex(160, 60),
               PolyVertex(140, 100),
               PolyVertex(160, 180),
               PolyVertex(80, 120),
               PolyVertex(20, 150)
               ]
    bmp = fill_polygon(polygon)

    plt.imshow(bmp, interpolation='nearest')
    plt.show()


if __name__ == "__main__":
    main()
