import sys
from pyquadkey2 import quadkey
from db.api import BaseDb


class AreaDb(BaseDb):

    def __init__(self, folder='./data', file_name='qk-fences.db'):
        super().__init__(folder=folder, file_name=file_name)
        res = self.query("select min(square_level), max(square_level) from geo_square")
        self.min_level = res[0][0]
        self.max_level = res[0][1]

    def query_quadkey(self, qk):
        quad_int = qk.to_quadint()
        level = quad_int & 31
        qk_int = quad_int >> (64 - (level * 2))
        level_count = self.max_level - self.min_level
        qk_list = [qk_int >> (n * 2) for n in range(level_count)]
        in_list = ",".join("?" * len(qk_list))

        sql = f"select square_id, fence_id, square_level from geo_square where square_qk in ({in_list})"
        return self.query(sql, qk_list)


def query(latitude, longitude):
    db = AreaDb()
    qk = quadkey.from_geo((latitude, longitude), db.max_level)
    return db.query_quadkey(qk)


def main():
    if len(sys.argv) < 3:
        print("Usage: python query.py latitude longitude")
    else:
        latitude = float(sys.argv[1])
        longitude = float(sys.argv[2])
        print(query(latitude, longitude))


if __name__ == "__main__":
    main()
