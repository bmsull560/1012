from typing import Dict, List, Optional
from simple_salesforce import Salesforce
from pydantic import BaseModel
import os

class SalesforceOpportunity(BaseModel):
    '''Salesforce Opportunity data'''
    id: str
    name: str
    account_name: str
    amount: float
    stage: str
    close_date: str
    owner_name: str

class SalesforceAdapter:
    '''Adapter for Salesforce API integration'''
    
    def __init__(self):
        self.username = os.getenv('SALESFORCE_USERNAME')
        self.password = os.getenv('SALESFORCE_PASSWORD')
        self.security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
        self.domain = os.getenv('SALESFORCE_DOMAIN', 'login')  # or 'test' for sandbox
        
        self.sf = None
    
    def connect(self):
        '''Establish Salesforce connection'''
        try:
            self.sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                domain=self.domain
            )
            return True
        except Exception as e:
            print(f"Salesforce connection error: {e}")
            return False
    
    def get_opportunity(self, opportunity_id: str) -> Optional[SalesforceOpportunity]:
        '''Fetch a single opportunity'''
        if not self.sf:
            self.connect()
        
        try:
            result = self.sf.Opportunity.get(opportunity_id)
            return SalesforceOpportunity(
                id=result['Id'],
                name=result['Name'],
                account_name=result['Account']['Name'],
                amount=result['Amount'] or 0.0,
                stage=result['StageName'],
                close_date=result['CloseDate'],
                owner_name=result['Owner']['Name']
            )
        except Exception as e:
            print(f"Error fetching opportunity: {e}")
            return None
    
    def list_opportunities(self, filters: Dict = None) -> List[SalesforceOpportunity]:
        '''List opportunities with optional filters'''
        if not self.sf:
            self.connect()
        
        # Build SOQL query
        query = "SELECT Id, Name, Account.Name, Amount, StageName, CloseDate, Owner.Name FROM Opportunity"
        
        if filters:
            conditions = []
            if 'stage' in filters:
                conditions.append(f"StageName = '{filters['stage']}'")
            if 'owner_id' in filters:
                conditions.append(f"OwnerId = '{filters['owner_id']}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += " LIMIT 100"
        
        try:
            results = self.sf.query(query)
            
            opportunities = []
            for record in results['records']:
                opportunities.append(SalesforceOpportunity(
                    id=record['Id'],
                    name=record['Name'],
                    account_name=record['Account']['Name'],
                    amount=record['Amount'] or 0.0,
                    stage=record['StageName'],
                    close_date=record['CloseDate'],
                    owner_name=record['Owner']['Name']
                ))
            
            return opportunities
        except Exception as e:
            print(f"Error listing opportunities: {e}")
            return []
    
    def update_opportunity(self, opportunity_id: str, fields: Dict) -> bool:
        '''Update opportunity fields'''
        if not self.sf:
            self.connect()
        
        try:
            self.sf.Opportunity.update(opportunity_id, fields)
            return True
        except Exception as e:
            print(f"Error updating opportunity: {e}")
            return False
    
    def create_custom_field_update(self, opportunity_id: str, roi_estimate: str, value_drivers: str):
        '''Update custom VROS fields'''
        return self.update_opportunity(opportunity_id, {
            'ROI_Estimate__c': roi_estimate,
            'Value_Drivers__c': value_drivers
        })
