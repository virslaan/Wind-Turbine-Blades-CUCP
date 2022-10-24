import streamlit as st
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
from streamlit_folium import st_folium
import folium
import requests
import json
from datetime import timedelta
from geopy import Nominatim
# import certifi


st.set_page_config()

st.title('Capstone')
st.markdown("""
Description ....


**Data source:** link
""")

# load the data
useful_columns = ['case_id','t_state','t_county','t_fips','p_name','p_year',
                  'p_tnum','p_cap','t_manu','t_model','t_cap','t_hh','t_rd',
                  't_rsa','t_ttlh','xlong','ylat']

# url = 'https://raw.githubusercontent.com/JiayuanCui/Wind-Turbine-Blades-CUCP/main/streamlit%20app/uswtdb_v5_2_20221012.csv?token=GHSAT0AAAAAAB2DPJLLXXWPDWCZEEJ6TSASY2WFKYA'
# df = pd.read_csv(url, encoding='latin-1', usecols=useful_columns)
df = pd.read_csv('uswtdb_v5_2_20221012.csv', encoding='latin-1', usecols=useful_columns)
df = df[df.t_state=='NY']


df_turb_proj = pd.DataFrame(df.groupby(['p_name'])['case_id'].count())
df_turb_proj.reset_index(inplace=True)
df_turb_proj.columns = ['Project','Number of Turbines']
df_turb_proj.sort_values(by=['Number of Turbines'], ascending = False).reset_index(drop=True).head()

df_proj_yr = pd.DataFrame(df.groupby(['p_year'])['p_name'].nunique())
df_proj_yr.reset_index(inplace=True)
df_proj_yr.columns = ['Year','Number of Projects that Became Operational']
df_proj_yr.sort_values(by=['Year']).reset_index(drop=True).head()

df_man_model = pd.DataFrame(df.groupby(['t_manu'])['t_model'].nunique())
df_man_model.reset_index(inplace=True)
df_man_model.columns = ['Manufacturer','Number of Models']
df_man_model.sort_values(by=['Number of Models'], ascending = False).reset_index(drop=True).head()

# # # 1st map
# columns = df_turb_proj['Project'].tolist()
# option = st.selectbox(
#     'Select a project',
#     columns)

# df1 = df[(df['p_name']== option)]
# df1.rename(columns={'xlong':'longitude', 'ylat':'latitude'}, inplace=True)
# # st.map(df1, zoom=7)

# map = folium.Map(location = [df1.latitude.mean(), df1.longitude.mean()], zoom_start=7, control_scale=True)

# # locationlist = df1[["latitude","longitude"]].values.tolist()
# # labels = df1["p_name"].values.tolist()

# # for point in range(len(locationlist)):
# #     folium.Marker(
# #         locationlist[point],
# #         popup=labels[point]
# #         ).add_to(map)

# for index, location_info in df1.iterrows():
#     folium.Marker(
#         [location_info["latitude"], location_info["longitude"]], 
#         popup=location_info["case_id"]).add_to(map)

# # call to render Folium map in Streamlit
# st_data = st_folium(map, width = 725)


# 2nd map
st.header("Map 1")

project_data = pd.DataFrame(df.groupby(['p_name'])[['xlong','ylat','p_tnum','t_cap']].mean())
project_data.columns = ['longitude','latitude','numb_turbines','avg_turbine_capacity']
project_data.reset_index(drop=False,inplace=True)
project_data.sort_values(by=['p_name'],ascending=False,inplace=True)
project_data['text'] = 'Project Name: ' + project_data['p_name'] + '<br>Number of Turbines: ' + project_data['numb_turbines'].astype(str) + '<br>Average Turbine Capacity: ' + (project_data['avg_turbine_capacity']).astype(str) + " MW"

map2 = folium.Map(location = [project_data.latitude.mean(), project_data.longitude.mean()], zoom_start=7, control_scale=True)

for index, location_info in project_data.iterrows():
    folium.CircleMarker(
        location = [location_info["latitude"], location_info["longitude"]], 
        radius = location_info['numb_turbines']/2,
        fill_color ='blue',
        popup = folium.Popup(location_info["text"], min_width=250, max_width=250)
        ).add_to(map2)

# headmap doesn't work need to figure it out
# heat_data = project_data.values.tolist()  
# folium.plugins.HeatMap(heat_data).add_to(map2)

st_data = st_folium(map2, width = 725)


# 3rd Map
st.header("Map 2")

# add the 1st selectbox for selecting the project
column1 = df['p_name'].unique().tolist()
option1 = st.selectbox(
    'Select a project',
    column1)
df_selected1 = df.loc[df.p_name == option1]

# add the 2nd selectbox for selecting the exact turbine of the selecting project
column2 = df.loc[df['p_name'] == option1]['case_id'].tolist()
option2 = st.selectbox(
    'Select a case ID',
    column2)  
df_selected2 = df_selected1.loc[df.case_id == option2]
st.write(df_selected2)

df_selected2.rename(columns={'xlong':'longitude', 'ylat':'latitude'}, inplace=True)
Origin = float(df_selected2.latitude),float(df_selected2.longitude)

# add a text input box for inputing a destination location
input = st.text_input("Input a destination (For example, 'Delaware Park, Buffalo, NY') ")
locator = Nominatim(user_agent='myGeocoder')
location = locator.geocode(str(input))

# get latitude, longitude and distance of the destination
def TravelInfo(origin, destination):
  
  """
  orgin: (x,y) where x and y represent latitude and longitude respectively
  destination: (x,y) where x and y represent latitude and longitude respectively
  """
  # Unpack the latitudes and longitudes
  (lat1, lon1) = origin
  (lat2, lon2) = destination
  # Make API call to OSRM (Open Source Routing Machine) for travel info
  r = requests.get(f"""http://router.project-osrm.org/route/v1/car/{lon1},{lat1};{lon2},{lat2}?overview=false""")
  # Unpack desired info
  route_1 = json.loads(r.content)["routes"][0]
  distance = route_1['distance']
  duration = route_1['duration']
  # Print output
  st.write(f"Driving Distance (mi): {distance/1609}")
  st.write(f"Driving Time: {str(timedelta(seconds=duration))}")
  return None

# create a map
if location is None:
    map = folium.Map(location = Origin, zoom_start=7, control_scale=True)
    folium.Marker(Origin, popup="Origin").add_to(map)
    st.write("Please Enter a Destination")
else:
    Destination = float(location.latitude),float(location.longitude)
    TravelInfo(Origin, Destination)
    map = folium.Map(location = Origin, zoom_start=7, control_scale=True)
    folium.Marker(Origin, popup="Origin").add_to(map)
    folium.Marker(Destination, popup="Destination").add_to(map)
    folium.PolyLine([Origin, Destination],color='red').add_to(map)
    
st_data = st_folium(map, width = 725)











