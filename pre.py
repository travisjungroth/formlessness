#!/usr/bin/env python3
import subprocess

if subprocess.run(["git", "status", "--untracked-files=no", "--porcelain"]).stdout:
    print("Uncomitted changes.")
    exit(1)

exit_code = 1
tries = 0
while exit_code:
    if tries == 4:
        print(f'Gave up after {tries} tries.')
        exit(1)
    exit_code = subprocess.run(["pre-commit", "run", "--all-files"]).returncode
    tries += 1
if tries > 1:
    subprocess.run(["git", "commit", "-am", "pre-commit"])
