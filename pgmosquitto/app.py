import argparse
import base64
import os
import random
import sys

from passlib.hash import pbkdf2_sha256
from passlib.utils.binary import HASH64_CHARS, ab64_decode
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    print('Please set DATABASE_URL')
    sys.exit(1)


engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    superuser = Column(Boolean())


class ACL(Base):
    __tablename__ = 'acl'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True, index=True)
    topic = Column(String(255), nullable=False, index=True)
    permissions = Column(Integer)


def crypt(plain):
    chars = []
    for i in range(16):
        chars.append(random.choice(HASH64_CHARS))
    salt = ''.join(chars).encode()
    h = pbkdf2_sha256.using(salt=salt).hash(plain).split('$')

    return 'PBKDF2$sha256${}${}${}'.format(
        h[2], ab64_decode(h[3]).decode(),
        base64.b64encode(ab64_decode(h[4])).decode())


def parse_args():
    parser = argparse.ArgumentParser(description='Postgres Mosquitto Tool')
    parser.add_argument('--list-accounts', action='store_true')
    parser.add_argument('--list-acls', action='store_true')
    parser.add_argument('--add-account', nargs=3,
                        metavar=('USERNAME', 'PASSWORD', 'SUPERUSER'))
    parser.add_argument('--add-acl', nargs=3,
                        metavar=('USERNAME', 'TOPIC', 'PERMISSIONS'))
    parser.add_argument('--remove-account', metavar=('USERNAME'))
    parser.add_argument('--remove-acl', nargs=2,
                        metavar=('USERNAME', 'TOPIC'))
    parser.add_argument('--drop-all', action='store_true')

    return (parser, parser.parse_args())


def add_account(args):
    username = args[0]
    password = crypt(args[1])
    superuser = args[2]

    if superuser.lower().startswith('y') or superuser == '1':
        superuser = True
    else:
        superuser = False

    account = Account(
        username=username,
        password=password,
        superuser=superuser
    )

    session.add(account)
    session.commit()

    print('Added account {}.'.format(username))


def add_acl(args):
    username = args[0]
    topic = args[1]
    permissions = args[2]

    acl = ACL(
        username=username,
        topic=topic,
        permissions=permissions
    )

    session.add(acl)
    session.commit()

    print('Added acl {} topic {} permissions {}.'.format(
        username, topic, permissions))


def remove_account(username):
    account = session.query(Account).filter_by(username=username).first()
    if account:
        session.delete(account)
        session.commit()

        print('Removed account {}.'.format(username))


def remove_acl(args):
    username = args[0]
    topic = args[1]
    acl = session.query(ACL).filter_by(
                username=username, topic=topic).first()
    if acl:
        session.delete(acl)
        session.commit()

        print('Removed acl {} topic {}.'.format(username, topic))


def list_accounts():
    for account in session.query(Account).all():
        username = account.username
        superuser = account.superuser

        if superuser:
            superuser = 'YES'
        else:
            superuser = 'NO'

        print('Username: {} Superuser: {}'.format(username, superuser))


def list_acls():
    perms_map = [
        'none',
        'read',
        'write',
        'read and write',
        'subscribe',
        'read and subscribe',
        'write and subscribe',
        'read, write, and subscribe'
    ]

    for acl in session.query(ACL).all():
        print('Username: {} Topic: {} Permissions: {}'.format(
            acl.username, acl.topic, perms_map[acl.permissions]
        ))


def main():
    Base.metadata.create_all(engine)

    (parser, args) = parse_args()

    if args.drop_all:
        Base.metadata.drop_all(engine)

        print('Dropped all tables.')
        sys.exit(0)

    if args.add_account:
        add_account(args.add_account)
    elif args.add_acl:
        add_acl(args.add_acl)
    elif args.remove_account:
        remove_account(args.remove_account)
    elif args.remove_acl:
        remove_acl(args.remove_acl)
    elif args.list_accounts:
        list_accounts()
    elif args.list_acls:
        list_acls()
    else:
        parser.print_help()
