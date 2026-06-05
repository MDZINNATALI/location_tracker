from flask import Flask, render_template, request, jsonify
import folium
import os
from datetime import datetime

app = Flask(__name__)

# লোকেশন সংরক্ষণের জন্য ডিকশনারি (প্রোডাকশনে ডাটাবেস ইউজ করবেন)
latest_location = {
    "latitude": None,
    "longitude": None,
    "timestamp": None
}

@app.route('/')
def index():
    """হোম পেজ - জিপিএস সেন্ড করার ফর্ম"""
    return render_template('index.html')

@app.route('/update-location', methods=['POST'])
def update_location():
    """ফোন থেকে জিপিএস লোকেশন রিসিভ করা"""
    data = request.json
    latest_location['latitude'] = data.get('latitude')
    latest_location['longitude'] = data.get('longitude')
    latest_location['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f" লোকেশন আপডেট: {latest_location['latitude']}, {latest_location['longitude']}")
    
    # সাথে সাথে ম্যাপ জেনারেট করুন
    generate_map()
    
    return jsonify({"status": "success", "message": "Location received!"})

@app.route('/get-map')
def get_map():
    """জেনারেটেড ম্যাপ দেখানো"""
    if latest_location['latitude'] is None:
        return "কোনো লোকেশন এখনো পাইনি। ফোন থেকে লোকেশন পাঠান!"
    
    return render_template('map.html')

def generate_map():
    """ফোলিয়াম ব্যবহার করে ম্যাপ তৈরি করা"""
    if latest_location['latitude'] and latest_location['longitude']:
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
            radius=50,
            color='blue',
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
        
        # টেমপ্লেট ফোল্ডারে সেভ করুন
        m.save('templates/map.html')

if __name__ == '__main__':
    app.run(debug=True)