# orchestration/bronze_to_silver_flow.py
from pathlib import Path
from prefect import flow, task
from prefect_shell import ShellOperation


@task(
    log_prints=True,
    name="Run Bronze to Silver ELT Script",
    retries=2,
    retry_delay_seconds=10,
)
def run_bronze_to_silver_script() -> None:
    project_root = Path(__file__).parent.parent
    script_path = project_root / "silver" / "run_bronze_to_silver.sh"

    print(f"Executing script to transform data from Bronze to Silver at: {script_path}")

    # short-running operation
    ShellOperation(commands=[f"bash {script_path}"]).run()

    print("Script executed successfully.")


@task(log_prints=True, name="Refresh Silver External Tables")
def refresh_silver_external_tables() -> None:
    project_root = Path(__file__).parent.parent
    script_path = project_root / "silver" / "create_external_table_silver.sh"

    print(f"Executing script to refresh Silver external tables at: {script_path}")

    with ShellOperation(commands=[f"bash {script_path}"]) as refresh_operation:

        process = refresh_operation.trigger()
        process.wait_for_completion()

        output_lines = process.fetch_result()
        print("\n".join(output_lines))

    print("Script executed successfully.")


@flow(log_prints=True, name="Bronze to Silver ELT Flow")
def bronze_to_silver_flow() -> None:
    print("Starting Bronze to Silver ELT Flow...")

    run_bronze_to_silver_script()
    refresh_silver_external_tables()

    print("Bronze to Silver ETL Flow completed.")


if __name__ == "__main__":
    bronze_to_silver_flow()
