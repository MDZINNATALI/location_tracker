from flask import Flask, render_template, request, jsonify, render_template_string
import folium
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)

# লোকেশন স্টোর (মেমরিতে)
latest_location = {
    "latitude": None,
    "longitude": None,
    "timestamp": None,
    "accuracy": None
}

# SQLite ডাটাবেস সেটআপ (হিস্ট্রির জন্য)
def init_db():
    conn = sqlite3.connect('locations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS location_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  latitude REAL,
                  longitude REAL,
                  timestamp TEXT,
                  accuracy REAL)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    """ফোনের পেজ - লোকেশন পাঠানোর ফর্ম"""
    return render_template('index.html')

@app.route('/map')
def map_view():
    """লাইভ ম্যাপ ভিউয়ার"""
    return render_template('map.html')

@app.route('/update-location', methods=['POST'])
def update_location():
    """ফোন থেকে লোকেশন রিসিভ করা (AJAX)"""
    data = request.json
    latest_location['latitude'] = data.get('latitude')
    latest_location['longitude'] = data.get('longitude')
    latest_location['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latest_location['accuracy'] = data.get('accuracy', 0)
    
    # ডাটাবেসে সেভ করুন
    conn = sqlite3.connect('locations.db')
    c = conn.cursor()
    c.execute("INSERT INTO location_history (latitude, longitude, timestamp, accuracy) VALUES (?, ?, ?, ?)",
              (latest_location['latitude'], latest_location['longitude'], 
               latest_location['timestamp'], latest_location['accuracy']))
    conn.commit()
    conn.close()
    
    print(f"[LIVE] লোকেশন আপডেট: {latest_location['latitude']}, {latest_location['longitude']}")
    
    return jsonify({"status": "success", "message": "Location received!"})

@app.route('/get-location-json')
def get_location_json():
    """AJAX কলের জন্য বর্তমান লোকেশন JSON আকারে"""
    if latest_location['latitude'] is None:
        return jsonify({"error": "No location yet"})
    
    return jsonify({
        "latitude": latest_location['latitude'],
        "longitude": latest_location['longitude'],
        "timestamp": latest_location['timestamp'],
        "accuracy": latest_location['accuracy']
    })

@app.route('/get-history')
def get_history():
    """লোকেশন হিস্ট্রি JSON আকারে"""
    conn = sqlite3.connect('locations.db')
    c = conn.cursor()
    c.execute("SELECT latitude, longitude, timestamp, accuracy FROM location_history ORDER BY id DESC LIMIT 50")
    locations = c.fetchall()
    conn.close()
    
    history = []
    for lat, lon, ts, acc in locations:
        history.append({
            "latitude": lat,
            "longitude": lon,
            "timestamp": ts,
            "accuracy": acc
        })
    
    return jsonify(history)

@app.route('/static-map')
def static_map():
    """স্ট্যাটিক ম্যাপ (পুরোনো Folium ম্যাপ)"""
    if latest_location['latitude'] is None:
        return "কোনো লোকেশন এখনো পাইনি। ফোন থেকে লোকেশন পাঠান!"
    
    m = folium.Map(
        location=[latest_location['latitude'], latest_location['longitude']], 
        zoom_start=15
    )
    
    folium.Marker(
        [latest_location['latitude'], latest_location['longitude']], 
        popup=f"Your Location<br>{latest_location['timestamp']}",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    folium.Circle(
        [latest_location['latitude'], latest_location['longitude']],
        radius=latest_location['accuracy'] or 50,
        color='blue',
        fill=True,
        fill_opacity=0.2,
        popup=f"Accuracy: {latest_location['accuracy']}m"
    ).add_to(m)
    
    return m._repr_html_()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)