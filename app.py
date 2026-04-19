import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim
import pandas as pd
import requests

API_URL = "http://localhost:8000/reports"

st.set_page_config(page_title="CivicFix - Public Portal", page_icon="🗺️", layout="wide")

st.markdown("""
<style>
    /* Hide Streamlit header and footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main app background */
    .stApp {
        background-color: #011e41;
        background-image: radial-gradient(circle at 15% 50%, rgba(4, 38, 70, 1), transparent 50%), 
                          radial-gradient(circle at 85% 30%, rgba(4, 38, 70, 1), transparent 50%);
    }
    
    /* Style Text and Headings */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, label {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Navbar Injection */
    .custom-navbar {
        background-color: #c4e4cd; 
        padding: 1rem 3rem; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        margin-top: -6rem; 
        margin-left: -5rem; 
        margin-right: -5rem; 
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Specific Streamlit Elements */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 5px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        color: #fff !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4caf50 !important;
        border-radius: 8px;
    }
    
    /* Glowing Primary Button */
    button[kind="primary"] {
        background-color: #000 !important;
        color: #00ffff !important;
        border: 2px solid #00ffff !important;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.6) !important;
        border-radius: 30px !important;
        font-weight: 800 !important;
        transition: all 0.3s ease !important;
        padding: 0.5rem 2rem !important;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 0 25px rgba(0, 255, 255, 0.9) !important;
        background-color: rgba(0, 255, 255, 0.1) !important;
        transform: translateY(-2px);
    }
    
    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: rgba(0, 0, 0, 0.3);
        border-radius: 12px;
        padding: 10px;
        border: 1px dashed #00ffff;
    }
    
    /* Dashboard metrics */
    [data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    [data-testid="stMetricValue"] {
        color: #00ffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Custom Navbar
st.markdown("""
<div class="custom-navbar">
    <div style="color: #2e7d32; font-size: 1.5rem; font-weight: 800;">🗺️ Civic<span style="color: #f57c00;">Fix</span></div>
    <div style="display: flex; gap: 1.5rem;">
        <a style="color: #1a1a1a; text-decoration: none; font-weight: 600;" href="#">Home</a>
        <a style="color: #1a1a1a; text-decoration: none; font-weight: 600;" href="#">About Us</a>
        <a style="color: #1a1a1a; text-decoration: none; font-weight: 600;" href="#">Vision</a>
        <a style="color: #1a1a1a; text-decoration: none; font-weight: 600;" href="#">Mission</a>
    </div>
    <button style="background-color: #4caf50; color: white; border: none; padding: 0.5rem 1.5rem; border-radius: 20px; font-weight: bold; cursor: pointer;">Login</button>
</div>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: 1px; color: white; margin-bottom: 0;">LIVE DEMO OF CIVICFIX</h1>
    <p style="color: #4caf50; font-size: 1.2rem; font-weight: 600; margin-top: 0;"><span style="color: #4caf50; font-weight: 800;">|</span> Click below to start reporting</p>
</div>
""", unsafe_allow_html=True)

geolocator = Nominatim(user_agent="civicfix_app")

def get_exif_data(image):
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    return exif_data

def get_decimal_from_dms(dms, ref):
    degrees, minutes, seconds = dms[0], dms[1], dms[2]
    try:
        degrees, minutes, seconds = float(degrees), float(minutes), float(seconds)
    except:
        pass
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']: decimal = -decimal
    return decimal

def get_lat_lon(exif_data):
    lat, lon = None, None
    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]
        if gps_info.get("GPSLatitude") and gps_info.get("GPSLongitude"):
            lat = get_decimal_from_dms(gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N"))
            lon = get_decimal_from_dms(gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E"))
    return lat, lon

def get_address(lat, lon):
    try:
        location = geolocator.reverse(f"{lat}, {lon}")
        return location.address if location else "Address not found"
    except:
        return "Address fetch failed"

tab1, tab2 = st.tabs(["📢 Report an Issue", "📊 Public Dashboard"])

with tab1:
    st.markdown("### Help keep your city clean and safe!")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1. Issue Details")
        username = st.text_input("Your Name (Optional)", placeholder="Citizen")
        title = st.text_input("Issue Title", placeholder="Massive Pothole on Main St")
        category = st.selectbox("Category", ["Pothole", "Illegal Dumping", "Broken Streetlight", "Water Leak", "Other"])
        severity = st.slider("Severity Level", 1, 5, 3)
        description = st.text_area("Description")
        
    with col2:
        st.markdown("#### 2. Location")
        loc_method = st.radio("Provide location:", ["Use Live GPS", "Extract from Geotagged Photo"])
        lat, lon = None, None
        
        if loc_method == "Use Live GPS":
            location = streamlit_geolocation()
            if location and location.get('latitude'):
                lat, lon = location['latitude'], location['longitude']
                st.success("✅ GPS Acquired!")
        else:
            uploaded_file = st.file_uploader("Upload Geotagged Photo", type=['jpg', 'jpeg', 'png'])
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)
                exif = get_exif_data(image)
                lat, lon = get_lat_lon(exif)
                if not lat: st.warning("⚠️ No GPS found.")
                else: st.success("✅ GPS Extracted!")

    if lat and lon and title:
        st.markdown("---")
        st.markdown("#### 3. Review & Submit")
        address = get_address(lat, lon)
        st.write(f"**Location:** {address}")
        
        if st.button("🚀 Submit Report", type="primary"):
            payload = {
                "username": username or "Anonymous",
                "title": title,
                "category": category,
                "severity": severity,
                "description": description,
                "address": address,
                "latitude": lat,
                "longitude": lon
            }
            try:
                resp = requests.post(API_URL, json=payload)
                if resp.status_code == 200:
                    st.success("🎉 Report submitted successfully!")
                    st.balloons()
                else:
                    st.error("Server error.")
            except:
                st.error("Failed to connect to backend server. Make sure FastAPI is running!")

with tab2:
    st.markdown("### Public Dashboard")
    try:
        reports = requests.get(API_URL).json()
        if reports:
            df = pd.DataFrame(reports)
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Total Issues", len(df))
            col_b.metric("Critical Hazards", len(df[df['severity'] >= 4]))
            col_c.metric("Resolved", len(df[df['status'] == 'Solved']))
            
            # Map
            first = df.iloc[0]
            city_map = folium.Map(location=[first['latitude'], first['longitude']], zoom_start=13)
            for _, row in df.iterrows():
                color = "green" if row['status'] == "Solved" else ("red" if row['severity'] >= 4 else "orange")
                folium.Marker(
                    [row['latitude'], row['longitude']], 
                    popup=f"<b>{row['title']}</b><br>Status: {row['status']}", 
                    icon=folium.Icon(color=color)
                ).add_to(city_map)
            st_folium(city_map, width=1000, height=500)
            
            st.dataframe(df[['upload_date', 'title', 'category', 'severity', 'status', 'address']], use_container_width=True)
        else:
            st.info("No reports yet.")
    except:
        st.error("Backend server is not running.")
