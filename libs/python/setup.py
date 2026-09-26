"""Bundle shared canonical data in wheels and sdists without a second editable copy."""
from pathlib import Path
import shutil
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

HERE = Path(__file__).resolve().parent


def copy_data(destination):
    # sdist builds have a local data directory; a checkout uses repository-root data.
    source = HERE / "data" if (HERE / "data").is_dir() else HERE.parents[1] / "data/generated"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


class BuildWithData(build_py):
    def run(self):
        super().run()
        copy_data(Path(self.build_lib) / "orvin/_data")


class SdistWithData(sdist):
    def make_release_tree(self, base_dir, files):
        super().make_release_tree(base_dir, files)
        copy_data(Path(base_dir) / "data")
        source = HERE if (HERE / "NOTICE").is_file() else HERE.parents[1]
        for name in ("LICENSE", "NOTICE"):
            shutil.copyfile(source / name, Path(base_dir) / name)


setup(cmdclass={"build_py": BuildWithData, "sdist": SdistWithData})
