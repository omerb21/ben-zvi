from typing import Optional, Dict

from pydantic import BaseModel


class ClientBase(BaseModel):
    idNumber: str
    fullName: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    addressStreet: Optional[str] = None
    addressCity: Optional[str] = None
    addressPostalCode: Optional[str] = None
    birthDate: Optional[str] = None
    gender: Optional[str] = None
    maritalStatus: Optional[str] = None
    birthCountry: Optional[str] = None
    employerName: Optional[str] = None
    employerHp: Optional[str] = None
    employerAddress: Optional[str] = None
    employerPhone: Optional[str] = None
    addressHouseNumber: Optional[str] = None
    addressApartment: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientRead(ClientBase):
    id: int

    class Config:
        from_attributes = True


class SnapshotBase(BaseModel):
    fundCode: str
    fundType: Optional[str] = None
    fundName: Optional[str] = None
    fundNumber: Optional[str] = None
    source: Optional[str] = None
    amount: float
    snapshotDate: str
    isActive: bool = True
    extraField1: Optional[str] = None
    extraField2: Optional[str] = None


class SnapshotCreate(SnapshotBase):
    pass


class SnapshotRead(SnapshotBase):
    id: int
    clientId: int

    class Config:
        from_attributes = True


class ClientSummaryItem(BaseModel):
    id: int
    fullName: str
    idNumber: str
    totalAmount: float
    sources: str
    rawSources: str
    fundCount: int
    lastUpdate: Optional[str] = None


class SummaryResponse(BaseModel):
    month: Optional[str]
    totalAssets: float
    bySource: Dict[str, float]
    byFundType: Dict[str, float]


class MonthlyChangePoint(BaseModel):
    month: str
    total: float
    change: Optional[float] = None
    percentChange: Optional[float] = None


class HistoryPoint(BaseModel):
    month: str
    amount: float


class FundHistoryPoint(BaseModel):
    date: str
    amount: float
    source: str
    change: Optional[float] = None


class NoteBase(BaseModel):
    note: str
    reminderAt: Optional[str] = None


class NoteCreate(NoteBase):
    pass


class NoteRead(NoteBase):
    id: int
    createdAt: str
    dismissedAt: Optional[str] = None


class ReminderRead(BaseModel):
    id: int
    note: str
    createdAt: str
    reminderAt: Optional[str] = None
    dismissedAt: Optional[str] = None
    clientId: int
    clientName: str


class ClientUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    addressStreet: Optional[str] = None
    addressCity: Optional[str] = None
    addressPostalCode: Optional[str] = None
    birthDate: Optional[str] = None
    gender: Optional[str] = None
    maritalStatus: Optional[str] = None
    birthCountry: Optional[str] = None
    employerName: Optional[str] = None
    employerHp: Optional[str] = None
    employerAddress: Optional[str] = None
    employerPhone: Optional[str] = None
    addressHouseNumber: Optional[str] = None
    addressApartment: Optional[str] = None
