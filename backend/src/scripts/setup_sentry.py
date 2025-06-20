# backend/scripts/setup_sentry.py
import os
import sys

def setup_sentry_project():
    """Helper script to set up Sentry project and get DSN."""
    print("🔧 Sentry Setup Helper")
    print("=" * 50)
    
    print("1. Go to https://sentry.io and create an account")
    print("2. Create a new project for 'FastAPI'")
    print("3. Copy the DSN from the project settings")
    print("4. Add it to your .env file as SENTRY_DSN=your-dsn-here")
    print()
    
    dsn = input("Enter your Sentry DSN (or press Enter to skip): ").strip()
    
    if dsn:
        if dsn.startswith(('https://', 'http://')):
            # Update .env file
            env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            
            try:
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                # Update SENTRY_DSN line
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('SENTRY_DSN='):
                        lines[i] = f'SENTRY_DSN={dsn}\n'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'SENTRY_DSN={dsn}\n')
                
                with open(env_path, 'w') as f:
                    f.writelines(lines)
                
                print(f"✅ Sentry DSN updated in .env file")
                print("🔄 Restart your server to enable Sentry")
                
            except Exception as e:
                print(f"❌ Failed to update .env file: {e}")
                print(f"Please manually add: SENTRY_DSN={dsn}")
        else:
            print("❌ Invalid DSN format. It should start with https://")
    else:
        print("⏭️  Skipping Sentry setup. You can configure it later.")

if __name__ == "__main__":
    setup_sentry_project()