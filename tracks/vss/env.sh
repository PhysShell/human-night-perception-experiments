# Source me: headless software Vulkan (Mesa lavapipe/llvmpipe) for the VSS wgpu build. No GPU needed.
# Store paths come from the repo-pinned nixpkgs:
#   nix build --no-link --print-out-paths --inputs-from . nixpkgs#mesa nixpkgs#vulkan-loader nixpkgs#vulkan-tools
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
_R=/home/user/human-night-perception-experiments
_P=$(cd $_R && nix build --no-link --print-out-paths --inputs-from . nixpkgs#mesa nixpkgs#vulkan-loader 2>/dev/null)
_MESA=$(echo "$_P" | grep -- '-mesa-' | head -1); _VKL=$(echo "$_P" | grep -- 'vulkan-loader' | head -1)
export VK_ICD_FILENAMES=$_MESA/share/vulkan/icd.d/lvp_icd.x86_64.json
export LD_LIBRARY_PATH=$_VKL/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export WGPU_BACKEND=vulkan
export VSS_SRC=$_R/research-cache/vss/visual-system-simulator
export VSS_BIN=${VSS_BIN:-$_R/research-cache/vss/bin/vss-desktop}  # copy of target/release/vss-desktop (target/ deleted to save disk; rebuild with build.sh)
