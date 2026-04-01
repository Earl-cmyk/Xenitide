import logging
from datetime import datetime
from ..core.config import settings
from ..services.subscription import xendit_service

logger = logging.getLogger(__name__)

def startup_checks():
    """Perform startup checks and warnings"""
    print("\n" + "="*80)
    print("🚀 XENITIDE STARTUP CHECKS")
    print("="*80)
    
    # Check required environment variables
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "JWT_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
    else:
        print("✅ All required environment variables are set")
    
    # Check Xendit configuration
    if settings.XENDIT_DONATION_LINK:
        print(f"✅ Xendit donation link configured: {settings.XENDIT_DONATION_LINK}")
        xendit_service.log_link_status()
    else:
        print("⚠️  Xendit donation link not configured")
    
    # Check subscription limits
    print(f"📊 Free tier project limit: {settings.FREE_PROJECT_LIMIT}")
    print(f"💎 Premium tier project limit: {settings.SUBSCRIPTION_REQUIRED_PROJECT_LIMIT}")
    
    # Database connection check
    if settings.DATABASE_URL:
        print("✅ Database URL configured")
        # Note: Actual connection test would be done in the database module
    else:
        print("❌ Database URL not configured")
    
    print("="*80)
    print(f"🕐 Server started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def log_startup_info():
    """Log startup information for monitoring"""
    logger.info("Xenitide application starting up")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"API prefix: {settings.API_V1_PREFIX}")
    
    if settings.XENDIT_DONATION_LINK:
        link_status = xendit_service.check_link_expiry_warning()
        if link_status:
            logger.warning(f"Xendit link warning: {link_status}")
        else:
            logger.info("Xendit link status: OK")
