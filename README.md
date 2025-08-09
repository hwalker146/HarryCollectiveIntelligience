# Podcast Analysis Application v2

A comprehensive podcast analysis platform that transforms podcast episodes into organized, searchable knowledge using AI-powered analysis. This application features multi-user support, personal knowledge bases, enhanced analysis with key quotes, and automated email digests.

## 🚀 Features

### Core Functionality
- **AI-Powered Analysis**: Comprehensive episode summaries with key insights and memorable quotes
- **Multi-User Support**: Email-based authentication and user-specific data
- **Personal Knowledge Base**: Organize insights by categories, add personal notes, and create searchable repositories
- **Reading Time Estimates**: Know exactly how long each analysis will take to read
- **Weekly Email Digests**: Receive beautiful HTML emails with your week's best insights
- **Smart Search**: Full-text search across your entire knowledge base
- **Custom Categories**: Create and manage your own podcast categories
- **Background Processing**: Celery-powered RSS monitoring and episode processing

### Enhanced Features (v2)
- **Key Quote Extraction**: AI automatically extracts the most impactful quotes from episodes
- **Knowledge Base Integration**: Transform analyses into organized learning entries
- **Category Management**: Custom color-coded categories with descriptions
- **Favorites System**: Mark important insights for quick access
- **Timeline View**: Chronological organization of your learning journey
- **Export Capabilities**: Export categories and analyses in various formats
- **Migration Support**: Seamless migration from v1 with data preservation

## 📋 Requirements

- Python 3.8+
- PostgreSQL (or SQLite for development)
- Redis (for background tasks)
- OpenAI API key (for transcription)
- Anthropic API key (for analysis)

## 🛠️ Installation

### Quick Setup

1. **Clone and Setup**
   ```bash
   cd podcast_app_v2
   python setup.py
   ```

   This will:
   - Check dependencies
   - Install Python packages
   - Create necessary directories
   - Set up environment configuration
   - Run database migration from v1 (if available)
   - Test the installation

### Manual Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

3. **Configure Database**
   ```bash
   # For PostgreSQL (production)
   DATABASE_URL=postgresql://user:password@localhost/podcast_app_v2
   
   # For SQLite (development)
   DATABASE_URL=sqlite:///./podcast_app_v2.db
   ```

4. **Run Migration** (if upgrading from v1)
   ```bash
   python migration/migrate_v1_to_v2.py
   ```

5. **Start Services**
   ```bash
   # Start Redis (required for background tasks)
   redis-server
   
   # Start the web application
   python main.py
   
   # Start background worker (optional)
   celery -A app.tasks worker --loglevel=info
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Application environment | `development` |
| `DATABASE_URL` | Database connection string | SQLite |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `OPENAI_API_KEY` | OpenAI API key for transcription | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key for analysis | Required |
| `SMTP_HOST` | Email server host | `smtp.gmail.com` |
| `SMTP_USERNAME` | Email username | Required for emails |
| `SMTP_PASSWORD` | Email password/app password | Required for emails |

### API Keys Setup

1. **OpenAI API Key**
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Add to `.env` file

2. **Anthropic API Key**
   - Visit https://console.anthropic.com/
   - Create a new API key
   - Add to `.env` file

## 📚 Usage

### Web Interface

1. **Access the Application**
   - Open http://localhost:8000
   - Create an account or sign in

2. **Add Podcasts**
   - Navigate to "Podcasts" page
   - Click "Add Podcast"
   - Enter RSS feed URL
   - Optionally add custom analysis prompt

3. **Manage Knowledge Base**
   - View organized insights in "Knowledge Base"
   - Create custom categories
   - Add personal notes and tags
   - Search across all entries

4. **Configure Settings**
   - Set up email digest preferences
   - Manage API keys
   - Configure privacy settings

### API Endpoints

The application provides RESTful API endpoints:

- `GET /api/podcasts` - List user's podcasts
- `POST /api/podcasts` - Add new podcast
- `GET /api/analysis/{id}` - Get analysis report
- `GET /api/knowledge-base` - List knowledge entries
- `POST /api/knowledge-base` - Create knowledge entry

## 🏗️ Architecture

### Backend Structure
```
app/
├── core/           # Core configuration and database
├── models/         # SQLAlchemy database models
├── services/       # Business logic services
├── api/           # FastAPI route handlers
└── tasks/         # Background task definitions
```

### Frontend Structure
```
templates/         # Jinja2 HTML templates
└── static/       # CSS, JavaScript, and assets
```

### Key Components

1. **Analysis Service** (`app/services/analysis_service.py`)
   - AI-powered episode analysis
   - Key quote extraction
   - Reading time calculation

2. **Knowledge Base Service** (`app/services/knowledge_base_service.py`)
   - Personal learning organization
   - Category management
   - Search functionality

3. **Email Service** (`app/services/email_service.py`)
   - Weekly digest generation
   - HTML email templates
   - Knowledge base highlights

4. **Migration Scripts** (`migration/`)
   - V1 to V2 data migration
   - Transcript preservation
   - User data mapping

## 🔄 Migration from v1

The application includes comprehensive migration tools to preserve your existing data:

```bash
python migration/migrate_v1_to_v2.py
```

**What gets migrated:**
- All podcasts and episodes
- Existing analysis reports
- Transcript files (smart reuse)
- RSS feed subscriptions
- User preferences

**What's new in v2:**
- Multi-user support
- Enhanced analysis with key quotes
- Personal knowledge base
- Category management
- Email digest system

## 🧪 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Development Server
```bash
# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Monitoring

The application includes built-in monitoring:

- **Health Checks**: `/health` endpoint
- **Metrics**: Background task statistics
- **Logging**: Structured logging with rotation
- **Error Tracking**: Comprehensive error handling

## 🔒 Security

### Authentication
- Email-based user authentication
- JWT token support
- Session management

### Data Protection
- API key encryption
- Secure password hashing
- CSRF protection
- Rate limiting

### Privacy
- User data isolation
- Configurable data retention
- Export functionality
- Account deletion

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t podcast-analysis-v2 .

# Run with Docker Compose
docker-compose up -d
```

### Production Considerations
- Use PostgreSQL for database
- Set up Redis cluster
- Configure reverse proxy (nginx)
- Enable SSL/HTTPS
- Set up monitoring and backups

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

1. **Migration Fails**
   - Check v1 database path in `.env`
   - Ensure proper file permissions
   - Verify SQLite file accessibility

2. **API Keys Not Working**
   - Verify keys are valid and active
   - Check API usage limits
   - Ensure proper environment variable names

3. **Email Delivery Issues**
   - Verify SMTP configuration
   - Check firewall settings
   - Use app passwords for Gmail

### Getting Help

- Check the troubleshooting section
- Review application logs in `logs/`
- Open an issue on GitHub
- Contact support team

## 🗺️ Roadmap

### Planned Features
- [ ] Mobile responsive design improvements
- [ ] Podcast discovery recommendations
- [ ] Social sharing features
- [ ] Advanced search filters
- [ ] Bulk operations
- [ ] API rate limiting
- [ ] Multi-language support
- [ ] Podcast analytics dashboard

### Performance Improvements
- [ ] Database query optimization
- [ ] Caching layer implementation
- [ ] CDN integration
- [ ] Background task optimization

---

**Built with ❤️ for podcast learners everywhere**