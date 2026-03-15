from __future__ import annotations

import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from staticnest.cli import build_parser, main


class BuildParserTests(unittest.TestCase):
    def test_default_command_is_build(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.command, "build")

    def test_build_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["build"])
        self.assertEqual(args.command, "build")

    def test_serve_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["serve"])
        self.assertEqual(args.command, "serve")

    def test_preview_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["preview"])
        self.assertEqual(args.command, "preview")

    def test_init_command(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["init", "my-site"])
        self.assertEqual(args.command, "init")
        self.assertEqual(args.path, "my-site")

    def test_default_path_is_dot(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["init"])
        self.assertEqual(args.path, ".")

    def test_default_config(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.config, "site.toml")

    def test_custom_config(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--config", "custom.toml"])
        self.assertEqual(args.config, "custom.toml")

    def test_default_host(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.host, "127.0.0.1")

    def test_default_port(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.port, 8000)

    def test_custom_host_and_port(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--host", "0.0.0.0", "--port", "9000"])
        self.assertEqual(args.host, "0.0.0.0")
        self.assertEqual(args.port, 9000)

    def test_default_remote_and_branch(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["gh-deploy"])
        self.assertEqual(args.remote, "origin")
        self.assertEqual(args.branch, "gh-pages")

    def test_custom_remote_and_branch(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["gh-deploy", "--remote", "upstream", "--branch", "docs"])
        self.assertEqual(args.remote, "upstream")
        self.assertEqual(args.branch, "docs")

    def test_invalid_command_exits(self) -> None:
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["unknown-command"])


class MainFunctionTests(unittest.TestCase):
    def _make_site(self, tmp_dir: str) -> Path:
        root = Path(tmp_dir)
        (root / "content").mkdir()
        (root / "content" / "index.md").write_text("# Home\n\nWelcome.\n")
        (root / "site.toml").write_text(
            'title = "Test"\ndescription = ""\nbase_url = "/"\n'
            'content_dir = "content"\noutput_dir = "dist"\n'
            '[brand]\nname = "Test"\n[links]\ngithub = "#"\n[theme]\nname = "nest"\n'
        )
        return root

    def test_init_command_creates_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "new-project"
            with patch("sys.argv", ["staticnest", "init", str(target)]):
                result = main()
            self.assertEqual(result, 0)
            self.assertTrue((target / "site.toml").exists())

    def test_init_command_prints_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "new-project"
            with patch("sys.argv", ["staticnest", "init", str(target)]):
                with patch("builtins.print") as mock_print:
                    main()
                    printed = " ".join(str(c) for c in mock_print.call_args_list)
                    self.assertIn("Initialized", printed)

    def test_init_command_exits_1_on_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "proj"
            # Create once so second call fails
            with patch("sys.argv", ["staticnest", "init", str(target)]):
                main()
            parser = build_parser()
            exited_with = None
            with patch.object(parser, "exit", side_effect=SystemExit) as mock_exit:
                from staticnest import cli
                with patch.object(cli, "build_parser", return_value=parser):
                    with patch("sys.argv", ["staticnest", "init", str(target)]):
                        with self.assertRaises(SystemExit):
                            main()

    def test_build_command_returns_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = self._make_site(tmp_dir)
            config = root / "site.toml"
            with patch("sys.argv", ["staticnest", "build", "--config", str(config)]):
                result = main()
            self.assertEqual(result, 0)

    def test_build_command_prints_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = self._make_site(tmp_dir)
            config = root / "site.toml"
            with patch("sys.argv", ["staticnest", "build", "--config", str(config)]):
                with patch("builtins.print") as mock_print:
                    main()
                    printed = " ".join(str(c) for c in mock_print.call_args_list)
                    self.assertIn("Built", printed)

    def test_publish_command_returns_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = self._make_site(tmp_dir)
            config = root / "site.toml"
            dest = root / "published"
            with patch("sys.argv", ["staticnest", "publish", "--config", str(config), "--destination", str(dest)]):
                result = main()
            self.assertEqual(result, 0)

    def test_serve_command_calls_serve_site(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = self._make_site(tmp_dir)
            config = root / "site.toml"
            with patch("staticnest.cli.serve_site") as mock_serve:
                with patch("sys.argv", ["staticnest", "serve", "--config", str(config)]):
                    main()
                mock_serve.assert_called_once()
                call_kwargs = mock_serve.call_args
                self.assertEqual(call_kwargs[1].get("host") or call_kwargs[0][1], "127.0.0.1")

    def test_preview_command_calls_serve_site(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = self._make_site(tmp_dir)
            config = root / "site.toml"
            with patch("staticnest.cli.serve_site") as mock_serve:
                with patch("sys.argv", ["staticnest", "preview", "--config", str(config)]):
                    main()
                mock_serve.assert_called_once()


if __name__ == "__main__":
    unittest.main()
