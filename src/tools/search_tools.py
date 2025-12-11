"""
Search Tools for Universal Racing Analytics.

Provides tools for:
1. Dataset search - natural language queries on racing data
2. Web search - real-time information from the internet
3. Schema exploration - understanding dataset structure
"""

from langchain_core.tools import tool
from typing import Optional, List, Dict, Any
from pathlib import Path
import pandas as pd
import json
import re


@tool
def search_dataset(query: str, table_name: str = "auto") -> str:
    """
    Search within the racing dataset using natural language.
    
    Use this tool to explore data, find specific information, or understand
    what data is available. Works with any racing dataset (F1, MotoGP, etc.).
    
    Args:
        query: Natural language query like:
            - "list all drivers in 2023"
            - "show data for Verstappen"
            - "what circuits are in the dataset"
            - "results from Bahrain GP"
            - "top 5 riders by points"
        table_name: Specific table to search, or "auto" to detect
    
    Returns:
        Relevant data, statistics, or information as a formatted string
    
    Examples:
        search_dataset("list all teams") -> Returns list of unique teams
        search_dataset("show results for Monaco 2023") -> Returns race results
        search_dataset("who won the most races") -> Returns aggregated statistics
    """
    from src.config import get_raw_data_path
    from src.tools.schema_detector import get_schema
    
    data_path = get_raw_data_path()
    schema = get_schema(data_path)
    query_lower = query.lower()
    
    results = []
    
    try:
        # Determine what kind of query this is
        is_list_query = any(kw in query_lower for kw in ["list", "show all", "what", "who", "which"])
        is_count_query = any(kw in query_lower for kw in ["how many", "count", "total"])
        is_top_query = any(kw in query_lower for kw in ["top", "best", "highest", "most", "winner"])
        is_specific_query = any(kw in query_lower for kw in ["for", "about", "at", "in"])
        
        # Extract potential filters from query
        years = re.findall(r'\b(19|20)\d{2}\b', query)
        
        # Load relevant tables based on query keywords
        tables_to_search = []
        
        if table_name != "auto":
            tables_to_search = [table_name]
        else:
            # Auto-detect relevant tables
            for table_name_key, table_info in schema.tables.items():
                columns_lower = [c.lower() for c in table_info.columns.keys()]
                
                # Check if any query keywords match column names or semantic types
                if any(kw in query_lower for kw in ["driver", "rider", "competitor"]):
                    if any("driver" in c or "rider" in c for c in columns_lower):
                        tables_to_search.append(table_name_key)
                
                if any(kw in query_lower for kw in ["team", "constructor"]):
                    if any("team" in c or "constructor" in c for c in columns_lower):
                        tables_to_search.append(table_name_key)
                
                if any(kw in query_lower for kw in ["race", "result", "position", "point"]):
                    if any("result" in c or "position" in c or "point" in c for c in columns_lower):
                        tables_to_search.append(table_name_key)
                
                if any(kw in query_lower for kw in ["circuit", "track", "venue"]):
                    if any("circuit" in c or "track" in c for c in columns_lower):
                        tables_to_search.append(table_name_key)
            
            # If no specific tables found, use all tables with results
            if not tables_to_search:
                tables_to_search = [
                    name for name, t in schema.tables.items()
                    if any("result" in c.lower() or "position" in c.lower() 
                           for c in t.columns.keys())
                ]
                if not tables_to_search:
                    tables_to_search = list(schema.tables.keys())[:3]
        
        tables_to_search = list(set(tables_to_search))[:5]  # Limit to 5 tables
        
        for tbl_name in tables_to_search:
            if tbl_name not in schema.tables:
                continue
                
            table_info = schema.tables[tbl_name]
            file_path = Path(table_info.path)
            
            if not file_path.exists():
                file_path = data_path / f"{tbl_name}.csv"
            
            if not file_path.exists():
                continue
            
            df = pd.read_csv(file_path)
            
            # Apply year filter if present
            if years:
                year_cols = [c for c in df.columns if "year" in c.lower() or "season" in c.lower()]
                if year_cols:
                    df = df[df[year_cols[0]].astype(str).isin(years)]
            
            # Apply entity filters
            entity_keywords = []
            for word in query.split():
                if len(word) > 3 and word.lower() not in ["show", "list", "what", "which", "from", "with", "about"]:
                    entity_keywords.append(word)
            
            if entity_keywords and is_specific_query:
                # Search for entities in string columns
                mask = pd.Series([False] * len(df))
                for col in df.select_dtypes(include="object").columns:
                    for kw in entity_keywords:
                        mask |= df[col].astype(str).str.lower().str.contains(kw.lower(), na=False)
                if mask.any():
                    df = df[mask]
            
            if len(df) == 0:
                continue
            
            # Format output based on query type
            if is_count_query:
                results.append(f"**{tbl_name}**: {len(df)} rows")
                
            elif is_list_query:
                # Find the most relevant column to list
                list_cols = []
                for col_name, col_info in table_info.columns.items():
                    if col_info.semantic_type in ["competitor", "team", "event", "venue"]:
                        list_cols.append(col_name)
                
                if not list_cols:
                    list_cols = [c for c in df.columns if df[c].dtype == "object"][:2]
                
                if list_cols:
                    for col in list_cols[:2]:
                        unique_vals = df[col].dropna().unique()[:20]
                        results.append(f"**{col}** ({len(df[col].unique())} unique): {list(unique_vals)}")
                        
            elif is_top_query:
                # Find numeric columns to rank by
                numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                points_col = [c for c in numeric_cols if "point" in c.lower()]
                position_col = [c for c in numeric_cols if "position" in c.lower()]
                
                rank_col = points_col[0] if points_col else (numeric_cols[0] if numeric_cols else None)
                
                if rank_col:
                    # Find entity column
                    entity_cols = [c for c in df.columns if any(kw in c.lower() for kw in ["driver", "rider", "name", "team"])]
                    if entity_cols:
                        top_df = df.groupby(entity_cols[0])[rank_col].sum().sort_values(ascending=False).head(10)
                        results.append(f"**Top by {rank_col}**:\n{top_df.to_string()}")
                    else:
                        results.append(f"**Top 10 by {rank_col}**:\n{df.nlargest(10, rank_col).to_string()}")
            
            else:
                # General query - show sample data
                results.append(f"**{tbl_name}** ({len(df)} rows, {len(df.columns)} columns):")
                results.append(f"Columns: {list(df.columns)}")
                results.append(f"Sample:\n{df.head(5).to_string()}")
        
        if results:
            return "\n\n".join(results)
        else:
            return f"No data found matching query: {query}. Available tables: {list(schema.tables.keys())}"
            
    except Exception as e:
        return f"Error searching dataset: {str(e)}"


@tool
def get_schema_info(table_name: str = "all") -> str:
    """
    Get detailed schema information about the racing dataset.
    
    Use this tool to understand what data is available, column names,
    data types, and relationships between tables.
    
    Args:
        table_name: Specific table name or "all" for complete schema
    
    Returns:
        Formatted schema information including:
        - Table names and row counts
        - Column names and types
        - Sample values
        - Detected semantic types (competitor, team, event, etc.)
    
    Examples:
        get_schema_info("all") -> Returns complete dataset overview
        get_schema_info("results") -> Returns detailed info about results table
    """
    from src.config import get_raw_data_path
    from src.tools.schema_detector import get_schema
    
    try:
        schema = get_schema(get_raw_data_path())
        
        if table_name == "all":
            return schema.get_summary()
        
        # Find matching table
        matching = [t for t in schema.tables.keys() if table_name.lower() in t.lower()]
        
        if not matching:
            return f"Table '{table_name}' not found. Available: {list(schema.tables.keys())}"
        
        results = []
        for tbl_name in matching:
            table = schema.tables[tbl_name]
            results.append(f"=== {table.name} ===")
            results.append(f"Path: {table.path}")
            results.append(f"Rows: {table.row_count:,}")
            results.append(f"Columns ({len(table.columns)}):")
            
            for col_name, col_info in table.columns.items():
                semantic = f" [{col_info.semantic_type}]" if col_info.semantic_type else ""
                samples = str(col_info.sample_values[:3]) if col_info.sample_values else "[]"
                results.append(f"  • {col_name}: {col_info.dtype}{semantic}")
                results.append(f"    Unique: {col_info.unique_count}, Nulls: {col_info.null_count}")
                results.append(f"    Samples: {samples}")
            
            if table.potential_keys:
                results.append(f"Potential keys: {table.potential_keys}")
            if table.potential_foreign_keys:
                results.append(f"Foreign keys: {table.potential_foreign_keys}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error getting schema: {str(e)}"


@tool
def search_web(query: str, search_type: str = "general") -> str:
    """
    Search the web for racing-related information.
    
    Use this to get real-time context, recent news, or background information
    about races, competitors, teams, or events.
    
    Args:
        query: Search query (e.g., "Marc Marquez 2019 injuries", 
               "Red Bull F1 2023 dominance", "MotoGP rule changes 2024")
        search_type: Type of search:
            - "general": DuckDuckGo web search
            - "wikipedia": Wikipedia article lookup
            - "news": Recent news focus
    
    Returns:
        Search results with relevant information and sources
    
    Examples:
        search_web("Verstappen 2023 season", "general") -> Recent info
        search_web("Formula One history", "wikipedia") -> Wikipedia article
    """
    try:
        if search_type == "wikipedia":
            try:
                from langchain_community.utilities import WikipediaAPIWrapper
                wiki = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=2000)
                result = wiki.run(query)
                return f"**Wikipedia: {query}**\n\n{result}"
            except ImportError:
                return f"Wikipedia search not available. Install: pip install wikipedia"
            except Exception as e:
                return f"Wikipedia error: {str(e)}"
        
        else:
            # Use DuckDuckGo
            try:
                from duckduckgo_search import DDGS
                
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                
                if not results:
                    return f"No results found for: {query}"
                
                output = [f"**Web Search: {query}**\n"]
                for i, r in enumerate(results, 1):
                    output.append(f"{i}. **{r.get('title', 'No title')}**")
                    output.append(f"   {r.get('body', 'No description')}")
                    output.append(f"   Source: {r.get('href', 'Unknown')}\n")
                
                return "\n".join(output)
                
            except ImportError:
                return "Web search not available. Install: pip install duckduckgo-search"
            except Exception as e:
                return f"Search error: {str(e)}. Try a different query."
    
    except Exception as e:
        return f"Error during web search: {str(e)}"


@tool
def explore_dataset_columns(pattern: str = "*") -> str:
    """
    Explore dataset columns matching a pattern.
    
    Use this to find columns related to specific concepts like "time", "position", etc.
    
    Args:
        pattern: Column name pattern to search for (e.g., "time", "position", "driver")
                 Use "*" to list all columns organized by table.
    
    Returns:
        List of matching columns with their table and type information
    """
    from src.config import get_raw_data_path
    from src.tools.schema_detector import get_schema
    
    try:
        schema = get_schema(get_raw_data_path())
        
        results = []
        pattern_lower = pattern.lower()
        
        for table_name, table in schema.tables.items():
            matching_cols = []
            for col_name, col_info in table.columns.items():
                if pattern == "*" or pattern_lower in col_name.lower():
                    matching_cols.append(f"  • {col_name}: {col_info.dtype}")
            
            if matching_cols:
                results.append(f"**{table_name}**:")
                results.extend(matching_cols)
                results.append("")
        
        if results:
            return "\n".join(results)
        else:
            return f"No columns matching '{pattern}' found."
            
    except Exception as e:
        return f"Error exploring columns: {str(e)}"
