mkdir -p ~/src && \
cd ~/src && \
( [ -d kilocode ] || git clone https://github.com/Kilo-Org/kilocode.git ) && \
cd kilocode && \
git checkout main && \
git pull origin main && \
git fetch origin "refs/pull/*:refs/remotes/origin/pr/*" && \
git checkout -B all-prs main && \
for pr in $(git branch -r | grep 'origin/pr/' | sed 's/ *origin\/pr\///'); do \
  echo "Merging PR #$pr" && \
  git merge --no-edit "origin/pr/$pr" || (echo "Merge conflict with PR #$pr, stopping." && git merge --abort && exit 1); \
done && \
( command -v pnpm >/dev/null || (echo "Installing pnpm via corepack…" && corepack enable pnpm) ) && \
pnpm install && \
pnpm build && \
VSIX="$(ls -1 bin/kilo-code-*.vsix | tail -n1)" && \
echo "Built VSIX: $VSIX" && \
INSTALLER=$(command -v cursor || command -v code) && \
"$INSTALLER" --install-extension "$VSIX" --force && \
echo "Installed into Cursor/VS Code from all PRs (forced)" && \
"$INSTALLER" --list-extensions | grep -i kilo
