from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Text

from server.schlagwortdb.database import Base


class Schlagwort(Base):
    __tablename__ = "Schlagworte"

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

    pkey: Mapped[int] = mapped_column(primary_key=True)
    feldname: Mapped[str] = mapped_column(
        type_=Text(), server_default="empty", unique=True
    )
    schlagwort: Mapped[int] = mapped_column(ForeignKey("Schlagworte.pkey"))
    feldtyp: Mapped[str] = mapped_column(type_=Text(), server_default="empty")

    schlagwort_obj = relationship("Schlagwort", back_populates="felder")

    def __repr__(self):
        return f"<Feld {self.feldname} for {self.schlagwort_obj.schlagwort}>"
