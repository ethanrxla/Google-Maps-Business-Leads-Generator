#!/usr/bin/env python3
"""
Lead scoring and qualification module
"""

from typing import Dict, List, Any
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

class LeadScoringEngine:
    def __init__(self):
        self.scoring_rules = self.load_scoring_rules()
        self.model = self.load_scoring_model()
        
    def score_leads(self, leads: List[Dict], company_context: Dict = None) -> List[Dict]:
        """Score leads using rule-based and ML approaches"""
        scored_leads = []
        
        for lead in leads:
            # Rule-based scoring
            rule_score = self.calculate_rule_score(lead)
            
            # ML-based scoring (if model available)
            ml_score = self.calculate_ml_score(lead) if self.model else 0.5
            
            # Combined score
            final_score = (rule_score * 0.7) + (ml_score * 0.3)
            
            lead['lead_score'] = round(final_score * 100, 2)
            lead['qualification_tier'] = self.determine_qualification_tier(final_score)
            lead['scoring_breakdown'] = {
                'rule_based': rule_score,
                'ml_based': ml_score,
                'final_score': final_score
            }
            
            scored_leads.append(lead)
        
        return sorted(scored_leads, key=lambda x: x['lead_score'], reverse=True)
    
    def calculate_rule_score(self, lead: Dict) -> float:
        """Calculate score based on business rules"""
        score = 0.0
        
        # Email factors
        if lead.get('email_verified'):
            score += 0.3
        
        if lead.get('email_pattern_confidence', 0) > 0.7:
            score += 0.2
        
        # Role/Title factors
        title = lead.get('job_title', '').lower()
        if any(role in title for role in ['director', 'vp', 'head of', 'chief']):
            score += 0.3
        elif any(role in title for role in ['manager', 'lead', 'senior']):
            score += 0.2
        elif any(role in title for role in ['engineer', 'developer', 'analyst']):
            score += 0.1
        
        # Department factors
        department = lead.get('department', '').lower()
        dept_scores = {
            'executive': 0.3,
            'sales': 0.25,
            'marketing': 0.2,
            'it': 0.15,
            'engineering': 0.15,
            'finance': 0.1,
            'hr': 0.1
        }
        score += dept_scores.get(department, 0.05)
        
        # Company size factor (if available)
        company_size = lead.get('company_size', '')
        if '1000+' in company_size:
            score += 0.1
        elif '500-1000' in company_size:
            score += 0.08
        
        return min(score, 1.0)
    
    def determine_qualification_tier(self, score: float) -> str:
        """Determine lead qualification tier"""
        if score >= 0.8:
            return "Hot Lead"
        elif score >= 0.6:
            return "Warm Lead"
        elif score >= 0.4:
            return "Cold Lead"
        else:
            return "Unqualified"