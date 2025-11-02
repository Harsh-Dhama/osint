"""
Number/Email Tracker Service
Coordinates bot queries, credit management, and result processing
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.database.models import (
    NumberEmailSearch, NumberEmailResult, User, Case, 
    CreditTransaction, AuditLog
)
from backend.schemas.tracker import (
    TrackerModule, MODULE_CREDITS, SearchType, ConfidenceLevel
)
from backend.modules.telegram_bot_service import get_telegram_service

logger = logging.getLogger(__name__)


class TrackerService:
    """Service for number/email tracking with bot integration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.telegram_service = get_telegram_service()
    
    def calculate_credits_required(self, modules: List[TrackerModule]) -> int:
        """Calculate total credits required for selected modules"""
        total = 0
        for module in modules:
            total += MODULE_CREDITS.get(module, 0)
        return total
    
    def check_user_credits(self, user_id: int, required_credits: int) -> tuple[bool, int]:
        """
        Check if user has sufficient credits
        
        Returns:
            (has_enough, current_balance)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, 0
        
        return user.credits >= required_credits, user.credits
    
    def deduct_credits(
        self,
        user_id: int,
        amount: int,
        search_id: int,
        description: str
    ) -> bool:
        """
        Deduct credits from user account
        
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or user.credits < amount:
                return False
            
            balance_before = user.credits
            user.credits -= amount
            balance_after = user.credits
            
            # Create transaction record
            transaction = CreditTransaction(
                user_id=user_id,
                transaction_type="debit",
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                module="tracker",
                reference_id=search_id,
                description=description
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(f"Deducted {amount} credits from user {user_id}. New balance: {balance_after}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deduct credits: {e}")
            self.db.rollback()
            return False
    
    def add_credits(
        self,
        user_id: int,
        amount: int,
        admin_id: int,
        description: str = None
    ) -> bool:
        """
        Add credits to user account (admin function)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            balance_before = user.credits
            user.credits += amount
            balance_after = user.credits
            
            # Create transaction record
            transaction = CreditTransaction(
                user_id=user_id,
                transaction_type="credit",
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                module="tracker",
                description=description or f"Credit top-up by admin",
                created_by=admin_id
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            logger.info(f"Added {amount} credits to user {user_id}. New balance: {balance_after}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add credits: {e}")
            self.db.rollback()
            return False
    
    async def create_search(
        self,
        user_id: int,
        case_id: int,
        search_type: SearchType,
        search_value: str,
        modules: List[TrackerModule]
    ) -> tuple[Optional[NumberEmailSearch], str]:
        """
        Create a new tracker search
        
        Returns:
            (search_object, error_message)
        """
        try:
            # Calculate credits
            credits_required = self.calculate_credits_required(modules)
            
            # Check credits
            has_enough, current_balance = self.check_user_credits(user_id, credits_required)
            if not has_enough:
                return None, f"Insufficient credits. Required: {credits_required}, Available: {current_balance}"
            
            # Verify case exists
            case = self.db.query(Case).filter(Case.id == case_id).first()
            if not case:
                return None, "Case not found"
            
            # Create search record
            search = NumberEmailSearch(
                user_id=user_id,
                case_id=case_id,
                search_type=search_type.value,
                search_value=search_value,
                credits_used=0,  # Will be updated as modules complete
                status="pending",
                modules_requested=",".join([m.value for m in modules])
            )
            
            self.db.add(search)
            self.db.commit()
            self.db.refresh(search)
            
            # Log action
            audit_log = AuditLog(
                user_id=user_id,
                action="tracker_search_created",
                module="tracker",
                details=json.dumps({
                    'search_id': search.id,
                    'search_type': search_type.value,
                    'search_value': search_value,
                    'modules': [m.value for m in modules],
                    'credits_required': credits_required
                })
            )
            self.db.add(audit_log)
            self.db.commit()
            
            logger.info(f"Created search {search.id} for user {user_id}")
            return search, ""
            
        except Exception as e:
            logger.error(f"Failed to create search: {e}")
            self.db.rollback()
            return None, str(e)
    
    async def execute_search(
        self,
        search_id: int,
        modules: List[TrackerModule]
    ) -> Dict[str, Any]:
        """
        Execute the tracker search by querying bots
        
        Returns:
            Dict with execution results
        """
        search = self.db.query(NumberEmailSearch).filter(
            NumberEmailSearch.id == search_id
        ).first()
        
        if not search:
            return {'success': False, 'error': 'Search not found'}
        
        if not self.telegram_service or not self.telegram_service.is_connected:
            return {
                'success': False,
                'error': 'Telegram service not available. Contact administrator.'
            }
        
        search.status = "in_progress"
        self.db.commit()
        
        results = []
        total_credits_used = 0
        successful_modules = 0
        
        try:
            # Query each module
            for module in modules:
                module_credits = MODULE_CREDITS.get(module, 0)
                
                logger.info(f"Querying module {module.value} for search {search_id}")
                
                # Query the bot
                bot_response = await self.telegram_service.query_bot(
                    module=module.value,
                    search_type=search.search_type,
                    search_value=search.search_value,
                    timeout=60
                )
                
                if bot_response.get('success'):
                    # Deduct credits for successful query
                    if self.deduct_credits(
                        user_id=search.user_id,
                        amount=module_credits,
                        search_id=search_id,
                        description=f"Tracker search - {module.value}"
                    ):
                        total_credits_used += module_credits
                        successful_modules += 1
                        
                        # Store result
                        result = NumberEmailResult(
                            search_id=search_id,
                            module_name=module.value,
                            result_type=module.value,
                            result_data=json.dumps(bot_response.get('parsed_data', {})),
                            source=bot_response.get('bot'),
                            confidence=bot_response.get('confidence', 'medium')
                        )
                        
                        self.db.add(result)
                        results.append({
                            'module': module.value,
                            'status': 'success',
                            'confidence': bot_response.get('confidence'),
                            'data': bot_response.get('parsed_data')
                        })
                else:
                    # Failed query - still log it
                    result = NumberEmailResult(
                        search_id=search_id,
                        module_name=module.value,
                        result_type=module.value,
                        result_data=json.dumps({'error': bot_response.get('error')}),
                        source=bot_response.get('bot'),
                        confidence='low'
                    )
                    
                    self.db.add(result)
                    results.append({
                        'module': module.value,
                        'status': 'failed',
                        'error': bot_response.get('error')
                    })
            
            # Update search record
            search.credits_used = total_credits_used
            search.status = "completed" if successful_modules > 0 else "failed"
            self.db.commit()
            
            logger.info(f"Search {search_id} completed. {successful_modules}/{len(modules)} modules successful.")
            
            return {
                'success': True,
                'search_id': search_id,
                'modules_completed': successful_modules,
                'total_modules': len(modules),
                'credits_used': total_credits_used,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error executing search {search_id}: {e}")
            search.status = "failed"
            self.db.commit()
            
            return {
                'success': False,
                'error': str(e),
                'search_id': search_id
            }
    
    def get_search_results(self, search_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete results for a search
        
        Returns:
            Dict with search details and all module results
        """
        search = self.db.query(NumberEmailSearch).filter(
            NumberEmailSearch.id == search_id
        ).first()
        
        if not search:
            return None
        
        # Get all results
        results = self.db.query(NumberEmailResult).filter(
            NumberEmailResult.search_id == search_id
        ).all()
        
        # Parse result data
        module_results = []
        for result in results:
            try:
                parsed_data = json.loads(result.result_data) if result.result_data else {}
            except:
                parsed_data = {}
            
            module_results.append({
                'module': result.module_name,
                'confidence': result.confidence,
                'data': parsed_data,
                'source': result.source,
                'retrieved_at': result.retrieved_at.isoformat()
            })
        
        # Generate summary with cross-module insights
        summary = self._generate_summary(module_results, search.search_value)
        
        return {
            'search_id': search.id,
            'case_id': search.case_id,
            'search_type': search.search_type,
            'search_value': search.search_value,
            'searched_at': search.searched_at.isoformat(),
            'status': search.status,
            'credits_used': search.credits_used,
            'modules_requested': search.modules_requested.split(',') if search.modules_requested else [],
            'module_results': module_results,
            'summary': summary
        }
    
    def _generate_summary(self, module_results: List[Dict], search_value: str) -> Dict[str, Any]:
        """Generate cross-module insights and summary"""
        summary = {
            'identity': {
                'names': [],
                'primary_name': None
            },
            'contact': {
                'emails': [],
                'phone_numbers': [],
                'social_profiles': []
            },
            'financial': {
                'upi_ids': [],
                'banks': []
            },
            'verification': {
                'aadhaar_linked': False,
                'vehicle_registered': False
            },
            'data_leaks': {
                'breaches_found': 0,
                'exposed_data': []
            },
            'confidence_assessment': 'medium'
        }
        
        # Aggregate data from all modules
        for result in module_results:
            data = result.get('data', {})
            module = result.get('module')
            
            # Extract names
            if 'name' in data and data['name']:
                summary['identity']['names'].append(data['name'])
            
            # Extract emails
            if 'emails' in data:
                summary['contact']['emails'].extend(data.get('emails', []))
            if 'primary_email' in data and data['primary_email']:
                summary['contact']['emails'].append(data['primary_email'])
            
            # Extract phone numbers
            if 'numbers' in data:
                summary['contact']['phone_numbers'].extend(data.get('numbers', []))
            
            # Extract social profiles
            if 'profiles' in data:
                for platform, url in data['profiles'].items():
                    summary['contact']['social_profiles'].append({
                        'platform': platform,
                        'url': url
                    })
            
            # Extract financial info
            if 'upi_ids' in data:
                summary['financial']['upi_ids'].extend(data.get('upi_ids', []))
            if 'banks' in data:
                summary['financial']['banks'].extend(data.get('banks', []))
            
            # Verification flags
            if module == 'aadhaar' and data.get('aadhaar_linked'):
                summary['verification']['aadhaar_linked'] = True
            if module == 'vehicle' and data.get('registration_number'):
                summary['verification']['vehicle_registered'] = True
            
            # Data breaches
            if module == 'deep_search':
                summary['data_leaks']['breaches_found'] = len(data.get('breaches_found', []))
                if 'leaked_data' in data:
                    summary['data_leaks']['exposed_data'] = list(data['leaked_data'].keys())
        
        # Deduplicate lists
        summary['identity']['names'] = list(set(summary['identity']['names']))
        summary['contact']['emails'] = list(set(summary['contact']['emails']))
        summary['contact']['phone_numbers'] = list(set(summary['contact']['phone_numbers']))
        summary['financial']['upi_ids'] = list(set(summary['financial']['upi_ids']))
        summary['financial']['banks'] = list(set(summary['financial']['banks']))
        
        # Set primary name (most common)
        if summary['identity']['names']:
            summary['identity']['primary_name'] = summary['identity']['names'][0]
        
        # Calculate overall confidence
        high_confidence_count = sum(1 for r in module_results if r.get('confidence') == 'high')
        if high_confidence_count >= len(module_results) * 0.6:
            summary['confidence_assessment'] = 'high'
        elif high_confidence_count >= len(module_results) * 0.3:
            summary['confidence_assessment'] = 'medium'
        else:
            summary['confidence_assessment'] = 'low'
        
        return summary
    
    def get_user_credit_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get credit transaction history for a user"""
        transactions = self.db.query(CreditTransaction).filter(
            CreditTransaction.user_id == user_id
        ).order_by(CreditTransaction.timestamp.desc()).limit(limit).all()
        
        return [
            {
                'id': t.id,
                'type': t.transaction_type,
                'amount': t.amount,
                'balance_before': t.balance_before,
                'balance_after': t.balance_after,
                'module': t.module,
                'description': t.description,
                'timestamp': t.timestamp.isoformat()
            }
            for t in transactions
        ]
    
    def get_tracker_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get tracker module statistics"""
        query = self.db.query(NumberEmailSearch)
        
        if user_id:
            query = query.filter(NumberEmailSearch.user_id == user_id)
        
        searches = query.all()
        
        total_searches = len(searches)
        phone_searches = sum(1 for s in searches if s.search_type == 'phone')
        email_searches = sum(1 for s in searches if s.search_type == 'email')
        total_credits_spent = sum(s.credits_used for s in searches)
        
        # Calculate success rate
        completed_searches = sum(1 for s in searches if s.status == 'completed')
        success_rate = (completed_searches / total_searches * 100) if total_searches > 0 else 0
        
        # Find most used module
        module_usage = {}
        for search in searches:
            if search.modules_requested:
                for module in search.modules_requested.split(','):
                    module_usage[module] = module_usage.get(module, 0) + 1
        
        most_used_module = max(module_usage.items(), key=lambda x: x[1])[0] if module_usage else None
        
        # Recent searches
        recent_searches = [
            {
                'id': s.id,
                'search_type': s.search_type,
                'search_value': s.search_value,
                'status': s.status,
                'credits_used': s.credits_used,
                'searched_at': s.searched_at.isoformat()
            }
            for s in sorted(searches, key=lambda x: x.searched_at, reverse=True)[:10]
        ]
        
        return {
            'total_searches': total_searches,
            'phone_searches': phone_searches,
            'email_searches': email_searches,
            'total_credits_spent': total_credits_spent,
            'success_rate': round(success_rate, 2),
            'most_used_module': most_used_module,
            'recent_searches': recent_searches
        }
