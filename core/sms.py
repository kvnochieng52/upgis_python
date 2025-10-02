"""
SMS Notification System for UPG Management
Supports multiple SMS providers with fallback capabilities
"""

import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
import requests
import json

logger = logging.getLogger(__name__)


class SMSProvider:
    """Base SMS provider class"""

    def send_sms(self, phone_number, message):
        """Send SMS message to phone number"""
        raise NotImplementedError


class AfricasTalkingSMSProvider(SMSProvider):
    """Africa's Talking SMS provider for Kenya"""

    def __init__(self):
        self.api_key = getattr(settings, 'AFRICAS_TALKING_API_KEY', '')
        self.username = getattr(settings, 'AFRICAS_TALKING_USERNAME', 'sandbox')
        self.base_url = 'https://api.africastalking.com/version1/messaging'

    def send_sms(self, phone_number, message):
        """Send SMS via Africa's Talking API"""
        if not self.api_key:
            logger.warning("Africa's Talking API key not configured")
            return False

        headers = {
            'apiKey': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

        data = {
            'username': self.username,
            'to': phone_number,
            'message': message,
            'from': getattr(settings, 'SMS_SENDER_ID', 'UPG_SYS')
        }

        try:
            response = requests.post(self.base_url, headers=headers, data=data)
            response.raise_for_status()

            result = response.json()
            if result.get('SMSMessageData', {}).get('Recipients'):
                logger.info(f"SMS sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"SMS failed to send to {phone_number}: {result}")
                return False

        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            return False


class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider as fallback"""

    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

    def send_sms(self, phone_number, message):
        """Send SMS via Twilio API"""
        if not all([self.account_sid, self.auth_token, self.from_number]):
            logger.warning("Twilio credentials not configured")
            return False

        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)

            message = client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )

            logger.info(f"SMS sent successfully via Twilio to {phone_number}")
            return True

        except ImportError:
            logger.error("Twilio library not installed. Install with: pip install twilio")
            return False
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return False


class ConsoleSMSProvider(SMSProvider):
    """Console SMS provider for development/testing"""

    def send_sms(self, phone_number, message):
        """Print SMS to console instead of sending"""
        print(f"\n--- SMS NOTIFICATION ---")
        print(f"To: {phone_number}")
        print(f"Message: {message}")
        print(f"Timestamp: {timezone.now()}")
        print(f"--- END SMS ---\n")
        return True


class SMSService:
    """Main SMS service with provider management"""

    def __init__(self):
        self.providers = []
        self._setup_providers()

    def _setup_providers(self):
        """Setup SMS providers based on settings"""
        # Primary provider: Africa's Talking (for Kenya)
        self.providers.append(AfricasTalkingSMSProvider())

        # Fallback provider: Twilio
        self.providers.append(TwilioSMSProvider())

        # Development provider: Console
        if settings.DEBUG:
            self.providers.append(ConsoleSMSProvider())

    def send_sms(self, phone_number, message, template_name=None, context=None):
        """Send SMS with fallback providers"""
        # Format phone number for Kenya (+254)
        formatted_number = self._format_kenyan_number(phone_number)

        # Use template if provided
        if template_name and context:
            message = render_to_string(f'sms/{template_name}', context)

        # Truncate message if too long (SMS limit is usually 160 chars)
        if len(message) > 160:
            message = message[:157] + '...'

        # Try each provider until one succeeds
        for provider in self.providers:
            try:
                if provider.send_sms(formatted_number, message):
                    # Log successful SMS
                    self._log_sms(formatted_number, message, True, provider.__class__.__name__)
                    return True
            except Exception as e:
                logger.error(f"Provider {provider.__class__.__name__} failed: {e}")
                continue

        # All providers failed
        self._log_sms(formatted_number, message, False, 'All providers failed')
        return False

    def _format_kenyan_number(self, phone_number):
        """Format phone number for Kenyan SMS"""
        # Remove all non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))

        # Handle different Kenyan number formats
        if clean_number.startswith('254'):
            return f'+{clean_number}'
        elif clean_number.startswith('0'):
            return f'+254{clean_number[1:]}'
        elif len(clean_number) == 9:
            return f'+254{clean_number}'
        else:
            return f'+{clean_number}'

    def _log_sms(self, phone_number, message, success, provider):
        """Log SMS attempt"""
        try:
            from .models import SMSLog
            SMSLog.objects.create(
                phone_number=phone_number,
                message=message,
                success=success,
                provider=provider,
                sent_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Failed to log SMS: {e}")

    def send_training_reminder(self, household, training):
        """Send training reminder SMS"""
        context = {
            'household': household,
            'training': training,
            'date': training.start_date,
            'location': training.location,
        }

        return self.send_sms(
            household.primary_contact_phone,
            template_name='training_reminder.txt',
            context=context
        )

    def send_bulk_training_reminders(self, training):
        """Send training reminders to all enrolled households"""
        success_count = 0
        enrolled_households = training.enrolled_households.filter(
            enrollment_status='enrolled'
        ).select_related('household')

        for enrollment in enrolled_households:
            if self.send_training_reminder(enrollment.household, training):
                success_count += 1

        return success_count, enrolled_households.count()


# Global SMS service instance
sms_service = SMSService()