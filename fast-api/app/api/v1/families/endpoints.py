from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from app.schemas import DgtResponse
from app.utils.logger import logger as LOGGER
router = APIRouter()

# Transaction families exposed through this gateway.
# Token families (bgt/dec) were removed from dgt-mini - no financial semantics.
TX_FAMILIES = {}

@router.get("/tx_families",response_model=DgtResponse)
async def get_tx_families(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """
    get  tx families
    """
    LOGGER.debug('Request tx_families endpoint=%s',request)
    return query._wrap_response(
        request,
        data=TX_FAMILIES,
        metadata=query._get_metadata(request, None)
        )

@router.get("/run") #,response_model=DgtResponse)
async def run_transaction(request: Request,family: str,cmd: str,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """
    run transaction for a registered family
    """
    # undefined families
    return query._wrap_response(
      request,
       data=None,
       metadata={
       'link': '',
      }
    )
