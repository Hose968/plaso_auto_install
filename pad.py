import os
import subprocess
import sys
import configparser
import logging
import dataclasses
import urllib.parse as up
from typing import Union
import shutil

logger = logging.getLogger(__name__)

try:
    import git
except ImportError as e:
    logger.warning(f"{e}, installing...")

    try:
        subprocess.run(['pip', 'install', 'GitPython'], check=True)
    except subprocess.SubprocessError as w:
        logger.critical(f'error while installing "GitPython" module, reason= {w}')
        sys.exit(1)

    try:
        import git
    except ImportError as q:
        logger.critical(f'error while importing module "git", reason = {q}')
        sys.exit(1)

try:
    import docker
except ImportError as e:
    logger.warning(f"{e}, installing....")

    try:
        subprocess.run(['pip', 'install', 'docker'], check=True)
    except subprocess.SubprocessError as w:
        logger.critical(f'error while installing "docker" module, reason= {w}')
        sys.exit(1)

    try:
        import docker
    except ImportError as q:
        logger.critical(f'error while importing module "docker", reason = {e}')
        sys.exit(1)


@dataclasses.dataclass
class ToolPath:
    path: str
    base_path: str = None

    def __post_init__(self):
        if self.is_path():
            self.path = os.path.abspath(self.path)

    def is_url(self):
        try:
            res = up.urlparse(self.path)
            return all([res.scheme, res.netloc])
        except ValueError:
            return False

    def is_path(self):
        return os.path.exists(self.path)

    def to_string(self):
        return self.path


@dataclasses.dataclass
class PlasoPath(ToolPath):
    # path: str # = "https://github.com/log2timeline/plaso.git"

    def __post_init__(self):
        self.base_path = 'plaso/'


@dataclasses.dataclass
class ScriptsPath(ToolPath):
    # path: str # = "single-file-utils"

    def __post_init__(self):
        self.base_path = 'single-file-utils/'

@dataclasses.dataclass
class Config:
    plaso_path: Union[PlasoPath, str] = "https://github.com/log2timeline/plaso.git"
    scripts: Union[ScriptsPath, str] = "single-file-utils"
    plaso_parser: str = None
    reg_reader: str = None
    plaso_start: str = None
    work_dir: str = 'plaso/config/docker/'
    switch: str = None
    dockerfile: str = None

    def set_parsers_path(self, pl_p: str, r_rd: str, pl_s: str, sw_p: str, df_p: str):
        self.plaso_parser = pl_p
        self.plaso_start = pl_s
        self.reg_reader = r_rd
        self.switch = sw_p
        self.dockerfile = df_p

    def __post_init__(self):
        self.plaso_path = PlasoPath(path=self.plaso_path)
        self.scripts = ScriptsPath(path=self.scripts)

    def set_plaso_path(self, path):
        self.plaso_path = PlasoPath(path)


def check_config(config_path: str = 'config.ini') -> Config:
    config = configparser.ConfigParser()
    config.read(config_path)

    plaso_docker = config['PAD'].get("plaso_docker", 'https://github.com/log2timeline/plaso.git')
    parsers = config['PAD'].get('parsers', './single-file-utils/')
    parsers_link = config['PAD'].get('parsers_link', '')

    if parsers_link == '':
        return Config(plaso_path=plaso_docker, scripts=parsers)
    else:
        return Config(plaso_path=plaso_docker, scripts=parsers_link)


def scripts_from_dir(dir_path: str = 'single-file-utils/'):
    pl_p = os.path.join(*[dir_path, 'plaso_parser', 'p2.py'])
    r_rd = os.path.join(*[dir_path, 'reg_reader', 'registry_reader.py'])
    pl_s = os.path.join(*[dir_path, 'start_pl', 'start_pl.sh'])
    pl_df = os.path.join(*[dir_path, 'start_pl', 'Dockerfile.dev'])
    pl_sw = os.path.join(*[dir_path, 'start_pl', 'plaso-switch.dev.sh'])

    ret = list()

    if os.path.isdir(dir_path):
        if os.path.exists(pl_p) and os.path.exists(r_rd) and os.path.exists(pl_s):
            ret.append(pl_p)
            ret.append(r_rd)
            ret.append(pl_s)
        else:
            raise FileNotFoundError("[-] one of parsers not on it's place, exiting!")
        if os.path.exists(pl_df) and os.path.exists(pl_sw):
            ret.append(pl_df)
            ret.append(pl_sw)
        else:
            raise FileNotFoundError("[-] one of builder's files not on it's place, exiting!")

        return ret
    else:
        raise FileExistsError("directory wits scripts not existing!")



def get_scripts(config: Config) -> None:
    saved_path = None
    if config.scripts.is_url():
        git.Repo.clone_from(config.scripts, config.scripts.base_path)
        saved_path = config.scripts.base_path
    else:
        saved_path = config.scripts.to_string()

    f = scripts_from_dir(saved_path)
    pl_p, r_rd, pl_s, df_p, sw_p = f
    config.set_parsers_path(pl_p=pl_p, pl_s=pl_s, r_rd=r_rd, sw_p=sw_p, df_p=df_p)

    return


def plaso_form_tgz(plaso_path: str = 'plaso/') -> str:
    # TODO: realize function that can extract *.tgz archived plaso docker and return path to folder
    return str()


def get_plaso_container(config: Config):
    if config.plaso_path.is_url():
        git.Repo.clone_from(config.plaso_path.to_string(), config.plaso_path.base_path)
        saved_path = config.plaso_path.base_path
    else:
        saved_path = plaso_form_tgz(config.plaso_path.to_string())

    # sw_p, df_p = exec_from_plaso_folder(saved_path)
    config.set_plaso_path(saved_path)

    return


def set_executables(config: Config) -> bool:
    shutil.copy(src=config.plaso_parser, dst=config.work_dir)
    shutil.copy(src=config.reg_reader, dst=config.work_dir)
    shutil.copy(src=config.plaso_start, dst=config.work_dir)
    shutil.copy(src=config.switch, dst=config.work_dir)
    shutil.copy(src=config.dockerfile, dst=config.work_dir)
    return True


def build_plaso_container(config: Config):
    client = docker.from_env()
    logger.warning(f"Building a docker container")
    with open(config.dockerfile, newline='', encoding='utf-8', mode='r') as dockerfile:
        doc_file = dockerfile.read()
    image, _ = client.images.build(
        path=config.work_dir, dockerfile=doc_file, tag='plaso'
    )

    return image


def on_stop():
    subprocess.run(['pip', 'uninstall', 'docker', 'GitPython', '-y'], check=True)


def main():
    configs = check_config()
    get_scripts(configs)
    get_plaso_container(configs)
    set_executables(configs)
    build_plaso_container(configs)


if __name__ == '__main__':
    main()
