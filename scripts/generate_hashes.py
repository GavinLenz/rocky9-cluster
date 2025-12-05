#!/usr/bin/env python3

import getpass
import sys

from passlib.hash import sha512_crypt


def main():
    print("Enter password to hash (input hidden):")
    pw = getpass.getpass()

    if not pw:
        print("Error: empty password not allowed")
        sys.exit(1)

    hash_val = sha512_crypt.hash(pw)

    print("\nGenerated SHA-512 password hash:")
    print(hash_val)
    print("\nCopy and paste these lines into your .env file:")
    print(f'PXE_ROOT_PASSWORD_HASH="{hash_val}"')
    print(f'PXE_LOCAL_USER_PASSWORD_HASH="{hash_val}"')


if __name__ == "__main__":
    main()
