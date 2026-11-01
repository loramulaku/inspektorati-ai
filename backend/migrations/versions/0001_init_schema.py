"""init schema: create the 16 tables of the inspektorati database

Revision ID: 0001
Revises:
Create Date: 2026-11-01 23:20:10.764746

Tables are created in dependency order so every foreign key points at a table
that already exists. Every foreign key column gets its own index.

This file is a frozen snapshot: it does not import app.db.models, so later
changes to the models never change what this migration does.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_OPTIONS = dict(
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
)

# Creation order (downgrade drops them in reverse).
TABLES = [
    'kategorite',
    'perdoruesit',
    'refresh_tokens',
    'masat_shkallezimi',
    'subjektet',
    'lokacionet',
    'kerkesat',
    'kerkesa_ai',
    'procesverbalet',
    'dokumentet_ligjore',
    'nenet_ligjore',
    'attachments',
    'vendimet',
    'ankesat',
    'njoftimet',
    'audit_log',
]


def _id():
    return sa.Column('id', sa.Integer(), autoincrement=True, nullable=False)


def _created_at():
    return sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True)


def _updated_at():
    return sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True)


def _fk(column, target, ondelete, table):
    referred_table = target.split('.')[0]
    return sa.ForeignKeyConstraint(
        [column], [target],
        name=op.f(f'fk_{table}_{column}_{referred_table}'),
        ondelete=ondelete,
    )


def _index(table, *columns):
    for column in columns:
        op.create_index(op.f(f'ix_{table}_{column}'), table, [column], unique=False)


def upgrade() -> None:
    """Create all 16 tables."""
    # 1. kategorite
    op.create_table('kategorite',
        _id(),
        sa.Column('emri', sa.String(length=100), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('pershkrimi', sa.String(length=255), nullable=True),
        _created_at(),
        _fk('parent_id', 'kategorite.id', 'SET NULL', 'kategorite'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_kategorite')),
        **TABLE_OPTIONS
    )
    _index('kategorite', 'parent_id')

    # 2. perdoruesit
    op.create_table('perdoruesit',
        _id(),
        sa.Column('emri', sa.String(length=80), nullable=False),
        sa.Column('mbiemri', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('inspektor', 'drejtor', 'admin'), nullable=False),
        sa.Column('sektori_id', sa.Integer(), nullable=True),
        sa.Column('telefoni', sa.String(length=30), nullable=True),
        sa.Column('aktiv', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        _created_at(),
        _updated_at(),
        _fk('sektori_id', 'kategorite.id', 'SET NULL', 'perdoruesit'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_perdoruesit')),
        sa.UniqueConstraint('email', name=op.f('uq_perdoruesit_email')),
        **TABLE_OPTIONS
    )
    _index('perdoruesit', 'sektori_id')

    # 3. refresh_tokens
    op.create_table('refresh_tokens',
        _id(),
        sa.Column('perdoruesi_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
        _created_at(),
        _fk('perdoruesi_id', 'perdoruesit.id', 'CASCADE', 'refresh_tokens'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_tokens')),
        **TABLE_OPTIONS
    )
    _index('refresh_tokens', 'perdoruesi_id')

    # 4. masat_shkallezimi
    op.create_table('masat_shkallezimi',
        _id(),
        sa.Column('kategori_id', sa.Integer(), nullable=False),
        sa.Column('rendi', sa.Integer(), nullable=False),
        sa.Column('emri', sa.String(length=80), nullable=False),
        sa.Column('pershkrimi', sa.String(length=255), nullable=True),
        _created_at(),
        _fk('kategori_id', 'kategorite.id', 'CASCADE', 'masat_shkallezimi'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_masat_shkallezimi')),
        **TABLE_OPTIONS
    )
    _index('masat_shkallezimi', 'kategori_id')

    # 5. subjektet
    op.create_table('subjektet',
        _id(),
        sa.Column('emri', sa.String(length=160), nullable=False),
        sa.Column('lloji', sa.Enum('biznes', 'person', 'firme'), nullable=False),
        sa.Column('nui', sa.String(length=20), nullable=True),
        sa.Column('adresa', sa.String(length=255), nullable=True),
        sa.Column('kontakti', sa.String(length=80), nullable=True),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_subjektet')),
        sa.UniqueConstraint('nui', name=op.f('uq_subjektet_nui')),
        **TABLE_OPTIONS
    )

    # 6. lokacionet
    op.create_table('lokacionet',
        _id(),
        sa.Column('pershkrimi', sa.String(length=255), nullable=True),
        sa.Column('lagjja', sa.String(length=120), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_lokacionet')),
        **TABLE_OPTIONS
    )

    # 7. kerkesat
    op.create_table('kerkesat',
        _id(),
        sa.Column('numri_gjurmimit', sa.String(length=20), nullable=False),
        sa.Column('teksti_origjinal', sa.Text(), nullable=False),
        sa.Column('kanali', sa.Enum('portal', 'telefon', 'fizik', 'email'), server_default='portal', nullable=False),
        sa.Column('raportuesi_emri', sa.String(length=120), nullable=True),
        sa.Column('raportuesi_kontakti', sa.String(length=80), nullable=True),
        sa.Column('anonim', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
        sa.Column('kategori_id', sa.Integer(), nullable=True),
        sa.Column('subjekt_id', sa.Integer(), nullable=True),
        sa.Column('lokacion_id', sa.Integer(), nullable=True),
        sa.Column('urgjenca', sa.Enum('e_ulet', 'mesme', 'e_larte'), nullable=True),
        sa.Column('status', sa.Enum('e_re', 'kategorizuar', 'caktuar', 'ne_terren', 'procesverbal', 'vendim_propozuar', 'vendim_miratuar', 'mase_aktive', 'riinspektim', 'mbyllur', 'ankese'), server_default='e_re', nullable=False),
        sa.Column('shkallezim_nivel', sa.Integer(), nullable=True),
        sa.Column('inspektori_id', sa.Integer(), nullable=True),
        sa.Column('caktuar_nga', sa.Integer(), nullable=True),
        _created_at(),
        _updated_at(),
        _fk('kategori_id', 'kategorite.id', 'SET NULL', 'kerkesat'),
        _fk('subjekt_id', 'subjektet.id', 'SET NULL', 'kerkesat'),
        _fk('lokacion_id', 'lokacionet.id', 'SET NULL', 'kerkesat'),
        _fk('inspektori_id', 'perdoruesit.id', 'SET NULL', 'kerkesat'),
        _fk('caktuar_nga', 'perdoruesit.id', 'SET NULL', 'kerkesat'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_kerkesat')),
        sa.UniqueConstraint('numri_gjurmimit', name=op.f('uq_kerkesat_numri_gjurmimit')),
        **TABLE_OPTIONS
    )
    _index('kerkesat', 'status', 'kategori_id', 'subjekt_id', 'lokacion_id', 'inspektori_id', 'caktuar_nga')

    # 8. kerkesa_ai (1:1 with kerkesat; the UNIQUE index also serves the FK)
    op.create_table('kerkesa_ai',
        _id(),
        sa.Column('kerkesa_id', sa.Integer(), nullable=False),
        sa.Column('kategoria_propozuar', sa.String(length=100), nullable=True),
        sa.Column('lokacioni_nxjerre', sa.String(length=160), nullable=True),
        sa.Column('subjekti_nxjerre', sa.String(length=160), nullable=True),
        sa.Column('kohezgjatja', sa.String(length=80), nullable=True),
        sa.Column('urgjenca_propozuar', sa.String(length=20), nullable=True),
        sa.Column('info_mungon', sa.JSON(), nullable=True),
        sa.Column('besueshmeria', sa.Float(), nullable=True),
        sa.Column('model_perdorur', sa.String(length=40), nullable=True),
        _created_at(),
        _fk('kerkesa_id', 'kerkesat.id', 'CASCADE', 'kerkesa_ai'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_kerkesa_ai')),
        sa.UniqueConstraint('kerkesa_id', name=op.f('uq_kerkesa_ai_kerkesa_id')),
        **TABLE_OPTIONS
    )

    # 9. procesverbalet
    op.create_table('procesverbalet',
        _id(),
        sa.Column('kerkesa_id', sa.Integer(), nullable=False),
        sa.Column('inspektori_id', sa.Integer(), nullable=True),
        sa.Column('subjekt_emri_sakte', sa.String(length=160), nullable=True),
        sa.Column('nui_sakte', sa.String(length=20), nullable=True),
        sa.Column('adresa_sakte', sa.String(length=255), nullable=True),
        sa.Column('gjendja_konstatuar', sa.Text(), nullable=True),
        sa.Column('permasat', sa.String(length=120), nullable=True),
        sa.Column('konstatimi', sa.Enum('shkelje', 'pa_shkelje'), nullable=True),
        sa.Column('data_inspektimit', sa.DateTime(), nullable=True),
        sa.Column('konfirmuar', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
        _created_at(),
        _fk('kerkesa_id', 'kerkesat.id', 'CASCADE', 'procesverbalet'),
        _fk('inspektori_id', 'perdoruesit.id', 'SET NULL', 'procesverbalet'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_procesverbalet')),
        **TABLE_OPTIONS
    )
    _index('procesverbalet', 'kerkesa_id', 'inspektori_id')

    # 10. dokumentet_ligjore
    op.create_table('dokumentet_ligjore',
        _id(),
        sa.Column('titulli', sa.String(length=200), nullable=False),
        sa.Column('skedari_path', sa.String(length=255), nullable=True),
        sa.Column('versioni', sa.String(length=20), nullable=True),
        sa.Column('statusi', sa.Enum('aktive', 'ne_perpunim', 'arkivuar'), server_default='ne_perpunim', nullable=False),
        sa.Column('nr_neneve', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        _created_at(),
        _updated_at(),
        _fk('uploaded_by', 'perdoruesit.id', 'SET NULL', 'dokumentet_ligjore'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_dokumentet_ligjore')),
        **TABLE_OPTIONS
    )
    _index('dokumentet_ligjore', 'uploaded_by')

    # 11. nenet_ligjore
    op.create_table('nenet_ligjore',
        _id(),
        sa.Column('dokument_id', sa.Integer(), nullable=False),
        sa.Column('numri_nenit', sa.String(length=20), nullable=True),
        sa.Column('titulli', sa.String(length=200), nullable=True),
        sa.Column('teksti', sa.Text(), nullable=False),
        sa.Column('faqja', sa.Integer(), nullable=True),
        sa.Column('vector_ref', sa.String(length=80), nullable=True),
        _created_at(),
        _fk('dokument_id', 'dokumentet_ligjore.id', 'CASCADE', 'nenet_ligjore'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_nenet_ligjore')),
        **TABLE_OPTIONS
    )
    _index('nenet_ligjore', 'dokument_id')

    # 12. attachments
    op.create_table('attachments',
        _id(),
        sa.Column('lloji', sa.Enum('foto', 'dokument'), nullable=False),
        sa.Column('path', sa.String(length=255), nullable=False),
        sa.Column('kerkesa_id', sa.Integer(), nullable=True),
        sa.Column('procesverbal_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        _created_at(),
        _fk('kerkesa_id', 'kerkesat.id', 'CASCADE', 'attachments'),
        _fk('procesverbal_id', 'procesverbalet.id', 'CASCADE', 'attachments'),
        _fk('uploaded_by', 'perdoruesit.id', 'SET NULL', 'attachments'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_attachments')),
        **TABLE_OPTIONS
    )
    _index('attachments', 'kerkesa_id', 'procesverbal_id', 'uploaded_by')

    # 13. vendimet
    op.create_table('vendimet',
        _id(),
        sa.Column('kerkesa_id', sa.Integer(), nullable=False),
        sa.Column('procesverbal_id', sa.Integer(), nullable=True),
        sa.Column('nen_id', sa.Integer(), nullable=True),
        sa.Column('masa', sa.Text(), nullable=True),
        sa.Column('shkallezim_nivel', sa.Integer(), nullable=True),
        sa.Column('draft_tekst', sa.Text(), nullable=True),
        sa.Column('pdf_path', sa.String(length=255), nullable=True),
        sa.Column('statusi', sa.Enum('propozuar', 'miratuar', 'modifikuar', 'refuzuar'), server_default='propozuar', nullable=False),
        sa.Column('eshte_ai', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        sa.Column('vendosur_nga', sa.Integer(), nullable=True),
        sa.Column('aprovuar_nga', sa.Integer(), nullable=True),
        sa.Column('afati', sa.DateTime(), nullable=True),
        sa.Column('nenshkruar_at', sa.DateTime(), nullable=True),
        _created_at(),
        _updated_at(),
        _fk('kerkesa_id', 'kerkesat.id', 'CASCADE', 'vendimet'),
        _fk('procesverbal_id', 'procesverbalet.id', 'SET NULL', 'vendimet'),
        _fk('nen_id', 'nenet_ligjore.id', 'SET NULL', 'vendimet'),
        _fk('vendosur_nga', 'perdoruesit.id', 'SET NULL', 'vendimet'),
        _fk('aprovuar_nga', 'perdoruesit.id', 'SET NULL', 'vendimet'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_vendimet')),
        **TABLE_OPTIONS
    )
    _index('vendimet', 'kerkesa_id', 'procesverbal_id', 'nen_id', 'vendosur_nga', 'aprovuar_nga')

    # 14. ankesat
    op.create_table('ankesat',
        _id(),
        sa.Column('vendim_id', sa.Integer(), nullable=False),
        sa.Column('arsyeja', sa.Text(), nullable=True),
        sa.Column('statusi', sa.Enum('e_re', 'ne_shqyrtim', 'pranuar', 'refuzuar'), server_default='e_re', nullable=False),
        sa.Column('shqyrtuar_nga', sa.Integer(), nullable=True),
        sa.Column('vendim_i_ri_id', sa.Integer(), nullable=True),
        _created_at(),
        _updated_at(),
        _fk('vendim_id', 'vendimet.id', 'CASCADE', 'ankesat'),
        _fk('shqyrtuar_nga', 'perdoruesit.id', 'SET NULL', 'ankesat'),
        _fk('vendim_i_ri_id', 'vendimet.id', 'SET NULL', 'ankesat'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ankesat')),
        **TABLE_OPTIONS
    )
    _index('ankesat', 'vendim_id', 'shqyrtuar_nga', 'vendim_i_ri_id')

    # 15. njoftimet
    op.create_table('njoftimet',
        _id(),
        sa.Column('perdoruesi_id', sa.Integer(), nullable=True),
        sa.Column('kerkesa_id', sa.Integer(), nullable=True),
        sa.Column('lloji', sa.Enum('caktim', 'afat', 'ndryshim_statusi', 'aprovim', 'ankese', 'mesazh'), nullable=False),
        sa.Column('teksti', sa.String(length=255), nullable=False),
        sa.Column('lexuar', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
        _created_at(),
        _fk('perdoruesi_id', 'perdoruesit.id', 'CASCADE', 'njoftimet'),
        _fk('kerkesa_id', 'kerkesat.id', 'CASCADE', 'njoftimet'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_njoftimet')),
        **TABLE_OPTIONS
    )
    _index('njoftimet', 'perdoruesi_id', 'kerkesa_id')

    # 16. audit_log (perdoruesi_id NULL = system / AI)
    op.create_table('audit_log',
        _id(),
        sa.Column('perdoruesi_id', sa.Integer(), nullable=True),
        sa.Column('veprimi', sa.String(length=120), nullable=False),
        sa.Column('entiteti', sa.String(length=60), nullable=True),
        sa.Column('entitet_id', sa.Integer(), nullable=True),
        sa.Column('kerkesa_id', sa.Integer(), nullable=True),
        sa.Column('vlera_vjeter', sa.JSON(), nullable=True),
        sa.Column('vlera_re', sa.JSON(), nullable=True),
        sa.Column('eshte_ai', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
        _created_at(),
        _fk('perdoruesi_id', 'perdoruesit.id', 'SET NULL', 'audit_log'),
        _fk('kerkesa_id', 'kerkesat.id', 'SET NULL', 'audit_log'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_log')),
        **TABLE_OPTIONS
    )
    _index('audit_log', 'perdoruesi_id', 'kerkesa_id')


def downgrade() -> None:
    """Drop all 16 tables, in reverse creation order.

    Indexes and foreign keys are dropped together with their table. Dropping
    a FK's index on its own first would fail in MySQL.
    """
    for table in reversed(TABLES):
        op.drop_table(table)
