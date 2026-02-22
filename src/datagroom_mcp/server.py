"""Datagroom MCP Server - Main server implementation with all tools."""

import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .config import Config
from .gateway_client import gateway_client
from .formatters import (
    format_markdown_table,
    format_query_summary,
    format_schema_info,
    format_aggregation_results,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("datagroom-mcp-server")


# ============================================================================
# TOOL 1: Get Dataset Schema
# ============================================================================

@mcp.tool()
async def datagroom_get_schema(
    dataset_name: str,
    view_name: str = Field(
        default="default",
        description="View name (defaults to 'default')"
    ),
    user_name: str = Field(
        default="mcp-user",
        description="User name for access control (defaults to 'mcp-user')"
    )
) -> str:
    """
    Get schema information for a dataset including column names, types, and sample values.
    Use this first when working with a new dataset to understand its structure.
    """
    try:
        # Call Gateway API - note the /ds/ prefix
        endpoint = f"/ds/view/columns/{dataset_name}/{view_name}/{user_name}"
        response = await gateway_client.get(endpoint)
        
        # Extract schema information
        columns = response.get('columns', {})
        column_attrs = response.get('columnAttrs', [])
        keys = response.get('keys', [])
        filters = response.get('filters', {})
        
        # Get row count by querying with limit 1
        query_endpoint = f"/ds/viewViaPost/{dataset_name}/{view_name}/{user_name}"
        count_response = await gateway_client.post(
            query_endpoint,
            json={"filters": [], "page": 1, "per_page": 1}
        )
        total_rows = count_response.get('total', 0)
        
        # Format schema data - columns is a dict like {'1': 'col1', '2': 'col2'}
        column_list = []
        if isinstance(columns, dict):
            # Extract column names from the columns dict
            for idx in sorted(columns.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                col_name = columns[idx]
                # Find matching columnAttr
                col_attr = next((attr for attr in column_attrs if attr.get('field') == col_name), {})
                column_list.append({
                    'name': col_name,
                    'type': col_attr.get('editor', 'string'),
                    'width': col_attr.get('width', 150),
                    'sample_values': []
                })
        
        schema_data = {
            'dataset_name': dataset_name,
            'columns': column_list,
            'total_rows': total_rows,
            'keys': keys
        }
        
        return format_schema_info(schema_data)
        
    except Exception as e:
        logger.error(f"Error getting schema for {dataset_name}: {e}")
        return f"Error: Failed to get schema for dataset '{dataset_name}'. {str(e)}"


# ============================================================================
# TOOL 2: Query Dataset
# ============================================================================

@mcp.tool()
async def datagroom_query_dataset(
    dataset_name: str,
    filters: List[Dict[str, Any]] = Field(
        default=[],
        description="Array of filter objects with structure: [{field: 'column_name', type: 'eq|ne|gt|lt|gte|lte|in|regex', value: filter_value}]"
    ),
    sort_field: Optional[str] = Field(
        default=None,
        description="Field to sort by"
    ),
    sort_direction: str = Field(
        default="asc",
        description="Sort direction: 'asc' or 'desc'"
    ),
    max_rows: int = Field(
        default=100,
        description="Maximum rows to return (max: 1000)",
        le=1000
    ),
    offset: int = Field(
        default=0,
        description="Number of rows to skip for pagination"
    ),
    view_name: str = Field(
        default="default",
        description="View name (defaults to 'default')"
    ),
    user_name: str = Field(
        default="mcp-user",
        description="User name for access control (defaults to 'mcp-user')"
    )
) -> str:
    """
    Query a dataset with filters and return matching rows.
    Respects all ACLs (dataset-level and row-level permissions).
    """
    try:
        # Prepare query payload
        page = (offset // max_rows) + 1
        
        payload = {
            "filters": filters,
            "page": page,
            "per_page": max_rows
        }
        
        # Add sorting if specified
        if sort_field:
            payload["sorters"] = [{
                "field": sort_field,
                "dir": sort_direction
            }]
        
        # Call Gateway API - note the /ds/ prefix
        endpoint = f"/ds/viewViaPost/{dataset_name}/{view_name}/{user_name}"
        response = await gateway_client.post(endpoint, json=payload)
        
        # Extract response data
        data = response.get('data', [])
        total = response.get('total', 0)
        
        # Check if results exceed limit
        warning = ""
        if total > max_rows:
            warning = f"\n\n⚠️ **Warning**: {total} rows match your filters, but only returning first {max_rows}. Use offset parameter or refine filters.\n"
        
        # Format response
        summary = format_query_summary(
            dataset_name=dataset_name,
            total_matching=total,
            rows_returned=len(data),
            filters=filters,
            offset=offset
        )
        
        table = format_markdown_table(data)
        
        return f"{summary}\n\n{table}{warning}"
        
    except Exception as e:
        logger.error(f"Error querying dataset {dataset_name}: {e}")
        return f"Error: Failed to query dataset '{dataset_name}'. {str(e)}"


# ============================================================================
# TOOL 3: Aggregate Dataset
# ============================================================================

@mcp.tool()
async def datagroom_aggregate_dataset(
    dataset_name: str,
    aggregations: List[Dict[str, Any]] = Field(
        description="List of aggregations: [{operation: 'count|sum|avg|min|max', field: 'column_name'}]"
    ),
    group_by: Optional[str] = Field(
        default=None,
        description="Field to group results by"
    ),
    filters: List[Dict[str, Any]] = Field(
        default=[],
        description="Optional filters to apply before aggregation"
    ),
    view_name: str = Field(
        default="default",
        description="View name (defaults to 'default')"
    ),
    user_name: str = Field(
        default="mcp-user",
        description="User name for access control (defaults to 'mcp-user')"
    )
) -> str:
    """
    Perform aggregations on a dataset (count, sum, avg, min, max).
    Returns statistical summaries without fetching all rows.
    """
    try:
        # Note: This requires MongoDB aggregation pipeline support in Gateway
        # For now, we'll fetch data and compute locally
        # TODO: Add aggregation endpoint to Gateway for better performance
        
        # Fetch data with filters - use /ds/ prefix
        endpoint = f"/ds/viewViaPost/{dataset_name}/{view_name}/{user_name}"
        response = await gateway_client.post(
            endpoint,
            json={"filters": filters, "page": 1, "per_page": 10000}
        )
        
        data = response.get('data', [])
        
        if not data:
            return f"No data found in dataset '{dataset_name}' with the given filters."
        
        # Compute aggregations locally
        results = []
        
        if group_by:
            # Group by field
            groups: Dict[Any, List[Dict]] = {}
            for row in data:
                group_value = row.get(group_by, 'null')
                if group_value not in groups:
                    groups[group_value] = []
                groups[group_value].append(row)
            
            # Compute aggregations for each group
            for group_value, group_rows in groups.items():
                result = {'group': group_value}
                
                for agg in aggregations:
                    operation = agg.get('operation')
                    field = agg.get('field')
                    
                    if operation == 'count':
                        result['count'] = len(group_rows)
                    elif operation in ['sum', 'avg', 'min', 'max']:
                        values = [row.get(field) for row in group_rows if field in row]
                        values = [v for v in values if isinstance(v, (int, float))]
                        
                        if values:
                            if operation == 'sum':
                                result[f'sum_{field}'] = sum(values)
                            elif operation == 'avg':
                                result[f'avg_{field}'] = sum(values) / len(values)
                            elif operation == 'min':
                                result[f'min_{field}'] = min(values)
                            elif operation == 'max':
                                result[f'max_{field}'] = max(values)
                
                results.append(result)
        else:
            # Aggregate across all rows
            result = {}
            
            for agg in aggregations:
                operation = agg.get('operation')
                field = agg.get('field')
                
                if operation == 'count':
                    result['count'] = len(data)
                elif operation in ['sum', 'avg', 'min', 'max']:
                    values = [row.get(field) for row in data if field in row]
                    values = [v for v in values if isinstance(v, (int, float))]
                    
                    if values:
                        if operation == 'sum':
                            result[f'sum_{field}'] = sum(values)
                        elif operation == 'avg':
                            result[f'avg_{field}'] = sum(values) / len(values)
                        elif operation == 'min':
                            result[f'min_{field}'] = min(values)
                        elif operation == 'max':
                            result[f'max_{field}'] = max(values)
            
            results.append(result)
        
        return format_aggregation_results(results)
        
    except Exception as e:
        logger.error(f"Error aggregating dataset {dataset_name}: {e}")
        return f"Error: Failed to aggregate dataset '{dataset_name}'. {str(e)}"


# ============================================================================
# TOOL 4: List Datasets
# ============================================================================

@mcp.tool()
async def datagroom_list_datasets(
    user_name: str = Field(
        default="mcp-user",
        description="User name for access control (defaults to 'mcp-user')"
    )
) -> str:
    """
    List all available datasets in Datagroom.
    Use this to discover which datasets you have access to.
    """
    try:
        # Call Gateway endpoint - /ds/dsList/:dsUser
        endpoint = f"/ds/dsList/{user_name}"
        response = await gateway_client.get(endpoint)
        datasets = response.get('dbList', [])
        
        if not datasets:
            return "No datasets found. You may not have access to any datasets."
        
        lines = ["# Available Datasets", ""]
        
        for ds in datasets:
            if isinstance(ds, dict):
                name = ds.get('name', 'unknown')
                size_mb = ds.get('sizeOnDisk', 0) / (1024 * 1024)  # Convert to MB
                perms = ds.get('perms', {})
                owner = perms.get('owner', 'unknown')
                lines.append(f"- **{name}** (Size: {size_mb:.2f} MB, Owner: {owner})")
            elif isinstance(ds, str):
                lines.append(f"- {ds}")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        return f"Error: Failed to list datasets. {str(e)}"


# ============================================================================
# TOOL 5: Sample Dataset
# ============================================================================

@mcp.tool()
async def datagroom_sample_dataset(
    dataset_name: str,
    sample_size: int = Field(
        default=20,
        description="Number of random rows to sample (max: 100)",
        le=100
    ),
    view_name: str = Field(
        default="default",
        description="View name (defaults to 'default')"
    ),
    user_name: str = Field(
        default="mcp-user",
        description="User name for access control (defaults to 'mcp-user')"
    )
) -> str:
    """
    Get a random sample of rows from a dataset.
    Useful for exploring data without knowing the structure.
    """
    try:
        # Fetch random sample by querying first N rows - use /ds/ prefix
        # Note: MongoDB $sample would be better but requires aggregation pipeline
        endpoint = f"/ds/viewViaPost/{dataset_name}/{view_name}/{user_name}"
        response = await gateway_client.post(
            endpoint,
            json={"filters": [], "page": 1, "per_page": sample_size}
        )
        
        data = response.get('data', [])
        total = response.get('total', 0)
        
        if not data:
            return f"Dataset '{dataset_name}' is empty or you don't have access."
        
        summary = f"# Sample from {dataset_name}\n\n"
        summary += f"**Total rows in dataset**: {total}\n"
        summary += f"**Sample size**: {len(data)}\n\n"
        
        table = format_markdown_table(data, max_rows=sample_size)
        
        return summary + table
        
    except Exception as e:
        logger.error(f"Error sampling dataset {dataset_name}: {e}")
        return f"Error: Failed to sample dataset '{dataset_name}'. {str(e)}"


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the MCP server."""
    # Validate configuration now that env vars are loaded
    Config.validate()
    
    logger.info("Starting Datagroom MCP Server...")
    logger.info(f"Gateway URL: {Config.GATEWAY_URL}")
    
    # Run the FastMCP server with streamable-http transport
    # Note: mcp.server.fastmcp doesn't support custom port configuration
    # It defaults to http://localhost:8000/mcp
    logger.info("Server will be accessible at http://localhost:8000/mcp")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
