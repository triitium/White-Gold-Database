"""Use TEXT for movie_people.character_name."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'faeca19a6ed2'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "movie_people",
        "character_name",
        existing_type=sa.String(length=300),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "movie_people",
        "character_name",
        existing_type=sa.Text(),
        type_=sa.String(length=300),
        existing_nullable=True,
    )
