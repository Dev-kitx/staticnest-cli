from __future__ import annotations

import argparse
from pathlib import Path

from staticnest.devserver import serve_site
from staticnest.scaffold import init_project
from staticnest.site import DeployOptions, build_site, gh_deploy_site, publish_site


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="staticnest",
        description="Build a static documentation site with the Staticnest nest theme.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="build",
        choices=["build", "serve", "preview", "publish", "gh-deploy", "init"],
        help="Command to run.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory for the init command.",
    )
    parser.add_argument(
        "--config",
        default="site.toml",
        help="Path to the site configuration file.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host interface for serve mode.")
    parser.add_argument("--port", default=8000, type=int, help="Port for serve mode.")
    parser.add_argument(
        "--destination",
        help="Publish destination directory for the publish command.",
    )
    parser.add_argument("--remote", default="origin", help="Git remote for gh-deploy.")
    parser.add_argument("--branch", default="gh-pages", help="Git branch for gh-deploy.")
    parser.add_argument(
        "--message",
        default="Deploy staticnest site",
        help="Git commit message for gh-deploy.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init":
        try:
            project_dir = init_project(Path(args.path))
        except ValueError as exc:
            parser.exit(1, f"Error: {exc}\n")
        print(f"Initialized Staticnest project in {project_dir}")
        return 0

    config_path = Path(args.config).resolve()

    if args.command == "build":
        build_site(config_path)
        print(f"Built site from {config_path}")
    elif args.command in {"serve", "preview"}:
        serve_site(config_path, host=args.host, port=args.port)
    elif args.command == "publish":
        destination = Path(args.destination).resolve() if args.destination else None
        published_to = publish_site(config_path, destination=destination)
        print(f"Published site to {published_to}")
    elif args.command == "gh-deploy":
        deployed_to = gh_deploy_site(
            config_path,
            DeployOptions(remote=args.remote, branch=args.branch, message=args.message),
        )
        print(f"Deployed site to {deployed_to}")

    return 0
