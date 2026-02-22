# Datagroom MCP Server - Quick Start Guide

## Prerequisites

1. **Datagroom Gateway** running on `http://localhost:8887`
2. **Python 3.10+** installed
3. **Personal Access Token** from Datagroom

## Step 1: Install

```bash
cd datagroom-mcp-server
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -e .
```

## Step 2: Configure

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATAGROOM_GATEWAY_URL=http://localhost:8887
DATAGROOM_PAT_TOKEN=dgpat_your_actual_token_here
MCP_SERVER_PORT=3000
```

### Get Your PAT Token

1. Open Datagroom in browser
2. Go to **Settings** → **Personal Access Tokens**
3. Click **"Generate New Token"**
4. Copy the token (only shown once!)
5. Paste into `.env` file

## Step 3: Run Server

```bash
python -m datagroom_mcp.server
```

You should see:

```
Starting Datagroom MCP Server...
Gateway URL: http://localhost:8887
Server will be accessible at http://localhost:8000/mcp
```

## Step 4: Configure Cursor

1. Create or edit `~/.cursor/mcp.json` (Windows: `C:\Users\<username>\.cursor\mcp.json`)

2. Add configuration:

```json
{
  "mcpServers": {
    "datagroom": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "env": {
        "DATAGROOM_PAT_TOKEN": "dgpat_your_token_here",
        "DATAGROOM_GATEWAY_URL": "http://localhost:8887"
      }
    }
  }
}
```

3. Restart Cursor

## Step 5: Test

Ask Claude in Cursor:

```
What datasets are available in Datagroom?
```

```
Show me the schema for [your_dataset_name]
```

```
Query [dataset] and show me the first 10 rows
```

## Troubleshooting

### Server won't start

**Error**: `DATAGROOM_PAT_TOKEN environment variable is required`

**Solution**: Add your PAT token to `.env` file

### Connection refused

**Error**: `Failed to connect to Gateway`

**Solution**: 
- Check Gateway is running: `http://localhost:8887`
- Verify URL in `.env` is correct

### 401 Unauthorized

**Error**: `Invalid or expired access token`

**Solution**:
- Generate a new PAT token
- Update `.env` file
- Restart MCP server

### 403 Forbidden

**Error**: `Access denied`

**Solution**:
- Check dataset ACL in Datagroom
- Verify PAT token has access to dataset
- Contact dataset owner

## Example Queries

```
# List datasets
"What datasets can I access?"

# Get schema
"Show me the schema for transactions"

# Query data
"Show me all active users"
"Find transactions above $1000"
"Get rows where status equals 'failed'"

# Aggregations
"What's the average transaction amount?"
"Count rows by status"
"What's the total revenue by category?"

# Sample data
"Show me a sample of the logs dataset"
```

## Architecture

```
Cursor IDE → MCP Server → Gateway → MongoDB
   (Claude)    (Port 8000)  (Port 8887)
```

The MCP server is a thin proxy that:
- Adds PAT to Authorization header
- Calls Gateway REST APIs
- Formats responses for Claude

## Next Steps

- Explore available datasets
- Query your data with natural language
- Create aggregations and summaries
- Filter and sort data

## Support

- Gateway Repo: https://github.com/h-tendy/datagroom-gateway
- UI Repo: https://github.com/h-tendy/datagroom-ui
- Reference: https://github.com/hrishi2710/dg-mcp-server
