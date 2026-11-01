"""SQLAlchemy models for the `inspektorati` database.

One class per table. These describe the schema in Python; the tables themselves
are created by the Alembic migrations in backend/migrations/versions/.
"""

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column

# Predictable names for indexes and constraints, so migrations can refer to them.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Every table is InnoDB with utf8mb4 / utf8mb4_unicode_ci.
TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def id_column():
    return mapped_column(Integer, primary_key=True, autoincrement=True)


def created_at_column():
    return mapped_column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


def updated_at_column():
    return mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )


def fk_column(target, ondelete, nullable=True, **kwargs):
    """Foreign key column (INT), indexed unless it is already UNIQUE."""
    kwargs.setdefault("index", not kwargs.get("unique", False))
    return mapped_column(
        Integer, ForeignKey(target, ondelete=ondelete), nullable=nullable, **kwargs
    )


class Kategori(Base):
    __tablename__ = "kategorite"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    emri = mapped_column(String(100), nullable=False)
    # NULL parent = sector
    parent_id = fk_column("kategorite.id", "SET NULL")
    pershkrimi = mapped_column(String(255))
    created_at = created_at_column()


class Perdorues(Base):
    __tablename__ = "perdoruesit"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    emri = mapped_column(String(80), nullable=False)
    mbiemri = mapped_column(String(80), nullable=False)
    email = mapped_column(String(120), nullable=False, unique=True)
    password_hash = mapped_column(String(255), nullable=False)
    role = mapped_column(Enum("inspektor", "drejtor", "admin"), nullable=False)
    sektori_id = fk_column("kategorite.id", "SET NULL")
    telefoni = mapped_column(String(30))
    aktiv = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at = created_at_column()
    updated_at = updated_at_column()


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    perdoruesi_id = fk_column("perdoruesit.id", "CASCADE", nullable=False)
    token = mapped_column(String(255), nullable=False)
    expires_at = mapped_column(DateTime, nullable=False)
    revoked = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = created_at_column()


class MaseShkallezimi(Base):
    __tablename__ = "masat_shkallezimi"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    kategori_id = fk_column("kategorite.id", "CASCADE", nullable=False)
    rendi = mapped_column(Integer, nullable=False)
    emri = mapped_column(String(80), nullable=False)
    pershkrimi = mapped_column(String(255))
    created_at = created_at_column()


class Subjekt(Base):
    __tablename__ = "subjektet"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    emri = mapped_column(String(160), nullable=False)
    lloji = mapped_column(Enum("biznes", "person", "firme"), nullable=False)
    nui = mapped_column(String(20), unique=True)
    adresa = mapped_column(String(255))
    kontakti = mapped_column(String(80))
    created_at = created_at_column()
    updated_at = updated_at_column()


class Lokacion(Base):
    __tablename__ = "lokacionet"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    pershkrimi = mapped_column(String(255))
    lagjja = mapped_column(String(120))
    latitude = mapped_column(Numeric(9, 6))
    longitude = mapped_column(Numeric(9, 6))
    created_at = created_at_column()


class Kerkese(Base):
    __tablename__ = "kerkesat"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    numri_gjurmimit = mapped_column(String(20), nullable=False, unique=True)
    teksti_origjinal = mapped_column(Text, nullable=False)
    kanali = mapped_column(
        Enum("portal", "telefon", "fizik", "email"),
        nullable=False,
        server_default="portal",
    )
    raportuesi_emri = mapped_column(String(120))
    raportuesi_kontakti = mapped_column(String(80))
    anonim = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    kategori_id = fk_column("kategorite.id", "SET NULL")
    subjekt_id = fk_column("subjektet.id", "SET NULL")
    lokacion_id = fk_column("lokacionet.id", "SET NULL")
    urgjenca = mapped_column(Enum("e_ulet", "mesme", "e_larte"))
    status = mapped_column(
        Enum(
            "e_re",
            "kategorizuar",
            "caktuar",
            "ne_terren",
            "procesverbal",
            "vendim_propozuar",
            "vendim_miratuar",
            "mase_aktive",
            "riinspektim",
            "mbyllur",
            "ankese",
        ),
        nullable=False,
        server_default="e_re",
        index=True,
    )
    shkallezim_nivel = mapped_column(Integer)
    inspektori_id = fk_column("perdoruesit.id", "SET NULL")
    caktuar_nga = fk_column("perdoruesit.id", "SET NULL")
    created_at = created_at_column()
    updated_at = updated_at_column()


class KerkeseAI(Base):
    __tablename__ = "kerkesa_ai"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    # UNIQUE makes this 1:1 with kerkesat
    kerkesa_id = fk_column("kerkesat.id", "CASCADE", nullable=False, unique=True)
    kategoria_propozuar = mapped_column(String(100))
    lokacioni_nxjerre = mapped_column(String(160))
    subjekti_nxjerre = mapped_column(String(160))
    kohezgjatja = mapped_column(String(80))
    urgjenca_propozuar = mapped_column(String(20))
    info_mungon = mapped_column(JSON)
    besueshmeria = mapped_column(Float)
    model_perdorur = mapped_column(String(40))
    created_at = created_at_column()


class Procesverbal(Base):
    __tablename__ = "procesverbalet"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    kerkesa_id = fk_column("kerkesat.id", "CASCADE", nullable=False)
    inspektori_id = fk_column("perdoruesit.id", "SET NULL")
    subjekt_emri_sakte = mapped_column(String(160))
    nui_sakte = mapped_column(String(20))
    adresa_sakte = mapped_column(String(255))
    gjendja_konstatuar = mapped_column(Text)
    permasat = mapped_column(String(120))
    konstatimi = mapped_column(Enum("shkelje", "pa_shkelje"))
    data_inspektimit = mapped_column(DateTime)
    konfirmuar = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = created_at_column()


class DokumentLigjor(Base):
    __tablename__ = "dokumentet_ligjore"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    titulli = mapped_column(String(200), nullable=False)
    skedari_path = mapped_column(String(255))
    versioni = mapped_column(String(20))
    statusi = mapped_column(
        Enum("aktive", "ne_perpunim", "arkivuar"),
        nullable=False,
        server_default="ne_perpunim",
    )
    nr_neneve = mapped_column(Integer)
    uploaded_by = fk_column("perdoruesit.id", "SET NULL")
    created_at = created_at_column()
    updated_at = updated_at_column()


class NenLigjor(Base):
    __tablename__ = "nenet_ligjore"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    dokument_id = fk_column("dokumentet_ligjore.id", "CASCADE", nullable=False)
    numri_nenit = mapped_column(String(20))
    titulli = mapped_column(String(200))
    teksti = mapped_column(Text, nullable=False)
    faqja = mapped_column(Integer)
    # id of this article's embedding in Chroma
    vector_ref = mapped_column(String(80))
    created_at = created_at_column()


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    lloji = mapped_column(Enum("foto", "dokument"), nullable=False)
    path = mapped_column(String(255), nullable=False)
    kerkesa_id = fk_column("kerkesat.id", "CASCADE")
    procesverbal_id = fk_column("procesverbalet.id", "CASCADE")
    uploaded_by = fk_column("perdoruesit.id", "SET NULL")
    created_at = created_at_column()


class Vendim(Base):
    __tablename__ = "vendimet"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    kerkesa_id = fk_column("kerkesat.id", "CASCADE", nullable=False)
    procesverbal_id = fk_column("procesverbalet.id", "SET NULL")
    nen_id = fk_column("nenet_ligjore.id", "SET NULL")
    masa = mapped_column(Text)
    shkallezim_nivel = mapped_column(Integer)
    draft_tekst = mapped_column(Text)
    pdf_path = mapped_column(String(255))
    statusi = mapped_column(
        Enum("propozuar", "miratuar", "modifikuar", "refuzuar"),
        nullable=False,
        server_default="propozuar",
    )
    eshte_ai = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    vendosur_nga = fk_column("perdoruesit.id", "SET NULL")
    aprovuar_nga = fk_column("perdoruesit.id", "SET NULL")
    afati = mapped_column(DateTime)
    nenshkruar_at = mapped_column(DateTime)
    created_at = created_at_column()
    updated_at = updated_at_column()


class Ankese(Base):
    __tablename__ = "ankesat"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    vendim_id = fk_column("vendimet.id", "CASCADE", nullable=False)
    arsyeja = mapped_column(Text)
    statusi = mapped_column(
        Enum("e_re", "ne_shqyrtim", "pranuar", "refuzuar"),
        nullable=False,
        server_default="e_re",
    )
    shqyrtuar_nga = fk_column("perdoruesit.id", "SET NULL")
    vendim_i_ri_id = fk_column("vendimet.id", "SET NULL")
    created_at = created_at_column()
    updated_at = updated_at_column()


class Njoftim(Base):
    __tablename__ = "njoftimet"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    perdoruesi_id = fk_column("perdoruesit.id", "CASCADE")
    kerkesa_id = fk_column("kerkesat.id", "CASCADE")
    lloji = mapped_column(
        Enum("caktim", "afat", "ndryshim_statusi", "aprovim", "ankese", "mesazh"),
        nullable=False,
    )
    teksti = mapped_column(String(255), nullable=False)
    lexuar = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = created_at_column()


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = TABLE_OPTIONS

    id = id_column()
    # NULL = system / AI
    perdoruesi_id = fk_column("perdoruesit.id", "SET NULL")
    veprimi = mapped_column(String(120), nullable=False)
    entiteti = mapped_column(String(60))
    entitet_id = mapped_column(Integer)
    kerkesa_id = fk_column("kerkesat.id", "SET NULL")
    vlera_vjeter = mapped_column(JSON)
    vlera_re = mapped_column(JSON)
    eshte_ai = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = created_at_column()
