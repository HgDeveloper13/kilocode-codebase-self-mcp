mkdir -p ~/src && \
cd ~/src && \
( [ -d kilocode ] || git clone https://github.com/Kilo-Org/kilocode.git ) && \
cd kilocode && \
git checkout main && \
git pull origin main && \
( command -v pnpm >/dev/null || (echo "Installing pnpm via corepack…" && corepack enable pnpm) ) && \
pnpm install && \
pnpm build && \
VSIX="$(ls -1 bin/kilo-code-*.vsix | tail -n1)" && \
echo "Built VSIX: $VSIX" && \
INSTALLER=$(command -v cursor || command -v code) && \
"$INSTALLER" --install-extension "$VSIX" --force && \
echo "Installed into Cursor/VS Code from main branch (forced)" && \
"$INSTALLER" --list-extensions | grep -i kilo
