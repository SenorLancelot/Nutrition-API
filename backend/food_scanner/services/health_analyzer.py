import logging
import time
from typing import Dict, Any, List
from django.conf import settings
from ..models import HealthCondition
from .llm_service import llm_service
from django.db.models import Q
logger = logging.getLogger('food_scanner')


class HealthAnalyzerService:
    """Service for analyzing food nutrition against health conditions"""
    
    def __init__(self):
        self.condition_cache = {}
    
    def analyze_for_conditions(self, nutrition_data: Dict, health_conditions: List):
        """
        Analyze nutrition data against specified health conditions
        
        Args:
            nutrition_data: Dict containing nutrition information
            health_conditions: List of health condition names
            
        Returns:
            dict: {
                'remarks': list of health remarks,
                'overall_score': float (0-10),
                'condition_scores': dict of individual condition scores
            }
        """
        try:
            if not health_conditions:
                return {
                    'remarks': [],
                    'overall_score': 7.0,  # Neutral score
                    'condition_scores': {}
                }
            
            all_remarks = []
            condition_scores = {}
            
            for condition_name in health_conditions:
                condition = self._get_health_condition(condition_name)
                if condition:
                    analysis = self._analyze_single_condition(nutrition_data, condition)
                    all_remarks.extend(analysis['remarks'])
                    condition_scores[condition_name] = analysis['score']
                else:
                    logger.warning(f"Unknown health condition: {condition_name}")
            
            # Calculate overall health score
            overall_score = self._calculate_overall_score(condition_scores, nutrition_data)
            
            return {
                'remarks': all_remarks,
                'overall_score': overall_score,
                'condition_scores': condition_scores
            }
            
        except Exception as e:
            logger.error(f"Error analyzing health conditions: {str(e)}")
            return {
                'remarks': [{'condition': 'system', 'severity': 'info', 
                           'message': 'Health analysis temporarily unavailable'}],
                'overall_score': 5.0,
                'condition_scores': {}
            }
    
    def _analyze_single_condition(self, nutrition_data, condition):
        """Analyze nutrition data for a single health condition"""
        remarks = []
        score = 7.0  # Start with neutral score
        
        try:
            restrictions = condition.dietary_restrictions
            targets = condition.nutritional_targets
            
            # Check dietary restrictions
            for nutrient, limit in restrictions.items():
                nutrient_value = nutrition_data.get(nutrient.replace('max_', '').replace('min_', ''))
                
                if nutrient_value is not None:
                    if nutrient.startswith('max_') and nutrient_value > limit:
                        severity = self._get_severity_level(nutrient_value, limit, 'max')
                        message = self._format_restriction_message(condition, nutrient, nutrient_value, limit, 'max')
                        remarks.append({
                            'condition': condition.name,
                            'severity': severity,
                            'message': message,
                            'recommendation': self._get_recommendation(condition, nutrient, 'max')
                        })
                        score -= self._get_score_penalty(severity)
                    
                    elif nutrient.startswith('min_') and nutrient_value < limit:
                        severity = self._get_severity_level(nutrient_value, limit, 'min')
                        message = self._format_restriction_message(condition, nutrient, nutrient_value, limit, 'min')
                        remarks.append({
                            'condition': condition.name,
                            'severity': severity,
                            'message': message,
                            'recommendation': self._get_recommendation(condition, nutrient, 'min')
                        })
                        score -= self._get_score_penalty(severity)
            
            # Add positive remarks if food is suitable
            if score >= 7.0:
                remarks.append({
                    'condition': condition.name,
                    'severity': 'info',
                    'message': f"This food appears suitable for {condition.name}",
                    'recommendation': 'Continue monitoring portion sizes'
                })
            
            return {
                'remarks': remarks,
                'score': max(0.0, min(10.0, score))  # Clamp between 0-10
            }
            
        except Exception as e:
            logger.error(f"Error analyzing condition {condition.name}: {str(e)}")
            return {
                'remarks': [{
                    'condition': condition.name,
                    'severity': 'info',
                    'message': f"Unable to analyze for {condition.name}",
                    'recommendation': 'Consult healthcare provider'
                }],
                'score': 5.0
            }
    
    def _get_health_condition(self, condition_name):
        """Get health condition from cache or database"""
        if condition_name in self.condition_cache:
            return self.condition_cache[condition_name]
        
        try:
            condition = HealthCondition.objects.filter(
                Q(name__iexact=condition_name) | 
                Q(name__icontains=condition_name)
            ).first()
            
            if condition:
                self.condition_cache[condition_name] = condition
            
            return condition
            
        except Exception as e:
            logger.error(f"Error fetching health condition {condition_name}: {str(e)}")
            return None
    
    def _load_health_conditions(self):
        """Pre-load common health conditions into cache"""
        try:
            common_conditions = HealthCondition.objects.filter(is_active=True)[:20]
            for condition in common_conditions:
                self.condition_cache[condition.name.lower()] = condition
                
        except Exception as e:
            logger.error(f"Error loading health conditions: {str(e)}")
    
    def _get_severity_level(self, actual_value, limit_value, limit_type):
        """Determine severity level based on how much the limit is exceeded"""
        if limit_type == 'max':
            ratio = actual_value / limit_value
            if ratio > 2.0:
                return 'danger'
            elif ratio > 1.5:
                return 'warning'
            else:
                return 'info'
        else:  # min
            ratio = actual_value / limit_value
            if ratio < 0.5:
                return 'danger'
            elif ratio < 0.75:
                return 'warning'
            else:
                return 'info'
    
    def _format_restriction_message(self, condition, nutrient, actual, limit, limit_type):
        """Format a user-friendly restriction message"""
        nutrient_clean = nutrient.replace('max_', '').replace('min_', '').replace('_', ' ')
        
        if limit_type == 'max':
            return f"High {nutrient_clean} content ({actual:.1f}) may not be suitable for {condition.name} (limit: {limit})"
        else:
            return f"Low {nutrient_clean} content ({actual:.1f}) may not meet {condition.name} requirements (minimum: {limit})"
    
    def _get_recommendation(self, condition, nutrient, limit_type):
        """Get recommendation based on condition and nutrient"""
        recommendations = {
            'diabetes': {
                'max_sugar_g': 'Choose foods with less added sugar',
                'max_carbohydrates_g': 'Consider portion control for carbohydrates',
            },
            'hypertension': {
                'max_sodium_mg': 'Look for low-sodium alternatives',
            },
            'heart_disease': {
                'max_saturated_fat_g': 'Choose lean proteins and healthy fats',
            }
        }
        
        condition_name = condition.name.lower().replace(' ', '_')
        return recommendations.get(condition_name, {}).get(nutrient, 'Consult healthcare provider for guidance')
    
    def _get_score_penalty(self, severity):
        """Get score penalty based on severity"""
        penalties = {
            'info': 0.5,
            'warning': 1.5,
            'danger': 3.0
        }
        return penalties.get(severity, 1.0)
    
    def _calculate_overall_score(self, condition_scores, nutrition_data):
        """Calculate overall health score"""
        if not condition_scores:
            return 7.0  # Neutral score if no conditions
        
        # Average of all condition scores
        avg_score = sum(condition_scores.values()) / len(condition_scores)
        
        # Apply general nutrition bonuses/penalties
        if nutrition_data.get('fiber_g', 0) > 5:
            avg_score += 0.5
        if nutrition_data.get('sodium_mg', 0) > 2300:
            avg_score -= 0.5
        
        return max(0.0, min(10.0, avg_score))
