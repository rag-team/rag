from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import String  # Replace by Text for TEXT fields

from server.schlagwortdb.database import Base


class Schlagworte(Base):
    __tablename__ = "Schlagworte"

    pkey: Mapped[int] = mapped_column(primary_key=True)
    schlagwort: Mapped[str] = mapped_column(type_=String(255), server_default="empty")
    geschaeftsfeld: Mapped[str] = mapped_column(type_=String(255), server_default="empty")
    kategorie: Mapped[str] = mapped_column(type_=String(255), server_default="empty")
    dsgvo_relevant: Mapped[bool] = mapped_column(server_default="1")

    felder: Mapped[List["Felder"]] = relationship(
        "Felder", back_populates="schlagwort_obj"
    )
    synonyme: Mapped[List["Synonyme"]] = relationship(
        "Synonyme", back_populates="schlagwort_obj"
    )

    def __repr__(self):
        return f"<Schlagwort {self.schlagwort}>"


class Synonyme(Base):
    __tablename__ = "Synonyme"

    pkey: Mapped[int] = mapped_column(primary_key=True)
    schlagwort: Mapped[int] = mapped_column(ForeignKey("Schlagworte.pkey"))
    synonym: Mapped[str] = mapped_column(type_=String(255))

    schlagwort_obj = relationship("Schlagworte", back_populates="synonyme")

    def __repr__(self):
        return f"<Synonym {self.synonym} for {self.schlagwort_obj.schlagwort}>"


class Felder(Base):
    __tablename__ = "Felder"

    pkey: Mapped[int] = mapped_column(primary_key=True)
    feldname: Mapped[str] = mapped_column(type_=String(255), server_default="empty", unique=True)
    schlagwort: Mapped[int] = mapped_column(ForeignKey("Schlagworte.pkey"))
    feldtyp: Mapped[str] = mapped_column(type_=String(255), server_default="empty")

    schlagwort_obj = relationship("Schlagworte", back_populates="felder")

    def __repr__(self):
        return f"<Feld {self.feldname} for {self.schlagwort_obj.schlagwort}>"
