from mcp.server.fastmcp import FastMCP
import sys
import os
import httpx
import json
from typing import Dict, Any, Optional, List


print ("Starting TripAdvisor MCP server...", file=sys.stderr)


mcp = FastMCP("tripadvisor")
print("Successfully initialized TripAdvisor MCP server", file=sys.stderr)

TRIPADVISOR_API_KEY = os.environ.get("TRIPADVISOR_API_KEY")
API_BASE_URL = "https://api.content.tripadvisor.com/api/v1"

#Helper Functions
async def tripadvisor_api_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a request to the TripAdvisor API"""
    if not TRIPADVISOR_API_KEY:
        return {"error": "TripAdvisor API key not configured. Set TRIPADVISOR_API_KEY environment variable."}
    
    headers = {"accept": "application/json", "key": TRIPADVISOR_API_KEY}

    if params is None:
        params = {}

    params["key"] = TRIPADVISOR_API_KEY

    url = f"{API_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP error occurred: {e}",
                "details": str(e)
            }
        
#Resources for specific location details
@mcp.resource("location://{location_id}")
async def get_location_details(location_id: str) -> str:
    """Get details about a specific location by ID"""
    result = await tripadvisor_api_request(f"location/{location_id}/details")
    return json.dumps(result, indent=2)

@mcp.resource("photos://{location_id}")
async def get_location_photos(location_id: str) -> str:
    """Get photos for a specific location by ID"""
    result = await tripadvisor_api_request(f"location/{location_id}/photos")
    return json.dumps(result, indent=2)

@mcp.resource("reviews://{location_id}")
async def get_location_reviews(location_id: str) -> str:
    """Get reviews for a specific location by ID"""
    result = await tripadvisor_api_request(f"location/{location_id}/reviews")
    return json.dumps(result, indent=2)

#Resources for search and discovery
@mcp.resource("search://{query}/{category}")
async def get_search_results(query: str, category: str) -> str:
    """Get search results for a location query and store them as context
    
    This resource performs a search and returns up to 10 locations matching the query.
    The Location Search request returns up to 10 locations found by the given search query.
    You can use category ("hotels", "attractions", "restaurants", "geos") to search with more accuracy.
    
    
    This endpoint may also return bookable products (activities). For those activities that are returned there are no additional details available on the Location Details endpoint.
    """
    params = {
        "searchQuery": query,
        "category": category,
        "key": TRIPADVISOR_API_KEY
    }
    
    result = await tripadvisor_api_request("location/search", params)

    if "data" in result and isinstance(result["data"], list):
        result["data"] = result["data"][:10]
    
    return json.dumps(result, indent=2)


@mcp.resource("nearby://{latitude},{longitude}/{category}")
async def get_nearby_locations_resource(latitude: str, longitude: str, category: str) -> str:
    """Get up to 10 locations near coordinates by category as persistent context
    
    This resource finds nearby locations and makes them available as context for planning.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        category: Category filter (e.g., "hotels", "restaurants", "attractions",
        address: Address to filter the search results by)
    """
    params = {
        "latLong": f"{latitude},{longitude}",
        "category": category
    }
    
    result = await tripadvisor_api_request("location/nearby_search", params)
    
    # Extract just the top 10 results to keep context manageable
    if "data" in result and isinstance(result["data"], list):
        result["data"] = result["data"][:10]
    
    return json.dumps(result, indent=2)


#Tools
@mcp.tool()
async def search_locations(query: str, category: Optional[str] = None) -> str:
    """
    Search for locations on TripAdvisor
    
    Args:
        query: Search term (e.g., "hotels in Paris")
        category: Optional category filter (e.g., "hotels", "restaurants", "attractions")
    """
    params = {"searchQuery": query}
    if category:
        params["category"] = category
    
    result = await tripadvisor_api_request("location/search", params)
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_nearby_locations(latitude: float, longitude: float, category: Optional[str] = None) -> str:
    """
    Find locations near a specific latitude and longitude
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        category: Optional category filter (e.g., "hotels", "restaurants", "attractions")
    """
    params = {"latLong": f"{latitude},{longitude}"}
    if category:
        params["category"] = category
    
    result = await tripadvisor_api_request("location/nearby_search", params)
    return json.dumps(result, indent=2)

@mcp.tool()
async def get_location_details_tool(location_id: str) -> str:
    """
    Get comprehensive details about a location by ID
    
    Args:
        location_id: TripAdvisor location ID
    """
    # Get basic details
    details = await tripadvisor_api_request(f"location/{location_id}/details")
    
    # Get additional information if basic request was successful
    if "error" not in details:
        # Get photos
        photos = await tripadvisor_api_request(f"location/{location_id}/photos")
        details["photos"] = photos.get("data", [])
        
        # Get reviews
        reviews = await tripadvisor_api_request(f"location/{location_id}/reviews")
        details["reviews"] = reviews.get("data", [])
    
    return json.dumps(details, indent=2)

#Prompt
@mcp.prompt()
def vacation_planner() -> List[dict]:
    """Create an interactive prompt for planning a personalized vacation"""
    return [
        {
            "role": "assistant",
            "content": """
            I'll help you plan a personalized vacation itinerary using TripAdvisor data. To create the best plan for you, I need to know a few details:

            1. **Destination**: Where would you like to go?
            2. **Duration**: How many days will you be staying?
            3. **Meals**: Which meals should I include? (breakfast, lunch, dinner)
            4. **Pace**: How many attractions would you like to visit per day? (1-5)
            5. **Travel preferences**: Maximum drive time between stops? (in minutes)
            6. **Previous visits**: Any places you've already been to and want to skip?
            7. **Cuisine preferences**: Any specific types of food you prefer or dietary restrictions?
            8. **Budget level**: What's your approximate budget for activities and dining? (budget, moderate, luxury)
            9. **Special interests**: Any particular types of attractions you're interested in? (museums, outdoors, shopping, etc.)

            You don't need to answer all of these at once - we can work through them as we go. Let's start with your destination and how long you'll be staying.
            """
        }
    ]

print("Successfully initialized TripAdvisor MCP server", file=sys.stderr)


if __name__ == "__main__":
    mcp.run()
