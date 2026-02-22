"""Response formatting utilities for MCP tool outputs."""

from typing import Any, Dict, List


def format_markdown_table(data: List[Dict[str, Any]], max_rows: int = 50) -> str:
    """
    Format data as a markdown table.
    
    Args:
        data: List of row dictionaries
        max_rows: Maximum rows to display (truncate if more)
        
    Returns:
        Markdown-formatted table string
    """
    if not data:
        return "No data to display."
    
    # Limit rows for readability
    display_data = data[:max_rows]
    truncated = len(data) > max_rows
    
    # Get columns from first row
    columns = list(display_data[0].keys())
    
    # Filter out _id column if present
    columns = [col for col in columns if col != '_id']
    
    # Build table
    lines = []
    
    # Header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---" for _ in columns]) + " |"
    lines.append(header)
    lines.append(separator)
    
    # Rows
    for row in display_data:
        values = []
        for col in columns:
            value = row.get(col, "")
            # Handle complex types
            if isinstance(value, (dict, list)):
                value = str(value)[:50]  # Truncate complex values
            values.append(str(value))
        
        lines.append("| " + " | ".join(values) + " |")
    
    # Add truncation notice
    if truncated:
        lines.append("")
        lines.append(f"_(Showing first {max_rows} of {len(data)} rows)_")
    
    return "\n".join(lines)


def format_query_summary(
    dataset_name: str,
    total_matching: int,
    rows_returned: int,
    filters: List[Dict[str, Any]],
    offset: int = 0
) -> str:
    """
    Format query summary with statistics.
    
    Returns:
        Markdown-formatted summary
    """
    lines = [
        f"# Dataset: {dataset_name}",
        "",
        f"**Total Matching Rows**: {total_matching}",
        f"**Rows Returned**: {rows_returned}",
        f"**Offset**: {offset}",
    ]
    
    if filters:
        lines.append("")
        lines.append("**Applied Filters**:")
        for f in filters:
            field = f.get('field', 'unknown')
            filter_type = f.get('type', 'unknown')
            value = f.get('value', '')
            lines.append(f"- `{field}` {filter_type} `{value}`")
    
    return "\n".join(lines)


def format_schema_info(schema_data: Dict[str, Any]) -> str:
    """
    Format dataset schema information.
    
    Returns:
        Markdown-formatted schema
    """
    lines = [
        f"# Dataset: {schema_data.get('dataset_name', 'Unknown')}",
        "",
        f"**Total Rows**: {schema_data.get('total_rows', 0)}",
        "",
        "## Columns",
        ""
    ]
    
    columns = schema_data.get('columns', [])
    
    for col in columns:
        name = col.get('name', 'unknown')
        col_type = col.get('type', 'unknown')
        sample_values = col.get('sample_values', [])
        
        lines.append(f"### {name}")
        lines.append(f"- **Type**: {col_type}")
        
        if sample_values:
            samples_str = ", ".join([str(v) for v in sample_values[:5]])
            lines.append(f"- **Sample values**: {samples_str}")
        
        lines.append("")
    
    return "\n".join(lines)


def format_aggregation_results(results: List[Dict[str, Any]]) -> str:
    """
    Format aggregation results.
    
    Returns:
        Markdown-formatted results
    """
    if not results:
        return "No aggregation results."
    
    lines = ["# Aggregation Results", ""]
    
    for i, result in enumerate(results, 1):
        lines.append(f"## Result {i}")
        for key, value in result.items():
            if key != '_id':
                lines.append(f"- **{key}**: {value}")
        lines.append("")
    
    return "\n".join(lines)
