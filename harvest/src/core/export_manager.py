#!/usr/bin/env python3
"""
Export manager for lead data in various formats
"""

try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover
    pd = None
import json
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.job_result import HarvestJobResult

class LeadExportManager:
    def __init__(self, export_dir="exports"):
        self.export_dir = export_dir
        
    def export_crm_leads(self, leads: List[Dict], company_domain: str, crm_type: str = "salesforce"):
        """Export leads in CRM-ready format"""
        if crm_type == "salesforce":
            self.export_salesforce_format(leads, company_domain)
        elif crm_type == "hubspot":
            self.export_hubspot_format(leads, company_domain)
        elif crm_type == "outreach":
            self.export_outreach_format(leads, company_domain)
    
    def export_salesforce_format(self, leads: List[Dict], company_domain: str):
        """Export in Salesforce import format"""
        sf_data = []
        
        for lead in leads:
            sf_lead = {
                'FirstName': lead.get('first_name', ''),
                'LastName': lead.get('last_name', ''),
                'Email': lead.get('email', ''),
                'Company': lead.get('company', company_domain),
                'Title': lead.get('job_title', ''),
                'Department': lead.get('department', ''),
                'LeadSource': 'Automated Lead Generation',
                'Status': 'New',
                'Lead_Score__c': lead.get('lead_score', 0),
                'Rating': self.map_lead_score_to_rating(lead.get('lead_score', 0))
            }
            sf_data.append(sf_lead)
        
        df = pd.DataFrame(sf_data)
        filename = f"{self.export_dir}/crm_ready/salesforce_{company_domain}_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Salesforce leads exported: {filename}")
    
    def export_marketing_list(self, leads: List[Dict], company_domain: str):
        """Export for marketing automation"""
        marketing_data = []
        
        for lead in leads:
            marketing_lead = {
                'email': lead.get('email', ''),
                'first_name': lead.get('first_name', ''),
                'last_name': lead.get('last_name', ''),
                'company': lead.get('company', company_domain),
                'job_title': lead.get('job_title', ''),
                'department': lead.get('department', ''),
                'lead_score': lead.get('lead_score', 0),
                'qualification_tier': lead.get('qualification_tier', ''),
                'email_verified': lead.get('email_verified', False),
                'acquisition_date': datetime.now().strftime('%Y-%m-%d')
            }
            marketing_data.append(marketing_lead)
        
        df = pd.DataFrame(marketing_data)
        filename = f"{self.export_dir}/marketing/marketing_leads_{company_domain}_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False)
        
        # Also create a simple email list
        email_list = [lead['email'] for lead in leads if lead.get('email')]
        email_filename = f"{self.export_dir}/marketing/email_list_{company_domain}_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(email_filename, 'w') as f:
            for email in email_list:
                f.write(f"{email}\n")
        
        print(f"✅ Marketing lists exported: {filename}")
    
    def generate_lead_analytics(self, leads_data: Dict, company_domain: str):
        """Generate lead generation analytics report"""
        analytics = {
            'summary': {
                'total_leads_found': leads_data.get('total_leads', 0),
                'qualified_leads': len(leads_data.get('qualified_leads', [])),
                'qualification_rate': leads_data.get('qualification_rate', 0),
                'average_lead_score': self.calculate_average_score(leads_data.get('qualified_leads', [])),
                'generation_date': datetime.now().isoformat()
            },
            'department_breakdown': self.analyze_departments(leads_data.get('qualified_leads', [])),
            'score_distribution': self.analyze_score_distribution(leads_data.get('qualified_leads', [])),
            'company_intel': leads_data.get('enrichment_data', {}).get('company_info', {})
        }
        
        # Save analytics report
        analytics_file = f"{self.export_dir}/analytics/lead_analytics_{company_domain}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(analytics_file, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        print(f"✅ Analytics report exported: {analytics_file}")


def export_raw_results_to_csv(raw_paths: List[HarvestJobResult] | List[str], output_csv: str) -> None:
    """
    Export harvest job results to CSV. Accepts either list of HarvestJobResult
    or list of file path strings (legacy).
    """
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        headers = ["domain", "sources", "limit", "status", "raw_output_path", "error_message", "lines_in_raw"]
        writer.writerow(headers)
        for item in raw_paths:
            if isinstance(item, HarvestJobResult):
                row = _job_to_dict(item)
            else:
                row = {
                    "domain": "",
                    "sources": "",
                    "limit": "",
                    "status": "",
                    "raw_output_path": item,
                    "error_message": "",
                    "lines_in_raw": _lines_in_file(item),
                }
            writer.writerow([row.get(h) for h in headers])


def _lines_in_file(path: Optional[str]) -> int:
    if not path or not os.path.exists(path):
        return 0
    with open(path, "r") as f:
        return sum(1 for _ in f)


def _job_to_dict(job: HarvestJobResult) -> Dict[str, Any]:
    return {
        "domain": job.domain,
        "sources": job.sources,
        "limit": job.limit,
        "status": job.status,
        "raw_output_path": job.raw_output_path,
        "error_message": job.error_message,
        "lines_in_raw": _lines_in_file(job.raw_output_path),
        "emails_found": len(job.parsed_data.get("emails", [])) if job.parsed_data else 0,
        "hosts_found": len(job.parsed_data.get("hosts", [])) if job.parsed_data else 0,
        "started_at": job.started_at.isoformat(),
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


def export_structured_results_to_json(results: List[HarvestJobResult], output_json: str) -> None:
    """Write structured results to JSON."""
    payload = [_job_to_dict(job) for job in results]
    with open(output_json, "w") as f:
        json.dump(payload, f, indent=2)
