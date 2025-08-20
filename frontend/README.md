# 🚀 Claude SDK Server - Live Dashboard

A beautiful, real-time dashboard for monitoring Claude SDK Server events, performance metrics, and query processing.

![Dashboard Preview](https://img.shields.io/badge/Status-Live-green)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### Real-Time Event Streaming
- **Server-Sent Events (SSE)** for live updates
- Beautiful event cards with emoji indicators
- Automatic reconnection on connection loss
- Event filtering by type

### Performance Monitoring
- Live token usage tracking (input/output/total)
- Query processing time metrics
- Active connections counter
- Server uptime display

### Interactive Query Interface
- Send queries directly from the dashboard
- Session continuity support
- Response display with syntax highlighting
- Loading states and error handling

### Beautiful UI Design
- Gradient backgrounds with modern aesthetics
- Responsive layout for all screen sizes
- Smooth animations and transitions
- Dark/light theme support (coming soon)

## 🚀 Quick Start

### Prerequisites
- Claude SDK Server running on `http://localhost:8000`
- Python 3.7+ (for the frontend server)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Option 1: Using Make Commands

```bash
# Start the backend server first
make up

# Start the frontend dashboard
make frontend

# Or start both together
make start-all
```

### Option 2: Manual Start

```bash
# Start the backend server
docker-compose up -d

# Start the frontend server
cd frontend
python3 serve.py
```

### Option 3: Direct HTML Access

You can also open `frontend/index.html` directly in your browser, but make sure:
1. The backend server is running on `http://localhost:8000`
2. CORS is enabled in the backend

## 🎮 Usage Guide

### Sending Queries

1. Type your query in the input field
2. Press Enter or click "Send Query"
3. Watch events stream in real-time
4. View the response in the green box

### Event Filtering

Click on event type pills to filter:
- 🚀 **Query Start** - Query processing begins
- 💡 **Thinking** - Claude's reasoning process
- 🛠️ **Tools** - Tool usage events
- ⚡ **Performance** - Performance metrics
- 📊 **Tokens** - Token usage statistics

### Understanding Events

Each event shows:
- **Emoji Icon** - Visual indicator of event type
- **Event Type** - Category of the event
- **Timestamp** - When the event occurred
- **Message** - Human-readable description
- **Additional Data** - Extra context (expandable)

## 📊 Event Types Reference

| Emoji | Event Type | Description |
|-------|------------|-------------|
| 🚀 | query_start | Query processing begins |
| ✅ | query_complete | Query finished successfully |
| ❌ | query_error | Query encountered an error |
| 🔧 | session_init | Claude session initialized |
| 🤔 | thinking_start | Reasoning process begins |
| 💡 | thinking_insight | TODO or insight identified |
| 🛠️ | tool_use | Tool being called |
| 📦 | tool_result | Tool execution result |
| ⚠️ | tool_error | Tool execution failed |
| 📝 | todo_identified | TODO item found |
| 🎯 | decision_made | Key decision made |
| 📈 | step_progress | Progress update |
| ℹ️ | system_message | System information |
| 🤖 | assistant_message | Assistant response |
| ⚡ | performance_metric | Performance data |
| 📊 | token_usage | Token consumption |

## 🎨 Customization

### Changing Colors

Edit the CSS variables in `index.html`:

```css
/* Gradient background */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Event type colors */
.event-item.query_start { border-left-color: #667eea; }
.event-item.query_complete { border-left-color: #10b981; }
.event-item.thinking_insight { border-left-color: #f59e0b; }
```

### Modifying Event Filters

Add new filters in the HTML:
```html
<div class="filter-pill" data-type="your_event_type" onclick="toggleFilter(this)">
    Your Label
</div>
```

### Changing Server URL

Update the API base URL in the JavaScript:
```javascript
const API_BASE = 'http://localhost:8000/api/v1';
```

## 🛠️ Development

### Project Structure

```
frontend/
├── index.html      # Main dashboard HTML
├── serve.py        # Python HTTP server
└── README.md       # This file
```

### Adding New Features

1. **New Event Types**: Add to `eventEmojis` object
2. **New Metrics**: Add status cards in the left panel
3. **New Controls**: Add buttons in the control center
4. **New Visualizations**: Add panels to the dashboard grid

### Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🐛 Troubleshooting

### Connection Issues

**Problem**: "Disconnected" status
- **Solution**: Ensure backend is running on port 8000
- Check: `curl http://localhost:8000/api/v1/health`

### CORS Errors

**Problem**: Cross-origin errors in console
- **Solution**: Ensure CORS is enabled in backend
- The backend should allow origin `http://localhost:3000`

### No Events Appearing

**Problem**: Events not showing after query
- **Solution**: 
  1. Check browser console for errors
  2. Verify SSE endpoint: `curl http://localhost:8000/api/v1/stream/sse`
  3. Ensure filters aren't hiding events

### Performance Issues

**Problem**: Dashboard becomes slow
- **Solution**: 
  1. Clear events with "Clear Events" button
  2. Refresh the page
  3. Limit event history (default: 50 events)

## 📈 Performance Tips

1. **Event Limiting**: Dashboard keeps last 50 events in memory
2. **Auto-Reconnect**: SSE reconnects automatically on disconnect
3. **Debouncing**: Status updates every 5 seconds to reduce load
4. **Lazy Loading**: Event data expands only when clicked

## 🔮 Future Enhancements

- [ ] Dark/Light theme toggle
- [ ] Export events to JSON/CSV
- [ ] Event search and filtering by content
- [ ] Real-time chart visualizations
- [ ] Multi-session management
- [ ] Event replay functionality
- [ ] Mobile app version
- [ ] Keyboard shortcuts
- [ ] Event notifications
- [ ] Custom event webhooks

## 📝 License

MIT License - See parent LICENSE file

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- Built with vanilla JavaScript for simplicity
- Styled with pure CSS for performance
- Icons from emoji unicode characters
- Inspired by modern DevOps dashboards

---

**Made with ❤️ for Claude SDK Server**