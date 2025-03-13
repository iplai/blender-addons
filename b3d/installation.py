import os
import site
import subprocess
import sys

import bpy


def get_infos():
    data = {}
    data['site_packages'] = next((p for p in sys.path if p.endswith('site-packages')), None).replace('\\', '/')
    data['executable'] = sys.executable.replace("\\", "/")
    command = [sys.executable, "-m", "pip", "config", "get", "global.index-url"]
    data['index-url'] = subprocess.getoutput(command)
    from rich import print
    print(data)


def set_pip_index_url(index_url="https://pypi.org/simple"):
    # index_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    python_path = sys.executable
    command = [python_path, "-m", "pip", "config", "set", "global.index-url", index_url]
    print("Execute:", " ".join(command))
    subprocess.run(command, shell=True, check=True)


def set_pip_index_url():
    index_url = "https://pypi.org/simple"
    index_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    command = [sys.executable, "-m", "pip", "config", "set", "global.index-url", index_url]
    subprocess.run(command, shell=True)


def update_pip():
    command = [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
    subprocess.run(command, shell=True)


def get_site_packages_path():
    return site.getsitepackages()[-1]


def install_package(name: str):
    python_path = sys.executable
    modules_path = bpy.utils.user_resource("SCRIPTS", path="modules")
    command = [python_path, "-m", "pip", "install", name, "--target", modules_path]
    print("Execute:", " ".join(command))
    subprocess.run(command, cwd=os.path.dirname(python_path), check=True)


if __name__ == '<run_path>':
    print(get_site_packages_path())
