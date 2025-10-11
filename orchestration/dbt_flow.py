import os
import yaml
from prefect import flow
from prefect_gcp import GcpCredentials
from prefect_dbt import PrefectDbtRunner, PrefectDbtSettings
from pathlib import Path


@flow
def run_dbt():
    gcp = GcpCredentials.load("gcp-creds")
    profiles_dir = "/tmp/dbt_profiles"
    os.makedirs(profiles_dir, exist_ok=True)

    profile = {
        "dbt_hacker_news": {
            "target": "dev",
            "outputs": {
                "dev": {
                    "type": "bigquery",
                    "method": "service-account-json",
                    "project": gcp.project,
                    "keyfile_json": gcp.service_account_info.get_secret_value(),  # sửa chỗ này
                    "dataset": "hn_dev",
                    "location": "asia-southeast1",
                    "threads": 4,
                }
            },
        }
    }

    with open(f"{profiles_dir}/profiles.yml", "w") as f:
        yaml.dump(profile, f)

    project_path = str(Path(__file__).resolve().parents[1] / "dbt_hacker_news")

    settings = PrefectDbtSettings(
        project_dir=project_path,
        profiles_dir=profiles_dir,
    )

    runner = PrefectDbtRunner(settings=settings)

    runner.invoke(["deps"])
    runner.invoke(["run"])
    runner.invoke(["test"])


if __name__ == "__main__":
    run_dbt()
