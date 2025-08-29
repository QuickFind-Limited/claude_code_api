# Real-time Streaming Chatbot Test Guide

## Setup

1. **Start the server** (if not already running):
   ```bash
   make up
   ```

2. **Start the chatbot interface**:
   ```bash
   make chatbot
   ```

3. **Open the chatbot**:
   - Navigate to: http://localhost:3001/chatbot.html

## Test Cases for Real-time Streaming

### Test 1: Simple Query (No Tools)
**Query**: "What is 2+2?"

**Expected Real-time Behavior**:
- Typing indicator appears immediately
- Response streams in character by character
- Token usage updates in real-time
- Metadata box appears after completion

### Test 2: Tool Usage Query
**Query**: "Analyze the file test_simple.py and explain what it does"

**Expected Real-time Behavior**:
- Typing indicator appears
- 🛠️ Tool indicator shows "Read" when file is being read
- Live metadata updates showing:
  - Tool name and status
  - Token count incrementing
- Response streams after tool completes
- Final metadata box shows all tools used

### Test 3: Multiple Tools Query
**Query**: "Create a file called hello.txt with 'Hello World' content, then read it back to confirm"

**Expected Real-time Behavior**:
- Multiple tool indicators appear sequentially:
  - 🛠️ "Write" tool indicator
  - 🛠️ "Read" tool indicator
- Each tool shows completion status
- Token count updates after each tool
- Final metadata shows all tools in order

### Test 4: Complex Thinking Query
**Query**: "Help me design a REST API for a todo list application with CRUD operations"

**Expected Real-time Behavior**:
- 🤔 Thinking indicator may appear
- Multiple consideration points shown
- Token usage updates progressively
- Response streams with formatted content
- Metadata shows thinking time (if applicable)

## Visual Indicators to Watch For

### During Processing:
1. **Typing Indicator**: Animated dots showing processing
2. **Tool Usage Pills**: Live updates like "🛠️ Using: Read"
3. **Token Counter**: Real-time increment in the metrics panel
4. **Event Stream**: Live events in the console (if dev tools open)

### After Completion:
1. **Metadata Box**: Collapsible section with:
   - Response time
   - Tools used (with names and count)
   - Token usage breakdown
   - Thinking insights (if any)

## How to Verify Real-time Features

### Method 1: Visual Observation
1. Send a query that uses tools
2. Watch for live indicators during processing
3. Verify metadata appears after completion
4. Click metadata toggle to expand/collapse

### Method 2: Browser Console
1. Open browser developer console (F12)
2. Watch for SSE events being logged
3. Look for event types:
   - `tool_use`
   - `tool_result`
   - `token_usage`
   - `thinking_start`
   - `query_complete`

### Method 3: Network Tab
1. Open browser developer tools
2. Go to Network tab
3. Filter by "EventStream"
4. Send a query
5. Watch SSE connection and events flowing

## Common Issues and Solutions

### Issue: No real-time updates
**Solution**: 
- Check SSE connection in Network tab
- Verify server is running (`make up`)
- Check browser console for errors

### Issue: Metadata not showing
**Solution**:
- Wait for query to complete fully
- Check if response has metadata
- Look for JavaScript errors in console

### Issue: Tools not displaying
**Solution**:
- Use queries that actually require tools
- Check if tools are enabled on server
- Verify SSE events include tool_use

## Test Queries for Different Features

### For File Operations:
```
List all Python files in the src directory
```

### For Code Analysis:
```
Analyze the main.py file and explain its architecture
```

### For Creative Tasks:
```
Create a simple Python script that generates fibonacci numbers
```

### For Complex Reasoning:
```
Compare REST and GraphQL APIs, which is better for a mobile app?
```

## Success Criteria

✅ **All tests pass when**:
1. Tool usage appears in real-time during processing
2. Token counts update live as response generates
3. Metadata box appears with complete information
4. No duplicate messages in chat history
5. Session persists across page refreshes
6. New session button clears history properly

## Next Steps

After testing:
1. Try different model selections (Opus vs Sonnet)
2. Test session persistence by refreshing the page
3. Start a new session and verify clean state
4. Test with longer, more complex queries
5. Monitor performance with many messages