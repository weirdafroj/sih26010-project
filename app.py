import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(layout="wide")
st.title("SIH26010 - All India Land Survey")
st.write("Pure India me kahi bhi search karo aur click karke 7/12 dekho")

# Search
col1, col2 = st.columns([4,1])
with col1:
    search_query = st.text_input("Search All India", placeholder="Ex: Delhi, Mumbai, Jalna, Kolkata ya 28.6139, 77.2090")
with col2:
    st.write("")
    st.write("")
    search_btn = st.button("Search Karo")

if "center" not in st.session_state:
    st.session_state.center = [22.9734, 78.6569] # Center of India
    st.session_state.zoom = 5 # Full India dikhega

if search_btn and search_query:
    try:
        if "," in search_query:
            parts = search_query.split(",")
            if len(parts)==2 and parts[0].replace(".","").replace("-","").strip().isdigit():
                lat, lon = map(float, parts)
                st.session_state.center = [lat, lon]
                st.session_state.zoom = 19
            else:
                raise ValueError
        else:
            raise ValueError
    except:
        # Naam se search - All India
        try:
            geolocator = Nominatim(user_agent="sih26010_all_india")
            loc = geolocator.geocode(search_query + ", India")
            if loc:
                st.session_state.center = [loc.latitude, loc.longitude]
                st.session_state.zoom = 18
                st.success(f"Mil gaya: {loc.address}")
            else:
                st.error("Location nahi mila")
        except Exception as e:
            st.error(f"Error: {e}")

# Map 1 - All India
m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom, tiles="Esri.WorldImagery")
data = st_folium(m, width=1200, height=550)

if data and data.get("last_clicked"):
    lat = data["last_clicked"]["lat"]
    lon = data["last_clicked"]["lng"]
    st.success(f"Clicked: {lat:.6f}, {lon:.6f}")
    st.info(f"All India 7/12 Record | Owner: Demo | Area: 520 sqm | Status: Clear | Coords: {lat:.5f}, {lon:.5f}")

    m2 = folium.Map(location=[lat, lon], zoom_start=19, tiles="Esri.WorldImagery")
    folium.Marker([lat, lon]).add_to(m2)
    folium.Rectangle([[lat-0.0002, lon-0.0002],[lat+0.0002, lon+0.0002]], color="yellow", weight=4, fill=True, fill_opacity=0.4).add_to(m2)
    st_folium(m2, width=1200, height=450, key="detail")

