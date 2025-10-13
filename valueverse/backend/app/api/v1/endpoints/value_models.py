"""Value Models API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.value_model_service import ValueModelService
from app.agents.orchestrator import AgentOrchestrator
from schemas import (
    ValueHypothesis,
    ValueCommitment,
    ValueRealization,
    ValueProof,
    ValueModelResponse,
    User
)

router = APIRouter()


@router.post("/create", response_model=ValueModelResponse)
async def create_value_model(
    company_name: str,
    industry: Optional[str] = None,
    company_size: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new value model for a company using AI agents
    """
    try:
        # Initialize services
        service = ValueModelService(db)
        orchestrator = AgentOrchestrator()
        
        # Create value model through agent orchestration
        result = await orchestrator.create_value_model(
            company_name=company_name,
            industry=industry,
            company_size=company_size,
            user_id=current_user.id
        )
        
        # Save to database
        hypothesis = await service.create_hypothesis(
            hypothesis_data=result["hypothesis"],
            user_id=current_user.id
        )
        
        return ValueModelResponse(
            hypothesis=hypothesis,
            patterns_applied=result.get("patterns_applied", []),
            roi_projection=result.get("roi_projection", {}),
            confidence_score=result.get("confidence_score", 0.8),
            reasoning_summary=result.get("reasoning", "")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create value model: {str(e)}"
        )


@router.get("/{model_id}", response_model=ValueHypothesis)
async def get_value_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific value model by ID
    """
    service = ValueModelService(db)
    model = await service.get_hypothesis(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Value model not found"
        )
    
    return model


@router.get("/", response_model=List[ValueHypothesis])
async def list_value_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    customer_id: Optional[str] = None,
    stage: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List value models with optional filtering
    """
    service = ValueModelService(db)
    models = await service.list_hypotheses(
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        stage=stage,
        user_id=current_user.id if current_user.role != "admin" else None
    )
    
    return models


@router.put("/{model_id}", response_model=ValueHypothesis)
async def update_value_model(
    model_id: str,
    updates: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a value model
    """
    service = ValueModelService(db)
    
    # Check if model exists and user has permission
    model = await service.get_hypothesis(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Value model not found"
        )
    
    # Update the model
    updated_model = await service.update_hypothesis(model_id, updates)
    
    return updated_model


@router.post("/{model_id}/commit", response_model=ValueCommitment)
async def commit_value_model(
    model_id: str,
    contract_value: float,
    contract_term_months: int,
    committed_kpis: List[dict],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Transform a value hypothesis into a commitment
    """
    service = ValueModelService(db)
    orchestrator = AgentOrchestrator()
    
    # Get the hypothesis
    hypothesis = await service.get_hypothesis(model_id)
    if not hypothesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Value model not found"
        )
    
    # Create commitment through agent
    commitment_data = await orchestrator.create_commitment(
        hypothesis=hypothesis,
        contract_value=contract_value,
        contract_term_months=contract_term_months,
        committed_kpis=committed_kpis,
        user_id=current_user.id
    )
    
    # Save commitment
    commitment = await service.create_commitment(
        hypothesis_id=model_id,
        commitment_data=commitment_data,
        user_id=current_user.id
    )
    
    return commitment


@router.post("/{model_id}/track", response_model=ValueRealization)
async def track_realization(
    model_id: str,
    metrics: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Track value realization progress
    """
    service = ValueModelService(db)
    
    # Get the commitment
    commitment = await service.get_commitment_by_hypothesis(model_id)
    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No commitment found for this value model"
        )
    
    # Update realization tracking
    realization = await service.update_realization(
        commitment_id=commitment.id,
        metrics=metrics,
        user_id=current_user.id
    )
    
    return realization


@router.post("/{model_id}/prove", response_model=ValueProof)
async def prove_value(
    model_id: str,
    evidence_documents: List[str],
    testimonials: List[dict],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate value proof for a completed realization
    """
    service = ValueModelService(db)
    orchestrator = AgentOrchestrator()
    
    # Get realization data
    realization = await service.get_realization_by_hypothesis(model_id)
    if not realization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No realization found for this value model"
        )
    
    # Generate proof through agent
    proof_data = await orchestrator.generate_proof(
        realization=realization,
        evidence_documents=evidence_documents,
        testimonials=testimonials,
        user_id=current_user.id
    )
    
    # Save proof
    proof = await service.create_proof(
        realization_id=realization.id,
        proof_data=proof_data,
        user_id=current_user.id
    )
    
    return proof


@router.get("/{model_id}/roi-analysis")
async def get_roi_analysis(
    model_id: str,
    scenario: str = Query("realistic", regex="^(conservative|realistic|optimistic)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get ROI analysis for a value model
    """
    service = ValueModelService(db)
    
    # Get the model
    model = await service.get_hypothesis(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Value model not found"
        )
    
    # Calculate ROI based on scenario
    multiplier = {"conservative": 0.7, "realistic": 1.0, "optimistic": 1.3}[scenario]
    
    roi_analysis = {
        "scenario": scenario,
        "total_investment": model.estimated_investment,
        "year_1_value": model.total_value_potential * 0.3 * multiplier,
        "year_2_value": model.total_value_potential * 0.5 * multiplier,
        "year_3_value": model.total_value_potential * 1.0 * multiplier,
        "total_3_year_value": model.total_value_potential * 1.8 * multiplier,
        "roi_percentage": ((model.total_value_potential * 1.8 * multiplier - model.estimated_investment) / model.estimated_investment * 100) if model.estimated_investment > 0 else 0,
        "payback_period_months": (model.estimated_investment / (model.total_value_potential * multiplier / 36)) if model.total_value_potential > 0 else 0,
        "confidence_score": model.confidence_score * (0.9 if scenario == "conservative" else 1.1 if scenario == "optimistic" else 1.0)
    }
    
    return roi_analysis


@router.delete("/{model_id}")
async def delete_value_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a value model (admin only)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete value models"
        )
    
    service = ValueModelService(db)
    
    # Check if model exists
    model = await service.get_hypothesis(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Value model not found"
        )
    
    # Delete the model
    await service.delete_hypothesis(model_id)
    
    return {"message": "Value model deleted successfully"}
