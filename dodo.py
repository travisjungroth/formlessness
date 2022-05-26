import subprocess

DOIT_CONFIG = {"default_tasks": ["format", "test"]}


def task_format():
    return _shed(_changed_files("main"))


def task_format_all():
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True
    ).stdout.splitlines()
    return _shed(tracked)


def task_format_last():
    return _shed(_changed_files("HEAD~1"))


def task_test():
    return {
        "actions": ["pytest --doctest-modules"],
    }


def task_autoformat():
    return {"actions": [_autoformat]}


def _autoformat():
    message = "autoformat"
    out = subprocess.run(
        ["git", "log", "--format=%s", "-3"], capture_output=True, text=True
    ).stdout
    if out == f"{message}\n" * 3:
        print("Three times, enough already.")
        exit(1)

    subprocess.run(
        ["doit", "format_last"]
    )
    subprocess.run(["git", "commit", "-am", message])


def _changed_files(ref: str):
    out = subprocess.run(
        ["git", "diff", ref, "--name-only", "--diff-filter=d"],
        capture_output=True,
        text=True,
    ).stdout
    return out.splitlines()


def _shed(files):
    files = [f for f in files if f[-3:] in (".py", ".md")]
    return {"actions": [f"shed {' '.join(files)} --py39-plus"], "file_dep": files}
