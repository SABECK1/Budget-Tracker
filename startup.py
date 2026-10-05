import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
VUE_ROOT = PROJECT_ROOT / "tracker_vue"


def run(command, cwd=PROJECT_ROOT):
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def start_servers():
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    processes = []

    try:
        processes.append(
            subprocess.Popen(
                [sys.executable, "manage.py", "runserver"],
                cwd=PROJECT_ROOT,
            )
        )
        processes.append(
            subprocess.Popen(
                [npm_cmd, "run", "serve"],
                cwd=VUE_ROOT,
            )
        )
        print("Django and Vue development servers are running. Press Ctrl+C to stop.")
        for process in processes:
            process.wait()
    except FileNotFoundError as error:
        print(f"Could not start a development server: {error}")
        raise SystemExit(1) from error
    except KeyboardInterrupt:
        print("Stopping development servers...")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            process.wait()


def main():
    print("Starting Budget Tracker setup...")

    print("Installing Python requirements...")
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    print("Running database migrations...")
    run([sys.executable, "manage.py", "migrate", "--no-input"])

    print("Setting up transaction categories...")
    run([sys.executable, "setup.py"])

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    if not (VUE_ROOT / "node_modules").exists():
        print("Installing Vue dependencies...")
        run([npm_cmd, "install"], cwd=VUE_ROOT)
    else:
        print("Vue dependencies already installed.")

    start_servers()


if __name__ == "__main__":
    main()
