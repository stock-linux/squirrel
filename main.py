"""squirrel.

Usage:
  squirrel get (<package>)...
  squirrel remove <package>
  squirrel info <package>
  squirrel update <package>
  squirrel upgrade
  squirrel (-h | --help)
  squirrel (-v | --version)

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

from docopt import docopt
import operations

if __name__ == '__main__':
    args = docopt(__doc__, version="squirrel 1.0.0-dev")
    
    if args.get('get'):
        operations.get(args.get('<package>'))
    elif args.get('info'):
        operations.info(args.get('<package>'))
    elif args.get('remove'):
        operations.remove(args.get('<package>'))
    elif args.get('update'):
        operations.update(args.get('<package>'))
    elif args.get('upgrade'):
        operations.update()