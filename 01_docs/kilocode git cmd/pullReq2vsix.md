mkdir -p ~/src && \
cd ~/src && \
( [ -d kilocode ] || git clone https://github.com/Kilo-Org/kilocode.git ) && \
cd kilocode && \
git fetch origin pull/3933/head:pr-3933 && \
git switch pr-3933 && \
( command -v pnpm >/dev/null || (echo "Installing pnpm via corepack…" && corepack enable pnpm) ) && \
pnpm install && \
pnpm build && \
VSIX="$(ls -1 bin/kilo-code-*.vsix | tail -n1)" && \
echo "Built VSIX: $VSIX" && \
INSTALLER=$(command -v cursor || command -v code) && \
"$INSTALLER" --install-extension "$VSIX" --force && \
echo "Installed into Cursor/VS Code from PR #3933 (forced)" && \
"$INSTALLER" --list-extensions | grep -i kilo