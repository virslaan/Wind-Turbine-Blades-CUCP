import streamlit as st
import numpy as np
import pandas as pd
from streamlit_folium import st_folium
import folium
import requests
import json
from datetime import timedelta
from geopy import Nominatim


st.set_page_config()

st.title('Capstone')
st.markdown("""
Description ....


**Data source:** link
""")

# load the data
@st.cache
def get_data(filename):
	df = pd.read_csv(filename)
	return df

# load the data set
df1 = get_data('usgs_data.csv')
df2 = get_data('nyserda_data.csv')
df3 = get_data('ghg_radius_data.csv')
df4 = get_data('state_park_data.csv')
df5 = get_data('thruway_authority_data.csv')

st.header("Map 1")


map = folium.Map(location = [df1.latitude.mean(), df1.longitude.mean()], zoom_start=7, control_scale=True)

group0 = folium.FeatureGroup(name='<span style=\\"color: blue;\\">Exist Projects</span>')
for index, location_info in df1.iterrows():

    folium.CircleMarker(
        location = [location_info["latitude"], location_info["longitude"]], 
        radius = location_info['numb_turbines']/2,
        fill_color ='blue',
        popup = folium.Popup(location_info["text"], min_width=250, max_width=250)
        ).add_to(group0)
group0.add_to(map)

group1 = folium.FeatureGroup(name='<span style=\\"color: red;\\">Future Projects</span>')
for index, location_info in df2.iterrows():
    if pd.notnull(location_info['latitude']):
        folium.CircleMarker(
        location = [location_info["latitude"], location_info["longitude"]], 
        radius = 1,
        color = 'red',
        fill_color ='red',
        popup = folium.Popup(location_info["text"], min_width=250, max_width=250)
        ).add_to(group1)
group1.add_to(map)

folium.map.LayerControl('topleft', collapsed=False).add_to(map)


st_data = st_folium(map, width = 725)


st.header("Map 2")

# add the selectbox for selecting the project
column1 = df1['p_name'].unique().tolist()
option1 = st.selectbox(
    'Select a project',
    column1)
df_selected1 = df1.loc[df1.p_name == option1]

Origin = float(df_selected1.latitude),float(df_selected1.longitude)
Windmill = df_selected1

# add a text input box for inputing a destination location
input = st.text_input("Input a destination (For example, 'Delaware Park, Buffalo, NY') ")
locator = Nominatim(user_agent='myGeocoder')
location = locator.geocode(str(input))

# get latitude, longitude and distance of the destination
def TravelInfo(origin, destination):
  """
  orgin: (x,y) where x and y represent latitude and longitude respectively
  destination: (x,y) where x and y represent latitude and longitude respectively

  returns travel distance in mi
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
  return distance/1609

# calculate GHG emissions
def PredictTransportEmission(Windturbine,Destination):
  """
  Predicts GHG emissions for transporting one windmill blade

  destination: (x,y) where x and y represent latitude and longitude respectively

  Windturbine is a row from the df with windmill info.
  """
  # Assume flatbed is 16.2 meters, we need __ flatbeds for transport
  numb_trucks = np.ceil(Windturbine['turbine_blade_length']/16.2)
  # Transport Distance (mi)
  Origin = float(Windturbine.latitude),float(Windturbine.longitude)
  transport_distance = TravelInfo(Origin, Destination)
  # Shipment weight (lbs) --------------------------------------------------------- This we can create a model for if we can find some data
  weight_tons = float(Windturbine['turbine_blade_weight'])       # estimation based on XGBoost model
  # Total # of ton miles
  ton_miles = weight_tons * transport_distance
  # Trucks emit 161.8 grams per ton-mile
  emission_factor = 161.8

  ghg_emissions = transport_distance * weight_tons * emission_factor
  st.write(f'We expect **{ghg_emissions}** grams of GHG emissions.')
  st.write(f'That is **{ghg_emissions/1000}** kilograms of GHG emissions;')
  st.write(f'or, **{ghg_emissions/1000000000}** kilotons. ')

# create a map
if location is None:
    map = folium.Map(location = Origin, zoom_start=7, control_scale=True)
    folium.Marker(Origin, popup="Origin").add_to(map)
    
else:
    Destination = float(location.latitude),float(location.longitude)
    PredictTransportEmission(Windmill, Destination)
    map = folium.Map(location = Origin, zoom_start=7, control_scale=True)
    folium.Marker(Origin, popup="Origin").add_to(map)
    folium.Marker(Destination, popup="Destination").add_to(map)
    folium.PolyLine([Origin, Destination],color='red').add_to(map)
    
st_data = st_folium(map, width = 725)


st.header("Map 3")

# add the selectbox for selecting the project
column2 = df3['p_name'].unique().tolist()
option2 = st.selectbox(
    'Select a project',
    column2)
df_selected2 = df3.loc[df3.p_name == option2]

location = float(df_selected2.latitude),float(df_selected2.longitude)


map = folium.Map(location, zoom_start=7, control_scale=True)

group0 = folium.FeatureGroup(name='<span style=\\"color: crimson;\\">Wind Farm GHG Circles</span>')
folium.Circle(
    location = location, 
    radius = float(df_selected2['ghg_radius_m']),
    color='crimson',
    fill=True,
    fill_color='crimson',
    popup = folium.Popup(df_selected2["p_name"])
    ).add_to(group0)
group0.add_to(map)

group1 = folium.FeatureGroup(name='<span style=\\"color: green;\\">New York State Parks</span>')
for index, location_info in df4.iterrows():
    folium.Marker(
        location = [location_info["Latitude"], location_info["Longitude"]], 
        icon=folium.Icon(color='green'),
        popup = folium.Popup(location_info["Name"])
        ).add_to(group1)
group1.add_to(map)

group2 = folium.FeatureGroup(name='<span style=\\"color: blue;\\">Thruway Authority Capital Project</span>')
for index, location_info in df5.iterrows():
    folium.Marker(
        location = [location_info["Latitude"], location_info["Longitude"]], 
        icon=folium.Icon(color='blue')
        # popup = folium.Popup(location_info["name"])
        ).add_to(group2)
group2.add_to(map)

folium.map.LayerControl('topleft', collapsed=False).add_to(map)
# call to render Folium map in Streamlit
st_data = st_folium(map, width = 725)





