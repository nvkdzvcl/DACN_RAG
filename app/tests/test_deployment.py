"""Exercise the Windows production launcher without opening a network listener."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SHELL = shutil.which('pwsh') or shutil.which('powershell')

@unittest.skipUnless(os.name == 'nt' and SHELL, 'Windows deployment launcher')
class DeploymentTests(unittest.TestCase):
    def test_launcher_uses_selected_config_and_rejects_insecure_settings(self):
        with tempfile.TemporaryDirectory(prefix='deployment config ') as directory:
            root = Path(directory)
            capture = root / 'capture.json'
            # Replace only Uvicorn: dotenv, PowerShell, argument handling and configuration are real.
            (root / 'uvicorn.py').write_text(
                "import json, os, sys\nfrom pathlib import Path\n"
                "Path(os.environ['DEPLOYMENT_CAPTURE']).write_text(json.dumps({'args':sys.argv[1:],'env':{k:os.getenv(k) for k in ['APP_ENV','SERVE_FRONTEND','DATABASE_URL']}}))\n",
                encoding='utf-8')
            config = root / 'production.env'
            template = (ROOT / 'deploy/production.env.example').read_text(encoding='utf-8')
            config.write_text(template, encoding='utf-8')
            env = {**os.environ, 'PYTHONPATH': str(root), 'DEPLOYMENT_CAPTURE': str(capture),
                   'APP_ENV': 'development', 'DATABASE_URL': 'sqlite:///wrong-development.db'}
            command = [SHELL, '-NoProfile', '-File', str(ROOT / 'scripts/start-production.ps1'), '-EnvFile', str(config)]
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            recorded = json.loads(capture.read_text())
            self.assertEqual(recorded['env']['APP_ENV'], 'production')
            self.assertEqual(recorded['env']['SERVE_FRONTEND'], 'true')
            self.assertEqual(recorded['env']['DATABASE_URL'], 'sqlite:///./data/production/customer_support.db')
            args = recorded['args']
            for flag, value in [('--host', '127.0.0.1'), ('--port', '8000'), ('--workers', '1'), ('--forwarded-allow-ips', '127.0.0.1')]:
                self.assertEqual(args[args.index(flag)+1], value)
            self.assertNotIn('--reload', args)
            self.assertIn('--no-access-log', args)
            self.assertIn('--proxy-headers', args)
            for source, replacement in [('APP_ENV=production', 'APP_ENV=development'),
                                        ('CUSTOMER_PUBLIC_URL=https://support.example.com', 'CUSTOMER_PUBLIC_URL=http://support.example.com')]:
                capture.unlink()
                config.write_text(template.replace(source, replacement), encoding='utf-8')
                result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=30)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(capture.exists())
                capture.write_text('{}')

if __name__ == '__main__':
    unittest.main()
