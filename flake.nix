{
  inputs = {
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs-unstable }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs-unstable.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (system:
        let pkgs = nixpkgs-unstable.legacyPackages.${system}; in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              go
            ];

            shellHook = ''
              echo "Sem Shell Initialized"
            '';
          };
        });
    };
}
