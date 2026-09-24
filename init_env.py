import os
import shutil

# Copy .env.example to .env if it doesn't exist
if not os.path.exists('.env'):
    shutil.copy('.env.example', '.env')
