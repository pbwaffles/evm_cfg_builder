import re
import sys
import argparse
import logging
import os
from pkg_resources import require
from pyevmasm import disassemble_all

from crytic_compile import cryticparser, CryticCompile, InvalidCompilation, is_supported

from .cfg import CFG

logging.basicConfig()
logger = logging.getLogger("evm-cfg-builder")

def output_to_dot(d, filename, cfg):
    if not os.path.exists(d):
        os.makedirs(d)
    filename = os.path.basename(filename)
    filename = os.path.join(d, filename+ '_')
    cfg.output_to_dot(filename)
    for function in cfg.functions:
        function.output_to_dot(filename)

def parse_args():
    parser = argparse.ArgumentParser(description='evm-cfg-builder',
                                     usage="evm-cfg-builder contract.evm [flag]")

    parser.add_argument('filename',
                        help='contract.evm')

    parser.add_argument('--export-dot',
                        help='Export the functions to .dot files in the directory',
                        action='store',
                        dest='dot_directory',
                        default='crytic-export/evm')

    parser.add_argument('--version',
                        help='displays the current version',
                        version=require('evm-cfg-builder')[0].version,
                        action='version')

    cryticparser.init(parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    return args

def _run(bytecode, filename, args):
    cfg = CFG(bytecode)

    for function in cfg.functions:
        logger.info(function)

    if args.dot_directory:
        output_to_dot(args.dot_directory, filename, cfg)

def main():

    l = logging.getLogger('evm-cfg-builder')
    l.setLevel(logging.INFO)
    args = parse_args()

    if is_supported(args.filename):
        filename = args.filename
        del args.filename
        try:
            cryticCompile = CryticCompile(filename, **vars(args))
            for contract in cryticCompile.contracts_names:
                bytecode_init = cryticCompile.bytecode_init(contract)
                if bytecode_init:
                    logger.info(f'Analyze {contract}')
                    _run(bytecode_init, f'{filename}-{contract}-init', args)
                    _run(cryticCompile.bytecode_runtime(contract),  f'{filename}-{contract}-runtime', args)
        except InvalidCompilation as e:
            logger.error(e)

    else:
        with open(args.filename, 'rb') as f:
            bytecode = f.read()
        logger.info(f'Analyze {args.filename}')
        _run(bytecode, args.filename, args)





if __name__ == '__main__':
    main()
