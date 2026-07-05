# Copyright 2016, 2017 DGT NETWORK INC © Stanislav Parsov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import base64
import hashlib
import random
import time
from datetime import datetime
from dgt_signing import CryptoFactory,create_context
from app.utils.logger import logger as LOGGER


def _sha512(data):
    return hashlib.sha512(data).hexdigest()


_context = create_context('secp256k1')                                         
_private_key = _context.new_random_private_key()                          
_public_key = _context.get_public_key(_private_key)                  
_crypto_factory = CryptoFactory(_context)                                 
signer = _crypto_factory.new_signer(_private_key)                   
LOGGER.debug(' _signer PUBLIC_KEY=%s',_public_key.as_hex()[:8])








