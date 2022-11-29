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

st.title('Staying Ahead of Renewable Energy Curve and Analysis on Reusable Blades')
st.markdown("""
Our project is a proactive approach to finding more sustainable end-of-life alternatives compared to landfill and incineration.
NYC Town+Gown has identified several locations that want to reuse wind turbine blades to improve their own facilities. 

We will indirectly drive impact for the following by allocating retired turbine blades:
1. Public Parks
2. Modern Art Enthusiasts
3. Port Authorities
4. Fiberglass Manufacturers

Our primary goal is to find the optimal reuse location for decommissioned windmill blades. 
""")

# load the data function
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

# load json file for drawing border of NYS
with open('gz_2010_us_040_00_500k.json') as handle:
    state_geo = json.loads(handle.read())

for i in state_geo['features']:
    if i['properties']['NAME'] == 'New York':
        state = i
        break


####
st.header("New York State Wind Turbine Map")
st.markdown(
    """
    The map provides the locations of land-based and offshore wind turbines in New York State, 
    which has the option to control displaying active windmill projects or underdevelopment windmill projects. 
    """
)
st.text("")

# create a map for showing all windmill projects  
map = folium.Map(location = [df1.latitude.mean(), df1.longitude.mean()], tiles = 'cartodbpositron', zoom_start=7, control_scale=True)

# drow border of New York State
group2 = folium.FeatureGroup(name='<span style=\\"color: dark;\\">Show New York State Border</span>')
folium.GeoJson(state,
name='New York',
style_function = lambda x: {
    'color': 'black',
    'weight': 2.5,
    'fillOpacity': 0}).add_to(group2)
group2.add_to(map)    

# mark all active projects
group0 = folium.FeatureGroup(name='<span style=\\"color: blue;\\">Exist Windmill Projects</span>')

for index, location_info in df1.iterrows():

    folium.CircleMarker(
        location = [location_info["latitude"], location_info["longitude"]], 
        radius = 7,
        color = 'blue',
        fill = True,
        fill_color ='blue',
        popup = folium.Popup(location_info["text"], min_width=250, max_width=250)
        ).add_to(group0)

group0.add_to(map)

# mark all future projects
group1 = folium.FeatureGroup(name='<span style=\\"color: red;\\">Future Windmill Projects</span>')

for index, location_info in df2.iterrows():
    if pd.notnull(location_info['latitude']):
        folium.CircleMarker(
        location = [location_info["latitude"], location_info["longitude"]], 
        radius = 7,
        color = 'darkorange',
        fill = True,
        fill_color ='darkorange',
        popup = folium.Popup(location_info["text"], min_width=250, max_width=250)
        ).add_to(group1)

group1.add_to(map)

# put two groups and legend in the same layer
folium.TileLayer('openstreetmap').add_to(map)
folium.map.LayerControl('topleft', collapsed=False).add_to(map)

# call to render Folium map in Streamlit
st_data = st_folium(map, width = 725)


####
st.markdown("----------------------")
st.header("GHG Emissions Calculator")
st.markdown(
    """
    The site offers a quick and intuitive way to calculate greenhouse gas (GHG) emissions 
    to transport a windmill from its origin (project sites) to a potential destination. 
    """
)
st.subheader("How are GHG emissions calculated? ")
st.markdown(
    """
    The formula to calculate:
    \n**GHG emissions** = **Distance** * **Weight** * **Emissions Factor**
    \n* **Distance**: the distance your shipment has traveled (in miles)
    \n\t*calculated using Open Source Routing Machine (ORSM) API, which generates optimal routes based on latitude and longitude of origins and destinations*
    \n* **Weight**: the weight your shipment (in tones)
    \n\t*blade weights are estimated using XGboost model*
    \n\t*We assume that the turbine blades will be cut when they are taken off the windmill on-site. 
    When calculating the emissions, we will have to consider one truck and then multiply by the number of necessary flatbeds.*
    \n\t*To decide how many flatbeds are necessary, we divide the blade length by the size of a flatbed,
    then multiply that by the number of windmill blades for transport.*
    \n* **Emissions Factor**: the model's specific emissions factor
    \n\t*the emissions factor of a flatbed is 161.8*
    """
)
st.subheader("How to use GHG Emissions Calculator?")
st.markdown(
    """
    1. **Select a windmill project**: the start point of travel displayed on the map
    2. **Input a destination**: the endpoint of travel displayed on the map and emissions displays
    3. **Input the length of the flatbed in meters**: the length of flatbed trailer you choose to use for transportation
    4. **Input number of blades**: the number of blade transported
    """
)

# add the selectbox for selecting the project
column1 = df1['p_name'].unique().tolist()
option1 = st.selectbox(
    'Select a windmill project',
    column1)
df_selected1 = df1.loc[df1.p_name == option1]
# get lagitude and latitude of origin
Origin = float(df_selected1.latitude),float(df_selected1.longitude)
# assign selected row
Windmill = df_selected1

# add a text input box for inputing a destination location
input1 = st.text_input("Input a destination (For example, 'Delaware Park, Buffalo, NY') ")
locator = Nominatim(user_agent='myGeocoder')
location = locator.geocode(str(input1))

# add a text input box for inputing a flatbed length
input2 = st.number_input("Input a length of flatbed in meters (For example, '16.2') ", value = 16.2)
st.write(input2)
len_flatbed = float(input2)

# add a text input box for inputing a number of blade transported
input3 = st.number_input("Input number of blade (For example, '3') ", value = 3)
st.write(input3)
num_blade = float(input3)

# get distance between the origin and the destination
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
  return distance/1609

# calculate GHG emissions
def PredictTransportEmission(Windturbine,Destination,Length_flatbed, Number_blade):
  """
  Predicts GHG emissions for transporting one windmill blade

  destination: (x,y) where x and y represent latitude and longitude respectively

  Windturbine is a row from the df with windmill info.
  """
  # Assume flatbed is 16.2 meters, we need __ flatbeds for transport
  numb_trucks = np.ceil(float(Windturbine['turbine_blade_length'])/Length_flatbed * Number_blade)
  # Transport Distance (mi)
  Origin = float(Windturbine.latitude),float(Windturbine.longitude)
  transport_distance = TravelInfo(Origin, Destination)
  # Shipment weight (lbs) --------------------------------------------------------- This we can create a model for if we can find some data
  weight_tons = float(Windturbine['turbine_blade_weight'])       # estimation based on XGBoost model
  # Trucks emit 161.8 grams per ton-mile
  emission_factor = 161.8

  ghg_emissions_one_truck = transport_distance * weight_tons * emission_factor
  ghg_emissions = ghg_emissions_one_truck * numb_trucks
  
  st.write(f'We expect **{ghg_emissions}** grams of GHG emissions.')
  st.write(f'That is **{ghg_emissions/1000}** kilograms of GHG emissions;')
  st.write(f'or, **{ghg_emissions/1000000000}** kilotons. ')

# create travel map
if location is None:
    map = folium.Map(location = Origin, zoom_start=7, control_scale=True)
    # mark the origin on the map and add the border of NYS
    folium.Marker(Origin, popup="Origin").add_to(map)
    folium.GeoJson(state,
               name='New York', 
               style_function = lambda x: {'weight': 1.5}
               ).add_to(map)
    
else:
    # get langitude and latitude of destination
    Destination = float(location.latitude),float(location.longitude)
    # call GHG emission calculation function
    PredictTransportEmission(Windmill, Destination, len_flatbed, num_blade)

    map = folium.Map(location = Origin, zoom_start=7, control_scale=True)
    # mark the origin and destination, connect them with a line on the map and add the border of NYS
    folium.Marker(Origin, popup="Origin").add_to(map)
    folium.Marker(Destination, popup="Destination").add_to(map)
    folium.PolyLine([Origin, Destination],color='black').add_to(map)
    folium.GeoJson(state,
               name='New York', style_function = lambda x: {'weight': 1.5}
               ).add_to(map)

# call to render Folium map in Streamlit    
st_data = st_folium(map, width = 725)


####
st.markdown("------------------------------------")
st.header("Turbine Re-use Analysis within GHG Circles")
st.subheader("What are examples of turbine blade repurposing?")
st.markdown(
    """
    **NYS Parks**
    \n**NYS Thruway Authority for sound barriers**
    \nCapital Program: for the safety of the traveling public it is necessary to rehabilitate, 
    replace or improve certain components of the Thruway’s aging infrastructure.
    \n**Other potential uses**:
    \n* City and town government re-uses with a focus on parks
    \n* County government re-uses with a focus on parks
    \n* New York State highways/roads for sound barriers
    """
)
st.subheader("How to use GHG Circles?")
st.markdown(
    """
    1. **Select a windmill project**: the GHG circle of the project displayed on the map
    2. **Select a purpose**: filter the use of blades using the checkbox on the upper-left corner of the map 
    """
)

# add the selectbox for selecting the project
column2 = df3['p_name'].unique().tolist()
option2 = st.selectbox(
    'Select a windmill project',
    column2)
df_selected2 = df3.loc[df3.p_name == option2]
# get longitude and latitude of windmill chose
location = float(df_selected2.latitude),float(df_selected2.longitude)

# create GHG circle map
map = folium.Map(location, zoom_start=7, control_scale=True)

# plot the GHG radius circle chose
group0 = folium.FeatureGroup(name='<span style=\\"color: crimson;\\">Wind Farm GHG Circles</span>')
folium.Circle(
    location = location, 
    radius = float(df_selected2['ghg_radius_m']),
    color='crimson',
    fill=True,
    fill_color='crimson',
    popup = folium.Popup(df_selected2["p_name"], min_width=250, max_width=250)
    ).add_to(group0)
group0.add_to(map)

# mark all New York State Parks
group1 = folium.FeatureGroup(name='<span style=\\"color: green;\\">New York State Parks</span>')
for index, location_info in df4.iterrows():
    folium.Marker(
        location = [location_info["Latitude"], location_info["Longitude"]], 
        icon=folium.Icon(color='green', icon = 'tree conifer', prefix='fa'),
        popup = folium.Popup(location_info["Name"])
        ).add_to(group1)
group1.add_to(map)

# mark all NYS Thruway Authority Capital Project
group2 = folium.FeatureGroup(name='<span style=\\"color: blue;\\">NYS Thruway Authority Capital Project</span>')
for index, location_info in df5.iterrows():
    folium.Marker(
        location = [location_info["Latitude"], location_info["Longitude"]], 
        icon=folium.Icon(color='blue', icon = 'road', prefix='fa'),
        popup = folium.Popup(location_info["text"])
        ).add_to(group2)
group2.add_to(map)

folium.map.LayerControl('topleft', collapsed=False).add_to(map)
# call to render Folium map in Streamlit
st_data = st_folium(map, width = 725)





