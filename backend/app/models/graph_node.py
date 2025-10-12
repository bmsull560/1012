from sqlalchemy import Column, String, Integer, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base

class GraphNode(Base):
    '''A node in the value graph representing a value driver, outcome, or metric'''
    __tablename__ = 'graph_nodes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Node type: hypothesis, commitment, realization, proof
    node_type = Column(String(50), nullable=False)
    
    # Lifecycle phase: 0=hypothesis, 1=commitment, 2=realization, 3=proof
    phase = Column(Integer, nullable=False, default=0)
    
    # Flexible properties as JSON
    properties = Column(JSON, nullable=False, default=dict)
    
    # Temporal tracking
    valid_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    valid_to = Column(DateTime, nullable=True)
    
    # Confidence score 0-1
    confidence_score = Column(Float, default=0.5)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GraphNode {self.node_type} phase={self.phase}>"
