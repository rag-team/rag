from server.schlagwortdb.database import SessionLocal
from server.schlagwortdb.models import Adresse, Kunde

# Create a session
session = SessionLocal()

adresse_data = [
    Adresse(strasse="Musterstraße", hausnummer=1, hausnummerZusatz="A", plz=10115, ort="Berlin"),
    Adresse(strasse="Beispielweg", hausnummer=23, hausnummerZusatz="", plz=80331, ort="München"),
    Adresse(strasse="Hauptstraße", hausnummer=45, hausnummerZusatz="B", plz=50667, ort="Köln"),
    Adresse(strasse="Bahnhofstraße", hausnummer=67, hausnummerZusatz="C", plz=20095, ort="Hamburg"),
    Adresse(strasse="Gartenweg", hausnummer=89, hausnummerZusatz="", plz=70173, ort="Stuttgart")
]

kunde_data = [
    Kunde(anrede="Herr", vorname="Max", name="Mustermann", geburtsdatum="1985-05-10", geburtsort="Berlin", staatsangehoerigkeit="Deutsch", vorwahl=30, telefonnummer=12345678, email="max.mustermann@example.com", familienstand=1, adresse=1),
    Kunde(anrede="Frau", vorname="Erika", name="Musterfrau", geburtsdatum="1990-07-20", geburtsort="München", staatsangehoerigkeit="Deutsch", vorwahl=89, telefonnummer=23456789, email="erika.musterfrau@example.com", familienstand=2, adresse=2),
    Kunde(anrede="Herr", vorname="Hans", name="Beispielmann", geburtsdatum="1978-09-15", geburtsort="Köln", staatsangehoerigkeit="Deutsch", vorwahl=221, telefonnummer=34567890, email="hans.beispielmann@example.com", familienstand=1, adresse=3),
    Kunde(anrede="Frau", vorname="Anna", name="Testfrau", geburtsdatum="1982-11-30", geburtsort="Hamburg", staatsangehoerigkeit="Deutsch", vorwahl=40, telefonnummer=45678901, email="anna.testfrau@example.com", familienstand=3, adresse=4),
    Kunde(anrede="Herr", vorname="Peter", name="Beispielmann", geburtsdatum="1995-03-25", geburtsort="Stuttgart", staatsangehoerigkeit="Deutsch", vorwahl=711, telefonnummer=56789012, email="peter.beispielmann@example.com", familienstand=1, adresse=5)
]

# Add Kunde data to session
session.add_all(kunde_data)
session.add_all(adresse_data)
session.commit()
