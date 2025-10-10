from prefect import flow
from prefect_shell import ShellOperation


@flow
def run_dbt():
    ShellOperation(
        commands=["dbt deps", "dbt run", "dbt test"], working_dir="dbt_hacker_news"
    ).run()


if __name__ == "__main__":
    run_dbt()
