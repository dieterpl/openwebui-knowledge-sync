import os
import subprocess
import requests
import logging
import time
from dotenv import load_dotenv
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv(".env")

# Git and sync configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
REPO_URL = os.getenv("REPO_URL")
SYNC_DIRECTORY = os.getenv("SYNC_DIRECTORY", "/app/data")
WEBUI_URL = os.getenv("WEBUI_URL", "")
TOKEN = os.getenv("TOKEN", "your-webui-token-here")
KNOWLEDGE_ID = os.getenv("KNOWLEDGE_ID", "")

# Sync interval in seconds (default to 1 hour)
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "3600"))

# Read allowed file extensions from environment
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", ".md,.txt").split(',')

def run_command(command, cwd=None, error_message=None, hide_output=False):
    """
    Run a shell command with error handling
    :param command: Command to run
    :param cwd: Working directory for the command
    :param error_message: Custom error message if command fails
    :param hide_output: Hide command output
    :return: Command output
    """
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=hide_output, 
            text=True, 
            cwd=cwd
        )
        return result.stdout.strip() if result.stdout and not hide_output else ""
    except subprocess.CalledProcessError as e:
        error_msg = error_message or f"Command failed: {command}"
        logger.error(f"{error_msg}. Error: {e.stderr}")
        raise

def configure_git_credentials():
    """Configure git username and email"""
    if not GITHUB_USERNAME or not GITHUB_TOKEN:
        logger.warning("GitHub credentials not fully configured. Skipping git configuration.")
        return False
    
    try:
        # Configure git username and email
        run_command(f'git config --global user.name "{GITHUB_USERNAME}"', hide_output=True)
        run_command(f'git config --global user.email "{GITHUB_USERNAME}@users.noreply.github.com"', hide_output=True)
        
        logger.info("Git credentials configured")
        return True
    except Exception as e:
        logger.error(f"Failed to configure git credentials: {e}")
        return False

def get_authenticated_repo_url():
    """
    Convert repository URL to include authentication token
    Supports HTTPS URLs
    """
    if not REPO_URL:
        raise ValueError("REPO_URL must be set in .env")
    
    # If GitHub token is available, use it for authentication
    if GITHUB_TOKEN:
        parsed_url = urlparse(REPO_URL)
        authenticated_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@{parsed_url.netloc}{parsed_url.path}"
        return authenticated_url
    
    return REPO_URL

def ensure_directory(directory):
    """Ensure directory exists with proper permissions"""
    try:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")
    except PermissionError:
        logger.error(f"Permission denied creating directory: {directory}")
        raise
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        raise

def clone_or_pull_repository():
    """Clone or pull the latest changes from the repository"""
    # Check if repository URL is provided
    if not REPO_URL:
        logger.warning("No repository URL provided. Skipping repository sync.")
        return False
    
    # Configure git credentials (optional)
    configure_git_credentials()
    
    ensure_directory(SYNC_DIRECTORY)
    
    try:
        authenticated_url = get_authenticated_repo_url()
        
        # Check if repository is already cloned
        if os.path.exists(os.path.join(SYNC_DIRECTORY, '.git')):
            # Pull latest changes
            run_command('git pull', cwd=SYNC_DIRECTORY, error_message="Failed to pull repository")
            logger.info("Pulled latest changes from repository")
        else:
            # Clone repository with authentication
            run_command(f'git clone {authenticated_url} .', 
                        cwd=SYNC_DIRECTORY, 
                        error_message="Failed to clone repository")
            logger.info("Cloned repository")
        
        return True
    except Exception as e:
        logger.error(f"Repository sync failed: {e}")
        return False

def is_allowed_extension(filename):
    """Check if file has an allowed extension"""
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

def upload_to_webui(file_path):
    """Upload file to WebUI"""
    url = f'{WEBUI_URL}/api/v1/files/'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Accept': 'application/json'
    }
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        logger.info(f"Upload successful: {file_path}")
        file_info = response.json()
        add_file_to_knowledge(file_info['id'])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error uploading file {file_path}: {e}")

def add_file_to_knowledge(file_id):
    """Add file to knowledge base"""
    url = f'{WEBUI_URL}/api/v1/knowledge/{KNOWLEDGE_ID}/file/add'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {'file_id': file_id}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"File {file_id} added to knowledge base.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding file {file_id} to knowledge base: {e}")

def sync_process():
    """Synchronization process"""
    try:
        # Ensure data directory exists
        ensure_directory(SYNC_DIRECTORY)
        
        # Clone or pull repository (optional)
        repo_synced = clone_or_pull_repository()
        
        # If repository sync failed, continue with existing files
        if not repo_synced:
            logger.warning("Repository sync skipped. Proceeding with existing files.")
        
        # Upload allowed files to WebUI
        files_uploaded = 0
        for root, _, files in os.walk(SYNC_DIRECTORY):
            for filename in files:
                file_path = os.path.join(root, filename)
                # Skip git-related files and directories
                if '.git' in file_path:
                    continue
                
                # Check file extension
                if is_allowed_extension(filename):
                    upload_to_webui(file_path)
                    files_uploaded += 1
        
        logger.info(f"Sync process completed. Files uploaded: {files_uploaded}")
    
    except Exception as e:
        logger.error(f"Synchronization process failed: {e}")
        raise

def main():
    """Main loop for continuous synchronization"""
    logger.info(f"Starting continuous sync process. Interval: {SYNC_INTERVAL} seconds")
    
    while True:
        try:
            sync_process()
        except Exception as e:
            logger.error(f"Error in sync loop: {e}")
        
        # Wait before next sync attempt
        logger.info(f"Waiting {SYNC_INTERVAL} seconds before next sync...")
        time.sleep(SYNC_INTERVAL)

if __name__ == "__main__":
    main()
