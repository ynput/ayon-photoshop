import sys
import platform

def main():
    machine = platform.machine()
    if machine in ('arm64', 'aarch64'):
        print('ARM')
    elif machine in ('x86_64', 'AMD64'):
        print('x86_64')
    else:
        print(f'Unknown architecture: {machine}')
        sys.exit(1)

if __name__ == '__main__':
    main()
