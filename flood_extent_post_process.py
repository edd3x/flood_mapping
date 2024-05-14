import os
import glob
import pyproj
import pandas as pd
import geopandas as gpd
from datetime import datetime

sepa_schema = {'properties': {'OBJECTID': 'int',
  'event_type': 'str:22',
  'obj_desc': 'str:36',
  'det_method': 'str:25',
  'notation': 'str:21',
  'dmg_src_id': 'int',
  'area': 'float',
  'eventphase': 'str:14',
  'sensor_gsd': 'str:254',
  'source_nam': 'str:28',
  'source_tm': 'str:254',
  'src_date': 'str:254',
  'sourcedate': 'str:255',
  'Shape_Length': 'float',
  'Shape_Area': 'float'},
 'geometry': 'Polygon'}

### Set path to .GPKG files in outputs_for_charter
### Outputs are a stored in outputs_for_charter_final folder
fld_ext_file = glob.glob('.../outputs_for_charter/*.gpkg')

print('loading LC Maps...')
lc_map = gpd.read_file('./scott_sub_lc_map/scott_lcover_class2.shp', engine='fiona')
print('LC Loaded')

for shp in fld_ext_file:
    print(shp)
    fld_ext_shp = gpd.read_file(shp, engine='fiona').to_crs('EPSG:27700')
    fld_ext_true = fld_ext_shp[fld_ext_shp.raster_val==1.0]

    print('Masking...')
    fld_ext_lc_mask = fld_ext_true.overlay(lc_map, how="difference", keep_geom_type=True)

    vector_dict = {k:[] for k in list(sepa_schema['properties'].keys())+['geometry']}
    name = os.path.basename(shp).split('.')[0].split('_')
    aoiID = int(f'{name[1][-1]}')
    sensor_res = f'{name[2][1:]}m'
    # print(sensor_res)
    sensor_name  =  name[0] 
    time = datetime.strptime(name[4], '%H%M%S').strftime("%H:%M:%S")
    date = datetime.strptime(f'{name[3]}', '%Y%m%d').strftime("%Y-%m-%d")

    for idx, geom in enumerate(fld_ext_lc_mask.geometry.explode(index_parts=True)):
        geom_area = geom.area
        geom_length = geom.length

        schema_keys = list(sepa_schema['properties'].keys())+['geometry']
        schema_attribs = [idx+1,'5-Flood','Riverine flood','Semi-automatic extraction','Flooded area',aoiID,geom_area/10000,'Post-event',f'{sensor_res}',sensor_name,time,date,date,geom_length,geom_area,geom]

        for s, a in zip(schema_keys, schema_attribs):
            # print(s,'->',a)
            vector_dict[s].append(a)
    print('Saving...')
    new_gdf = gpd.GeoDataFrame(pd.DataFrame(vector_dict), crs='EPSG:27700')
    new_gdf.to_file(f'.../A_flood_extent_AoI-ID{aoiID}_{name[0]}_{name[3]}_{name[4]}.gpkg', schema=sepa_schema, driver='GPKG')