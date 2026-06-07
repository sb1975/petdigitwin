"""
PetDigiTwin Gemini Agent
Main orchestrator that runs the agent loop with tool calling
"""
import json
import os
from google import genai
import google.auth
from opentelemetry import trace
from src.tools import PetDigiTwinTools, PETDIGITWIN_TOOLS
from dotenv import load_dotenv

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel as VertexGenerativeModel
except Exception:
    vertexai = None
    VertexGenerativeModel = None

load_dotenv()
TRACER = trace.get_tracer("petdigitwin.agent")

class PetDigiTwinAgent:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.tools = PetDigiTwinTools()
        self.client = genai.Client(api_key=self.api_key)
        self.use_vertex_sdk = os.getenv("USE_VERTEX_SDK", "false").lower() == "true"

        # Detect project ID automatically for Vertex AI
        try:
            _, self.gcp_project = google.auth.default()
        except Exception:
            self.gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")

        self.gcp_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
        self.model_fallbacks = [
            self.model_name,
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-1.5-flash",
        ]
        self.vertex_ready = False

        if self.use_vertex_sdk:
            if vertexai is None or VertexGenerativeModel is None:
                raise RuntimeError(
                    "USE_VERTEX_SDK=true but Vertex SDK is not installed. "
                    "Install google-cloud-aiplatform and retry."
                )
            if not self.gcp_project:
                raise RuntimeError(
                    "USE_VERTEX_SDK=true requires GOOGLE_CLOUD_PROJECT in environment."
                )
            vertexai.init(project=self.gcp_project, location=self.gcp_location)
            self.vertex_ready = True
        self.system_instruction = """You are PetDigiTwin, an intelligent pet health advisor.
Your role is to:
1. Monitor and track pet health status
2. Provide personalized nutrition recommendations
3. Suggest natural recovery methods for common pet ailments
4. Proactively recommend veterinary checkups when needed
5. Help find pet sitters/volunteers for vacation planning

Always prioritize pet health and safety. Be friendly and supportive with pet owners.
When you don't have information, be honest about it and recommend consulting a veterinarian."""

    def _generate_with_model(self, prompt: str) -> str:
        """Generate a response using either direct Gemini API or Vertex SDK."""
        last_error = None
        for model_name in self.model_fallbacks:
            try:
                if self.vertex_ready:
                    model = VertexGenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    text = getattr(response, "text", None)
                else:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    text = response.text

                if text:
                    return text.strip()
            except Exception as model_error:
                last_error = model_error
                continue

        return f"I hit an error while generating a response: {last_error}"
    
    def _handle_tool_call(self, tool_name: str, tool_args: dict) -> str:
        """Route tool calls to the appropriate handler"""
        
        if tool_name == "search_health_knowledge":
            return self.tools.search_health_knowledge(
                condition=tool_args.get("condition"),
                symptom=tool_args.get("symptom")
            )
        elif tool_name == "find_suitable_food":
            return self.tools.find_suitable_food(
                pet_id=tool_args.get("pet_id"),
                condition=tool_args.get("condition"),
                budget=tool_args.get("budget", 100)
            )
        elif tool_name == "predict_checkup_need":
            return self.tools.predict_checkup_need(
                pet_id=tool_args.get("pet_id")
            )
        elif tool_name == "find_volunteers_for_pet":
            return self.tools.find_volunteers_for_pet(
                pet_id=tool_args.get("pet_id"),
                start_date=tool_args.get("start_date"),
                end_date=tool_args.get("end_date"),
                max_distance_km=tool_args.get("max_distance_km", 50)
            )
        elif tool_name == "get_pet_health_summary":
            return self.tools.get_pet_health_summary(
                pet_id=tool_args.get("pet_id")
            )
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    def _build_tool_context(self, user_query: str, pet_id: str = None) -> dict:
        """Create relevant context by calling local tools based on query intent."""
        with TRACER.start_as_current_span("agent.build_tool_context") as span:
            query_l = user_query.lower()
            context = {"tool_outputs": []}
            span.set_attribute("petdigitwin.pet_id", pet_id or "")
            span.set_attribute("petdigitwin.query_length", len(user_query or ""))

            if pet_id:
                context["tool_outputs"].append(
                    {
                        "tool": "get_pet_health_summary",
                        "result": json.loads(self.tools.get_pet_health_summary(pet_id=pet_id)),
                    }
                )
                context["tool_outputs"].append(
                    {
                        "tool": "predict_checkup_need",
                        "result": json.loads(self.tools.predict_checkup_need(pet_id=pet_id)),
                    }
                )

            if any(k in query_l for k in ["food", "nutrition", "diet", "feed"]):
                if pet_id:
                    context["tool_outputs"].append(
                        {
                            "tool": "find_suitable_food",
                            "result": json.loads(self.tools.find_suitable_food(pet_id=pet_id)),
                        }
                    )

            if any(k in query_l for k in ["sitter", "volunteer", "babysit", "vacation"]):
                if pet_id:
                    context["tool_outputs"].append(
                        {
                            "tool": "find_volunteers_for_pet",
                            "result": json.loads(
                                self.tools.find_volunteers_for_pet(
                                    pet_id=pet_id,
                                    start_date="2026-07-01",
                                    end_date="2026-07-15",
                                    max_distance_km=50,
                                )
                            ),
                        }
                    )

            health_keywords = [
                "joint",
                "limp",
                "skin",
                "allergy",
                "itch",
                "arthritis",
                "pain",
                "breathing",
                "checkup",
                "vet",
                "remedy",
            ]
            if any(k in query_l for k in health_keywords):
                guessed_condition = "joint_pain"
                if "skin" in query_l or "itch" in query_l or "allergy" in query_l:
                    guessed_condition = "skin_sensitivity"
                elif "breath" in query_l:
                    guessed_condition = "breathing_issues"
                elif "dental" in query_l or "teeth" in query_l:
                    guessed_condition = "dental_care"
                elif "weight" in query_l:
                    guessed_condition = "weight_management"

                context["tool_outputs"].append(
                    {
                        "tool": "search_health_knowledge",
                        "result": json.loads(
                            self.tools.search_health_knowledge(condition=guessed_condition)
                        ),
                    }
                )

            span.set_attribute("petdigitwin.tool_output_count", len(context["tool_outputs"]))

            return context

    def run(self, user_query: str, pet_id: str = None, max_iterations: int = 5) -> str:
        """
        Run the agent loop
        
        Args:
            user_query: The user's question or request
            pet_id: Optional pet ID for context
            max_iterations: Max number of tool calls before giving final response
        
        Returns:
            Final agent response
        """
        
        with TRACER.start_as_current_span("agent.run") as span:
            try:
                span.set_attribute("petdigitwin.pet_id", pet_id or "")
                span.set_attribute("petdigitwin.max_iterations", max_iterations)
                span.set_attribute("petdigitwin.query_length", len(user_query or ""))
                tool_context = self._build_tool_context(user_query=user_query, pet_id=pet_id)

                prompt = (
                    f"System:\n{self.system_instruction}\n\n"
                    f"Available tools metadata:\n{json.dumps(PETDIGITWIN_TOOLS)}\n\n"
                    f"Resolved tool outputs:\n{json.dumps(tool_context)}\n\n"
                    f"User query:\n{user_query}\n\n"
                    "Generate a concise and practical answer. If needed, add a short 'When to see a vet' section."
                )

                response_text = self._generate_with_model(prompt)
                span.set_attribute("petdigitwin.response_length", len(response_text or ""))
                return response_text or "I couldn't generate a response. Please try again."
            except Exception as e:
                span.record_exception(e)
                return f"I hit an error while generating a response: {e}"


def main():
    """Test the agent"""
    from src.db import PetDigiTwinDB
    
    # Initialize database with sample data
    db = PetDigiTwinDB()
    db.initialize_collections()
    db.load_sample_data()
    
    # Create and run agent
    agent = PetDigiTwinAgent()
    
    # Test queries
    test_queries = [
        ("Max has been limping for 2 days. What natural remedies can help?", "pet_001"),
        ("I'm going on vacation July 1-15. Can you find a pet sitter for Bella?", "pet_002"),
        ("What's the best food for Charlie given his conditions?", "pet_003"),
        ("Tell me about Daisy's health and when she needs her next checkup.", "pet_004")
    ]
    
    for query, pet_id in test_queries[:1]:  # Run first query for demo
        print(f"\n{'='*70}")
        print(f"USER: {query}")
        print(f"{'='*70}")
        
        response = agent.run(query, pet_id=pet_id)
        
        print(f"\nAGENT: {response}")


if __name__ == "__main__":
    main()
