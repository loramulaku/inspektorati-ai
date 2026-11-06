"""kerkesa intake: applicant, type and declaration columns for the citizen portal

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-02 19:30:00

Adds to `kerkesat` the data the public form collects. The older columns
raportuesi_emri / raportuesi_kontakti / anonim are kept (unused by the
portal; other channels may use them later). Category, urgency etc. stay as
they are: they are filled later, not at intake.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_COLUMNS = [
    'lloji',
    'aplikuesi_emri',
    'aplikuesi_mbiemri',
    'aplikuesi_numri_personal',
    'aplikuesi_email',
    'aplikuesi_telefoni',
    'aplikuesi_adresa',
    'deklarata_pranuar',
    'deklarata_emri',
]


def upgrade() -> None:
    """Add the intake columns to kerkesat."""
    op.add_column('kerkesat', sa.Column('lloji', sa.Enum('kerkese', 'ankese'), nullable=False))
    op.add_column('kerkesat', sa.Column('aplikuesi_emri', sa.String(length=80), nullable=False))
    op.add_column('kerkesat', sa.Column('aplikuesi_mbiemri', sa.String(length=80), nullable=False))
    op.add_column('kerkesat', sa.Column('aplikuesi_numri_personal', sa.String(length=10), nullable=False))
    op.add_column('kerkesat', sa.Column('aplikuesi_email', sa.String(length=120), nullable=True))
    op.add_column('kerkesat', sa.Column('aplikuesi_telefoni', sa.String(length=30), nullable=False))
    op.add_column('kerkesat', sa.Column('aplikuesi_adresa', sa.String(length=255), nullable=True))
    op.add_column('kerkesat', sa.Column('deklarata_pranuar', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False))
    op.add_column('kerkesat', sa.Column('deklarata_emri', sa.String(length=160), nullable=False))


def downgrade() -> None:
    """Remove exactly the columns added above."""
    for column in reversed(NEW_COLUMNS):
        op.drop_column('kerkesat', column)
