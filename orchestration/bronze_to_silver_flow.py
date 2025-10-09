# orchestration/bronze_to_silver_flow.py
from prefect import flow, task
from .run_bronze_to_silver import run_bronze_to_silver
from .create_external_table_silver import run_create_external_table


@task(
    log_prints=True,
    name="Run Bronze to Silver ELT Task",
    retries=2,
    retry_delay_seconds=10,
)
def run_bronze_to_silver_script() -> None:
    run_bronze_to_silver()


@task(log_prints=True, name="Refresh Silver External Tables")
def refresh_silver_external_tables() -> None:
    run_create_external_table()


@flow(log_prints=True, name="Bronze to Silver ELT Flow")
def bronze_to_silver_flow() -> None:
    print("Starting Bronze to Silver ELT Flow...")

    run_bronze_to_silver_script()
    refresh_silver_external_tables()

    print("Bronze to Silver ETL Flow completed.")


if __name__ == "__main__":
    bronze_to_silver_flow()
