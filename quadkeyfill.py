import math
import numba
import geojson
import sys

from pyquadkey2 import quadkey
from dataclasses import dataclass
from operator import attrgetter
from numba import njit
from db.api import BaseDb


set_type = numba.types.Set(numba.types.int64)


def load_geojson(file_name):
    with open(file_name) as f:
        gj = geojson.load(f)
        return gj


class AreaDb(BaseDb):

    def __init__(self, folder='./data', file_name='qk-fences.db'):
        super().__init__(folder=folder, file_name=file_name)

    def insert_areas(self, area_name, areas):
        conn = self.connect()
        cur = conn.cursor()
        sql = "insert into geo_fence (fence_name) values (?)"

        cur.execute(sql, [area_name])
        conn.commit()
        cur.close()

        fence_id = cur.lastrowid

        sql = "insert into geo_square (fence_id, square_level, square_qk) values (?,?,?)"

        cur = conn.cursor()
        for area in areas:
            for level, qks in area.items():
                cur.executemany(sql, [(fence_id, level, qk) for qk in qks])
        conn.commit()
        cur.close()
        conn.close()


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


class Borders:

    def __init__(self, file_name):
        self.geo_json = load_geojson(file_name)

    def get_countries(self):
        countries = []
        if self.geo_json.is_valid:
            features = self.geo_json["features"]
            for f in features:
                countries.append(f["properties"]["ADMIN"])
        return countries

    def get_country(self, country_name):
        country = None
        if self.geo_json.is_valid:
            features = self.geo_json["features"]
            for f in features:
                if f["properties"]["ADMIN"] == country_name:
                    country = f
                    break
        return country


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
    result = [edge.to_active() for edge in edges if edge.y_min == y]
    return result


def remove_edges(active, y):
    result = [edge for edge in active if edge.y_max != y]
    return result


def to_poly_vertex(latitude, longitude, level):
    """
    Converts a latitude, longitude and level into a PolyVertex.
    """
    qk = quadkey.from_geo((latitude, longitude), level)
    tile = qk.to_tile()[0]
    # test = qk_to_str(tile_to_qk(tile[0], tile[1], level), level)
    return PolyVertex(tile[0], tile[1])


@njit
def tile_to_qk(x, y, level):
    """
    Converts tile coordinates to a quadkey
    Code adapted from https://docs.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system
    :param x: Tile x coordinate
    :param y: Tile y coordinate
    :param level: Detail leve;
    :return: QuadKey
    """
    q = numba.types.int64(0)
    for i in range(level, 0, -1):
        mask = 1 << (i - 1)

        q = q << 2
        if (x & mask) != 0:
            q += 1
        if (y & mask) != 0:
            q += 2
    return q


def qk_to_str(qk, level):
    s = ""
    for i in range(level):
        shift = (level - i - 1) * 2
        mask = 3 << shift
        val = (qk & mask) >> shift
        s = s + chr(ord('0') + val)
    return s


def insert_qk(area, qk, level):
    inflating = True

    while inflating:
        if level not in area:
            area[level] = set()
        z = area[level]

        if ((qk & 3) == 3) and ((qk - 1) in z) and ((qk - 2) in z) and ((qk - 3) in z):
            z.remove(qk - 1)
            z.remove(qk - 2)
            z.remove(qk - 3)

            qk = qk >> 2
            level -= 1
            # area = insert_qk(area, qk >> 2, level - 1)
        else:
            z.add(qk)
            inflating = False

    return area


def plot0(area, x_range, y, level):
    qks = [tile_to_qk(x, y, level) for x in x_range]
    if level not in area:
        area[level] = set()
    area[level].update(qks)
    return area


def plot1(area, x_range, y, level):
    qks = [tile_to_qk(x, y, level) for x in x_range]
    for qk in qks:
        area = insert_qk(area, qk, level)
    return area


def fill_multi_polygon(multi_polygon, level):
    area = dict()
    edges = []
    y_max = -sys.maxsize - 1
    y_min = sys.maxsize
    x_max = -sys.maxsize - 1

    for ring in multi_polygon:
        y_min = min(y_min, min(ring, key=attrgetter("y")).y)
        y_max = max(y_max, max(ring, key=attrgetter("y")).y)
        x_max = max(x_max, max(ring, key=attrgetter("x")).x)

        edges.extend(edges_from_ring(ring))

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

                x_range = range(round(edge0.x), math.floor(edge1.x) + 1)
                if y_line % 2 == 0:
                    area = plot0(area, x_range, y_line, level)
                else:
                    area = plot1(area, x_range, y_line, level)

        y_line += 1
        for edge in active_edges:
            edge.x += edge.incr
    return area


def main():
    country = "Portugal"
    borders = Borders("data/countries.geojson")
    # print(borders.get_countries())

    pt = borders.get_country(country)
    geo = pt["geometry"]

    # print(len(geo["coordinates"]))
    level = 20

    areas = []

    for shape in geo["coordinates"]:
        multi_polygon = []
        for ring in shape:
            multi_polygon.append([to_poly_vertex(p[1], p[0], level) for p in ring])

        print(multi_polygon)

        area = fill_multi_polygon(multi_polygon, level)
        areas.append(area)

        # Print out the total number of quad-keys in the area
        total = 0
        for values in area.values():
            total += len(values)
        print(total)

    db = AreaDb()
    db.insert_areas(country, areas)


if __name__ == "__main__":
    main()
