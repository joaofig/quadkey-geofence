# quadkey-geofence
This project implements Python code to create geofences using quadkeys.


![This picture displays the hierarchical square discretization of continetal Portugal.](/pictures/quadkey-pt.png )

# Using the Code
Start by creating the supporting SQLite database on the `data` folder, named
`qk-geofences.db`.
Run the scripts from the `sql` folder in the following order: `geo_fence.sql`, 
`geo_square.sql`, and `ix_geo_square_fence_level.sql`.
Download the country borders data file from the [datasets/geo-countries](https://github.com/datasets/geo-countries)
GitHub repository, and place the `countries.geojson` file in the `data` folder.
Now you can run the code that generates a country's geofence as a hierarchical
set of quadkeys: `quadkeyfill.py`.
Note that you must select the country name in the source file.

The `polyfill.py` file contains code to illustrate how a scanline polygon
filling algorithm works, without the geospatial intricacies.
It uses a `NumPy` array as the bitmap and displays it at the end.

The two Jupyter notebooks generate the images used in the article.
You can only run the `qk-geofence.ipynb` notebook after running the 
`quadkeyfill.py` script, as it generates geofence data to the database.