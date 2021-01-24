"""BinBin object definition"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import click
import halo  # type: ignore
import userpath  # type: ignore

from . import dep_resolver, enums, git, interface, json_to_obj, utils

BBIN_URL = "https://github.com/ThatXliner/binbin_files.git"


class Index:
    # pylint: disable=C
    def __init__(
        self,
        bbin_path: str = "~/.config/binbin",
        bin_path: str = "~/bin",
        app_path: str = "~/app",
    ):
        bbin_dir = Path(bbin_path).expanduser()
        binaries_dir = Path(bin_path).expanduser()
        app_dir = Path(app_path).expanduser()

        self._bbin_path = bbin_dir
        self._app_path = app_dir
        self._bin_path = binaries_dir

        if not (bbin_dir.exists() and bbin_dir.is_dir()):
            interface.warn("Bbin's index is not initialized! Initalizing...")
            git.clone(
                BBIN_URL,
                str(bbin_dir),
                with_spinner=False,
                success_text=f"Finished initializing bbin's index at {bbin_dir}",
            )
        else:
            self.update()

        if not (binaries_dir.exists() and binaries_dir.is_dir()):
            with halo.Halo(f"Creating binary directory at {bin_path}") as spinner:  # type: ignore
                binaries_dir.mkdir(parents=True)
                # Make sure it is on the $PATH
                userpath.append(str(binaries_dir))  # type: ignore
                spinner.succeed("Done")  # type: ignore

        if not (app_dir.exists() and app_dir.is_dir()):
            with halo.Halo(f"Creating app directory at {app_dir}") as spinner:  # type: ignore
                app_dir.mkdir(parents=True)
                spinner.succeed("Done")  # type: ignore

        assert bbin_dir.exists() and bbin_dir.is_dir()
        assert app_dir.exists() and app_dir.is_dir()
        assert binaries_dir.exists() and binaries_dir.is_dir()

    def update(self) -> None:
        git.pull(str(self._bbin_path), success_text="Updated index")

    def get_url(self, package_name: str) -> Optional[str]:
        found = json.loads(Path(self.index_path).read_text()).get(package_name)  # type: ignore
        assert found is None or isinstance(found, str)  # type: ignore
        return found

    def download(self, package_name: str, url: str) -> Path:
        output = Path(self.repo_path).joinpath(package_name)
        if output.exists() and output.is_dir():
            raise click.ClickException("Error: package already installed")
        git.clone(url, directory=str(output))
        return output

    def build(self, repository_path: Path) -> Optional[str]:
        assert repository_path.exists() and repository_path.is_dir()
        try:  # TODO: Implement dependency resolution
            # TODO: Implement compiler bootstrap
            package_json = repository_path.joinpath("package.json")

            json_stuff = json.loads(package_json.read_text())  # type: ignore

            git.checkout(str(repository_path), json_stuff["version"])  # type: ignore

            build_script = json_to_obj.BuildInstructions(json_stuff["build"]).get()  # type: ignore
            deps: List[Dict[str, str]] = json_stuff.get("deps", [])  # type: ignore
            assert isinstance(deps, list)
            compiler = dep_resolver.resolve_compiler(json_stuff["compiler"])  # type: ignore
            build_script.insert(0, compiler)
            check_sum = json_to_obj.Hashes(json_stuff["hashes"]).get()  # type: ignore

            outcome = utils.run_subprocess(
                build_script,
                loading_text=f"Building (script: {' '.join(build_script)})",
                fail_text="Build failed!",
                success_text="Build succeeded!",
                text_color="yellow",
                spinner_color="cyan",
                stderr=subprocess.STDOUT,
                cwd=str(repository_path),
            )
            ctx = click.get_current_context()
            if outcome is not None:
                log_path = self.create_build_log(outcome.stdout.decode())  # type: ignore
                ctx.fail(f"See the build log at {log_path}")

            target_exe = Path(repository_path.joinpath(json_stuff["target"]))  # type: ignore
            if not utils.is_an_executable(target_exe):
                ctx.fail("Could not find target executable!")
            with halo.Halo("Checking hash") as spinner:  # type: ignore
                if utils.check_hash(target_exe.read_bytes(), check_sum):
                    spinner.succeed("Built executable matched checksum!")  # type: ignore
                else:
                    spinner.fail(f"Checksum mismatched (checksum: {check_sum})")  # type: ignore
            return str(target_exe)

        except OSError as exception:
            raise click.ClickException(
                "The package.json does not exist for this package. Please consult the maintainer"
            ) from exception
        except KeyError as exception:
            raise click.ClickException(
                "The package.json is invalid. Please consult the maintainer"
            ) from exception

    def create_build_log(self, contents: str, prefix: Optional[str] = None) -> str:
        build_log = tempfile.mkstemp(
            prefix=prefix, suffix="log", dir=self.build_log_path, text=True
        )[-1]
        with open(build_log, "w") as file:
            file.write(contents)
        return build_log

    def install(self, executable: str, action: Union[enums.InstallAction, str]) -> None:
        # TODO: refactor code to reduce duplication
        # TODO: Handle already exists
        if action in {enums.InstallAction.move, "move"}:
            with halo.Halo("Moving %s to %s" % (executable, self._bin_path)) as spinner:  # type: ignore
                shutil.move(executable, str(self.bin_path))
                spinner.succeed("Done!")  # type: ignore
        elif action in {enums.InstallAction.symlink, "symlink"}:
            with halo.Halo("Symlinking %s to %s" % (executable, self._bin_path)) as spinner:  # type: ignore
                self._bin_path.joinpath(Path(executable).name).symlink_to(
                    Path(executable)
                )
                spinner.succeed("Done!")  # type: ignore
        elif action in {enums.InstallAction.copy, "copy"}:
            with halo.Halo("Copying %s to %s" % (executable, self._bin_path)) as spinner:  # type: ignore
                shutil.copy2(executable, self.bin_path)
                spinner.succeed("Done!")  # type: ignore

    @property
    def path(self) -> Path:
        return self._bbin_path

    @property
    def repo_path(self) -> Path:
        return self._bbin_path.joinpath("repos")

    @property
    def bin_path(self) -> Path:
        return self._bin_path

    @property
    def app_path(self) -> Path:
        return self._app_path

    @property
    def index_path(self) -> Path:
        return self._bbin_path.joinpath("index.json")

    @property
    def build_log_path(self) -> Path:
        return self._bbin_path.joinpath("build_logs")
