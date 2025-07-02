import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import random

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["RideApp-DriverDB-dev"]

sample_coords = [
    [77.5946, 12.9716],  # MG Road
    [77.6412, 12.9719],  # Indiranagar
    [77.6271, 12.9344],  # Koramangala
    [77.6110, 12.9141],  # HSR Layout
    [77.5665, 12.9981],  # Malleswaram
]

async def seed_driver_locations():
    await db.driver_locations.delete_many({})

    driver_docs = []

    for i in range(5):
        driver_id = ObjectId()
        vehicle_id = f"VEH{i + 1}"

        coords = random.choice(sample_coords)

        driver_docs.append({
            "_id": driver_id,
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "name": f"Driver{i + 1}",
            "phone": f"+91-900000000{i}",
            "location": {
                "type": "Point",
                "coordinates": coords
            },
            "isActive": True
        })

    await db.driver_locations.insert_many(driver_docs)
    await db.driver_locations.create_index([("location", "2dsphere")])

    print("✅ Seeded driver_locations with vehicle_id and 2dsphere index (no vehicle details).")

if __name__ == "__main__":
    asyncio.run(seed_driver_locations())
