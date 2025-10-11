from prefect.variables import Variable
from pathlib import Path


def load_terraform_variables_to_prefect(env_file: Path = Path(".env")) -> None:
    """
    To run this script, ensure you had run:
    - bash: chmod +x scripts/generate_env.sh
    - bash: ./scripts/generate_env.sh
    This script reads the .env file from the root of the project and loads the variables into Prefect.
    """

    if not env_file.exists():
        raise FileNotFoundError(f"The specified .env file does not exist: {env_file}")

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # Skip empty lines and comments
            if "=" not in line:
                continue  # Skip lines that don't contain '='
            key, value = line.split("=", 1)
            key = key.lower()
            Variable.set(key, value, overwrite=True)

            print(f"Set Prefect variable: {key}={value}")


if __name__ == "__main__":
    load_terraform_variables_to_prefect()
