from pathlib import Path

import dotenv

env_path = Path(__file__).parent.parent / ".env-example"
dotenv.load_dotenv(dotenv_path=env_path)
