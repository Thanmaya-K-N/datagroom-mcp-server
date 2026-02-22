# Datagroom MCP Server

Python MCP server that enables LLMs (like Claude in Cursor IDE) to query Datagroom datasets through natural language.

## Features

- 🔍 Query datasets with filters, sorting, and pagination
- 📊 Get dataset schemas and metadata
- 📈 Perform aggregations (count, sum, avg, min, max)
- 🎲 Random sampling for data exploration
- 🔒 Respects all Datagroom ACLs (dataset and row-level)

## Installation

### Prerequisites

- Python 3.10 or higher
- Running Datagroom Gateway instance
- Personal Access Token from Datagroom

### Setup

1. **Clone and navigate to project**:
   ```bash
   cd datagroom-mcp-server
   ```

2. **Create virtual environment (recommended)**:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e .
   ```

4. **Configure environment** (for local testing):
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your PAT token:
   ```env
   DATAGROOM_PAT_TOKEN=dgpat_your_token_here
   ```
   
   **Note**: When running as an MCP server from Cursor, configure these variables in your `mcp.json` file instead (see Cursor IDE Configuration section below).

### Generate PAT Token

1. Open Datagroom in browser
2. Go to Settings > Personal Access Tokens
3. Click "Generate New Token"
4. Name it "MCP Server" or similar
5. Select dataset and expiry
6. Copy the token (shown only once!)
7. Paste into `.env` file

## Running the Server

### Development Mode

```bash
python -m datagroom_mcp.server
```

### Production Mode

```bash
datagroom-mcp
```

The server will start on `http://localhost:8000/mcp` (default port for MCP SDK's FastMCP)

## Cursor IDE Configuration

Add the Datagroom MCP server to your Cursor `mcp.json` configuration:

1. Open or create `~/.cursor/mcp.json` (on Windows: `C:\Users\<username>\.cursor\mcp.json`)

2. Add the configuration:
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

3. Start the MCP server:
   ```bash
   python -m datagroom_mcp.server
   ```
   
   Or use the command:
   ```bash
   datagroom-mcp
   ```

4. Restart Cursor to load the MCP server configuration

5. Test by asking Claude:
   - "What datasets are available?"
   - "Show me the schema for [dataset_name]"
   - "Query [dataset] where [condition]"

## Available Tools

### 1. datagroom_get_schema

Get dataset structure including columns, types, and sample values.

**Example:**

```
Claude in Cursor: "Show me the schema for transactions dataset"
```

### 2. datagroom_query_dataset

Query dataset with filters, sorting, and pagination.

**Example:**

```
Claude: "Show me failed transactions above $1000 from last month"

Claude will call:
- dataset_name: "transactions"
- filters: [
    {field: "status", type: "eq", value: "failed"},
    {field: "amount", type: "gt", value: 1000}
  ]
```

### 3. datagroom_aggregate_dataset

Perform statistical aggregations.

**Example:**

```
Claude: "What's the average transaction amount by status?"

Claude will call:
- aggregations: [{operation: "avg", field: "amount"}]
- group_by: "status"
```

### 4. datagroom_list_datasets

List all available datasets.

**Example:**

```
Claude: "What datasets can I access?"
```

### 5. datagroom_sample_dataset

Get random sample for exploration.

**Example:**

```
Claude: "Show me a sample of the users dataset"
```

## Filter Syntax

Filters use this structure:

```json
{
  "field": "column_name",
  "type": "operator",
  "value": filter_value
}
```

### Operators:

- `eq`: Equal to
- `ne`: Not equal to
- `gt`: Greater than
- `lt`: Less than
- `gte`: Greater than or equal
- `lte`: Less than or equal
- `in`: In array
- `regex`: Regular expression match

### Example filters:

```python
# Equal
{"field": "status", "type": "eq", "value": "active"}

# Greater than
{"field": "amount", "type": "gt", "value": 1000}

# In array
{"field": "category", "type": "in", "value": ["A", "B", "C"]}

# Regex
{"field": "email", "type": "regex", "value": "@example.com"}
```

## Troubleshooting

### "DATAGROOM_PAT_TOKEN not set"

- Generate a token in Datagroom UI
- Add to `.env` file
- Restart MCP server

### "401 Unauthorized"

- Token may be expired
- Generate new token
- Update `.env` file

### "403 Forbidden"

- You don't have access to this dataset
- Check dataset ACL in Datagroom
- Contact dataset owner

### "Connection refused"

- Datagroom Gateway not running
- Check Gateway is running on port 8887
- Update `DATAGROOM_GATEWAY_URL` in `.env`

### "Dataset listing not available"

- Check Gateway `/ds/dsList/:dsUser` endpoint is available
- Verify PAT token has valid dataset access
- Or ask user for dataset name directly

## Gateway API Endpoints Used

The MCP server calls these Datagroom Gateway REST APIs:

- `GET /ds/dsList/:dsUser` - List all datasets accessible to user
- `GET /ds/view/columns/:dsName/:dsView/:dsUser` - Get dataset schema and metadata
- `POST /ds/viewViaPost/:dsName/:dsView/:dsUser` - Query dataset with filters, sorting, pagination

**URL Pattern**: All dataset routes follow `/ds/<operation>/:dsName/:dsView/:dsUser`

**Authentication**: PAT token in `Authorization: Bearer <token>` header

**Reference**: See [datagroom-gateway/routes/dsReadApi.js](https://github.com/h-tendy/datagroom-gateway/blob/main/routes/dsReadApi.js)

## Architecture

```
┌─────────────────────────────┐
│ Claude in Cursor IDE        │
│ "Show me failed txns > $1k" │
└──────────┬──────────────────┘
           │ (Calls MCP tool)
           ▼
┌─────────────────────────────┐
│ Datagroom MCP Server        │
│ - Parses request            │
│ - Adds PAT to header        │
│ - Calls Gateway API         │
└──────────┬──────────────────┘
           │ Authorization: Bearer dgpat_...
           ▼
┌─────────────────────────────┐
│ Datagroom Gateway           │
│ - Verifies PAT              │
│ - Checks ACLs               │
│ - Queries MongoDB           │
│ - Returns filtered results  │
└─────────────────────────────┘
```

**Key Points:**

- MCP server is a thin proxy
- All auth/ACL logic stays in Gateway
- No direct MongoDB access from MCP
- PAT enforces same permissions as UI

## Development

### Run Tests

```bash
pytest
```

### Add New Tool

1. Add function in `server.py` with `@mcp.tool()` decorator
2. Add type hints and docstring
3. Call Gateway API using `gateway_client`
4. Format response using `formatters`
5. Test in Cursor

### Project Structure

```
src/datagroom_mcp/
├── server.py          # All tools (5 total)
├── gateway_client.py  # HTTP client
├── formatters.py      # Response formatting
└── config.py          # Environment config
```

Total: ~400 lines of Python code

## License

MIT License - See LICENSE file

---

## OPTIONAL: Gateway Endpoint Addition

If the `/api/datasets` endpoint doesn't exist in Gateway, add this to `server.js`:

```javascript
// Add after other route registrations
app.get('/api/datasets', authenticate, async (req, res) => {
  try {
    const dbAbstraction = new DbAbstraction();
    const databases = await dbAbstraction.listDatabases();
    
    // Filter out system databases
    const filtered = databases.filter(db => 
      !['admin', 'local', 'config'].includes(db)
    );
    
    // Optionally get row counts
    const datasetsWithCounts = [];
    for (const dbName of filtered) {
      try {
        const count = await dbAbstraction.countDocuments(dbName, "data", {}, {});
        datasetsWithCounts.push({ name: dbName, row_count: count });
      } catch (e) {
        datasetsWithCounts.push({ name: dbName, row_count: null });
      }
    }
    
    res.json({ datasets: datasetsWithCounts });
  } catch (error) {
    logger.error(error, "Error listing datasets");
    res.status(500).json({ error: error.message });
  }
});
```

## Testing Checklist

After implementation, verify:

### 1. Server Startup

```bash
python -m datagroom_mcp.server
# Should show: "Starting Datagroom MCP Server..."
# Should not error with "PAT_TOKEN not set"
```

### 2. Gateway Connection

```python
# In Python console:
from datagroom_mcp.gateway_client import gateway_client
import asyncio

async def test():
    result = await gateway_client.get("/api/datasets")
    print(result)

asyncio.run(test())
# Should return list of datasets
```

### 3. Tool Execution

In Cursor IDE, ask:

- "What datasets are available?" → Should list datasets
- "Show me the schema for [dataset]" → Should show columns
- "Query [dataset] for all rows" → Should return data table

### 4. Filter Testing

Ask Claude:

- "Show me rows where status equals 'active'"
- "Find records with amount greater than 1000"
- "Get rows where category is in ['A', 'B']"

### 5. ACL Testing

- Generate PAT for user with limited access
- Try to query restricted dataset
- Should get 403 Forbidden error

### 6. Error Handling

- Stop Gateway → Should show connection error
- Use invalid token → Should show 401 error
- Query non-existent dataset → Should show clear error
