"""
MCP Tools for PetDigiTwin Agent
These tools are called by the Gemini agent via function calling
"""
import json
from src.db import PetDigiTwinDB
from datetime import datetime, timedelta

class PetDigiTwinTools:
    def __init__(self):
        self.db = PetDigiTwinDB()
    
    # ============ TOOL 1: SEARCH VET KNOWLEDGE ============
    def search_health_knowledge(self, condition: str, symptom: str = None) -> str:
        """
        Search veterinary knowledge base for health information
        """
        query = {
            "$or": [
                {"condition": {"$regex": condition, "$options": "i"}},
                {"title": {"$regex": condition, "$options": "i"}},
                {"content": {"$regex": symptom or condition, "$options": "i"}}
            ]
        }
        
        results = list(self.db.db.vet_knowledge.find(query).limit(3))
        
        if not results:
            return json.dumps({
                "status": "no_results",
                "message": f"No knowledge base entry found for '{condition}'"
            })
        
        formatted = []
        for doc in results:
            formatted.append({
                "condition": doc.get("condition"),
                "title": doc.get("title"),
                "content": doc.get("content"),
                "natural_remedies": doc.get("natural_remedies", [])
            })
        
        return json.dumps({
            "status": "success",
            "results": formatted
        })
    
    # ============ TOOL 2: FIND SUITABLE FOOD ============
    def find_suitable_food(self, pet_id: str, condition: str = None, budget: int = 100) -> str:
        """
        Find food recommendations based on pet condition and budget
        """
        pet = self.db.db.pets.find_one({"id": pet_id})
        
        if not pet:
            return json.dumps({
                "status": "error",
                "message": f"Pet {pet_id} not found"
            })
        
        # Build food query
        conditions = pet.get("conditions", []) + (condition.split(",") if condition else [])
        
        food_query = {
            "$and": [
                {"suitable_for": {"$in": conditions}},
                {"price": {"$lte": budget}}
            ]
        }
        
        foods = list(self.db.db.pet_foods.find(food_query).limit(5))
        
        if not foods:
            # Fallback: recommend any reasonably priced food
            foods = list(self.db.db.pet_foods.find({"price": {"$lte": budget}}).limit(3))
        
        formatted = []
        for food in foods:
            # Check for allergies
            has_allergen = False
            if pet.get("food_allergies"):
                for ingredient in food.get("ingredients", []):
                    if any(allergy.lower() in ingredient.lower() for allergy in pet["food_allergies"]):
                        has_allergen = True
                        break
            
            formatted.append({
                "name": food.get("name"),
                "brand": food.get("brand"),
                "price": food.get("price"),
                "suitable_for": food.get("suitable_for"),
                "calories_per_cup": food.get("calories_per_cup"),
                "has_allergen": has_allergen,
                "note": "⚠️ Contains allergen" if has_allergen else "✅ Safe"
            })
        
        return json.dumps({
            "status": "success",
            "pet_name": pet.get("name"),
            "pet_conditions": pet.get("conditions"),
            "food_allergies": pet.get("food_allergies", []),
            "recommendations": formatted
        })
    
    # ============ TOOL 3: PREDICT CHECKUP NEED ============
    def predict_checkup_need(self, pet_id: str) -> str:
        """
        Predict if pet needs a checkup based on last visit and conditions
        """
        pet = self.db.db.pets.find_one({"id": pet_id})
        
        if not pet:
            return json.dumps({
                "status": "error",
                "message": f"Pet {pet_id} not found"
            })
        
        last_checkup = pet.get("last_checkup")
        if isinstance(last_checkup, str):
            last_checkup = datetime.fromisoformat(last_checkup)
        
        days_since_checkup = (datetime.utcnow() - last_checkup).days
        
        # Decision logic
        needs_checkup = False
        reason = ""
        urgency = "low"
        
        conditions = pet.get("conditions", [])
        
        # Rule 1: Senior dogs (5+ years) need checkup every 6 months
        if pet.get("age", 0) >= 5 and days_since_checkup > 180:
            needs_checkup = True
            reason = "Senior dog - regular monitoring recommended"
            urgency = "medium"
        
        # Rule 2: Dogs with chronic conditions need checkup every 3 months
        chronic_conditions = ["arthritis", "diabetes", "breathing_issues"]
        if any(c in chronic_conditions for c in conditions) and days_since_checkup > 90:
            needs_checkup = True
            reason = f"Chronic condition detected: {', '.join([c for c in conditions if c in chronic_conditions])}"
            urgency = "medium"
        
        # Rule 3: Any dog overdue for annual checkup
        if days_since_checkup > 365:
            needs_checkup = True
            reason = "Annual checkup overdue"
            urgency = "high"
        
        return json.dumps({
            "status": "success",
            "pet_name": pet.get("name"),
            "pet_id": pet_id,
            "last_checkup": last_checkup.isoformat(),
            "days_since": days_since_checkup,
            "needs_checkup": needs_checkup,
            "reason": reason,
            "urgency": urgency,
            "recommended_action": "Schedule vet appointment" if needs_checkup else "Continue monitoring"
        })
    
    # ============ TOOL 4: FIND VOLUNTEERS ============
    def find_volunteers_for_pet(self, pet_id: str, start_date: str, end_date: str, max_distance_km: int = 50) -> str:
        """
        Find available volunteers for pet sitting
        """
        pet = self.db.db.pets.find_one({"id": pet_id})
        
        if not pet:
            return json.dumps({
                "status": "error",
                "message": f"Pet {pet_id} not found"
            })
        
        # Parse dates (format: YYYY-MM-DD)
        try:
            start = datetime.fromisoformat(start_date).date()
            end = datetime.fromisoformat(end_date).date()
        except:
            return json.dumps({
                "status": "error",
                "message": "Invalid date format. Use YYYY-MM-DD"
            })
        
        # Mock: In real impl, check availability against actual calendar
        # For now, assume all volunteers are available
        
        # Find volunteers with matching experience
        breed = pet.get("breed", "")
        conditions = pet.get("conditions", [])
        
        # Query: volunteers experienced with this breed
        vol_query = {
            "experience_breeds": {"$regex": breed, "$options": "i"}
        }
        
        volunteers = list(self.db.db.volunteers.find(vol_query).limit(5))
        
        formatted = []
        for vol in volunteers:
            # Check experience with pet conditions
            condition_match = sum(1 for c in conditions if c in vol.get("experience_conditions", []))
            
            formatted.append({
                "name": vol.get("name"),
                "rating": vol.get("rating"),
                "experience_breeds": vol.get("experience_breeds"),
                "price_per_day": vol.get("price_per_day"),
                "condition_expertise": condition_match,
                "availability": vol.get("availability"),
                "bio": vol.get("bio")
            })
        
        # Sort by rating and condition expertise
        formatted.sort(key=lambda x: (x["condition_expertise"], x["rating"]), reverse=True)
        
        return json.dumps({
            "status": "success",
            "pet_name": pet.get("name"),
            "dates": f"{start_date} to {end_date}",
            "volunteer_count": len(formatted),
            "volunteers": formatted[:3]  # Top 3 matches
        })
    
    # ============ TOOL 5: GET PET HEALTH SUMMARY ============
    def get_pet_health_summary(self, pet_id: str) -> str:
        """
        Get comprehensive health summary for a pet
        """
        pet = self.db.db.pets.find_one({"id": pet_id})
        
        if not pet:
            return json.dumps({
                "status": "error",
                "message": f"Pet {pet_id} not found"
            })
        
        # Calculate age category
        age = pet.get("age", 0)
        if age < 2:
            age_category = "Young"
        elif age < 5:
            age_category = "Adult"
        elif age < 8:
            age_category = "Senior"
        else:
            age_category = "Geriatric"
        
        # Check weight category (rough estimate)
        breed = pet.get("breed", "")
        weight = pet.get("weight_kg", 0)
        
        weight_categories = {
            "Labrador": 32,
            "German Shepherd": 32,
            "Golden Retriever": 32,
            "Bulldog": 25,
            "Husky": 28,
            "Beagle": 13,
            "Poodle": 25,
            "Dachshund": 11,
            "Shiba Inu": 10,
            "Corgi": 14
        }
        
        ideal_weight = weight_categories.get(breed, 25)
        weight_status = "Ideal" if abs(weight - ideal_weight) < 2 else ("Overweight" if weight > ideal_weight else "Underweight")
        
        return json.dumps({
            "status": "success",
            "pet_name": pet.get("name"),
            "pet_id": pet_id,
            "breed": breed,
            "age": age,
            "age_category": age_category,
            "weight_kg": weight,
            "weight_status": weight_status,
            "conditions": pet.get("conditions", []),
            "health_notes": pet.get("health_notes"),
            "food_allergies": pet.get("food_allergies", []),
            "last_checkup_days_ago": (datetime.utcnow() - pet.get("last_checkup")).days if pet.get("last_checkup") else "Unknown",
            "owner": pet.get("owner_name")
        })

# Tool definitions for Gemini function calling
PETDIGITWIN_TOOLS = [
    {
        "name": "search_health_knowledge",
        "description": "Search the veterinary knowledge base for information about pet health conditions, symptoms, and natural remedies",
        "input_schema": {
            "type": "object",
            "properties": {
                "condition": {
                    "type": "string",
                    "description": "The health condition to search for (e.g., 'joint_pain', 'skin_sensitivity')"
                },
                "symptom": {
                    "type": "string",
                    "description": "Specific symptom description (optional)"
                }
            },
            "required": ["condition"]
        }
    },
    {
        "name": "find_suitable_food",
        "description": "Find food recommendations for a pet based on its health conditions and budget",
        "input_schema": {
            "type": "object",
            "properties": {
                "pet_id": {
                    "type": "string",
                    "description": "The pet's unique identifier (e.g., 'pet_001')"
                },
                "condition": {
                    "type": "string",
                    "description": "Additional health conditions to consider (optional, comma-separated)"
                },
                "budget": {
                    "type": "integer",
                    "description": "Maximum price budget in dollars (default: 100)"
                }
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "predict_checkup_need",
        "description": "Determine if a pet needs a veterinary checkup based on age, conditions, and last visit date",
        "input_schema": {
            "type": "object",
            "properties": {
                "pet_id": {
                    "type": "string",
                    "description": "The pet's unique identifier"
                }
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "find_volunteers_for_pet",
        "description": "Find available volunteers/pet sitters for a pet during specific dates",
        "input_schema": {
            "type": "object",
            "properties": {
                "pet_id": {
                    "type": "string",
                    "description": "The pet's unique identifier"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                },
                "max_distance_km": {
                    "type": "integer",
                    "description": "Maximum distance in kilometers (default: 50)"
                }
            },
            "required": ["pet_id", "start_date", "end_date"]
        }
    },
    {
        "name": "get_pet_health_summary",
        "description": "Get a comprehensive health profile summary for a pet",
        "input_schema": {
            "type": "object",
            "properties": {
                "pet_id": {
                    "type": "string",
                    "description": "The pet's unique identifier"
                }
            },
            "required": ["pet_id"]
        }
    }
]
