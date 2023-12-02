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

campania = regions_gdf[regions_gdf['DEN_REG']=='Campania'].squeeze()
print(campania)



campania_data = ox.features_from_polygon(
    polygon=campania.geometry,
    tags={'historic': True}
)

excluded_keys = ['aircraft', 'aircraft; memorial', 'anchor', 'battlefield', 'bomb_crater', 'boundary_stone', 'cannon', 'cattle_crush', 'district', 'highwater_mark', 'hotel', 'locomotive', 'memorial', 'ogham_stone', 'railway', 'railway_car', 'railway_station', 'road', 'shieling', 'ship', 'tank', 'vehicle', 'wayside_cross', 'wayside_shrine', 'wreck', 'yes']

campania_data = campania_data[['historic', 'name', 'historic:civilization', 'geometry']]
campania_data = campania_data[~campania_data['historic'].isin(excluded_keys)]
campania_data = campania_data[campania_data['name'].notna()]
campania_data.reset_index(inplace=True)
campania_data_count = len(campania_data.index)
campania_data['geometry'] = campania_data.geometry.to_crs(epsg=7791)

campania_polygons = campania_data[campania_data['element_type']=='way']
campania_polygons['geometry'] = campania_polygons.geometry.to_crs(epsg=7791)
campania_polygons['centroid'] = campania_polygons.geometry.centroid
campania_polygons.drop(columns={'geometry'}, inplace=True)
campania_polygons.rename(columns={'centroid': 'geometry'}, inplace=True)

campania_final = pd.concat([campania_polygons, campania_data[campania_data['element_type']=='node']])
campania_final.drop(columns={'element_type'}, inplace=True)
campania_final.sort_values(by='name', inplace=True)
campania_final = gpd.GeoDataFrame(campania_final, geometry='geometry')
campania_site_count = len(campania_final.index)
print('Campania site count {}'.format(campania_data_count))

campania_group = campania_final.groupby(by='historic').count()
campania_group.drop(columns={'name', 'historic:civilization', 'geometry'}, inplace=True)
campania_group.rename(columns={'osmid': 'count'}, inplace=True)
campania_group.sort_values(by='count', ascending=False, inplace=True)
print(campania_group)






contextily_tile_crs = 3857
target_data = 'archaeological_site'


campania_polygon = gpd.GeoDataFrame(geometry=gpd.GeoSeries(campania.geometry), crs=osm_crs).to_crs(contextily_tile_crs)
campania_archaeological_site = campania_final[campania_final['historic']==target_data]

c_minx, c_miny, c_maxx, c_maxy = campania_polygon.squeeze().bounds

campania_img, campania_ext = cx.bounds2img(w=c_minx, s=c_miny, e=c_maxx, n=c_maxy, ll=False)

fig2, ax2 = plt.subplots(figsize=(10, 10))
ax2.get_xaxis().set_visible(False)
ax2.get_yaxis().set_visible(False)
plt.title(f'Siti archeologici in Campania: {len(campania_archaeological_site.index)}')

ax2.imshow(campania_img, extent=campania_ext, zorder=0)
campania_polygon.boundary.plot(ax=ax2, edgecolor='black', zorder=1)
campania_archaeological_site.to_crs(contextily_tile_crs).plot(ax=ax2, marker="o", facecolor='red', edgecolor='white', markersize=50, zorder=2)


f = open("./data/output_campania.txt", mode="wt")
f.write(campania_archaeological_site.to_json())
f.flush()
f.close()