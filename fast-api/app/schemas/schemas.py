from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union

class DgtBaseResponse(BaseModel):
    link: str


class DgtResponse(DgtBaseResponse):
    data: Dict[str,Any]

class DgtListResponse(DgtBaseResponse):
    data: List[Any]

class DgtPagingListResponse(DgtListResponse):
    head: Optional[str]
    paging: Dict[str,Any]

class DgtPagingDictResponse(DgtResponse):
    head: Optional[str]
    paging: Dict[str,Any]


class UserBase(BaseModel):
    name: str


class UserCreate(UserBase):
    password: str
    email   : str

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True
        #orm_mode = True

class OwnerSignPayload(BaseModel):     

    emitter    :  str              # owner pub key                              
    signature  :  str              # signature
    payload    :  Optional[bytes] = None            #   

class CertInfo(BaseModel):
    COUNTRY_NAME              : str = "CA"
    STATE_OR_PROVINCE_NAME    : str = "ONTARIO"
    LOCALITY_NAME             : str = "BARRIE"
    ORGANIZATION_NAME         : str = "YOUR ORGANIZATION NAME" 
    COMMON_NAME               : str = "NODE SAMPLE"
    DNS_NAME                  : str = "dgt.world"
    EMAIL_ADDRESS             : str = "adminmail@mail.com"
    PSEUDONYM                 : str = "dgt00000000000000000"
    JURISDICTION_COUNTRY_NAME : str = "CA"
    BUSINESS_CATEGORY         : str = "YOUR BUSINESS CATEGORY"
    USER_ID                   : str = "000000000000000001" 
    #
    FIRST_NAME                : Optional[str] = "CA"
    LAST_NAME                 : Optional[str] = "CA"
    PHONE                     : Optional[str] = "CA"
    FULL_ADDRESS              : Optional[str] = "CA"
    DATE_OF_BIRTH             : Optional[str] = "CA"
    PASSPORT_ID_DOCUMENT      : Optional[str] = "CA" # hash
    PHOTOGRAPH                : Optional[str] = "CA" # hash

class CertInfoCreate(BaseModel):                            
    cert         : CertInfo                
    owner        : str 

        
class CertCreate(BaseModel):                                   
    info         : CertInfoCreate                
    signed       : Optional[OwnerSignPayload] = None
    photograph   : Optional[bytes] = None           
    document     : Optional[bytes] = None 

class DgtMetricItems(BaseModel):
    values : List[Dict[str,Any]]

class DgtMetricResponse(DgtBaseResponse):     
    #columns: List[str] 
    data : DgtMetricItems                        
