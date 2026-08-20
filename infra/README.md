# Database backups

`backup-db.sh` dumps the production Postgres container to a local
`.sql.gz` file and, if configured, uploads it to S3. `restore-db.sh`
reverses the process. Both expect to be run on the server, from inside
this repo, with `.env.prod` already filled in.

Set this up before there are real registrations to lose.

## One-time setup

**1. Create the S3 bucket** (from your own machine, with `aws` configured,
or via the console):

```bash
aws s3 mb s3://<your-unique-bucket-name> --region <your-region>
```

Add a lifecycle rule so old offsite copies expire automatically instead of
accumulating cost forever — Console: bucket → **Management** → **Create
lifecycle rule** → expire objects after e.g. 30 days.

**2. Give the server permission to write to it.** On AWS EC2, use an IAM
instance role rather than static keys on disk:

- IAM → **Roles** → **Create role** → trusted entity: **EC2**
- Attach an inline policy scoped to just this bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::<your-unique-bucket-name>/*"
    }
  ]
}
```

- EC2 → your instance → **Actions → Security → Modify IAM role** → attach
  the new role. No AWS keys are ever written to `.env.prod` this way.

**3. Install the AWS CLI on the server** (needed for the upload step):

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip awscliv2.zip && sudo ./aws/install
```

**4. Set `BACKUP_S3_BUCKET` in `.env.prod`** on the server to the bucket
name from step 1.

**5. Wire up the cron job**:

```bash
crontab -e
```

```
0 3 * * * /home/ubuntu/siavonga-independence-api/infra/backup-db.sh >> /home/ubuntu/db-backups/backup.log 2>&1
```

(Adjust the path to wherever the repo is actually cloned.)

## Restoring

```bash
./infra/restore-db.sh /home/ubuntu/db-backups/siavonga_run_20260101_030000.sql.gz
```

Prompts for confirmation before dropping anything — it's destructive by
design (drops and recreates the database, then loads the dump).

To pull a specific backup down from S3 first:

```bash
aws s3 cp s3://<bucket>/siavonga_run_20260101_030000.sql.gz /tmp/restore.sql.gz
./infra/restore-db.sh /tmp/restore.sql.gz
```

**Test this at least once** after setting it up — an untested backup
strategy is not a backup strategy. Run a backup, then restore it into a
throwaway local Postgres (`docker compose up -d db`, point `restore-db.sh`
at your local `.env` instead) to confirm the dump is actually valid.

## Local dev

None of this applies to `docker-compose.yml` (local dev) — that database
is disposable by design. These scripts only target
`docker-compose.prod.yml`.
