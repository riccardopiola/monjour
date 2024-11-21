from dataclasses import dataclass

@dataclass
class Config:
    # Currency code (ISO 4217)
    currency: str

    # Locale code (ISO 3166-1)
    locale: str

    # Time zone code (IANA Time Zone Database)
    time_zone: str

    # Directory where the imported files are archived
    appdata_dir: str

    # Name of the user
    name: str = ""

    # Surname of the user
    surname: str = ""
