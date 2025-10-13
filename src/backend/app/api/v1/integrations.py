from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from app.integrations.salesforce import SalesforceAdapter, SalesforceOpportunity

router = APIRouter(prefix="/integrations", tags=["integrations"])

sf_adapter = SalesforceAdapter()

@router.get("/salesforce/opportunities", response_model=List[SalesforceOpportunity])
def list_salesforce_opportunities(
    stage: Optional[str] = None,
    owner_id: Optional[str] = None
):
    '''List Salesforce opportunities'''
    try:
        filters = {}
        if stage:
            filters['stage'] = stage
        if owner_id:
            filters['owner_id'] = owner_id
        
        opportunities = sf_adapter.list_opportunities(filters)
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/salesforce/opportunities/{opportunity_id}", response_model=SalesforceOpportunity)
def get_salesforce_opportunity(opportunity_id: str):
    '''Get single Salesforce opportunity'''
    try:
        opportunity = sf_adapter.get_opportunity(opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return opportunity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/salesforce/opportunities/{opportunity_id}")
def update_salesforce_opportunity(
    opportunity_id: str,
    fields: Dict[str, str]
):
    '''Update Salesforce opportunity fields'''
    try:
        success = sf_adapter.update_opportunity(opportunity_id, fields)
        if not success:
            raise HTTPException(status_code=500, detail="Update failed")
        return {"status": "updated", "opportunity_id": opportunity_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/salesforce/opportunities/{opportunity_id}/roi")
def update_roi_fields(
    opportunity_id: str,
    roi_estimate: str,
    value_drivers: str
):
    '''Update custom ROI fields in Salesforce'''
    try:
        success = sf_adapter.create_custom_field_update(
            opportunity_id, roi_estimate, value_drivers
        )
        if not success:
            raise HTTPException(status_code=500, detail="Update failed")
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/salesforce/health")
def check_salesforce_connection():
    '''Check Salesforce connection status'''
    try:
        connected = sf_adapter.connect()
        return {"status": "connected" if connected else "disconnected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
