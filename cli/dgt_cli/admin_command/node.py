# Copyright 2020 DGT NETWORK INC © Stanislav Parsov 
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

import os
import shutil
import sys
import json
from dgt_cli.exceptions import CliException
from dgt_cli.admin_command.config import get_key_dir
from dgt_cli.keygen import create_new_key,_read_signer
from dgt_signing import create_context
from dgt_signing.core import X509_COUNTRY_NAME,X509_STATE_OR_PROVINCE_NAME,X509_LOCALITY_NAME,X509_ORGANIZATION_NAME,X509_COMMON_NAME,X509_DNS_NAME

DGT_TOP = os.environ.get('DGT_TOP',"dgt")
PROJ_DGT = f'/project/{DGT_TOP}'
PROJ_PEER = '/project/peer'
PROJ_ETC  = f'{PROJ_DGT}/etc'
DEF_PEER = 'dgt1'
DYN_CLUST = 'dyn'
DYN_SUFF = ".dyn"
STATIC_SUFF = '.static'
DGT_NET_MAP = "dgt.net.map"
NET_NEST_NM = "dgt.net.nest"
CERT_SRC_NM = 'certificate.json'
CERT_NM     = 'certificate.pem' 
KYC_NM      = 'kyc.txt'
DATA_DIR = "data"
ETC_DIR  = "etc"
KEYS_DIR = "keys"
LOGS_DIR = "logs"
POLICY_DIR = "policy"

def add_node_parser(subparsers, parent_parser):
    """Adds subparser command and flags for 'keygen' command.

    Args:
        subparsers (:obj:`ArguementParser`): The subcommand parsers.
        parent_parser (:obj:`ArguementParser`): The parent of the subcomman
            parsers.
    """
    description = 'Generates dirs for the peer'

    epilog = (
        'The dirs are stored in '
        '/project/peer/ and '
        
    )

    parser = subparsers.add_parser(
        'node',
        help=description,
        description=description + '.',
        epilog=epilog,
        parents=[parent_parser])

    
    parser.add_argument(
        'cluster_name',
        help='name of the cluster',
        nargs='?')
    parser.add_argument(
        'peer_name',
        help='name of the peer',
        nargs='?')
    parser.add_argument(
        '--force',
        help="overwrite files if they exist",
        action='store_true')
    parser.add_argument(                              
        '-t', '--topo_type',                                
        type=str,                                          
        help='specify topology type',        
        default='static'                          
        ) 
    parser.add_argument(                 
        '-cb', '--crypto_back',               
        type=str,                             
        help='Specify a crypto back',         
        default='bitcoin')  
    parser.add_argument(                    
        '-kyc',             
        type=str,                           
        help='Specify KYC for NODE',       
        default=None)                  
                                                                       

    parser.add_argument(
        '-q',
        '--quiet',
        help="do not display output",
        action='store_true')



def get_topology_nest(map_nm,cnm,pnm):
    with open(map_nm,"r") as map_file:                              
        try:                                                              
            map_data =  map_file.read()                               
            mapping = json.loads(map_data)
            if cnm != DYN_CLUST:
                nest =  mapping[cnm][pnm]
            else:
                nest = DYN_CLUST
            print(f"PEER {cnm}.{pnm} -> {nest}")
            return nest
        except Exception as ex:   
            print(f"CANT GET MAPPING FOR PEER {cnm}.{pnm} FROM={map_nm} ({ex})")                                        
            return None                                                          

def get_cert_proto(fnm):
    with open(fnm,"r") as cert_file:                                                  
        try:                                                                            
            return json.load(cert_file)                                              
            
        except Exception as ex:                                                         
            print(f"CANT LOAD CERT FROM={fnm} ({ex})")        
            return {X509_COUNTRY_NAME : "ru",                   
                    X509_STATE_OR_PROVINCE_NAME:"Tomsk",        
                    X509_LOCALITY_NAME:"city",                  
                    X509_ORGANIZATION_NAME:"home",              
                    X509_COMMON_NAME:"stas",                    
                    X509_DNS_NAME:"dgt.net"                     
                    }                                           
        
def save_topology_nest(dst,topology_nest):
    print(f"SAVE NEST  {topology_nest} -> {dst}")
    with open(dst, 'w') as fd:                              
        fd.write(f"{topology_nest}\n")                                
        

def make_dir(dname,force=False):                                                          
                                                                              
    if os.path.exists(dname):                                                 
        print('Dir exists: {}'.format(dname), file=sys.stderr)                
        if force:                                                        
            print('Recreate : {}'.format(dname), file=sys.stderr)             
            os.rmdir(dname)                                                   
        else:                                                                 
            return                                                            
    print('Create Dir : {}'.format(dname), file=sys.stderr)                   
    os.mkdir(dname, mode=0o777)                                               
                                                                              
def copy_file(src,dst,force):                                                                               
    try:                                                                                              
        if not os.path.isfile(dst) or force:                                                     
            shutil.copyfile(src, dst)                                                                 
            shutil.copymode(src, dst)                                                                 
            print('Copy file: {}'.format(dst), file=sys.stdout)                                       
        else:                                                                                         
            print('Skip copy file: {} - already exists'.format(dst), file=sys.stdout)                 
    except Exception as ex:                                                                           
        print('Cant copy file: {} ({})'.format(dst,ex), file=sys.stdout)                              





def do_node(args):
    """Executes the dirs generation operation

    Args:
        args (:obj:`Namespace`): The parsed args.
    """
    KYC = args.kyc 
    if args.cluster_name is not None:
        cluster_name = args.cluster_name
    else:
        cluster_name = DYN_CLUST
    if args.peer_name is not None:
        peer_name = args.peer_name
    else:
        peer_name = DEF_PEER
    crypto_back = args.crypto_back
    crypto_suff = f".{crypto_back}" if crypto_back != 'bitcoin' else '.bitcoin'

    is_dyn_peering = (args.topo_type == 'dynamic')
    print(f"PEERING={args.topo_type} KYC={KYC}")
    node_dir = PROJ_PEER
    etc_dyn_dir  = f'{PROJ_DGT}/etc'
    if cluster_name == DYN_CLUST:
        etc_dir  = f'{PROJ_DGT}/etc' # config sources
    else:
        etc_dir = os.path.join(f"{PROJ_DGT}/clusters",cluster_name,peer_name,ETC_DIR)
        keys_dir = os.path.join(f"{PROJ_DGT}/clusters",cluster_name,peer_name,KEYS_DIR)

    if not os.path.exists(node_dir):
        raise CliException("Peer directory does not exist: {}".format(node_dir))
    
    
    try:
        topology_nest = None
        for filename in [DATA_DIR, ETC_DIR,KEYS_DIR,LOGS_DIR,POLICY_DIR]:                    
            dname = os.path.join(node_dir, filename) 
            make_dir(dname,force=args.force)                              
             
            if filename == ETC_DIR:
                # add config
                for fnm in ["validator.toml", "log_config.toml","dgt.conf","dgt.net",DGT_NET_MAP]:
                    dst = os.path.join(dname, fnm)
                    if fnm == "log_config.toml":
                        src = os.path.join(etc_dyn_dir, fnm+DYN_SUFF)
                    elif fnm == "dgt.conf":
                        src = os.path.join(etc_dyn_dir, fnm+(DYN_SUFF if is_dyn_peering else STATIC_SUFF))
                    elif fnm == "dgt.net":
                        src = os.path.join(etc_dyn_dir, fnm+(DYN_SUFF if is_dyn_peering else STATIC_SUFF))
                    elif fnm == DGT_NET_MAP:
                        # make mapping for this peer 
                        src = os.path.join(etc_dyn_dir, fnm)
                        topology_nest = get_topology_nest(src,cluster_name,peer_name)
                    else:
                        src = os.path.join(etc_dir, fnm+(DYN_SUFF if cluster_name == DYN_CLUST else ''))
                    copy_file(src,dst,force=args.force)

            elif filename == KEYS_DIR and cluster_name != DYN_CLUST:
                if topology_nest is not None:
                    dst = os.path.join(dname, NET_NEST_NM)
                    save_topology_nest(dst,topology_nest)
                for fnm in ["validator.priv", "validator.pub"]:
                    dst = os.path.join(dname, fnm)
                    src = os.path.join(keys_dir, f"{fnm}{crypto_suff}")
                    if not os.path.isfile(src):
                        print(f"NO VALIDTOR KEYS={src}")
                        create_new_key(src,os.path.join(keys_dir, f"validator.pub{crypto_suff}"),backend=crypto_back)
                    else:
                        print(f"VALIDATOR KEYS={src}->{dst}")

                    copy_file(src,dst,force=args.force)
                fcrt = os.path.join(dname, CERT_NM)
                if not os.path.isfile(fcrt):
                    # create certificate
                    signer = _read_signer(os.path.join(dname, "validator.priv"),backend=args.crypto_back)
                    cert_src_fnm = os.path.join(PROJ_ETC,CERT_SRC_NM)
                    info = get_cert_proto(cert_src_fnm)  
                    cert = signer.context.create_x509_certificate(info,signer.private_key,after=10)                                                                                                                     
                    with open(fcrt, "wb") as f:                                                                                                                                               
                        f.write(cert) 
                if KYC is not None:
                    # this file is trigger for notary mode
                    # and we should check notaries key into dgt.net.map
                    fkyc = os.path.join(dname, KYC_NM)
                    with open(fkyc, "w") as f:  
                        f.write(KYC)            


    except IOError as ioe:
        raise CliException('IOError: {}'.format(str(ioe)))
    except Exception as ex:
        raise CliException('Exception: {}'.format(str(ex)))
