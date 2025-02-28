# TripAdvisor Vacation Planner MCP Server

This MCP server provides access to TripAdvisor data for planning vacations, finding attractions, restaurants, and hotels.

## Features

- Search for locations by name and category
- Get detailed information about specific locations
- Find nearby attractions, restaurants, and hotels
- View photos and reviews
- Interactive vacation planning prompt

## Setup Instructions

### Prerequisites

- Docker
- TripAdvisor API key (get one from [TripAdvisor Developer Portal](https://developer.tripadvisor.com/))
- Claude Desktop

### Building the Docker Image

1. Clone this repository
2. Build the Docker image:
   ```bash
   docker build -t mcp/tripadvisor .
   ```

### Configuring Claude Desktop

1. Open Claude Desktop
2. Go to Settings > MCP Servers
3. Add a new server with the following configuration:
   ```json
   {
     "command": "docker",
     "args": [
       "run",
       "-i",
       "--rm",
       "-p",
       "8080:8080",
       "-e",
       "TRIPADVISOR_API_KEY=your_api_key_here",
       "mcp/tripadvisor"
     ]
   }
   ```
4. Replace `your_api_key_here` with your actual TripAdvisor API key

### Using the Vacation Planner

1. Start a new conversation in Claude
2. Select the "Vacation Planner" prompt
3. Follow the interactive prompts to plan your perfect vacation!

## API Endpoints Used

- Location Search: Find locations by name and category
- Location Details: Get comprehensive information about a location
- Location Photos: View photos of a location
- Location Reviews: Read reviews of a location
- Nearby Search: Find locations near a specific point

## Troubleshooting

- If you see 401 Unauthorized errors, check that your API key is correct and that your IP is whitelisted in the TripAdvisor Developer Portal
- If the server doesn't start, check Docker logs for error messages
