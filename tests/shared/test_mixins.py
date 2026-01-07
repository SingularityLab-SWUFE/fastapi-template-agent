from time import sleep

from sqlmodel import Field, Session, SQLModel, create_engine

from src.shared.mixins import TimestampMixin


class SampleModel(SQLModel, TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


def test_timestamp_mixin_updated_at_updates():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        record = SampleModel(name="original")
        session.add(record)
        session.commit()
        session.refresh(record)
        initial_updated_at = record.updated_at

        sleep(0.01)

        record.name = "modified"
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.updated_at > initial_updated_at


def test_timestamp_mixin_created_at_unchanged():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        record = SampleModel(name="original")
        session.add(record)
        session.commit()
        session.refresh(record)
        initial_created_at = record.created_at

        sleep(0.01)

        record.name = "modified"
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.created_at == initial_created_at
