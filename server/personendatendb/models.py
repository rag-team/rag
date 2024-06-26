from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.personendatendb.database import Base


class Adresse(Base):
    __tablename__ = "Adresse"
    __table_args__ = {"sqlite_autoincrement": True}

    pKey: Mapped[int] = mapped_column(primary_key=True)
    Strasse: Mapped[str] = mapped_column(
        type_=Text(), nullable=False, server_default=""
    )
    Hausnummer: Mapped[int] = mapped_column(nullable=False, server_default="1")
    HausnummerZusatz: Mapped[str] = mapped_column(
        type_=Text(), nullable=False, server_default=""
    )
    PLZ: Mapped[int] = mapped_column(nullable=False)
    Ort: Mapped[str] = mapped_column(type_=Text(), nullable=False, server_default="")
    
    person = relationship("Person", back_populates="adresse_obj")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "Strasse": self.Strasse,
            "Hausnummer": self.Hausnummer,
            "HausnummerZusatz": self.HausnummerZusatz,
            "PLZ": self.PLZ,
            "Ort": self.Ort,
        }


class Ausgabe(Base):
    __tablename__ = "Ausgabe"

    pKey: Mapped[int] = mapped_column(primary_key=True)
    PersonID: Mapped[int] = mapped_column(ForeignKey("Person.pKey"))
    Betrag: Mapped[float] = mapped_column(type_=Numeric)
    AusgabeTyp: Mapped[int] = mapped_column()
    AusgabeEntfaellt: Mapped[int] = mapped_column()

    person = relationship("Person", back_populates="ausgaben")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "PersonID": self.PersonID,
            "Betrag": float(self.Betrag) if self.Betrag is not None else None,
            "AusgabeTyp": self.AusgabeTyp,
            "AusgabeEntfaellt": self.AusgabeEntfaellt,
        }


class Bausparvertrag(Base):
    __tablename__ = "Bausparvertrag"

    pKey: Mapped[int] = mapped_column(primary_key=True)
    PersonID: Mapped[int] = mapped_column(ForeignKey("Person.pKey"))
    angesparterBetrag: Mapped[float] = mapped_column(type_=Numeric)
    Bausparkasse: Mapped[str] = mapped_column(type_=Text())
    Vertragsnummer: Mapped[str] = mapped_column(type_=Text())
    Tarif: Mapped[str] = mapped_column(type_=Text())
    Vertragsbeginn: Mapped[str] = mapped_column(type_=Text())
    Jahresentgelt: Mapped[float] = mapped_column(type_=Numeric)
    SparbetragMonatlich: Mapped[float] = mapped_column(type_=Numeric)
    Bausparsumme: Mapped[float] = mapped_column(type_=Numeric)
    Zuteilungsdatum: Mapped[str] = mapped_column(type_=Text())
    AufloesungAlsVerwendung: Mapped[int] = mapped_column()
    maximalerBetragVerwendung: Mapped[float] = mapped_column(type_=Numeric)

    person = relationship("Person", back_populates="bausparvertraege")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "PersonID": self.PersonID,
            "angesparterBetrag": (
                float(self.angesparterBetrag)
                if self.angesparterBetrag is not None
                else None
            ),
            "Bausparkasse": self.Bausparkasse,
            "Vertragsnummer": self.Vertragsnummer,
            "Tarif": self.Tarif,
            "Vertragsbeginn": self.Vertragsbeginn,
            "Jahresentgelt": (
                float(self.Jahresentgelt) if self.Jahresentgelt is not None else None
            ),
            "SparbetragMonatlich": (
                float(self.SparbetragMonatlich)
                if self.SparbetragMonatlich is not None
                else None
            ),
            "Bausparsumme": (
                float(self.Bausparsumme) if self.Bausparsumme is not None else None
            ),
            "Zuteilungsdatum": self.Zuteilungsdatum,
            "AufloesungAlsVerwendung": self.AufloesungAlsVerwendung,
            "maximalerBetragVerwendung": (
                float(self.maximalerBetragVerwendung)
                if self.maximalerBetragVerwendung is not None
                else None
            ),
        }


class Einnahme(Base):
    __tablename__ = "Einnahme"

    pKey: Mapped[int] = mapped_column(primary_key=True)
    PersonID: Mapped[int] = mapped_column(ForeignKey("Person.pKey"))
    Summe: Mapped[float] = mapped_column(type_=Numeric)
    EinnahmeTyp: Mapped[int] = mapped_column()
    Beginn: Mapped[str] = mapped_column(type_=Text())
    AnzahlProJahr: Mapped[float] = mapped_column(type_=Numeric)

    person = relationship("Person", back_populates="einnahmen")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "PersonID": self.PersonID,
            "Summe": float(self.Summe) if self.Summe is not None else None,
            "EinnahmeTyp": self.EinnahmeTyp,
            "Beginn": self.Beginn,
            "AnzahlProJahr": (
                float(self.AnzahlProJahr) if self.AnzahlProJahr is not None else None
            ),
        }


class Finanzdaten(Base):
    __tablename__ = "Finanzdaten"

    pKey: Mapped[int] = mapped_column(primary_key=True)
    PersonID: Mapped[int] = mapped_column(ForeignKey("Person.pKey"))
    Bruttojahreseinkommen: Mapped[float] = mapped_column(type_=Numeric)
    Bruttovorjahreseinkommen: Mapped[float] = mapped_column(type_=Numeric)
    Rentenbeginn: Mapped[str] = mapped_column(type_=Text())
    IBAN: Mapped[str] = mapped_column(type_=Text())
    BIC: Mapped[str] = mapped_column(type_=Text())
    Kontoinhaber: Mapped[str] = mapped_column(type_=Text())

    person = relationship("Person", back_populates="finanzdaten")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "PersonID": self.PersonID,
            "Bruttojahreseinkommen": (
                float(self.Bruttojahreseinkommen)
                if self.Bruttojahreseinkommen is not None
                else None
            ),
            "Bruttovorjahreseinkommen": (
                float(self.Bruttovorjahreseinkommen)
                if self.Bruttovorjahreseinkommen is not None
                else None
            ),
            "Rentenbeginn": self.Rentenbeginn,
            "IBAN": self.IBAN,
            "BIC": self.BIC,
            "Kontoinhaber": self.Kontoinhaber,
        }


class Immobilie(Base):
    __tablename__ = "Immobilie"

    pKey: Mapped[int] = mapped_column(primary_key=True)
    PersonID: Mapped[int] = mapped_column(ForeignKey("Person.pKey"))
    Adresse: Mapped[str] = mapped_column(type_=Text())
    ImmobilieTyp: Mapped[int] = mapped_column()
    Fertighaus: Mapped[int] = mapped_column()
    mitEinliegerwohnung: Mapped[int] = mapped_column()

    person = relationship("Person", back_populates="immobilien")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "PersonID": self.PersonID,
            "Adresse": self.Adresse,
            "ImmobilieTyp": self.ImmobilieTyp,
            "Fertighaus": self.Fertighaus,
            "mitEinliegerwohnung": self.mitEinliegerwohnung,
        }


class Person(Base):
    __tablename__ = "Person"

    pKey: Mapped[int] = mapped_column(primary_key=True)
    Anrede: Mapped[str] = mapped_column(
        type_=Text(), nullable=False, server_default="3"
    )
    Vorname: Mapped[str] = mapped_column(
        type_=Text(), nullable=False, server_default=""
    )
    Name: Mapped[str] = mapped_column(type_=Text(), nullable=False, server_default="")
    Geburtsdatum: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Geburtsort: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Staatsangehoerigkeit: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Vorwahl: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Telefonnummer: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Email: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Familienstand: Mapped[int] = mapped_column(nullable=True)
    Adresse: Mapped[int] = mapped_column(ForeignKey("Adresse.pKey"), nullable=True)
    Steuernummer: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Sozialversicherungsnummer: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Beschaeftigungstyp: Mapped[int] = mapped_column(nullable=True)
    Beruf: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Arbeitgeber: Mapped[str] = mapped_column(type_=Text(), nullable=True)
    Beschaeftigungsstatus: Mapped[int] = mapped_column(nullable=True)

    adresse_obj = relationship("Adresse", back_populates="person")
    ausgaben = relationship("Ausgabe", back_populates="person")
    bausparvertraege = relationship("Bausparvertrag", back_populates="person")
    einnahmen = relationship("Einnahme", back_populates="person")
    finanzdaten = relationship("Finanzdaten", back_populates="person")
    immobilien = relationship("Immobilie", back_populates="person")
    sparplaene = relationship("Sparplan", back_populates="person")
    verbindlichkeiten = relationship("Verbindlichkeit", back_populates="person")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "Anrede": self.Anrede,
            "Vorname": self.Vorname,
            "Name": self.Name,
            "Geburtsdatum": self.Geburtsdatum,
            "Geburtsort": self.Geburtsort,
            "Staatsangehoerigkeit": self.Staatsangehoerigkeit,
            "Vorwahl": self.Vorwahl,
            "Telefonnummer": self.Telefonnummer,
            "Email": self.Email,
            "Familienstand": self.Familienstand,
            "Steuernummer": self.Steuernummer,
            "Sozialversicherungsnummer": self.Sozialversicherungsnummer,
            "Beschaeftigungstyp": self.Beschaeftigungstyp,
            "Beruf": self.Beruf,
            "Arbeitgeber": self.Arbeitgeber,
            "Beschaeftigungsstatus": self.Beschaeftigungsstatus,
            "Adresse": self.adresse_obj.to_dict() if self.adresse_obj else None,
            "Ausgaben": [ausgabe.to_dict() for ausgabe in self.ausgaben],
            "Bausparvertraege": [
                vertrag.to_dict() for vertrag in self.bausparvertraege
            ],
            "Einnahmen": [einnahme.to_dict() for einnahme in self.einnahmen],
            "Finanzdaten": self.finanzdaten.to_dict() if self.finanzdaten else None,
            "Immobilien": [immobilie.to_dict() for immobilie in self.immobilien],
            "Sparplaene": [sparplan.to_dict() for sparplan in self.sparplaene],
            "Verbindlichkeiten": [
                verbindlichkeit.to_dict() for verbindlichkeit in self.verbindlichkeiten
            ],
        }


class Sparplan(Base):
    __tablename__ = "Sparplan"

    pKey: Mapped[int] = mapped_column(primary_key=True)
    PersonID: Mapped[int] = mapped_column(ForeignKey("Person.pKey"))
    Wert: Mapped[float] = mapped_column(type_=Numeric)
    monatlicheAusgabe: Mapped[float] = mapped_column(type_=Numeric)

    person = relationship("Person", back_populates="sparplaene")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "PersonID": self.PersonID,
            "Wert": float(self.Wert) if self.Wert is not None else None,
            "monatlicheAusgabe": (
                float(self.monatlicheAusgabe)
                if self.monatlicheAusgabe is not None
                else None
            ),
        }


class Verbindlichkeit(Base):
    __tablename__ = "Verbindlichkeit"
    __table_args__ = {"sqlite_autoincrement": True}

    pKey: Mapped[int] = mapped_column(primary_key=True)
    PersonID: Mapped[int] = mapped_column(ForeignKey("Person.pKey"))
    RateMonatlich: Mapped[float] = mapped_column(type_=Numeric)
    Glaeubiger: Mapped[str] = mapped_column(type_=Text())
    Laufzeitende: Mapped[str] = mapped_column(type_=Text())
    Restschuld: Mapped[float] = mapped_column(type_=Numeric)
    WirdAbgeloest: Mapped[int] = mapped_column()
    Kommentar: Mapped[str] = mapped_column(type_=Text(), nullable=True)

    person = relationship("Person", back_populates="verbindlichkeiten")

    def to_dict(self):
        return {
            "pKey": self.pKey,
            "PersonID": self.PersonID,
            "RateMonatlich": (
                float(self.RateMonatlich) if self.RateMonatlich is not None else None
            ),
            "Glaeubiger": self.Glaeubiger,
            "Laufzeitende": self.Laufzeitende,
            "Restschuld": (
                float(self.Restschuld) if self.Restschuld is not None else None
            ),
            "WirdAbgeloest": self.WirdAbgeloest,
            "Kommentar": self.Kommentar,
        }
