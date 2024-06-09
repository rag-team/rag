from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Text

from server.schlagwortdb.database import Base


class Schlagwort(Base):
    __tablename__ = "Schlagworte"
    __table_args__ = {"sqlite_autoincrement": True}

    pkey: Mapped[int] = mapped_column(primary_key=True)
    schlagwort: Mapped[str] = mapped_column(type_=Text(), server_default="empty")
    geschaeftsfeld: Mapped[str] = mapped_column(type_=Text(), server_default="empty")
    kategorie: Mapped[str] = mapped_column(type_=Text(), server_default="empty")
    dsgvo_relevant: Mapped[bool] = mapped_column(server_default="true")

    felder: Mapped[List["Feld"]] = relationship("Feld", back_populates="schlagwort_obj")
    synonyme: Mapped[List["Synonym"]] = relationship(
        "Synonym", back_populates="schlagwort_obj"
    )

    def __repr__(self):
        return f"<Schlagwort {self.schlagwort}>"


class Synonym(Base):
    __tablename__ = "Synonyme"
    __table_args__ = {"sqlite_autoincrement": True}

    pkey: Mapped[int] = mapped_column(primary_key=True)
    schlagwort: Mapped[int] = mapped_column(
        ForeignKey("Schlagworte.pkey"), server_default="empty"
    )
    synonym: Mapped[str] = mapped_column(type_=Text(), server_default="empty")

    schlagwort_obj = relationship("Schlagwort", back_populates="synonyme")

    def __repr__(self):
        return f"<Synonym {self.synonym} for {self.schlagwort_obj.schlagwort}>"


class Feld(Base):
    __tablename__ = "Felder"
    __table_args__ = {"sqlite_autoincrement": True}

    pkey: Mapped[int] = mapped_column(primary_key=True)
    feldname: Mapped[str] = mapped_column(
        type_=Text(), server_default="empty", unique=True
    )
    schlagwort: Mapped[int] = mapped_column(ForeignKey("Schlagworte.pkey"))
    feldtyp: Mapped[str] = mapped_column(type_=Text(), server_default="empty")

    schlagwort_obj = relationship("Schlagwort", back_populates="felder")

    def __repr__(self):
        return f"<Feld {self.feldname} for {self.schlagwort_obj.schlagwort}>"


class DokumentLookup(Base):
    __tablename__ = "Lookup_Dokumente"
    __table_args__ = {"sqlite_autoincrement": True}

    pkey: Mapped[int] = mapped_column(primary_key=True)
    schlagwort: Mapped[int] = mapped_column(ForeignKey("Schlagworte.pkey"))
    docName: Mapped[str] = mapped_column(type_=Text(), server_default="empty")
    docOrigName: Mapped[str] = mapped_column(type_=Text(), server_default="empty")

    schlagwort_obj = relationship("Schlagwort")

    def __repr__(self):
        return f"<Dokument {self.docName} for {self.schlagwort_obj.schlagwort}>"


class Adresse(Base):
    __tablename__ = "Adresse"
    __table_args__ = {"sqlite_autoincrement": True}

    pkey: Mapped[int] = mapped_column(primary_key=True)
    strasse: Mapped[str] = mapped_column(type_=Text(), server_default="empty")
    hausnummer: Mapped[int] = mapped_column(server_default="1")
    hausnummerZusatz: Mapped[str] = mapped_column(type_=Text(), server_default="empty")
    plz: Mapped[int] = mapped_column(server_default="10000")
    ort: Mapped[str] = mapped_column(type_=Text(), server_default="empty")


class Kunde(Base):
    __tablename__ = "Kunde"
    __table_args__ = {"sqlite_autoincrement": True}

    pkey: Mapped[int] = mapped_column(primary_key=True)
    anrede: Mapped[str] = mapped_column(type_=Text(), server_default="3")
    vorname: Mapped[str] = mapped_column(type_=Text(), server_default="empty")
    name: Mapped[str] = mapped_column(type_=Text(), server_default="empty")
    geburtsdatum: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    geburtsort: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    staatsangehoerigkeit: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    vorwahl: Mapped[int] = mapped_column(nullable=True)
    telefonnummer: Mapped[int] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    familienstand: Mapped[int] = mapped_column(nullable=True)
    adresse: Mapped[int] = mapped_column(ForeignKey("Adresse.pkey"))

    adresse_obj = relationship("Adresse")
