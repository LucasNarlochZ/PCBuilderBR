from pathlib import Path
import subprocess
import tempfile
import unittest
import os

ROOT = Path(__file__).resolve().parents[2]


class DeploymentTests(unittest.TestCase):
    def test_failed_build_stops_before_migrations(self):
        script = ROOT / 'scripts/deploy-homelab.sh'
        self.assertTrue(script.exists(), 'Homelab deploy script is missing')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / 'docker'
            docker.write_text('#!/bin/sh\nexit 42\n')
            docker.chmod(0o755)
            result = subprocess.run(['bash', str(script)], env={**os.environ, 'PATH': directory + ':' + os.environ['PATH'], 'DEPLOY_PATH': directory})
            self.assertNotEqual(result.returncode, 0)

    def test_health_check_retries_a_startup_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / 'docker'
            docker.write_text('#!/bin/sh\nif [ "$4" = exec ]; then\n if [ ! -f "$DEPLOY_PATH/attempt" ]; then touch "$DEPLOY_PATH/attempt"; exit 1; fi\nfi\nexit 0\n')
            docker.chmod(0o755)
            sleeper = root / 'sleep'
            sleeper.write_text('#!/bin/sh\nexit 0\n')
            sleeper.chmod(0o755)
            result = subprocess.run(['bash', str(ROOT / 'scripts/deploy-homelab.sh')], env={**os.environ, 'PATH': directory + ':' + os.environ['PATH'], 'DEPLOY_PATH': directory})
            self.assertEqual(result.returncode, 0)
