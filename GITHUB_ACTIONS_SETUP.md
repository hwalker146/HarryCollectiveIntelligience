# 🚀 GitHub Actions Cloud Automation Setup

Your podcast processing will run automatically every day at 6 AM EDT on GitHub's cloud infrastructure - completely free!

## 📋 Prerequisites

1. Your project is already in a GitHub repository
2. You have admin access to the repository

## 🔧 Step-by-Step Setup

### 1. Push Code to GitHub

First, make sure all your latest code is pushed to GitHub:

```bash
cd /Users/hwalker/Desktop/podcast_processor/podcast_app_v2

# Initialize git if not already done
git init
git add .
git commit -m "Add GitHub Actions automation for podcast processing"

# Add your GitHub repo (replace with your actual repo URL)
git remote add origin https://github.com/yourusername/podcast-processor.git
git push -u origin main
```

### 2. Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these **Repository secrets**:

#### API Keys
- **OPENAI_API_KEY**: Your OpenAI API key (for Whisper transcription)
- **ANTHROPIC_API_KEY**: Your Anthropic Claude API key (for analysis)

#### Email Configuration  
- **EMAIL_USER**: `hwalker146@outlook.com`
- **EMAIL_PASSWORD**: Your Outlook app password

#### Google Drive Integration
- **GOOGLE_CREDENTIALS_JSON**: Copy the entire contents of your `credentials.json` file
- **GOOGLE_TOKEN_JSON**: Copy the entire contents of your `token.json` file

### 3. Get Your Google Credentials

#### For GOOGLE_CREDENTIALS_JSON:
```bash
cat /Users/hwalker/Desktop/podcast_processor/podcast_app_v2/credentials.json
```
Copy the entire output and paste it as the `GOOGLE_CREDENTIALS_JSON` secret.

#### For GOOGLE_TOKEN_JSON:
```bash
cat /Users/hwalker/Desktop/podcast_processor/podcast_app_v2/token.json
```
Copy the entire output and paste it as the `GOOGLE_TOKEN_JSON` secret.

## ✅ How It Works

### Automatic Daily Processing
- **When**: Every day at 6:00 AM EDT (10:00 AM UTC)
- **What**: Runs your `improved_daily_automation.py` script
- **Where**: GitHub's cloud servers (Ubuntu Linux)

### Manual Triggering
You can also manually trigger the workflow:
1. Go to your GitHub repo → Actions tab
2. Click "Daily Podcast Processing" 
3. Click "Run workflow"

### Workflow Steps
1. **Setup**: Installs Python, ffmpeg, and all dependencies
2. **Authentication**: Sets up Google Drive credentials
3. **Database**: Downloads the latest database from previous runs
4. **Processing**: Runs your podcast automation
5. **Storage**: Uploads updated database and logs for next run

## 📊 Monitoring

### View Processing Status
- Go to GitHub repo → Actions tab
- See all workflow runs, success/failure status
- View detailed logs for each step

### Download Results
- Updated database is automatically saved for next run
- Processing logs are available for download
- Logs kept for 7 days, database for 30 days

## 💰 Cost

**Completely FREE** - GitHub Actions provides:
- 2,000 minutes/month for private repos (unlimited for public)
- Your workflow takes ~30-60 minutes = ~30 runs/month possible
- More than enough for daily automation

## 🔧 Troubleshooting

### If Workflow Fails

1. **Check the logs**: Go to Actions → Failed run → Click step to see error
2. **Common issues**:
   - Missing secrets (API keys not set)
   - Google authentication expired (refresh token.json)
   - API rate limits (usually temporary)

### Update Database Locally
If you make changes locally, you can upload your latest database:
1. Go to Actions → Latest successful run
2. Download the database artifact
3. Replace your local file

### Re-authenticate Google Drive
If Google authentication expires:
1. Run authentication locally: `python auth.py`
2. Copy new `token.json` contents to `GOOGLE_TOKEN_JSON` secret

## 🎯 What This Solves

✅ **No more computer sleep issues** - Runs in the cloud  
✅ **No more manual triggering** - Completely automated  
✅ **Always available** - Never depends on your computer  
✅ **Free and reliable** - GitHub's enterprise infrastructure  
✅ **Easy monitoring** - Web dashboard with detailed logs  

## 📞 Next Steps

1. Set up the GitHub secrets above
2. Push your code if not already done  
3. The workflow will automatically run tomorrow at 6 AM EDT
4. Check the Actions tab to confirm it worked

Your podcast processing is now fully automated in the cloud! 🎉