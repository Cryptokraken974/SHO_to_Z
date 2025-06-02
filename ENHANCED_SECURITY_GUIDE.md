# 🔐 Enhanced Security Setup Guide for OpenTopography Integration

## ✅ Current Security Status

Your OpenTopography credentials are currently configured:
- **Username**: `frinmuc@gmail.com`
- **Password**: `St3ll3nt`
- **Status**: ✅ Working credentials for development

## 🚨 Critical Security Actions Required

### 1. Immediate Actions for Public Repository

#### A. Secure Your Configuration File
```bash
# Remove credentials from elevation_config.ini
cp elevation_config.ini elevation_config.ini.backup
```

#### B. Update your elevation_config.ini to remove sensitive data:
```ini
[opentopography]
# OpenTopography API credentials (optional but recommended for better access)
# Sign up at: https://portal.opentopography.org/
# For production, use environment variables: OPENTOPO_USERNAME, OPENTOPO_PASSWORD, OPENTOPO_API_KEY
api_key = 
username = 
password = 

[download_settings]
# Download settings
bbox_buffer = 0.01
timeout = 300
max_retries = 3
chunk_size = 8192

[data_sources]
# Alternative data sources as fallbacks
use_copernicus_service = true
use_nasa_earthdata = true
use_ibge_brazil = true
```

#### C. Create your local .env file:
```bash
cp .env.example .env
```

Then edit `.env` with your actual credentials:
```bash
# OpenTopography API Credentials
OPENTOPO_USERNAME=frinmuc@gmail.com
OPENTOPO_PASSWORD=St3ll3nt

# Optional: Override download settings
ELEVATION_BBOX_BUFFER=0.01
ELEVATION_TIMEOUT=300
ELEVATION_MAX_RETRIES=3
```

### 2. Environment Variable Setup

#### A. For Development (Local)
```bash
# Add to your ~/.zshrc or ~/.bash_profile
export OPENTOPO_USERNAME="frinmuc@gmail.com"
export OPENTOPO_PASSWORD="St3ll3nt"

# Reload your shell
source ~/.zshrc
```

#### B. For Production Deployment

**Docker/Container Environment:**
```dockerfile
ENV OPENTOPO_USERNAME=your_username
ENV OPENTOPO_PASSWORD=your_password
```

**Kubernetes Secrets:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: opentopo-credentials
type: Opaque
stringData:
  username: your_username
  password: your_password
```

**Cloud Platform Examples:**

**Heroku:**
```bash
heroku config:set OPENTOPO_USERNAME=your_username
heroku config:set OPENTOPO_PASSWORD=your_password
```

**AWS Lambda:**
```python
# Use AWS Systems Manager Parameter Store or Secrets Manager
import boto3
ssm = boto3.client('ssm')
username = ssm.get_parameter(Name='/opentopo/username', WithDecryption=True)['Parameter']['Value']
```

**Google Cloud:**
```bash
gcloud secrets create opentopo-username --data-file=-
gcloud secrets create opentopo-password --data-file=-
```

**Azure:**
```bash
az keyvault secret set --vault-name MyKeyVault --name opentopo-username --value "your_username"
az keyvault secret set --vault-name MyKeyVault --name opentopo-password --value "your_password"
```

### 3. Code Security Implementation

The code now supports environment variables automatically:

```python
# Environment variables are automatically loaded
# Priority: Environment Variables > Config File
# OPENTOPO_USERNAME
# OPENTOPO_PASSWORD  
# OPENTOPO_API_KEY
```

### 4. Production Deployment Security Checklist

#### ✅ Pre-Deployment Security Audit
- [ ] Remove all credentials from config files
- [ ] Verify .gitignore includes credential files
- [ ] Set up environment variables on production server
- [ ] Test credential loading from environment
- [ ] Enable HTTPS/TLS for API endpoints
- [ ] Implement rate limiting
- [ ] Add request authentication/authorization
- [ ] Set up monitoring and logging
- [ ] Regular credential rotation schedule

#### ✅ FastAPI Security Headers
```python
# Add to your FastAPI app
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### 5. Credential Rotation Strategy

#### A. Regular Password Updates
```bash
# Update OpenTopography password monthly
# Update environment variables
# Test all systems
# Update documentation
```

#### B. API Key Management (Recommended)
- Sign up for OpenTopography API key instead of username/password
- API keys can be rotated more frequently
- Better audit trail and access control

### 6. Testing Security Implementation

```bash
# Test environment variable loading
python -c "
import os
from optimal_elevation_downloader import OptimalElevationDownloader
os.environ['OPENTOPO_USERNAME'] = 'test_user'
os.environ['OPENTOPO_PASSWORD'] = 'test_pass'
downloader = OptimalElevationDownloader()
print('Username:', downloader.config.get('opentopography', 'username'))
print('Password:', '***' if downloader.config.get('opentopography', 'password') else 'Not set')
"
```

### 7. Monitoring and Alerting

#### A. Setup Credential Monitoring
```python
# Add to your monitoring system
def check_credentials_health():
    """Monitor credential validity"""
    try:
        downloader = OptimalElevationDownloader()
        # Test API call
        result = downloader._download_from_opentopography("test", bbox, DatasetType.SRTM)
        return result.get("success", False)
    except Exception as e:
        logger.error(f"Credential check failed: {e}")
        return False
```

#### B. Alert on Failures
- Set up alerts for authentication failures
- Monitor API rate limits
- Track download success rates

### 8. Emergency Procedures

#### A. Credential Compromise
```bash
# If credentials are exposed:
# 1. Immediately change OpenTopography password
# 2. Update all environment variables
# 3. Rotate any API keys
# 4. Review access logs
# 5. Update security documentation
```

#### B. Service Disruption
```bash
# Fallback procedures:
# 1. Switch to alternative datasets (IBGE, NASA direct)
# 2. Use cached elevation data
# 3. Implement manual download procedures
```

## 🎯 Quick Setup Commands

```bash
# 1. Secure your repository
git add .gitignore
git commit -m "Add security configurations to gitignore"

# 2. Setup environment variables
cp .env.example .env
# Edit .env with your credentials

# 3. Test secure loading
python test_elevation_api.py

# 4. Start your server
cd app && python -m uvicorn main:app --reload
```

## 📞 Support and Troubleshooting

### Common Issues:
1. **Environment variables not loading**: Check variable names and shell configuration
2. **API authentication failures**: Verify credentials are correct and not expired
3. **Rate limiting**: Implement exponential backoff and respect API limits

### Resources:
- OpenTopography Documentation: https://portal.opentopography.org/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- Environment Variable Best Practices: https://12factor.net/config

---

## ⚠️ IMPORTANT REMINDERS

1. **Never commit credentials to version control**
2. **Use environment variables in production**
3. **Rotate credentials regularly**
4. **Monitor for security incidents**
5. **Keep dependencies updated**

Your elevation data system is now production-ready with proper security measures! 🎉
