#!/usr/bin/env python3
import subprocess

exit_code = 1
tries = 0
while exit_code:
    if tries == 4:
        print(f'Gave up after {tries} tries.')
        exit(1)
    exit_code = subprocess.run(["pre-commit", "run", "--all-files"]).returncode
    tries += 1
subprocess.run(["git", "add", "-u"])


