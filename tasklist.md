# Migration from AutoGen to LangGraph: Task List

## Overview
This document outlines the steps needed to migrate our YouTube Content Repurposer from AutoGen to LangGraph. LangGraph offers better state management, more flexible workflows, and improved coordination between agents.

## Migration Steps

### 1. Set Up Project for LangGraph
- [ ] Add LangGraph to requirements.txt (`langgraph`)
- [ ] Update virtual environment with new dependencies
- [ ] Keep existing API keys and environment variables

### 2. Design LangGraph Workflow Architecture
- [ ] Define nodes and edges of the graph-based workflow
- [ ] Map out state management system for content data
- [ ] Design proper error handling and recovery paths

### 3. Create Core State Management
- [ ] Define a proper TypedDict for the graph state
- [ ] Implement state transitions between processing steps
- [ ] Add utilities for state inspection and debugging

### 4. Implement LangGraph Nodes
- [ ] Convert YouTube extraction logic to LangGraph node
- [ ] Convert transcript refinement logic to LangGraph node
- [ ] Convert topic generation logic to LangGraph node 
- [ ] Convert blog/LinkedIn/Twitter content generation to nodes
- [ ] **Fix content generation output counts** (1 blog, 2 LinkedIn, 5 Twitter posts)
- [ ] Convert editing functionality to nodes
- [ ] Implement output compilation node

### 5. Build Graph Connections
- [ ] Connect nodes with appropriate conditional routing
- [ ] Implement entry and exit points
- [ ] Add proper state transitions between steps
- [ ] Set up error handling paths

### 6. Update Tool Functions
- [ ] Adapt existing tool functions for LangGraph compatibility
- [ ] Ensure all API interactions work with LangGraph's async nature
- [ ] Update function signatures to handle LangGraph state objects

### 7. Update Main Application
- [ ] Modify main.py to initialize and run the LangGraph workflow
- [ ] Implement proper progress tracking and logging
- [ ] Add visualization of the workflow (optional)

### 8. Testing and Validation
- [ ] Create test cases for each node
- [ ] Test full workflow with sample YouTube URLs
- [ ] Validate outputs against expected content specifications
- [ ] Compare performance with previous AutoGen implementation
- [ ] **Verify correct generation counts** (1 blog, 2 LinkedIn, 5 Twitter posts)

### 9. UI and User Experience
- [ ] Update any UI elements to show graph progress
- [ ] Implement checkpointing for long-running processes
- [ ] Add better error messages and recovery options

### 10. Documentation and Deployment
- [ ] Document the new architecture
- [ ] Update usage instructions
- [ ] Create deployment guide for the updated system

## Expected Benefits
- More visible workflow with better state tracking
- Improved error handling and recovery
- Better parallelization where possible
- Clearer separation of concerns between components
- More maintainable and extensible architecture 
- **Correct content generation counts and resource optimization** 