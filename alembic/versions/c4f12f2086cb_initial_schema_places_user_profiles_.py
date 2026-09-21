"""Initial schema: places, user_profiles, user_favorites

Revision ID: c4f12f2086cb
Revises: 
Create Date: 2026-09-20 16:03:29.959578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f12f2086cb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely."""
    bind = op.get_bind()
    from models.db_models import Base
    Base.metadata.create_all(bind)

    inspector = sa.inspect(bind)

    if inspector.has_table('places'):
        places_cols = [c['name'] for c in inspector.get_columns('places')]
        if 'place_type' not in places_cols:
            op.add_column('places', sa.Column('place_type', sa.String(length=64), nullable=True))
        if 'promo_text' not in places_cols:
            op.add_column('places', sa.Column('promo_text', sa.Text(), nullable=True))
        if 'schedule' not in places_cols:
            op.add_column('places', sa.Column('schedule', sa.String(length=255), nullable=True))
        if 'address' not in places_cols:
            op.add_column('places', sa.Column('address', sa.String(length=255), nullable=True))

    if inspector.has_table('user_profiles'):
        profiles_cols = [c['name'] for c in inspector.get_columns('user_profiles')]
        if 'created_at' not in profiles_cols:
            op.add_column('user_profiles', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    pass
