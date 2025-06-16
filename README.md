# 🐕 Datadog Notebook Generation and Deployment with LLM

Generate Datadog notebooks using AI/LLM and automatically deploy them to your Datadog organization. Perfect for support cases, metric demonstrations, escalations, and rapid prototyping.

## 🌟 Features

- **AI-Powered Generation**: Uses OpenAI's GPT models to generate intelligent notebook structures
- **Modern Web Interface**: Beautiful, responsive frontend with real-time previews
- **Datadog Integration**: Direct API integration to create notebooks in your Datadog org
- **Interactive Preview**: Tabbed interface with preview, JSON view, and details
- **Download & Copy**: Export generated notebooks as JSON files
- **Example Templates**: Quick-start templates for common use cases
- **Real-time Status**: Live system health monitoring
- **Validation**: Built-in notebook structure validation
- **Flexible Configuration**: Environment variables or config file setup

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Datadog API key and Application key

### Installation

1. **Clone and install dependencies**:
```bash
git clone <repository>
cd notebook-generator
pip install -r requirements.txt
```

2. **Configure your credentials**:
```bash
# Copy example config
cp config.example.py config.py

# Edit config.py with your actual credentials
```

3. **Run the application**:
```bash
python main.py
```

The application will be available at `http://localhost:8000`

## ⚙️ Configuration

### Option 1: Config File (Recommended)
Create `config.py` from `config.example.py`:

```python
# OpenAI Configuration
OPENAI_API_KEY = "sk-your-openai-api-key"

# Datadog Configuration  
DATADOG_API_KEY = "your-datadog-api-key"
DATADOG_APP_KEY = "your-datadog-app-key"
DATADOG_BASE_URL = "https://api.datadoghq.com"

# Frontend Configuration (automatically served)
# Static files served from /static directory

# Application Configuration
PORT = 8000
DEBUG = True
```

### Option 2: Environment Variables
```bash
export OPENAI_API_KEY="sk-your-openai-api-key"
export DATADOG_API_KEY="your-datadog-api-key"
export DATADOG_APP_KEY="your-datadog-app-key"
```

### Getting API Keys

#### OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new secret key
3. Copy the key (starts with `sk-`)

#### Datadog API Keys
1. Go to [Datadog API Keys](https://app.datadoghq.com/organization-settings/api-keys)
2. Create or copy your API key
3. Go to [Application Keys](https://app.datadoghq.com/organization-settings/application-keys)
4. Create or copy your Application key

## 🎨 Frontend Features

The modern web interface includes:
- **Tabbed Results**: Preview, JSON view, and detailed information
- **Example Templates**: Click cards to quickly fill the form
- **Real-time Status**: System health indicator in header
- **Keyboard Shortcuts**: Ctrl/Cmd + Enter to generate
- **Download/Copy**: Export generated notebooks
- **Responsive Design**: Works on desktop, tablet, and mobile

## 📝 Usage

### Web Interface

1. **Open your browser**: Navigate to `http://localhost:8000`
2. **Choose a template or describe your needs**: 
   - Click example cards for quick start templates
   - Or describe what you want to analyze in detail
3. **Fill in optional details**: Add your name and email for attribution
4. **Generate**: Click "Generate Notebook" or use Ctrl/Cmd + Enter
5. **Review results**: Use the tabbed interface to:
   - 📊 **Preview**: Human-readable summary
   - 📄 **JSON**: Full notebook structure
   - ℹ️ **Details**: Metadata and configuration
6. **Export or Deploy**: 
   - Download JSON file
   - Copy to clipboard
   - Create directly in Datadog (if enabled)

### Example Templates

Click any example card to auto-fill the form:
- 🛠️ **Support Case**: Memory investigation scenarios
- 📈 **Metric Demo**: Rollup and aggregation examples  
- 🚨 **Escalation**: Comprehensive incident analysis
- ⚡ **Prototyping**: Quick microservice monitoring setup

### API Endpoints

#### Generate Notebook
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Show CPU and memory usage for troubleshooting",
    "author_name": "Your Name",
    "author_email": "your.email@company.com",
    "create_in_datadog": false
  }'
```

#### Health Check
```bash
curl "http://localhost:8000/health"
```

#### List Notebooks
```bash
curl "http://localhost:8000/notebooks?count=5"
```

## 🎯 Use Cases

### Support Cases
- Investigate high memory usage on web servers causing timeouts
- Create error analysis for failed API requests in the last hour  
- Monitor memory leaks in Java application containers
- Debug performance issues with database connections
- Analyze response time spikes in web applications

### Metric Demonstrations
- Demonstrate rollup functions with different time windows (5m, 1h, 1d)
- Show grouping examples for multi-dimensional metrics
- Create threshold examples for alerting setup
- Compare different aggregation methods (avg, sum, max, p95)
- Visualize metric correlation across services

### Escalations
- Comprehensive analysis for database slowdown incidents
- Show correlation between deployment and error rates
- Generate performance comparison before/after optimization
- Multi-service impact analysis for infrastructure issues
- Historical trend analysis for capacity planning

### Prototyping
- Quick monitoring setup for new microservice deployments
- Prototype SLA tracking for customer-facing APIs  
- Test new metric collection for infrastructure monitoring
- Create proof-of-concept dashboards for new features
- Rapid monitoring iteration for development teams

## 🏗️ Architecture

```
┌─────────────────────────────────┐    ┌─────────────────┐
│         Web Frontend            │    │   API Client    │
│   ┌─────────────────────────┐   │    │                 │
│   │  Static Files (HTML,    │   │    │                 │
│   │  CSS, JavaScript)       │   │    │                 │
│   └─────────────────────────┘   │    │                 │
└─────────────┬───────────────────┘    └─────────┬───────┘
              │                                  │
              └──────────────┬───────────────────┘
                             │
                ┌─────────────┴─────────────┐
                │      FastAPI App          │
                │   ┌─────────────────┐     │
                │   │  Static File    │     │
                │   │  Serving        │     │
                │   └─────────────────┘     │
                └─────────────┬─────────────┘
                              │
        ┌─────────────────────┼─────────────────────────┐
        │                     │                         │
┌───────▼──────────┐  ┌──────▼────────────┐  ┌─────────▼────────┐
│ Notebook         │  │ OpenAI Client     │  │ Datadog Client   │
│ Generator        │  │ (GPT-4)           │  │                  │
│ • AI Prompting   │  │ • JSON Generation │  │ • API Integration│
│ • Validation     │  │ • Context Aware   │  │ • CRUD Operations│
└──────────────────┘  └───────────────────┘  └──────────────────┘
```

## 🔧 Development

### Running in Development Mode
```bash
# Enable debug mode
export DEBUG=True

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure
```
.
├── main.py                 # FastAPI application
├── notebook_generator.py   # LLM notebook generation logic
├── datadog_client.py      # Datadog API client
├── config.example.py      # Configuration template
├── requirements.txt       # Python dependencies
├── static/                # Frontend assets
│   ├── index.html         # Main web interface
│   ├── css/
│   │   └── style.css      # Modern styling
│   └── js/
│       └── app.js         # Interactive functionality
├── NotebookExample1.json  # Example notebook structure
├── NotebookAPIUsage.json  # API documentation
└── README.md             # This file
```

### Adding New Features

1. **New Cell Types**: Extend `notebook_generator.py` with additional cell types
2. **Enhanced Prompts**: Modify the LLM prompts for better generation  
3. **Custom Metrics**: Add domain-specific metric patterns
4. **Validation Rules**: Extend validation in `datadog_client.py`
5. **Frontend Enhancements**: Update `static/` files for new UI features
6. **Example Templates**: Add new examples in `static/js/app.js`

## 🐛 Troubleshooting

### Common Issues

**1. "Notebook generator not initialized"**
- Check your OpenAI API key is set correctly
- Verify the key starts with `sk-`

**2. "Datadog client not initialized"**  
- Ensure both API key and Application key are set
- Check your Datadog organization has the correct permissions

**3. "Failed to create notebook in Datadog"**
- Verify your Datadog API credentials have notebook creation permissions
- Check the generated JSON structure with the `/validate` endpoint

**4. Slack bot not responding**
- Verify bot token and signing secret are correct
- Check bot has necessary permissions in your Slack workspace
- Ensure slash command is configured correctly

### Debug Mode
Enable debug logging by setting `DEBUG=True` in your configuration.

## 📊 Example Outputs

### Generated Notebook Structure
```json
{
  "data": {
    "type": "notebooks",
    "attributes": {
      "name": "Analysis: CPU Performance Investigation",
      "cells": [
        {
          "type": "notebook_cells",
          "attributes": {
            "definition": {
              "type": "markdown",
              "text": "# CPU Performance Investigation\n\nGenerated notebook for troubleshooting..."
            }
          }
        },
        {
          "type": "notebook_cells", 
          "attributes": {
            "definition": {
              "type": "timeseries",
              "requests": [
                {
                  "q": "avg:system.cpu.user{*}",
                  "display_type": "line"
                }
              ]
            }
          }
        }
      ]
    }
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙋‍♀️ Support

For questions or support:
- Check the troubleshooting section
- Open an issue on GitHub
- Contact the development team

---

**Team Members**: @XJ Li, @Yue Song 