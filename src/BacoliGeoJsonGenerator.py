from pathlib import Path
import geopandas as gpd
import pandas as pd
from matplotlib import pyplot as plt
import contextily as cx
import osmnx as ox
import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')

print('Begin')
main_folder = Path.cwd().joinpath('data')
print('Main folder {}'.format(main_folder))
municipalities = main_folder.joinpath('comuni').joinpath('Com01012023_g_WGS84.shp')
print('Municipalities {}'.format(municipalities))
regions = main_folder.joinpath('regioni').joinpath('Reg01012023_g_WGS84.shp')
print('Regions {}'.format(regions))
osm_crs = 4326

municipalities_gdf = gpd.read_file(municipalities).to_crs(osm_crs)
regions_gdf = gpd.read_file(regions).to_crs(osm_crs)

bacoli = municipalities_gdf[municipalities_gdf['COMUNE']=='Bacoli'].squeeze()
print(bacoli)

bacoli_data = ox.features_from_polygon(
    polygon=bacoli.geometry,
    tags={'historic': True}
)

excluded_keys = ['aircraft', 'aircraft; memorial', 'anchor', 'battlefield', 'bomb_crater', 'boundary_stone', 'cannon', 'cattle_crush', 'district', 'highwater_mark', 'hotel', 'locomotive', 'memorial', 'ogham_stone', 'railway', 'railway_car', 'railway_station', 'road', 'shieling', 'ship', 'tank', 'vehicle', 'wayside_cross', 'wayside_shrine', 'wreck', 'yes']
bacoli_data = bacoli_data[['historic', 'name', 'historic:civilization', 'geometry']]
bacoli_data = bacoli_data[~bacoli_data['historic'].isin(excluded_keys)]
bacoli_data = bacoli_data[bacoli_data['name'].notna()]
bacoli_data.reset_index(inplace=True)
bacoli_site_count = len(bacoli_data.index)
bacoli_data['geometry'] = bacoli_data.geometry.to_crs(epsg=7791)
print('Bacoli count {}'.format(bacoli_site_count))

bacoli_polygons = bacoli_data[bacoli_data['element_type']=='way']
bacoli_polygons['geometry'] = bacoli_polygons.geometry.to_crs(epsg=7791)
bacoli_polygons['centroid'] = bacoli_polygons.geometry.centroid
bacoli_polygons.drop(columns={'geometry'}, inplace=True)
bacoli_polygons.rename(columns={'centroid': 'geometry'}, inplace=True)
bacoli_final = pd.concat([bacoli_polygons, bacoli_data[bacoli_data['element_type']=='node']])
bacoli_final.drop(columns={'element_type'}, inplace=True)
bacoli_final.sort_values(by='name', inplace=True)
bacoli_final = gpd.GeoDataFrame(bacoli_final, geometry='geometry')
bacoli_group = bacoli_final.groupby(by='historic').count()
bacoli_group.drop(columns={'name', 'historic:civilization', 'geometry'}, inplace=True)
bacoli_group.rename(columns={'osmid': 'count'}, inplace=True)
bacoli_group.sort_values(by='count', ascending=False, inplace=True)
print(bacoli_group)

contextily_tile_crs = 3857
target_data = 'archaeological_site'
bacoli_archaeological_site = bacoli_final[bacoli_final['historic']==target_data]

bacoli_polygon = gpd.GeoDataFrame(geometry=gpd.GeoSeries(bacoli.geometry), crs=osm_crs).to_crs(contextily_tile_crs)


b_minx, b_miny, b_maxx, b_maxy = bacoli_polygon.squeeze().bounds

bacoli_img, bacoli_ext = cx.bounds2img(w=b_minx, s=b_miny, e=b_maxx, n=b_maxy, ll=False)

fig, ax = plt.subplots(figsize=(10, 10))
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
plt.title(f'Siti archeologici nel Comune di Bacoli: {len(bacoli_archaeological_site.index)}')

ax.imshow(bacoli_img, extent=bacoli_ext, zorder=0)
bacoli_polygon.boundary.plot(ax=ax, edgecolor='black', zorder=1)
bacoli_archaeological_site.to_crs(contextily_tile_crs).plot(ax=ax, marker="o", facecolor='red', edgecolor='white', markersize=50, zorder=2)

f = open("./data/output.txt", mode="wt")
f.write(bacoli_archaeological_site.to_json())
f.flush()
f.close()