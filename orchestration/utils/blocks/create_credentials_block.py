from prefect_gcp.credentials import GcpCredentials

GcpCredentials(service_account_file="gcp-credentials.json").save("gcp-creds")
