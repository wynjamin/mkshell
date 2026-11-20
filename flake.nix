{
  description = "Dump current nix shell as a shell.nix file";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {nixpkgs, ...}: let
    name = "mkshell";
    systems = ["x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin"];
    forAllSystems = nixpkgs.lib.genAttrs systems;

    packages = forAllSystems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3;
    in {
      default = pkgs.writeShellApplication {
        inherit name;
        runtimeInputs = [python];
        text = ''
          exec ${python}/bin/python ${./${name}.py}
        '';
      };
    });
  in {
    inherit packages;

    apps = forAllSystems (system: {
      default = {
        type = "app";
        program = "${packages.${system}.default}/bin/${name}";
      };
    });
  };
}
