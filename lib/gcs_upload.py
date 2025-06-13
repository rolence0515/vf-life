import os
from google.cloud import storage

def upload_file_to_gcs(local_path, bucket_name, gcs_path, content_type=None):
    """
    將本地檔案 local_path 上傳到指定 GCS bucket/gcs_path。
    content_type 可選，預設自動判斷。
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path, content_type=content_type)
    # 若 bucket 啟用 uniform bucket-level access，不能用 make_public
    # 回傳 public url（需 bucket policy 允許 public read 才能直接下載）
    public_url = f'https://storage.googleapis.com/{bucket_name}/{gcs_path}'
    return public_url
