import pytest
from sqlalchemy.exc import IntegrityError
from backend.app.database import SessionLocal, Base
from backend.app.models.value_hypothesis import ValueHypothesis, ValueHypothesisBase, ValueHypothesisCreate, ValueHypothesisUpdate, ValueHypothesisRead
from backend.app.models.conversation import Conversation

@pytest.fixture
def db_session():
    engine = SessionLocal.kw['bind']
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = SessionLocal()
    yield session
    session.close()

def test_value_hypothesis_repr(db_session):
    conversation = Conversation(id=1)
    db_session.add(conversation)
    db_session.commit()
    value_hypothesis = ValueHypothesis(id=1, conversation_id=1, hypothesis='Test Hypothesis')
    db_session.add(value_hypothesis)
    db_session.commit()
    assert repr(value_hypothesis) == "ValueHypothesis(id=1, conversation_id=1, hypothesis='Test Hypothesis')"

def test_value_hypothesis_create(db_session):
    conversation = Conversation(id=1)
    db_session.add(conversation)
    db_session.commit()
    value_hypothesis = ValueHypothesis(conversation_id=1, hypothesis='Test Hypothesis')
    db_session.add(value_hypothesis)
    db_session.commit()
    assert value_hypothesis.id == 1
    assert value_hypothesis.conversation_id == 1
    assert value_hypothesis.hypothesis == 'Test Hypothesis'

def test_value_hypothesis_create_without_conversation(db_session):
    value_hypothesis = ValueHypothesis(conversation_id=1, hypothesis='Test Hypothesis')
    with pytest.raises(IntegrityError):
        db_session.add(value_hypothesis)
        db_session.commit()

def test_value_hypothesis_update(db_session):
    conversation = Conversation(id=1)
    db_session.add(conversation)
    db_session.commit()
    value_hypothesis = ValueHypothesis(conversation_id=1, hypothesis='Test Hypothesis')
    db_session.add(value_hypothesis)
    db_session.commit()
    value_hypothesis.hypothesis = 'Updated Test Hypothesis'
    db_session.commit()
    assert value_hypothesis.hypothesis == 'Updated Test Hypothesis'

def test_value_hypothesis_read(db_session):
    conversation = Conversation(id=1)
    db_session.add(conversation)
    db_session.commit()
    value_hypothesis = ValueHypothesis(conversation_id=1, hypothesis='Test Hypothesis')
    db_session.add(value_hypothesis)
    db_session.commit()
    read_value_hypothesis = ValueHypothesisRead(id=value_hypothesis.id, conversation_id=value_hypothesis.conversation_id, hypothesis=value_hypothesis.hypothesis, created_at=str(value_hypothesis.created_at), updated_at=str(value_hypothesis.updated_at))
    assert read_value_hypothesis.id == value_hypothesis.id
    assert read_value_hypothesis.conversation_id == value_hypothesis.conversation_id
    assert read_value_hypothesis.hypothesis == value_hypothesis.hypothesis
    assert read_value_hypothesis.created_at == str(value_hypothesis.created_at)
    assert read_value_hypothesis.updated_at == str(value_hypothesis.updated_at)

def test_value_hypothesis_base_model():
    value_hypothesis_base = ValueHypothesisBase(hypothesis='Test Hypothesis')
    assert value_hypothesis_base.hypothesis == 'Test Hypothesis'

def test_value_hypothesis_create_model():
    value_hypothesis_create = ValueHypothesisCreate(conversation_id=1, hypothesis='Test Hypothesis')
    assert value_hypothesis_create.conversation_id == 1
    assert value_hypothesis_create.hypothesis == 'Test Hypothesis'

def test_value_hypothesis_update_model():
    value_hypothesis_update = ValueHypothesisUpdate(hypothesis='Test Hypothesis')
    assert value_hypothesis_update.hypothesis == 'Test Hypothesis'

def test_value_hypothesis_read_model():
    value_hypothesis_read = ValueHypothesisRead(id=1, conversation_id=1, hypothesis='Test Hypothesis', created_at='2022-01-01 00:00:00', updated_at='2022-01-01 00:00:00')
    assert value_hypothesis_read.id == 1
    assert value_hypothesis_read.conversation_id == 1
    assert value_hypothesis_read.hypothesis == 'Test Hypothesis'
    assert value_hypothesis_read.created_at == '2022-01-01 00:00:00'
    assert value_hypothesis_read.updated_at == '2022-01-01 00:00:00'