# app/core/enums.py
import enum

class PaymentMethod(str, enum.Enum):
    CASH = "Cash"
    CHEQUE = "Cheque"

class PropertyType(str, enum.Enum):
    HOME = "Home"
    APARTMENT = "Apartment"

class LeadStatus(str, enum.Enum):
    new = "new"
    qualified = "qualified"
    viewing = "viewing"