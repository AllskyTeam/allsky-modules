Allsky S3 Upload (SkyVault)
---------------------------

Uploads images to S3 using boto3 with a lightweight retry cache.

How to use:
1) Install dependencies via the Module Installer (or ensure boto3 is present).
2) In the WebUI, configure:
   - AWS Access Key ID / Secret Access Key
   - AWS Region (e.g., eu-north-1)
   - S3 Bucket (your SkyVault user bucket)
   - Optional: prefixBase (default "allsky")
   - Storage Class (e.g., STANDARD_IA)
   - Enable During Day / Night
3) Place this module BEFORE or AFTER overlay modules to decide whether you upload
   the raw/pre-overlay image (before) or the final/post-overlay image (after).
4) 'periodic' is used to flush the retry cache. You can adjust the interval.

S3 keys:
  <prefixBase>/YYYY-MM-DD/HH/<filename>

Retry cache:
  If an upload fails, details are written to:
    /opt/allsky/modules/cache/allsky_s3upload/*.json
  These are flushed automatically on 'periodic' runs and opportunistically
  at the start of day/night events.

Security:
  Use a dedicated IAM user limited to:
    s3:PutObject on arn:aws:s3:::<bucket>/<prefixBase>/*
  Optional:
    s3:ListBucket with Condition s3:prefix = "<prefixBase>/*"
  Set a TLS-only bucket policy (Deny if aws:SecureTransport=false).

Notes:
  - This module uploads whatever file path Allsky exposes as the "current" image
    at the time it runs. Use module ordering to control pre/post overlay behavior.
  - All times for partitioning use UTC to avoid local-time gaps.

We built this for the community; feel free to use it standalone, or connect to SkyVault.