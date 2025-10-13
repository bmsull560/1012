# backend/app/integrations/__init__.py
from .salesforce import SalesforceAdapter, SalesforceOpportunity

__all__ = ["SalesforceAdapter", "SalesforceOpportunity"]
