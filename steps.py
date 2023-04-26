import subprocess
import sys

try:
    import git
except ImportError as e:
    print(f"{e}, installing...")
    subprocess.run(['pip', 'install', 'GitPython'], check=True)
    try:
        import git
    except ImportError as e:
        print(f'error while importing module "git", reason = {e}')
        sys.exit(1)

try:
    import docker
except ImportError as e:
    print(f"{e}, installing....")
    subprocess.run(['pip', 'install', 'docker'], check=True)
    try:
        import docker
    except ImportError as e:
        print(f'error while importing module "docker", reason = {e}')
        sys.exit(1)


def on_stop():
    subprocess.run(['pip', 'uninstall', 'docker', 'GitPython', '-y'])


def main():
    git.Repo.clone_from('https://github.com/othneildrew/Best-README-Template.git', './example/')
    on_stop()


if __name__ == '__main__':
    main()
