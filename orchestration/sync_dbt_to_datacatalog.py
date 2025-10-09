import os
import json
from dotenv import load_dotenv
from google.cloud import datacatalog_v1
from google.api_core.exceptions import AlreadyExists


# --- 1. Configure environment variables ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("GCP_REGION")
MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__), "../dbt_hacker_news/target/manifest.json"
)
MANIFEST_PATH = os.path.abspath(MANIFEST_PATH)


TAG_TEMPLATE_ID = "dbt_model_data"
FULL_TAG_TEMPLATE_NAME = (
    f"projects/{PROJECT_ID}/locations/{LOCATION}/tagTemplates/{TAG_TEMPLATE_ID}"
)

parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
client = datacatalog_v1.DataCatalogClient()

print("--- Configuration ---")
print(f"Project ID: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"Manifest Path: {MANIFEST_PATH}")
print("--------------------------------")

if not PROJECT_ID or not LOCATION:
    raise ValueError(
        "PROJECT_ID and GCP_REGION must be set in the environment variables."
    )

client = datacatalog_v1.DataCatalogClient()
print("Data Catalog client initialized.")


# --- 2. Create Tag Template if it doesn't exist ---
def get_or_create_tag_template() -> datacatalog_v1.TagTemplate:
    """
    This function checks if a Tag Template exists in Data Catalog.
    If it doesn't exist, it creates one.
    If it exists, it retrieves and returns the existing Tag Template.
    """

    # Create a new blank Tag Template object
    template = datacatalog_v1.TagTemplate()
    template.display_name = "dbt Model Metadata"

    # Define fields for the Tag Template
    template.fields["model_description"] = datacatalog_v1.TagTemplateField(
        display_name="Model Description",
        type=datacatalog_v1.FieldType(
            primitive_type=datacatalog_v1.FieldType.PrimitiveType.STRING
        ),
    )

    template.fields["materialization"] = datacatalog_v1.TagTemplateField(
        display_name="Materialization",
        type=datacatalog_v1.FieldType(
            primitive_type=datacatalog_v1.FieldType.PrimitiveType.STRING
        ),
    )

    template.fields["owner"] = datacatalog_v1.TagTemplateField(
        display_name="Owner",
        type=datacatalog_v1.FieldType(
            primitive_type=datacatalog_v1.FieldType.PrimitiveType.STRING
        ),
    )

    template.fields["tags"] = datacatalog_v1.TagTemplateField(
        display_name="Tags",
        type=datacatalog_v1.FieldType(
            primitive_type=datacatalog_v1.FieldType.PrimitiveType.STRING
        ),
    )

    template.fields["path"] = datacatalog_v1.TagTemplateField(
        display_name="Path",
        type=datacatalog_v1.FieldType(
            primitive_type=datacatalog_v1.FieldType.PrimitiveType.STRING
        ),
    )

    # Attempt to create the Tag Template
    try:
        print(f"Attempting to create Tag Template: {TAG_TEMPLATE_ID}")

        return client.create_tag_template(
            parent=parent, tag_template_id=TAG_TEMPLATE_ID, tag_template=template
        )

    except AlreadyExists:
        print(
            f"Tag Template {TAG_TEMPLATE_ID} already exists. Retrieving existing template."
        )
        return client.get_tag_template(name=FULL_TAG_TEMPLATE_NAME)

    except Exception as e:
        print(f"Error creating or retrieving Tag Template: {e}")
        raise


# --- 3. Sync dbt manifest to Data Catalog ---
def sync_dbt_manifest_to_datacatalog():
    """
    This function syncs dbt model metadata from the manifest.json file to Google Cloud Data Catalog.
    """

    # Ensure Tag Template exists
    print("Ensuring Tag Template exists...")
    tag_template = get_or_create_tag_template()
    print(f"Using Tag Template: {tag_template.name}")

    # Load dbt manifest.json
    print(f"Loading dbt manifest from {MANIFEST_PATH}...")
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    # Filter nodes to get only models
    models = {
        key: value
        for key, value in manifest["nodes"].items()
        if value["resource_type"] == "model"
    }
    print(f"Found {len(models)} models in the manifest.")

    # Iterate over each model and create/update Data Catalog entries
    for model_name, model_info in models.items():
        """
        In this loop, we will:
        - Find or create an Entry in Data Catalog for the model
        - Create a Tag for the Entry using the Tag Template
        - Populate the Tag with metadata from the dbt model
        """

        # Find or create an Entry for the model
        resource_name = f"//bigquery.googleapis.com/projects/{model_info['database']}/datasets/{model_info['schema']}/tables/{model_info['alias']}"
        try:
            entry = client.lookup_entry(request={"linked_resource": resource_name})
            print(f"    Found existing Entry for model {model_name}: {entry.name}")
        except Exception as e:
            print(f"    Error retrieving or creating Entry for model {model_name}: {e}")
            continue

        # Create a Tag for the Entry
        tag = datacatalog_v1.Tag()
        tag.template = tag_template.name

        tag.fields["model_description"] = datacatalog_v1.TagField(
            string_value=model_info.get("description", "No description")
        )
        tag.fields["materialization"] = datacatalog_v1.TagField(
            string_value=model_info["config"].get("materialized", "N/A")
        )
        tag.fields["owner"] = datacatalog_v1.TagField(
            string_value=model_info["config"].get("meta", {}).get("owner", "N/A")
        )
        tag.fields["tags"] = datacatalog_v1.TagField(
            string_value=", ".join(model_info.get("tags", []))
        )
        tag.fields["path"] = datacatalog_v1.TagField(
            string_value=model_info.get("original_file_path", "")
        )

        # Attach the Tag to the Entry
        tag_found_and_deleted = False
        for existing_tag in client.list_tags(parent=entry.name):
            if existing_tag.template == tag_template.name:
                print(f"  - Deleting existing dbt tag: {existing_tag.name}")
                client.delete_tag(name=existing_tag.name)
                tag_found_and_deleted = True

        if not tag_found_and_deleted:
            print("  - No existing dbt tag found to delete.")

        print("  - Attaching new dbt metadata tag...")
        try:
            client.create_tag(parent=entry.name, tag=tag)
            print(f"  - SUCCESS: Successfully tagged '{model_info['name']}'.")
        except Exception as e:
            print(f"  - ERROR: Failed to attach tag. Error: {e}")


if __name__ == "__main__":
    sync_dbt_manifest_to_datacatalog()
