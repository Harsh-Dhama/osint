"""
Telegram Bot Integration Service for OSINT Platform
Integrates with various Telegram bots for intelligence gathering
"""

import asyncio
import logging
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import User
from pathlib import Path

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Service to interact with Telegram OSINT bots"""
    
    # Bot configurations with their usernames and capabilities
    BOT_CONFIGS = {
        'youleakosint': {
            'username': '@YouLeakOsint_bot',
            'capabilities': ['deep_search', 'linked_emails', 'alternate_numbers'],
            'response_time': 30,  # seconds
        },
        'trucaller': {
            'username': '@TrucalllerBot',
            'capabilities': ['truename', 'alternate_numbers'],
            'response_time': 15,
        },
        'eyeofgod': {
            'username': '@EyeofGodBot',  # Example bot
            'capabilities': ['truename', 'social_media', 'vehicle'],
            'response_time': 20,
        },
        'getcontact': {
            'username': '@GetContactBot',  # Example bot
            'capabilities': ['truename', 'social_media'],
            'response_time': 15,
        },
        'upi_lookup': {
            'username': '@UPILookupBot',  # Example bot
            'capabilities': ['upi', 'bank_details'],
            'response_time': 25,
        },
        'aadhaar_lookup': {
            'username': '@AadhaarInfoBot',  # Example bot (Fictional - requires authorization)
            'capabilities': ['aadhaar'],
            'response_time': 30,
        },
    }
    
    def __init__(self, api_id: str, api_hash: str, session_name: str = "osint_bot_session"):
        """
        Initialize Telegram Bot Service
        
        Args:
            api_id: Telegram API ID (from my.telegram.org)
            api_hash: Telegram API Hash
            session_name: Session file name
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = Path(f"data/telegram_sessions/{session_name}")
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.pending_responses = {}
        
    async def connect(self):
        """Connect to Telegram"""
        try:
            self.client = TelegramClient(
                str(self.session_path),
                self.api_id,
                self.api_hash
            )
            
            await self.client.start()
            self.is_connected = True
            
            # Set up message handler
            @self.client.on(events.NewMessage())
            async def message_handler(event):
                await self._handle_bot_response(event)
            
            logger.info("✓ Connected to Telegram successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            logger.info("Disconnected from Telegram")
    
    async def _handle_bot_response(self, event):
        """Handle incoming messages from bots"""
        sender = await event.get_sender()
        if not isinstance(sender, User) or not sender.bot:
            return
        
        bot_username = f"@{sender.username}" if sender.username else None
        message_text = event.message.text
        
        # Store response for pending queries
        for query_id, query_info in self.pending_responses.items():
            if query_info['bot_username'] == bot_username:
                query_info['responses'].append({
                    'text': message_text,
                    'timestamp': datetime.now(),
                    'media': event.message.media
                })
                logger.info(f"Received response from {bot_username} for query {query_id}")
    
    async def query_bot(
        self,
        module: str,
        search_type: str,
        search_value: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Query a Telegram bot for information
        
        Args:
            module: Module name (e.g., 'truename', 'upi', 'aadhaar')
            search_type: 'phone' or 'email'
            search_value: Phone number or email to search
            timeout: Maximum wait time in seconds
            
        Returns:
            Dict with bot response and parsed data
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Telegram. Call connect() first.")
        
        # Find appropriate bot for this module
        bot_info = self._get_bot_for_module(module)
        if not bot_info:
            return {
                'success': False,
                'error': f'No bot configured for module: {module}',
                'module': module
            }
        
        bot_username = bot_info['username']
        query_id = f"{module}_{search_value}_{datetime.now().timestamp()}"
        
        # Initialize response tracker
        self.pending_responses[query_id] = {
            'bot_username': bot_username,
            'responses': [],
            'started_at': datetime.now()
        }
        
        try:
            # Format query based on bot type and module
            query_message = self._format_bot_query(module, search_type, search_value)
            
            # Send query to bot
            logger.info(f"Querying {bot_username} for {module}: {search_value}")
            await self.client.send_message(bot_username, query_message)
            
            # Wait for response with timeout
            start_time = datetime.now()
            while (datetime.now() - start_time).seconds < timeout:
                if self.pending_responses[query_id]['responses']:
                    break
                await asyncio.sleep(1)
            
            responses = self.pending_responses[query_id]['responses']
            
            if not responses:
                return {
                    'success': False,
                    'error': 'No response from bot within timeout',
                    'module': module,
                    'bot': bot_username
                }
            
            # Parse and structure the response
            parsed_result = self._parse_bot_response(module, responses, search_value)
            
            return {
                'success': True,
                'module': module,
                'bot': bot_username,
                'raw_responses': [r['text'] for r in responses],
                'parsed_data': parsed_result,
                'confidence': self._calculate_confidence(parsed_result)
            }
            
        except Exception as e:
            logger.error(f"Error querying bot {bot_username}: {e}")
            return {
                'success': False,
                'error': str(e),
                'module': module,
                'bot': bot_username
            }
        
        finally:
            # Clean up
            if query_id in self.pending_responses:
                del self.pending_responses[query_id]
    
    def _get_bot_for_module(self, module: str) -> Optional[Dict[str, Any]]:
        """Find the best bot for a given module"""
        for bot_name, config in self.BOT_CONFIGS.items():
            if module in config['capabilities']:
                return config
        return None
    
    def _format_bot_query(self, module: str, search_type: str, search_value: str) -> str:
        """Format query message for specific bot and module"""
        
        # Clean phone number
        if search_type == 'phone':
            clean_number = ''.join(filter(str.isdigit, search_value))
            if not clean_number.startswith('91') and len(clean_number) == 10:
                clean_number = '91' + clean_number
            search_value = clean_number
        
        # Module-specific query formats
        query_formats = {
            'truename': f"/search {search_value}",
            'social_media': f"/social {search_value}",
            'upi': f"/upi {search_value}",
            'vehicle': f"/vehicle {search_value}",
            'aadhaar': f"/aadhaar {search_value}",
            'deep_search': f"/deep {search_value}",
            'linked_emails': f"/emails {search_value}",
            'alternate_numbers': f"/altnums {search_value}",
            'bank_details': f"/bank {search_value}",
        }
        
        return query_formats.get(module, search_value)
    
    def _parse_bot_response(self, module: str, responses: List[Dict], search_value: str) -> Dict[str, Any]:
        """Parse bot response based on module type"""
        
        combined_text = "\n".join([r['text'] for r in responses])
        
        parsers = {
            'truename': self._parse_truename_response,
            'social_media': self._parse_social_response,
            'upi': self._parse_upi_response,
            'vehicle': self._parse_vehicle_response,
            'aadhaar': self._parse_aadhaar_response,
            'deep_search': self._parse_deep_search_response,
            'linked_emails': self._parse_emails_response,
            'alternate_numbers': self._parse_alternate_numbers_response,
            'bank_details': self._parse_bank_response,
        }
        
        parser = parsers.get(module, self._parse_generic_response)
        return parser(combined_text, search_value)
    
    def _parse_truename_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse true name and address information"""
        result = {
            'name': None,
            'address': None,
            'city': None,
            'state': None,
            'operator': None
        }
        
        # Extract name (various patterns)
        name_patterns = [
            r'Name[:\s]+(.+?)(?:\n|$)',
            r'Registered to[:\s]+(.+?)(?:\n|$)',
            r'Owner[:\s]+(.+?)(?:\n|$)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['name'] = match.group(1).strip()
                break
        
        # Extract address
        address_match = re.search(r'Address[:\s]+(.+?)(?:\n\n|$)', text, re.IGNORECASE | re.DOTALL)
        if address_match:
            result['address'] = address_match.group(1).strip()
        
        # Extract operator
        operator_match = re.search(r'Operator[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
        if operator_match:
            result['operator'] = operator_match.group(1).strip()
        
        return result
    
    def _parse_social_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse social media profiles"""
        result = {
            'platforms': [],
            'profiles': {}
        }
        
        # Look for platform mentions
        platforms = ['facebook', 'instagram', 'twitter', 'linkedin', 'telegram', 'whatsapp']
        for platform in platforms:
            if platform.lower() in text.lower():
                result['platforms'].append(platform)
                
                # Try to extract profile URL
                url_pattern = rf'{platform}\.com/[^\s]+'
                url_match = re.search(url_pattern, text, re.IGNORECASE)
                if url_match:
                    result['profiles'][platform] = url_match.group(0)
        
        return result
    
    def _parse_upi_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse UPI ID information"""
        result = {
            'upi_ids': [],
            'primary_upi': None,
            'bank_name': None
        }
        
        # Extract UPI IDs
        upi_pattern = r'[\w\.-]+@[\w]+'
        upi_matches = re.findall(upi_pattern, text)
        result['upi_ids'] = list(set(upi_matches))
        
        if result['upi_ids']:
            result['primary_upi'] = result['upi_ids'][0]
        
        # Extract bank name
        bank_pattern = r'(?:Bank|PSP)[:\s]+(.+?)(?:\n|$)'
        bank_match = re.search(bank_pattern, text, re.IGNORECASE)
        if bank_match:
            result['bank_name'] = bank_match.group(1).strip()
        
        return result
    
    def _parse_vehicle_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse vehicle registration information"""
        result = {
            'registration_number': None,
            'owner_name': None,
            'vehicle_type': None,
            'make_model': None,
            'registration_date': None
        }
        
        # Extract registration number
        reg_pattern = r'(?:Registration|Reg\.?\s*No\.?)[:\s]+([A-Z]{2}[\s-]?\d{1,2}[\s-]?[A-Z]{1,2}[\s-]?\d{1,4})'
        reg_match = re.search(reg_pattern, text, re.IGNORECASE)
        if reg_match:
            result['registration_number'] = reg_match.group(1).strip()
        
        # Extract owner name
        owner_pattern = r'Owner[:\s]+(.+?)(?:\n|$)'
        owner_match = re.search(owner_pattern, text, re.IGNORECASE)
        if owner_match:
            result['owner_name'] = owner_match.group(1).strip()
        
        # Extract vehicle type and model
        model_pattern = r'(?:Make|Model|Vehicle)[:\s]+(.+?)(?:\n|$)'
        model_match = re.search(model_pattern, text, re.IGNORECASE)
        if model_match:
            result['make_model'] = model_match.group(1).strip()
        
        return result
    
    def _parse_aadhaar_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse Aadhaar information (SENSITIVE)"""
        result = {
            'name': None,
            'aadhaar_linked': False,
            'dob': None,
            'address': None,
            'warning': 'This is sensitive PII data. Handle with extreme care.'
        }
        
        # Check if Aadhaar is linked
        if 'linked' in text.lower() or 'registered' in text.lower():
            result['aadhaar_linked'] = True
        
        # Extract name
        name_pattern = r'Name[:\s]+(.+?)(?:\n|$)'
        name_match = re.search(name_pattern, text, re.IGNORECASE)
        if name_match:
            result['name'] = name_match.group(1).strip()
        
        return result
    
    def _parse_deep_search_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse deep search / data breach information"""
        result = {
            'breaches_found': [],
            'leaked_data': {},
            'databases': []
        }
        
        # Look for breach mentions
        breach_pattern = r'(?:Breach|Database|Leak)[:\s]+(.+?)(?:\n|$)'
        breaches = re.findall(breach_pattern, text, re.IGNORECASE)
        result['breaches_found'] = breaches
        
        # Extract any exposed data
        email_pattern = r'[\w\.-]+@[\w\.-]+'
        emails = re.findall(email_pattern, text)
        if emails:
            result['leaked_data']['emails'] = list(set(emails))
        
        phone_pattern = r'\+?\d{10,15}'
        phones = re.findall(phone_pattern, text)
        if phones:
            result['leaked_data']['phones'] = list(set(phones))
        
        return result
    
    def _parse_emails_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse linked email addresses"""
        result = {
            'emails': [],
            'primary_email': None
        }
        
        email_pattern = r'[\w\.-]+@[\w\.-]+'
        emails = re.findall(email_pattern, text)
        result['emails'] = list(set(emails))
        
        if result['emails']:
            result['primary_email'] = result['emails'][0]
        
        return result
    
    def _parse_alternate_numbers_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse alternate phone numbers"""
        result = {
            'numbers': [],
            'operators': {}
        }
        
        phone_pattern = r'\+?\d{10,15}'
        numbers = re.findall(phone_pattern, text)
        result['numbers'] = list(set(numbers))
        
        # Try to match operators to numbers
        for number in result['numbers']:
            operator_pattern = rf'{number}[:\s]+(.+?)(?:\n|$)'
            operator_match = re.search(operator_pattern, text)
            if operator_match:
                result['operators'][number] = operator_match.group(1).strip()
        
        return result
    
    def _parse_bank_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Parse bank account information (SENSITIVE)"""
        result = {
            'banks': [],
            'account_types': [],
            'ifsc_codes': [],
            'warning': 'Highly sensitive financial data. Restricted access required.'
        }
        
        # Extract bank names
        bank_keywords = ['bank', 'sbi', 'hdfc', 'icici', 'axis', 'pnb']
        for keyword in bank_keywords:
            if keyword in text.lower():
                bank_pattern = rf'({keyword}[\w\s]+)(?:\n|$)'
                bank_match = re.search(bank_pattern, text, re.IGNORECASE)
                if bank_match:
                    result['banks'].append(bank_match.group(1).strip())
        
        # Extract IFSC codes
        ifsc_pattern = r'[A-Z]{4}0[A-Z0-9]{6}'
        ifsc_codes = re.findall(ifsc_pattern, text)
        result['ifsc_codes'] = list(set(ifsc_codes))
        
        return result
    
    def _parse_generic_response(self, text: str, search_value: str) -> Dict[str, Any]:
        """Generic parser for unknown module types"""
        return {
            'raw_text': text,
            'search_value': search_value,
            'extracted_data': {}
        }
    
    def _calculate_confidence(self, parsed_data: Dict[str, Any]) -> str:
        """Calculate confidence level based on data completeness"""
        
        # Count non-empty fields
        non_empty_fields = sum(1 for v in parsed_data.values() if v and v != [] and v != {})
        total_fields = len(parsed_data)
        
        if total_fields == 0:
            return 'low'
        
        completeness = non_empty_fields / total_fields
        
        if completeness >= 0.7:
            return 'high'
        elif completeness >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    async def query_multiple_modules(
        self,
        modules: List[str],
        search_type: str,
        search_value: str,
        delay_between_queries: int = 2
    ) -> Dict[str, Any]:
        """
        Query multiple modules sequentially
        
        Args:
            modules: List of module names
            search_type: 'phone' or 'email'
            search_value: Value to search
            delay_between_queries: Seconds to wait between queries
            
        Returns:
            Dict with results from all modules
        """
        results = {}
        
        for module in modules:
            logger.info(f"Querying module: {module}")
            result = await self.query_bot(module, search_type, search_value)
            results[module] = result
            
            # Delay between queries to avoid rate limiting
            if module != modules[-1]:
                await asyncio.sleep(delay_between_queries)
        
        return results


# Singleton instance
_telegram_service: Optional[TelegramBotService] = None


def get_telegram_service() -> Optional[TelegramBotService]:
    """Get the singleton Telegram bot service instance"""
    return _telegram_service


async def initialize_telegram_service(api_id: str, api_hash: str) -> bool:
    """Initialize the Telegram bot service"""
    global _telegram_service
    
    try:
        _telegram_service = TelegramBotService(api_id, api_hash)
        success = await _telegram_service.connect()
        return success
    except Exception as e:
        logger.error(f"Failed to initialize Telegram service: {e}")
        return False


async def shutdown_telegram_service():
    """Shutdown the Telegram bot service"""
    global _telegram_service
    
    if _telegram_service:
        await _telegram_service.disconnect()
        _telegram_service = None
