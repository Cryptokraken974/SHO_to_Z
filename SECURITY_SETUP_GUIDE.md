# Security Configuration Guide

## 🔐 CREDENTIALS SECURITY SETUP

Your OpenTopography credentials have been configured in `elevation_config.ini`. Here's how to keep them secure when deploying publicly:

### 1. Immediate Security Steps

#### A. Add to .gitignore
```bash
# Add these lines to .gitignore
elevation_config.ini
*.ini
.env
.env.local
config/secrets.ini
```

#### B. Remove from Git History (if already committed)
```bash
# Remove file from git tracking
git rm --cached elevation_config.ini

# If already in git history, remove completely:
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch elevation_config.ini' \
  --prune-empty --tag-name-filter cat -- --all
```

### 2. Production Deployment Options

#### Option A: Environment Variables (Recommended)
Create a `.env` file for local development:
```bash
# .env (DO NOT COMMIT)
OPENTOPOGRAPHY_USERNAME=frinmuc@gmail.com
OPENTOPOGRAPHY_PASSWORD=St3ll3nt
OPENTOPOGRAPHY_API_KEY=
```

#### Option B: Docker Secrets
```dockerfile
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    secrets:
      - opentopography_username
      - opentopography_password
    environment:
      - OPENTOPOGRAPHY_USERNAME_FILE=/run/secrets/opentopography_username
      - OPENTOPOGRAPHY_PASSWORD_FILE=/run/secrets/opentopography_password

secrets:
  opentopography_username:
    external: true
  opentopography_password:
    external: true
```

#### Option C: Cloud Provider Secrets
- **AWS**: Use AWS Secrets Manager or Systems Manager Parameter Store
- **Azure**: Use Azure Key Vault
- **Google Cloud**: Use Secret Manager
- **Heroku**: Use Config Vars

### 3. Code Modifications for Security

The optimal elevation downloader needs to be modified to read from environment variables as a fallback.

### 4. Repository Preparation

#### A. Create example config file
```ini
# elevation_config.example.ini
[opentopography]
# OpenTopography API credentials
# Sign up at: https://portal.opentopography.org/
api_key = your_api_key_here
username = your_username_here
password = your_password_here

[download_settings]
bbox_buffer = 0.01
timeout = 300
max_retries = 3
chunk_size = 8192

[data_sources]
use_copernicus_service = true
use_nasa_earthdata = true
use_ibge_brazil = true
```

#### B. Add setup instructions to README
```markdown
## Setup Instructions

1. Copy the example config file:
   ```bash
   cp elevation_config.example.ini elevation_config.ini
   ```

2. Add your OpenTopography credentials to `elevation_config.ini`

3. Or set environment variables:
   ```bash
   export OPENTOPOGRAPHY_USERNAME="your_username"
   export OPENTOPOGRAPHY_PASSWORD="your_password"
   ```
```

### 5. Security Best Practices

#### A. Credential Rotation
- Change passwords regularly
- Use API keys instead of passwords when possible
- Monitor access logs

#### B. Access Control
- Use read-only credentials when possible
- Implement IP whitelisting if supported
- Monitor for unusual usage patterns

#### C. Development Security
- Never commit credentials to version control
- Use different credentials for development/production
- Implement credential validation at startup

### 6. Deployment Checklist

- [ ] Credentials removed from code
- [ ] Environment variables configured
- [ ] .gitignore updated
- [ ] Example config file created
- [ ] Documentation updated
- [ ] Secrets manager configured (production)
- [ ] Access monitoring enabled
- [ ] Credential rotation schedule set

### 7. Emergency Procedures

If credentials are accidentally committed:
1. Immediately change the password at OpenTopography
2. Remove from git history using filter-branch
3. Force push the cleaned repository
4. Notify team members to re-clone the repository
5. Audit who had access to the exposed credentials

## Current Status

✅ Credentials configured in local `elevation_config.ini`
⚠️  File is not yet in .gitignore
❌ Environment variable fallback not implemented
❌ Example config file not created

## Next Steps

1. Implement environment variable support in the code
2. Add .gitignore entries
3. Create example config file
4. Test with environment variables
5. Document deployment procedures
