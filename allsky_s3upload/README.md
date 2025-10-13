# Allsky S3 Upload (SkyVault)

We built this for the community; feel free to use it standalone, or connect to SkyVault.

Uploads images to Amazon S3 with a lightweight retry cache.
- Respects module order: place **after** overlays to upload the overlaid image.
- If placed before “Save image”, it serializes the in-memory frame.
- S3 key layout: `<prefixBase>/YYYY-MM-DD/HH/<image-filename>`
- Dependencies: `boto3` (via `dependencies/allsky_s3upload/requirements.txt`)

## Development
- `allsky_s3upload.py` contains a **JSON-strict** `metaData` block.
- Keep `argumentdetails` simple (`type: text|password|select|checkbox|number`).
- S3 policy examples included

## Security
Use a dedicated IAM user limited to your bucket/prefix. See `example-iam-policy.json` and `example-bucket-policy.json`.

## License
MIT

Titan Astro S.L., Spain
