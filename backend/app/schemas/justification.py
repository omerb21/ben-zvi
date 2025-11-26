from typing import Optional, List

from pydantic import BaseModel


class SavingProductRead(BaseModel):
    id: int
    fundType: str
    companyName: str
    fundName: str
    fundCode: str
    yield1yr: Optional[float] = None
    yield3yr: Optional[float] = None
    riskLevel: Optional[int] = None
    guaranteedReturn: Optional[str] = None

    class Config:
        from_attributes = True


class ExistingProductRead(BaseModel):
    id: int
    clientId: int
    fundType: str
    companyName: str
    fundName: str
    fundCode: str
    yield1yr: Optional[float] = None
    yield3yr: Optional[float] = None
    personalNumber: str
    managementFeeBalance: Optional[float] = None
    managementFeeContributions: Optional[float] = None
    accumulatedAmount: Optional[float] = None
    employmentStatus: Optional[str] = None
    hasRegularContributions: Optional[bool] = None
    isVirtual: Optional[bool] = None

    class Config:
        from_attributes = True


class ExistingProductCreate(BaseModel):
    fundType: str
    companyName: str
    fundName: str
    fundCode: str
    yield1yr: Optional[float] = None
    yield3yr: Optional[float] = None
    personalNumber: str
    managementFeeBalance: Optional[float] = None
    managementFeeContributions: Optional[float] = None
    accumulatedAmount: Optional[float] = None
    employmentStatus: Optional[str] = None
    hasRegularContributions: Optional[bool] = None


class ExistingProductUpdate(BaseModel):
    fundType: Optional[str] = None
    companyName: Optional[str] = None
    fundName: Optional[str] = None
    fundCode: Optional[str] = None
    yield1yr: Optional[float] = None
    yield3yr: Optional[float] = None
    personalNumber: Optional[str] = None
    managementFeeBalance: Optional[float] = None
    managementFeeContributions: Optional[float] = None
    accumulatedAmount: Optional[float] = None
    employmentStatus: Optional[str] = None
    hasRegularContributions: Optional[bool] = None


class NewProductBase(BaseModel):
    fundType: str
    companyName: str
    fundName: str
    fundCode: str
    yield1yr: Optional[float] = None
    yield3yr: Optional[float] = None
    personalNumber: Optional[str] = None
    managementFeeBalance: Optional[float] = None
    managementFeeContributions: Optional[float] = None
    accumulatedAmount: Optional[float] = None
    employmentStatus: Optional[str] = None
    hasRegularContributions: Optional[bool] = None


class NewProductCreate(NewProductBase):
    existingProductId: Optional[int] = None


class NewProductRead(NewProductBase):
    id: int
    clientId: int
    existingProductId: Optional[int] = None

    class Config:
        from_attributes = True


class FormInstanceBase(BaseModel):
    templateFilename: str
    status: Optional[str] = None
    filledData: Optional[dict] = None
    fileOutputPath: Optional[str] = None


class FormInstanceCreate(FormInstanceBase):
    pass


class FormInstanceRead(FormInstanceBase):
    id: int
    newProductId: int

    class Config:
        from_attributes = True


class FormOverlayPayload(BaseModel):
    freeText: Optional[str] = None
    signatureDataUrl: Optional[str] = None
    signaturePosition: Optional[str] = None


class ClientSignatureSubmitPayload(BaseModel):
    signatureDataUrl: str


class PacketTrimPayload(BaseModel):
    pagesToRemove: List[int]
