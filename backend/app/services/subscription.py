from datetime import datetime, timedelta
from typing import Optional
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing subscription tiers and project limits"""
    
    @staticmethod
    def get_user_project_limit(user_tier: str = "free") -> int:
        """Get project limit based on user subscription tier"""
        if user_tier == "free":
            return settings.FREE_PROJECT_LIMIT
        elif user_tier == "premium":
            return settings.SUBSCRIPTION_REQUIRED_PROJECT_LIMIT
        else:
            return settings.FREE_PROJECT_LIMIT
    
    @staticmethod
    def can_create_project(user_tier: str, current_project_count: int) -> tuple[bool, str]:
        """Check if user can create more projects"""
        limit = SubscriptionService.get_user_project_limit(user_tier)
        
        if current_project_count >= limit:
            if user_tier == "free":
                return False, f"Free tier limit reached ({limit} projects). Upgrade to premium for unlimited projects."
            else:
                return False, f"Project limit reached ({limit} projects)."
        
        return True, f"You can create {limit - current_project_count} more projects."
    
    @staticmethod
    def get_subscription_features(user_tier: str = "free") -> dict:
        """Get features available for subscription tier"""
        features = {
            "free": {
                "projects": settings.FREE_PROJECT_LIMIT,
                "ai_actions": 100,
                "storage_mb": 100,
                "deployments": 10,
                "database_tables": 5,
                "priority_support": False
            },
            "premium": {
                "projects": settings.SUBSCRIPTION_REQUIRED_PROJECT_LIMIT,
                "ai_actions": "unlimited",
                "storage_mb": "unlimited",
                "deployments": "unlimited", 
                "database_tables": "unlimited",
                "priority_support": True
            }
        }
        return features.get(user_tier, features["free"])


class XenditService:
    """Service for managing Xendit payment links and expiry monitoring"""
    
    @staticmethod
    def check_link_expiry_warning() -> Optional[str]:
        """Check if Xendit link needs renewal and return warning message"""
        if not settings.XENDIT_DONATION_LINK:
            return None
        
        # For demo purposes, we'll use a fixed creation date
        # In production, you'd store the creation date in your database
        link_creation_date = datetime(2024, 1, 1)  # Replace with actual creation date
        expiry_days = settings.XENDIT_LINK_EXPIRY_DAYS
        expiry_date = link_creation_date + timedelta(days=expiry_days)
        
        days_until_expiry = (expiry_date - datetime.now()).days
        
        if days_until_expiry <= 5:
            return f"⚠️  WARNING: Xendit donation link expires in {days_until_expiry} days! Please renew your payment link."
        elif days_until_expiry <= 0:
            return f"🚨 CRITICAL: Xendit donation link EXPIRED {abs(days_until_expiry)} days ago! Please update immediately."
        
        return None
    
    @staticmethod
    def log_link_status():
        """Log current Xendit link status"""
        warning = XenditService.check_link_expiry_warning()
        
        if warning:
            logger.warning(f"XENDIT LINK WARNING: {warning}")
            print(f"\n{'='*60}")
            print(f"🔔 XENDIT LINK NOTIFICATION")
            print(f"{'='*60}")
            print(warning)
            print(f"Current link: {settings.XENDIT_DONATION_LINK}")
            print(f"Expiry period: {settings.XENDIT_LINK_EXPIRY_DAYS} days")
            print(f"{'='*60}\n")
        else:
            logger.info("Xendit link status: OK")
    
    @staticmethod
    def get_donation_link() -> Optional[str]:
        """Get the current donation link"""
        return settings.XENDIT_DONATION_LINK
    
    @staticmethod
    def is_link_active() -> bool:
        """Check if the donation link is still active"""
        warning = XenditService.check_link_expiry_warning()
        return warning is None or "EXPIRED" not in warning


# Initialize services
subscription_service = SubscriptionService()
xendit_service = XenditService()
