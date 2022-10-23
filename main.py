"""squirrel.

Usage:
  squirrel get (<package>)... [--no-index]
  squirrel remove (<package>)... [--no-index]
  squirrel info (<package>)...
  squirrel upgrade
  squirrel (-h | --help)
  squirrel (-v | --version)

Options:
  -h --help     Show this screen.
  -v --version     Show version.
  --no-index    Do not save installation in index (remove will be forced even if the package is not installed)
"""

from docopt import docopt
import operations

if __name__ == '__main__':
    args = docopt(__doc__, version="squirrel 1.0.0-dev")
    if args.get('get'):
        operations.get(args.get('<package>'), args.get('--no-index'))
    elif args.get('info'):
        operations.info(args.get('<package>'))
    elif args.get('remove'):
        operations.remove(args.get('<package>'), args.get('--no-index'))
    elif args.get('upgrade'):
        operations.upgrade()