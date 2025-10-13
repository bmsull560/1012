from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.graph_node import GraphNode as GraphNodeModel
from app.schemas.graph_node import GraphNode, GraphNodeCreate, GraphNodeUpdate

router = APIRouter(prefix="/graph", tags=["graph"])

@router.post("/nodes", response_model=GraphNode)
def create_node(
    node: GraphNodeCreate,
    db: Session = Depends(get_db)
):
    '''Create a new graph node'''
    db_node = GraphNodeModel(**node.dict())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return db_node

@router.get("/nodes/{node_id}", response_model=GraphNode)
def get_node(
    node_id: UUID,
    db: Session = Depends(get_db)
):
    '''Get a graph node by ID'''
    node = db.query(GraphNodeModel).filter(GraphNodeModel.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@router.get("/nodes", response_model=List[GraphNode])
def list_nodes(
    phase: Optional[int] = None,
    node_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    '''List graph nodes with optional filters'''
    query = db.query(GraphNodeModel)
    
    if phase is not None:
        query = query.filter(GraphNodeModel.phase == phase)
    if node_type:
        query = query.filter(GraphNodeModel.node_type == node_type)
    
    return query.all()

@router.patch("/nodes/{node_id}", response_model=GraphNode)
def update_node(
    node_id: UUID,
    updates: GraphNodeUpdate,
    db: Session = Depends(get_db)
):
    '''Update a graph node'''
    node = db.query(GraphNodeModel).filter(GraphNodeModel.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(node, field, value)
    
    db.commit()
    db.refresh(node)
    return node
