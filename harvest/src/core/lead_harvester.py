#!/usr/bin/env python3
"""
Lead Generation focused theHarvester automation
Optimized for extracting business contacts and company intelligence
"""

import subprocess
import json
try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover
    pd = None
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
from utils.email_validator import EmailValidator
from utils.pattern_matcher import PatternMatcher

class LeadHarvester:
    def __init__(self, output_dir="lead_intelligence", config: Optional[Dict[str, Any]] = None):
        self.output_dir = output_dir
        self.config = config or {}
        self.email_validator = EmailValidator()
        self.pattern_matcher = PatternMatcher()
        self.lead_criteria = self.load_lead_criteria()

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Minimal search stub that returns synthetic leads for testing.
        """
        raw_results = self._mock_source_results(query, limit)
        cleaned = []
        for entry in raw_results[:limit]:
            cleaned.append({
                "company_name": entry.get("company_name", "").strip(),
                "domain": entry.get("domain", "").lower().strip(),
            })
        return cleaned

    def generate_company_leads(self, company_domain: str, company_name: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive leads for a company
        """
        print(f"🎯 Generating leads for: {company_domain}")
        
        # Step 1: Basic theHarvester scan
        base_data = self.run_harvester_scan(company_domain)
        
        # Step 2: Email pattern generation
        generated_emails = self.generate_email_patterns(
            base_data.get('emails', []), 
            company_domain,
            company_name
        )
        
        # Step 3: Data enrichment
        enriched_data = self.enrich_lead_data(base_data, generated_emails)
        
        # Step 4: Lead scoring and qualification
        qualified_leads = self.qualify_leads(enriched_data)
        
        # Step 5: Generate reports and exports
        self.generate_lead_reports(qualified_leads, company_domain)
        
        return qualified_leads
    
    def run_harvester_scan(self, domain: str) -> Dict[str, Any]:
        """Run theHarvester with lead-optimized parameters"""
        cmd = [
            "theHarvester",
            "-d", domain,
            "-b", "google,bing,linkedin,github,twitter",
            "-l", "500",
            "-f", f"{self.output_dir}/raw/{domain}_scan"
        ]
        
        try:
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            if process.returncode == 0:
                return self.parse_harvester_output(f"{self.output_dir}/raw/{domain}_scan")
            else:
                print(f"⚠️  theHarvester error: {process.stderr}")
                return {}
                
        except subprocess.TimeoutExpired:
            print("⏰ theHarvester timed out")
            return {}
    
    def generate_email_patterns(self, found_emails: List[str], domain: str, company_name: str = None) -> List[Dict]:
        """Generate potential email addresses based on patterns"""
        email_patterns = self.pattern_matcher.analyze_email_patterns(found_emails)
        generated_emails = []
        
        # Common email patterns to try
        common_patterns = [
            "first.last@{domain}",
            "firstl@{domain}",
            "flast@{domain}",
            "first@{domain}",
            "last@{domain}",
            "f.last@{domain}",
            "first_last@{domain}"
        ]
        
        # If we have sample emails, extract and extend patterns
        if found_emails:
            analyzed_patterns = self.analyze_existing_patterns(found_emails)
            common_patterns.extend(analyzed_patterns)
        
        # Generate emails for common job titles/departments
        departments = self.load_departments()
        job_titles = self.load_job_titles()
        
        for pattern in common_patterns:
            for department in departments[:5]:  # Limit to top departments
                for title in job_titles[:3]:   # Limit to key titles
                    # This would integrate with name databases in real implementation
                    email = pattern.format(
                        domain=domain,
                        department=department.lower(),
                        title=title.lower().replace(' ', '')
                    )
                    generated_emails.append({
                        'email': email,
                        'pattern': pattern,
                        'department': department,
                        'title': title,
                        'confidence': 0.3,  # Base confidence for generated emails
                        'type': 'generated'
                    })
        
        return generated_emails
    
    def enrich_lead_data(self, base_data: Dict, generated_emails: List[Dict]) -> Dict[str, Any]:
        """Enrich lead data with additional intelligence"""
        enriched = {
            'company_info': self.extract_company_info(base_data),
            'contacts': self.process_contacts(base_data.get('emails', []), generated_emails),
            'technographics': self.extract_technographics(base_data),
            'social_links': self.extract_social_links(base_data),
            'domain_intelligence': self.analyze_domain_structure(base_data)
        }
        
        # Add verification data
        enriched['contacts'] = self.verify_emails(enriched['contacts'])
        
        return enriched
    
    def qualify_leads(self, enriched_data: Dict) -> Dict[str, Any]:
        """Score and qualify leads based on criteria"""
        leads = enriched_data['contacts']
        qualified_leads = []
        
        for lead in leads:
            score = self.calculate_lead_score(lead, enriched_data)
            lead['lead_score'] = score
            lead['status'] = self.determine_lead_status(score)
            lead['priority'] = self.determine_priority(lead)
            
            if score >= self.lead_criteria['min_qualification_score']:
                qualified_leads.append(lead)
        
        return {
            'qualified_leads': sorted(qualified_leads, key=lambda x: x['lead_score'], reverse=True),
            'total_leads': len(leads),
            'qualified_count': len(qualified_leads),
            'qualification_rate': len(qualified_leads) / len(leads) if leads else 0,
            'enrichment_data': enriched_data
        }
    
    def calculate_lead_score(self, lead: Dict, enriched_data: Dict) -> float:
        """Calculate lead score based on multiple factors"""
        score = 0.0
        
        # Email verification score
        if lead.get('verified', False):
            score += 30
        
        # Pattern confidence
        score += lead.get('confidence', 0) * 20
        
        # Department importance
        dept_score = self.lead_criteria['department_scores'].get(
            lead.get('department', '').lower(), 0
        )
        score += dept_score
        
        # Title importance
        title_score = self.lead_criteria['title_scores'].get(
            lead.get('title', '').lower(), 0
        )
        score += title_score
        
        # Social presence
        if lead.get('social_links'):
            score += 10
        
        return min(score, 100)
    
    def generate_lead_reports(self, qualified_leads: Dict, company_domain: str):
        """Generate various lead reports"""
        # CRM-ready export
        self.export_crm_leads(qualified_leads['qualified_leads'], company_domain)
        
        # Marketing list export
        self.export_marketing_list(qualified_leads, company_domain)
        
        # Analytics report
        self.generate_analytics_report(qualified_leads, company_domain)
        
        # Lead sheet
        self.generate_lead_sheet(qualified_leads, company_domain)

    # --- Helpers for simplified search testing ---
    def _mock_source_results(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Return synthetic lead records for testing."""
        base_domain = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-") or "example"
        return [
            {
                "company_name": f"Company {i+1}",
                "domain": f"{base_domain}{i+1}.com",
            }
            for i in range(limit)
        ]

    def load_lead_criteria(self) -> Dict[str, Any]:
        """Load lead criteria from config or defaults."""
        defaults = {
            "min_qualification_score": 50,
            "department_scores": {},
            "title_scores": {},
        }
        if self.config:
            defaults.update(self.config.get("lead_generation", {}))
        return defaults
