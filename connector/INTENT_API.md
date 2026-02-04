# Intent Router - LLM-Based Intent Classification

## Overview

The Intent Router is an LLM-powered system that parses free-text user questions into structured analysis intents. This eliminates the need for users to manually select analysis types through multiple clarification dialogs.

## Analysis Types

### 1. row_count - Count total rows
### 2. top_categories - Find top N items  
### 3. trend - Analyze trends over time
### 4. outliers - Detect anomalies
### 5. data_quality - Check for nulls, duplicates

## Example Queries

- "How many rows?" → row_count
- "Top products?" → top_categories  
- "Sales trends" → trend
- "Find outliers" → outliers
- "Check quality" → data_quality

## Implementation

Located in `connector/app/intent_router.py`

Uses GPT-4o-mini for fast, cost-effective intent parsing.

Returns structured JSON with:
- analysis_type
- required_params  
- target_columns

Integrated in `/chat` endpoint via `handle_message()`

## Benefits

1. Natural language queries
2. Fewer clarification dialogs
3. Intelligent routing
4. Fallback to manual selection if routing fails

See AI_MODE_CONFIGURATION.md for setup requirements.
