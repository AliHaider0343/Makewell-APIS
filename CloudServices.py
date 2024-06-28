from google.cloud import storage

def upload_file(source_file_name, destination_blob_name,bucket_name="prescription_descriptions"):
    storage_client = storage.Client.from_service_account_json('makewell-assistant-c511916855f0.json')
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    return blob.public_url