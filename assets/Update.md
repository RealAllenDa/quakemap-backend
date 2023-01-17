# Assets Update

## 1. Area

For _japan_areas.json_ and _tsunami_areas.json_, there isn't a need for updating, since JMA
**rarely (once in ~10 years)** changes its warning areas.

## 2. Centroid

For _area_position.json_ and _jma_area_centroid.csv_, there isn't a need for updating, since
JMA **rarely (once in ~10 years)** changes its warning areas.

For _observation_points.json_, update by running tools/obs_combiner/main.py.

For _intensity_stations.csv_, update by running tools/station_combiner/main.py.

## 3. PSWave

For _tjma2001_, there isn't a need for updating, since JMA **do not** update it.