import random, math
from pymongo import MongoClient, GEOSPHERE
from datetime import datetime
from faker import Faker

fake = Faker()
client = MongoClient("mongodb://localhost:27017")
db = client["cab_system"]

# Collections
drivers = db["drivers"]
driver_locations = db["driver_locations"]
user_locations = db["user_locations"]

# Indexes
driver_locations.create_index([("location", GEOSPHERE)])
user_locations.create_index([("location", GEOSPHERE)])

# Clear existing test data
drivers.delete_many({})
driver_locations.delete_many({})
user_locations.delete_many({})

# Bangalore center
BLR_LAT = 12.9716
BLR_LON = 77.5946

def generate_random_coords(center_lat, center_lon, radius_km):
    radius_in_deg = radius_km / 111
    u = random.random()
    v = random.random()
    w = radius_in_deg * (u ** 0.5)
    t = 2 * math.pi * v
    x = w * math.cos(t)
    y = w * math.sin(t)
    return center_lat + y, center_lon + x

# Seed drivers
for i in range(50):
    driver_id = f"driver{i:03d}"
    vehicle_id = f"vehicle{i:03d}"
    lat, lon = generate_random_coords(BLR_LAT, BLR_LON, 5)

    drivers.insert_one({
        "driver_id": driver_id,
        "name": fake.name(),
        "phone": fake.phone_number(),
        "vehicles": [{
            "vehicle_id": vehicle_id,
            "type": random.choice(["Sedan", "SUV", "Hatchback"]),
            "plate": fake.license_plate()
        }]
    })

    driver_locations.insert_one({
        "driver_id": driver_id,
        "vehicle_id": vehicle_id,
        "location": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "last_updated": datetime.utcnow(),
        "status": "online"
    })

# Seed users
for i in range(50):
    user_id = f"user{i:03d}"
    lat, lon = generate_random_coords(BLR_LAT, BLR_LON, 5)

    user_locations.insert_one({
        "user_id": user_id,
        "location": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "last_updated": datetime.utcnow(),
        "status": "online"
    })

print("✅ Seeded 50 drivers and 50 users with random GPS around Bangalore.")
