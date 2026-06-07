"""
MongoDB setup and schema initialization for PetDigiTwin
"""
import os
import time
from datetime import datetime

from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure, ServerSelectionTimeoutError

class PetDigiTwinDB:
    def __init__(self):
        self.primary_uri = os.getenv("MONGODB_URI", "").strip()
        self.local_uri = "mongodb://localhost:27017/petdigitwin"
        self.uri = self.primary_uri or self.local_uri
        self.client = None
        self.db = None
        self.connected_to = None
        self.connection_error = None
        self._connect()

    def _connect(self):
        """Try the configured MongoDB URI, then fall back to local MongoDB or in-memory storage."""
        if self.uri.startswith("mongodb+srv://"):
            client_kwargs = {"serverSelectionTimeoutMS": 5000}
            try:
                import certifi
                client_kwargs["tlsCAFile"] = certifi.where()
            except ImportError:
                pass
        else:
            client_kwargs = {"serverSelectionTimeoutMS": 5000}

        # Add a retry loop for Cloud Run to wait for Atlas firewall propagation
        max_retries = 6 if os.getenv("K_SERVICE") else 1
        last_exc = None
        
        for i in range(max_retries):
            try:
                self.client = MongoClient(self.uri, **client_kwargs)
                self.db = self.client.petdigitwin
                self.client.admin.command("ping")
                self.connected_to = self.uri
                return # Connection successful
            except Exception as exc:
                last_exc = exc
                if os.getenv("K_SERVICE") and i < max_retries - 1:
                    print(f"⏳ Waiting for Atlas IP propagation (attempt {i+1}/{max_retries})...")
                    time.sleep(10)
                    continue

            # Prevent silent fallback to mongomock in production (Cloud Run)
            if os.getenv("K_SERVICE"):
                print(f"❌ Production MongoDB connection failed after retries: {last_exc}")
                raise RuntimeError(f"Failed to connect to database at {self.uri}. Check credentials and Atlas IP whitelisting.") from last_exc

            self.connection_error = str(exc)
            if self.uri != self.local_uri:
                try:
                    fallback_kwargs = {"serverSelectionTimeoutMS": 3000}
                    self.client = MongoClient(self.local_uri, **fallback_kwargs)
                    self.db = self.client.petdigitwin
                    self.client.admin.command("ping")
                    self.uri = self.local_uri
                    self.connected_to = self.uri
                    print(f"⚠️  MongoDB Atlas connection failed, using local MongoDB fallback: {self.local_uri}")
                    return
                except Exception as local_exc:
                    self.connection_error = str(local_exc)

            try:
                import mongomock
                self.client = mongomock.MongoClient()
                self.db = self.client.petdigitwin
                self.uri = "mongomock://in-memory"
                self.connected_to = self.uri
                print("⚠️  MongoDB unavailable; using mongomock in-memory fallback for local development.")
            except ImportError as import_exc:
                msg = (
                    f"MongoDB connection failed for {self.uri}. "
                    f"Local fallback ({self.local_uri}) also failed. "
                    f"Install local MongoDB or add 'mongomock' for offline fallback. "
                    f"Last error: {self.connection_error}"
                )
                raise RuntimeError(msg) from import_exc

    def initialize_collections(self):
        """Create collections and indexes"""
        if self.db is None:
            raise RuntimeError(f"Database unavailable: {self.connection_error}")

        # 1. Pets collection
        try:
            self.db.create_collection("pets")
        except (OperationFailure, CollectionInvalid):
            pass

        self.db.pets.create_index([("owner_id", 1)])
        self.db.pets.create_index([("breed", 1)])

        # 2. Volunteers collection
        try:
            self.db.create_collection("volunteers")
        except (OperationFailure, CollectionInvalid):
            pass

        self.db.volunteers.create_index([("location", "2dsphere")])
        self.db.volunteers.create_index([("experience", 1)])

        # 3. Pet foods collection
        try:
            self.db.create_collection("pet_foods")
        except (OperationFailure, CollectionInvalid):
            pass

        self.db.pet_foods.create_index([("suitable_for", 1)])
        self.db.pet_foods.create_index([("breed_specific", 1)])

        # 4. Vet knowledge base
        try:
            self.db.create_collection("vet_knowledge")
        except (OperationFailure, CollectionInvalid):
            pass

        self.db.vet_knowledge.create_index([("condition", 1)])

        print(f"✅ MongoDB collections initialized ({self.connected_to})")

    def load_sample_data(self):
        """Load hardcoded sample data"""
        if self.db is None:
            raise RuntimeError(f"Database unavailable: {self.connection_error}")

        # Clear existing data
        self.db.pets.delete_many({})
        self.db.volunteers.delete_many({})
        self.db.pet_foods.delete_many({})
        self.db.vet_knowledge.delete_many({})

        # 1. Sample Pets
        pets = [
            {
                "id": "pet_001",
                "name": "Max",
                "breed": "Labrador",
                "age": 3,
                "owner_id": "owner_001",
                "owner_name": "Alice",
                "weight_kg": 32,
                "conditions": ["joint_pain", "weight_management"],
                "last_checkup": datetime(2026, 4, 15),
                "health_notes": "Slight limping in rear legs",
                "food_allergies": ["chicken"]
            },
            {
                "id": "pet_002",
                "name": "Bella",
                "breed": "German Shepherd",
                "age": 5,
                "owner_id": "owner_002",
                "owner_name": "Bob",
                "weight_kg": 28,
                "conditions": ["skin_sensitivity"],
                "last_checkup": datetime(2026, 3, 1),
                "health_notes": "Recurring ear infections",
                "food_allergies": ["wheat"]
            },
            {
                "id": "pet_003",
                "name": "Charlie",
                "breed": "Golden Retriever",
                "age": 7,
                "owner_id": "owner_003",
                "owner_name": "Carol",
                "weight_kg": 35,
                "conditions": ["arthritis", "diabetes"],
                "last_checkup": datetime(2026, 2, 10),
                "health_notes": "Senior dog, requires special diet",
                "food_allergies": []
            },
            {
                "id": "pet_004",
                "name": "Daisy",
                "breed": "Beagle",
                "age": 2,
                "owner_id": "owner_004",
                "owner_name": "David",
                "weight_kg": 12,
                "conditions": ["obesity_prevention"],
                "last_checkup": datetime(2026, 5, 1),
                "health_notes": "Energetic, needs portion control",
                "food_allergies": ["soy"]
            },
            {
                "id": "pet_005",
                "name": "Ella",
                "breed": "Poodle",
                "age": 4,
                "owner_id": "owner_005",
                "owner_name": "Eve",
                "weight_kg": 18,
                "conditions": ["dental_care"],
                "last_checkup": datetime(2026, 1, 20),
                "health_notes": "Needs regular dental cleanings",
                "food_allergies": []
            },
            {
                "id": "pet_006",
                "name": "Frank",
                "breed": "Bulldog",
                "age": 6,
                "owner_id": "owner_006",
                "owner_name": "Frank",
                "weight_kg": 25,
                "conditions": ["joint_pain", "breathing_issues"],
                "last_checkup": datetime(2026, 4, 5),
                "health_notes": "Brachycephalic breed, heat sensitive",
                "food_allergies": []
            },
            {
                "id": "pet_007",
                "name": "Grace",
                "breed": "Shiba Inu",
                "age": 3,
                "owner_id": "owner_007",
                "owner_name": "Grace",
                "weight_kg": 10,
                "conditions": ["weight_management"],
                "last_checkup": datetime(2026, 5, 10),
                "health_notes": "Prone to overeating",
                "food_allergies": ["beef"]
            },
            {
                "id": "pet_008",
                "name": "Hank",
                "breed": "Husky",
                "age": 4,
                "owner_id": "owner_008",
                "owner_name": "Henry",
                "weight_kg": 30,
                "conditions": ["skin_sensitivity"],
                "last_checkup": datetime(2026, 3, 15),
                "health_notes": "Double coat, needs omega-3 supplements",
                "food_allergies": []
            },
            {
                "id": "pet_009",
                "name": "Ivy",
                "breed": "Dachshund",
                "age": 5,
                "owner_id": "owner_009",
                "owner_name": "Iris",
                "weight_kg": 8,
                "conditions": ["back_pain", "weight_management"],
                "last_checkup": datetime(2026, 4, 1),
                "health_notes": "Long spine, needs support",
                "food_allergies": ["corn"]
            },
            {
                "id": "pet_010",
                "name": "Jack",
                "breed": "Corgi",
                "age": 2,
                "owner_id": "owner_010",
                "owner_name": "Jack",
                "weight_kg": 14,
                "conditions": ["obesity_prevention"],
                "last_checkup": datetime(2026, 5, 5),
                "health_notes": "Young and active, high metabolism",
                "food_allergies": []
            }
        ]
        
        self.db.pets.insert_many(pets)
        print(f"✅ Loaded {len(pets)} sample pets")
        
        # 2. Sample Volunteers
        volunteers = [
            {
                "id": "vol_001",
                "name": "Sophia",
                "location": {"type": "Point", "coordinates": [-118.2437, 34.0522]},  # LA
                "experience_breeds": ["Labrador", "Golden Retriever"],
                "experience_conditions": ["joint_pain", "weight_management"],
                "bio": "10 years pet sitting experience, loves retrievers",
                "rating": 4.9,
                "availability": ["weekends", "weekdays_evening"],
                "price_per_day": 50
            },
            {
                "id": "vol_002",
                "name": "Marcus",
                "location": {"type": "Point", "coordinates": [-87.6298, 41.8781]},  # Chicago
                "experience_breeds": ["German Shepherd", "Husky"],
                "experience_conditions": ["skin_sensitivity"],
                "bio": "Professional dog walker, experienced with large breeds",
                "rating": 4.8,
                "availability": ["weekdays"],
                "price_per_day": 45
            },
            {
                "id": "vol_003",
                "name": "Priya",
                "location": {"type": "Point", "coordinates": [-74.0060, 40.7128]},  # NYC
                "experience_breeds": ["Poodle", "Dachshund", "Beagle"],
                "experience_conditions": ["dental_care", "weight_management"],
                "bio": "Specialized in small dogs, certified pet care",
                "rating": 4.95,
                "availability": ["weekends", "holidays"],
                "price_per_day": 60
            },
            {
                "id": "vol_004",
                "name": "James",
                "location": {"type": "Point", "coordinates": [-118.2437, 34.0522]},  # LA
                "experience_breeds": ["Bulldog", "Pug", "French Bulldog"],
                "experience_conditions": ["breathing_issues"],
                "bio": "Loves brachycephalic breeds, first aid certified",
                "rating": 4.7,
                "availability": ["weekdays", "weekends"],
                "price_per_day": 55
            },
            {
                "id": "vol_005",
                "name": "Lisa",
                "location": {"type": "Point", "coordinates": [-117.1611, 32.7157]},  # San Diego
                "experience_breeds": ["Corgi", "Shiba Inu", "All small breeds"],
                "experience_conditions": ["weight_management"],
                "bio": "Animal nutritionist background, diet-aware pet care",
                "rating": 4.85,
                "availability": ["weekends"],
                "price_per_day": 50
            }
        ]
        
        self.db.volunteers.insert_many(volunteers)
        # Create geospatial index
        self.db.volunteers.create_index([("location", "2dsphere")])
        print(f"✅ Loaded {len(volunteers)} sample volunteers")
        
        # 3. Sample Pet Foods
        foods = [
            {
                "id": "food_001",
                "name": "Premium Joint Support Formula",
                "brand": "Royal Canin",
                "price": 85,
                "suitable_for": ["joint_pain", "arthritis"],
                "breed_specific": ["Labrador", "German Shepherd"],
                "ingredients": ["chicken", "fish oil", "glucosamine"],
                "calories_per_cup": 380
            },
            {
                "id": "food_002",
                "name": "Sensitive Skin & Coat",
                "brand": "Hill's Science Diet",
                "price": 60,
                "suitable_for": ["skin_sensitivity"],
                "breed_specific": ["German Shepherd", "Husky"],
                "ingredients": ["salmon", "sweet potato", "omega-3"],
                "calories_per_cup": 370
            },
            {
                "id": "food_003",
                "name": "Weight Management Adult",
                "brand": "Purina Pro Plan",
                "price": 45,
                "suitable_for": ["obesity_prevention", "weight_management"],
                "breed_specific": ["Beagle", "Corgi", "Dachshund"],
                "ingredients": ["chicken", "fiber", "low-fat"],
                "calories_per_cup": 310
            },
            {
                "id": "food_004",
                "name": "Prescription Dental Diet",
                "brand": "Royal Canin",
                "price": 70,
                "suitable_for": ["dental_care"],
                "breed_specific": ["Poodle", "Small breeds"],
                "ingredients": ["poultry", "minerals", "polyphosphate"],
                "calories_per_cup": 340
            },
            {
                "id": "food_005",
                "name": "Senior Formula (7+)",
                "brand": "Iams",
                "price": 50,
                "suitable_for": ["arthritis", "diabetes"],
                "breed_specific": ["All breeds"],
                "ingredients": ["chicken", "glucosamine", "antioxidants"],
                "calories_per_cup": 360
            },
            {
                "id": "food_006",
                "name": "Limited Ingredient Chicken",
                "brand": "Royal Canin",
                "price": 65,
                "suitable_for": ["allergies"],
                "breed_specific": ["All breeds"],
                "ingredients": ["chicken only", "rice", "no additives"],
                "calories_per_cup": 375
            },
            {
                "id": "food_007",
                "name": "Brachy (Flat-Faced) Breed",
                "brand": "Royal Canin",
                "price": 75,
                "suitable_for": ["breathing_issues"],
                "breed_specific": ["Bulldog", "Pug"],
                "ingredients": ["poultry", "bran", "easily digestible"],
                "calories_per_cup": 400
            },
            {
                "id": "food_008",
                "name": "Beef-Free Chicken Recipe",
                "brand": "Taste of Wild",
                "price": 55,
                "suitable_for": ["allergies", "weight_management"],
                "breed_specific": ["Shiba Inu"],
                "ingredients": ["chicken", "sweet potato"],
                "calories_per_cup": 365
            }
        ]
        
        self.db.pet_foods.insert_many(foods)
        print(f"✅ Loaded {len(foods)} sample pet foods")
        
        # 4. Sample Vet Knowledge
        vet_knowledge = [
            {
                "id": "knowledge_001",
                "condition": "joint_pain",
                "title": "Managing Joint Pain in Dogs",
                "content": "Joint pain is common in aging dogs. Treatment options include: 1) Glucosamine and chondroitin supplements, 2) Weight management to reduce stress on joints, 3) Low-impact exercise like swimming, 4) Prescription medications like carprofen, 5) Physical therapy and massage.",
                "natural_remedies": ["Turmeric (curcumin)", "Ginger supplements", "Fish oil (omega-3)", "Green-lipped mussel"]
            },
            {
                "id": "knowledge_002",
                "condition": "skin_sensitivity",
                "title": "Addressing Skin Sensitivity in Dogs",
                "content": "Skin sensitivity often stems from allergies or environmental factors. Management includes: 1) Identify and eliminate allergens, 2) Use hypoallergenic shampoos, 3) Add omega-3 fatty acids to diet, 4) Regular baths with mild soap, 5) Moisturizing treatments.",
                "natural_remedies": ["Coconut oil", "Apple cider vinegar (diluted)", "Oatmeal baths", "Aloe vera (non-toxic)"]
            },
            {
                "id": "knowledge_003",
                "condition": "obesity_prevention",
                "title": "Weight Management for Dogs",
                "content": "Maintaining healthy weight is critical for longevity. Strategies: 1) Portion control (measure meals), 2) Choose low-calorie treats, 3) Regular exercise (30+ min daily), 4) Avoid table scraps, 5) Regular weigh-ins every 2 weeks.",
                "natural_remedies": ["Green beans as treats", "Low-fat cottage cheese", "Carrots", "Apple slices"]
            },
            {
                "id": "knowledge_004",
                "condition": "arthritis",
                "title": "Arthritis in Senior Dogs",
                "content": "Senior dogs often develop arthritis. Care includes: 1) Joint supplements, 2) Comfortable bedding, 3) Gentle exercise, 4) Pain management, 5) Veterinary monitoring.",
                "natural_remedies": ["Turmeric", "Boswellia", "Devil's claw", "Hydrotherapy"]
            },
            {
                "id": "knowledge_005",
                "condition": "dental_care",
                "title": "Dental Health for Dogs",
                "content": "Good oral hygiene prevents health issues. Recommendations: 1) Brush teeth daily, 2) Use dental treats, 3) Professional cleanings annually, 4) Watch for bad breath (sign of disease), 5) Avoid hard objects that crack teeth.",
                "natural_remedies": ["Coconut oil (anti-bacterial)", "Turmeric rinse", "Dental chews", "Raw vegetables"]
            },
            {
                "id": "knowledge_006",
                "condition": "breathing_issues",
                "title": "Respiratory Support for Brachycephalic Dogs",
                "content": "Flat-faced breeds struggle with breathing. Support: 1) Avoid extreme heat/exercise, 2) Maintain healthy weight, 3) Sleep elevation, 4) Controlled environment temps, 5) Veterinary monitoring for surgery options.",
                "natural_remedies": ["Cool environment", "Humidifier use", "Limited strenuous activity", "Weight management"]
            }
        ]
        
        self.db.vet_knowledge.insert_many(vet_knowledge)
        print(f"✅ Loaded {len(vet_knowledge)} vet knowledge entries")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    db = PetDigiTwinDB()
    db.initialize_collections()
    db.load_sample_data()
