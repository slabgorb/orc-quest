# SideQuest Orchestrator — Cross-repo task runner

root := justfile_directory()
content := root / "sidequest-content" / "genre_packs"

import '.pennyfarthing/justfile.pf'

# API (Rust backend)
api-test:
    cd sidequest-api && cargo test

api-build:
    cd sidequest-api && cargo build

api-release:
    cd sidequest-api && cargo build --release

api-run *flags:
    cd sidequest-api && cargo run -p sidequest-server -- --genre-packs-path {{content}} {{flags}}

api-lint:
    cd sidequest-api && cargo clippy -- -D warnings

api-fmt:
    cd sidequest-api && cargo fmt

api-check:
    cd sidequest-api && cargo fmt --check && cargo clippy -- -D warnings && cargo test

# UI (React frontend)
ui-dev:
    cd sidequest-ui && npm run dev

ui-test:
    cd sidequest-ui && npx vitest run

ui-build:
    cd sidequest-ui && npm run build

ui-lint:
    cd sidequest-ui && npm run lint

ui-install:
    cd sidequest-ui && npm install

# Daemon (Python media services)
daemon-run:
    cd sidequest-daemon && SIDEQUEST_GENRE_PACKS={{content}} sidequest-renderer --warmup

daemon-status:
    cd sidequest-daemon && sidequest-renderer --status

daemon-stop:
    cd sidequest-daemon && sidequest-renderer --shutdown

daemon-test:
    cd sidequest-daemon && SIDEQUEST_GENRE_PACKS={{content}} pytest

daemon-lint:
    cd sidequest-daemon && ruff check .

daemon-install:
    cd sidequest-daemon && pip install -e ".[dev]"

# Watcher (telemetry tail)
watch port="8765":
    python3 scripts/watch.py --port {{port}}

# Quick-start aliases
warmup: daemon-run
server *flags:
    just api-run --trace {{flags}}
client: ui-dev

# Cross-repo
check-all: api-check ui-lint ui-test

# First-time dev environment setup
setup:
    #!/usr/bin/env bash
    echo "=== SideQuest Dev Environment Setup ==="
    echo ""

    # API (Rust)
    if [ -d "sidequest-api" ]; then
        echo "--- Rust toolchain ---"
        rustup component add clippy
        echo "--- API dependencies ---"
        cd sidequest-api && cargo build
        cd ..
        echo "✓ API ready"
    else
        echo "⚠ sidequest-api not cloned. Run: git clone git@github.com:slabgorb/sidequest-api.git"
    fi

    echo ""

    # UI (React)
    if [ -d "sidequest-ui" ]; then
        echo "--- UI dependencies ---"
        cd sidequest-ui && npm install
        cd ..
        echo "✓ UI ready"
    else
        echo "⚠ sidequest-ui not cloned. Run: git clone git@github.com:slabgorb/sidequest-ui.git"
    fi

    echo ""

    # Daemon (Python)
    if [ -d "sidequest-daemon" ]; then
        echo "--- Daemon dependencies ---"
        cd sidequest-daemon && pip install -e ".[dev]"
        cd ..
        echo "✓ Daemon ready"
    else
        echo "⚠ sidequest-daemon not cloned. Run: git clone git@github.com:slabgorb/sidequest-daemon.git"
    fi

    echo ""
    echo "=== Setup complete ==="

# Headless playtest
playtest-server *flags:
    cd sidequest-api && cargo run -p sidequest-server -- --genre-packs-path {{content}} --headless {{flags}}

playtest *flags:
    python3 scripts/playtest.py {{flags}}

playtest-scenario file:
    python3 scripts/playtest.py --scenario scenarios/{{file}}.yaml

# Dev environment — all services + OTEL dashboard in one tmux window
# Usage: just dev              (solo — one browser tab)
#        just dev-multi        (multiplayer — player1 + player2 tabs)
#        just dev 9000         (custom dashboard port)
dev dashboard_port="9765":
    #!/usr/bin/env bash
    set -euo pipefail
    just _dev-launch "{{dashboard_port}}" 1

# Multiplayer dev — opens browser tabs for player1.local and player2.local
dev-multi dashboard_port="9765":
    #!/usr/bin/env bash
    set -euo pipefail
    just _dev-launch "{{dashboard_port}}" 2

_dev-launch dashboard_port players:
    #!/usr/bin/env bash
    set -euo pipefail
    SESSION="sidequest-dev"
    ROOT="{{justfile_directory()}}"
    CONTENT="$ROOT/sidequest-content/genre_packs"
    PLAYERS="{{players}}"
    DP="{{dashboard_port}}"

    # Kill existing session if present
    tmux kill-session -t "$SESSION" 2>/dev/null || true

    # Create session with daemon pane
    tmux new-session -d -s "$SESSION" -n dev \
      -x 200 -y 50 \
      "cd $ROOT/sidequest-daemon && SIDEQUEST_GENRE_PACKS=$CONTENT sidequest-renderer --warmup; read"

    # Split for server (right of daemon)
    tmux split-window -t "$SESSION:dev" -h \
      "cd $ROOT/sidequest-api && cargo run -p sidequest-server -- --genre-packs-path $CONTENT --trace; read"

    # Split for client (below server)
    tmux split-window -t "$SESSION:dev.1" -v \
      "cd $ROOT/sidequest-ui && npm run dev; read"

    # Split for OTEL dashboard (below daemon)
    tmux split-window -t "$SESSION:dev.0" -v \
      "sleep 3 && cd $ROOT && python3 scripts/playtest.py --dashboard-only --dashboard-port $DP; read"

    # Label panes
    tmux select-pane -t "$SESSION:dev.0" -T "daemon"
    tmux select-pane -t "$SESSION:dev.1" -T "server"
    tmux select-pane -t "$SESSION:dev.2" -T "client"
    tmux select-pane -t "$SESSION:dev.3" -T "otel-dashboard"

    # Tiled layout
    tmux select-layout -t "$SESSION:dev" tiled

    # Open in Ghostty
    open -na "Ghostty.app" --args -e "tmux attach-session -t $SESSION"

    # Wait for services to start, then open browser
    echo "Waiting for services..."
    sleep 8
    open "http://player1.local:$DP/"
    open "http://player1.local:5173/"
    if [ "$PLAYERS" -ge 2 ]; then
      open "http://player2.local:5173/"
    fi
    echo "Dev environment launched ($PLAYERS player(s)): tmux attach-session -t $SESSION"

status:
    @echo "=== API ===" && cd sidequest-api && git status --short
    @echo "=== UI ===" && cd sidequest-ui && git status --short
    @echo "=== Daemon ===" && cd sidequest-daemon && git status --short 2>/dev/null || echo "(not cloned)"
    @echo "=== Orchestrator ===" && git status --short
