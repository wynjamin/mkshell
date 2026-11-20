import os, subprocess, json
from typing import Optional
from dataclasses import dataclass


@dataclass
class BuildInput:
    name: str
    version: str
    path: str


def parse_input(inp: str) -> BuildInput:
    parts = inp.split("-")
    parts.reverse()

    return BuildInput(name=parts[1], version=parts[0], path=inp)


def run_cmd(cmd: str) -> str:
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

    if proc.stdout is None:
        return ""

    decoded = proc.stdout.read().decode()

    if decoded.endswith("\n"):
        return decoded[:-1]
    return decoded


def search_package(inp: BuildInput) -> Optional[str]:
    result = json.loads(run_cmd(f"nix search --json nixpkgs {inp.name}"))

    candidates = []

    for package_attr_name, data in result.items():
        if data["version"] != inp.version:
            continue
        if not inp.name in data["pname"]:
            continue

        package_path = ".".join(package_attr_name.split(".")[2:])
        candidates.append(package_path)

    if len(candidates) == 0:
        return None

    candidates.sort(key=lambda x: len(x))
    return candidates[0]


def is_in_shell() -> bool:
    var = os.environ.get("IN_NIX_SHELL")
    return not var is None and len(var.strip()) != 0


def get_inputs() -> list[str]:
    inputs: list[str] = []

    var = os.environ.get("buildInputs")
    if var is None or len(var.strip()) == 0:
        return inputs

    for input_path in var.strip().split(" "):
        build_input = parse_input(input_path)
        package = search_package(build_input)

        if not package is None:
            print(package)
            inputs.append(package)

    return inputs


def format_shell_file(inputs: list[str]) -> str:
    return """
{{ pkgs ? import <nixpkgs> {{}} }}:

pkgs.mkShell {{
  packages = with pkgs; [
    {inputs}
  ];
}}
""".format(inputs=("\n" + " " * 2 * 2).join(inputs)).strip()


def main():
    if not is_in_shell():
        print("Not currently in a shell (nix-shell).")
        return

    inputs = get_inputs()
    if len(inputs) == 0:
        print("No inputs were found.")
        return

    content = format_shell_file(inputs)
    with open("shell.nix", "w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
