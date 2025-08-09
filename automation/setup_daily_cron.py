#!/usr/bin/env python3
"""
Setup Daily Cron Job for Podcast Automation
This script sets up a cron job to run the daily automation every morning
"""
import os
import subprocess
from pathlib import Path
import getpass

def create_cron_script():
    """Create the cron script that will be executed daily"""
    current_dir = Path(__file__).parent.absolute()
    python_path = subprocess.check_output(['which', 'python3']).decode().strip()
    
    cron_script_content = f"""#!/bin/bash
# Daily Podcast Processing Automation
# Generated on {subprocess.check_output(['date']).decode().strip()}

# Set working directory
cd "{current_dir}"

# Set Python path and virtual environment if needed
export PATH="{os.environ.get('PATH', '')}"

# Run the daily automation
{python_path} enhanced_daily_automation.py >> daily_automation.log 2>&1

# Check exit code and log result
if [ $? -eq 0 ]; then
    echo "$(date): Daily automation completed successfully" >> daily_automation.log
else
    echo "$(date): Daily automation failed" >> daily_automation.log
fi
"""
    
    script_path = current_dir / "daily_automation_cron.sh"
    
    with open(script_path, 'w') as f:
        f.write(cron_script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    print(f"✅ Created cron script: {script_path}")
    return script_path

def setup_cron_job(script_path, run_time="08:00"):
    """Setup the cron job"""
    hour, minute = run_time.split(':')
    
    cron_entry = f"{minute} {hour} * * * {script_path}"
    
    # Get current crontab
    try:
        current_crontab = subprocess.check_output(['crontab', '-l']).decode()
    except subprocess.CalledProcessError:
        current_crontab = ""
    
    # Check if our cron job already exists
    if 'daily_automation_cron.sh' in current_crontab:
        print("⚠️  Cron job already exists. Updating...")
        # Remove existing entry
        lines = current_crontab.split('\n')
        lines = [line for line in lines if 'daily_automation_cron.sh' not in line]
        current_crontab = '\n'.join(lines)
    
    # Add new cron entry
    new_crontab = current_crontab.rstrip() + '\n' + cron_entry + '\n'
    
    # Write new crontab
    process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
    process.communicate(input=new_crontab.encode())
    
    if process.returncode == 0:
        print(f"✅ Cron job scheduled for {run_time} daily")
        print(f"📝 Command: {cron_entry}")
        return True
    else:
        print("❌ Failed to schedule cron job")
        return False

def create_env_template():
    """Create .env template file"""
    env_template = """# Podcast Automation Environment Variables
# Copy this to .env and fill in your values

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
DAILY_EMAIL_RECIPIENT=harris.m.walker@gmail.com

# Google Drive (optional)
# Download credentials.json from Google Cloud Console
# Place it in the same directory as this file

# OpenAI API Key (for analysis)
OPENAI_API_KEY=your_openai_api_key

# Database Path (optional, defaults to podcast_app_v2.db)
DATABASE_PATH=podcast_app_v2.db
"""
    
    env_file = Path(__file__).parent / ".env.template"
    
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print(f"✅ Created environment template: {env_file}")
    print("📝 Copy this to .env and configure your settings")

def test_automation():
    """Test the automation script"""
    current_dir = Path(__file__).parent.absolute()
    python_path = subprocess.check_output(['which', 'python3']).decode().strip()
    
    print("🧪 Testing automation script...")
    
    # Run a dry run
    result = subprocess.run([
        python_path, 
        str(current_dir / "enhanced_daily_automation.py")
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode == 0:
        print("✅ Automation test completed successfully")
        return True
    else:
        print("❌ Automation test failed")
        return False

def main():
    """Main setup function"""
    print("🔧 Setting up Daily Podcast Automation")
    print("=" * 50)
    
    # Create environment template
    create_env_template()
    
    # Create cron script
    script_path = create_cron_script()
    
    # Ask user for preferred time
    print("\n⏰ When would you like the automation to run daily?")
    run_time = input("Enter time (HH:MM format, default 08:00): ").strip()
    
    if not run_time:
        run_time = "08:00"
    
    # Validate time format
    try:
        hour, minute = run_time.split(':')
        if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
            raise ValueError("Invalid time")
    except:
        print("❌ Invalid time format. Using default 08:00")
        run_time = "08:00"
    
    # Setup cron job
    if setup_cron_job(script_path, run_time):
        print(f"\n✅ Daily automation scheduled for {run_time}")
    
    # Test automation
    print(f"\n🧪 Would you like to test the automation now? (y/n): ", end="")
    if input().lower().startswith('y'):
        test_automation()
    
    print("\n📋 Next Steps:")
    print("1. Configure .env file with your email and API credentials")
    print("2. Set up Google Drive integration (optional)")
    print("3. Check that all required Python packages are installed")
    print("4. Monitor daily_automation.log for execution logs")
    print(f"\n📅 Your automation will run daily at {run_time}")
    print("🔍 Check cron jobs with: crontab -l")
    print("📝 View logs with: tail -f daily_automation.log")

if __name__ == "__main__":
    main()