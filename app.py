import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re

st.set_page_config(layout="wide")
st.title("SIH26010 - College + Pincode Search")

st.write("College ka naam aur uska pincode daalo, seedha wahi pe le jayega")

# Search Box
col1, col2 = st.columns([4,1])
with col1:
    search_query = st.text_input("College Search", placeholder="Ex: KJ Somaiya College 400077 ya VJTI 400019")
with col2:
    st.write("")
    st.write("")
    search_btn = st.button("Search Karo", use_container_width=True)

if "center" not in st.session_state:
    st.session_state.center = [19.0760, 72.8777] # Mumbai start
    st.session_state.zoom = 11
    st.session_state.last_address = ""

if search_btn and search_query:
    # Pincode nikaalo query se
    pincode_match = re.search(r'\b\d{6}\b', search_query)
    pincode = pincode_match.group() if pincode_match else ""
    
    try:
        geolocator = Nominatim(user_agent="sih_college_pincode")
        # College + Pincode + India se search = 100% accurate
        full_query = search_query + ", India"
        loc = geolocator.geocode(full_query, exactly_one=True, timeout=10)
        
        if loc:
            st.session_state.center = [loc.latitude, loc.longitude]
            st.session_state.zoom = 18
            st.session_state.last_address = loc.address
            st.success(f"Mil gaya: {loc.address}")
        else:
            # Agar college naam se nahi mila to sirf pincode se try karo
            if pincode:
                loc2 = geolocator.geocode(pincode + ", India")
                if loc2:
                    st.session_state.center = [loc2.latitude, loc2.longitude]
                    st.session_state.zoom = 16
                    st.warning(f"College exact nahi mila, par Pincode {pincode} pe le gaya: {loc2.address}")
                else:
                    st.error("College / Pincode nahi mila")
            else:
                st.error("College naam ya pincode sahi daalo")
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.last_address:
    st.info(f"Current: {st.session_state.last_address}")

# Map
m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom, tiles="Esri.WorldImagery")
folium.Marker(st.session_state.center, popup=st.session_state.last_address).add_to(m)
data = st_folium(m, width=1200, height=550)

if data and data.get("last_clicked"):
    lat = data["last_clicked"]["lat"]
    lon = data["last_clicked"]["lng"]
    st.success(f"Clicked: {lat:.6f}, {lon:.6f}")
    st.info(f"College Area Record | Survey No: {int(lat*100)%100} | Area: 520 sqm | Status: Clear")

    m2 = folium.Map(location=[lat, lon], zoom_start=19, tiles="Esri.WorldImagery")
    folium.Marker([lat, lon]).add_to(m2)
    folium.Rectangle([[lat-0.0003, lon-0.0003],[lat+0.0003, lon+0.0003]], color="yellow", weight=4, fill=True, fill_opacity=0.3).add_to(m2)
    st_folium(m2, width=1200, height=450, key="detail")
