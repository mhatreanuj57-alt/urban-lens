# Cloud deployment

Local development stays on `docker-compose.yml`. This covers the two hosted
pieces: the Next.js frontend on Vercel and the FastAPI backend on Render.

```
browser -> Vercel (frontend) -> Supabase Auth (JWT)
                              -> Render (FastAPI, business + geo logic) -> Supabase Postgres
                                                                        -> S3-compatible storage
```

## 1. Backend — Render

`render.yaml` at the repo root is the whole service definition.

1. render.com -> **New+ -> Blueprint** -> authorise the GitHub app on
   `mhatreanuj57-alt/urban-lens` -> pick `master`. Render names the service
   itself, so read the URL from the dashboard: this one is
   `https://urban-lens-dg3s.onrender.com`.
2. Fill the `sync: false` variables in the dashboard (Blueprint never overwrite
   them afterwards):

   | Key | Value |
   | --- | --- |
   | `DATABASE_URL` | `postgresql+asyncpg://postgres.<ref>:<pct-encoded-pw>@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres` |
   | `DATABASE_URL_SYNC` | same, `postgresql://`, with `?sslmode=require` appended |
   | `SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` |
   | `SUPABASE_SECRET_KEY` | `sb_secret_...` (server only) |
   | `STORAGE_*` | see step 3 |

   Percent-encode the DB password (`#` -> `%23`, `=` -> `%3D`). Do **not** put
   `sslmode` in the asyncpg URL — asyncpg rejects the kwarg and does opportunistic
   TLS by itself.
3. Object storage: `STORAGE_ENDPOINT` / `STORAGE_PUBLIC_ENDPOINT` must be
   reachable from the browser, because uploads are presigned `PUT`s straight from
   the client. Supabase Storage's S3 gateway is verified to work with this
   service (probed 2026-09-21: it answers path-style requests and signs with
   SigV4):

   | Key | Value |
   | --- | --- |
   | `STORAGE_ENDPOINT` | `https://<ref>.supabase.co/storage/v1/s3` |
   | `STORAGE_PUBLIC_ENDPOINT` | same |
   | `STORAGE_PUBLIC_URL_BASE` | `https://<ref>.supabase.co/storage/v1/object/public/urbanlens-public` |
   | `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` | *Project Settings -> Storage -> S3 Protocol -> Create new access key* |
   | `STORAGE_REGION` | `us-east-1` |
   | `STORAGE_PATH_STYLE` | `true` |
   | `STORAGE_BUCKET_PRIVATE` / `STORAGE_BUCKET_PUBLIC` | `urbanlens-private` / `urbanlens-public` |

   Create `urbanlens-private` and `urbanlens-public` in the Storage dashboard and
   flip **Public bucket** on the second one: `PutBucketPolicy` is not part of
   Supabase's S3 surface, so the anonymous-read grant cannot come from the app,
   and objects under `/object/public/` 404 until the flag is set. Cloudflare R2
   works too (`https://<account>.r2.cloudflarestorage.com`, region `auto`, public
   URL base = the bucket's dev/custom-domain URL), but its `r2.dev` public
   gateway needs a paid plan, so it is not the free-tier answer.

   Whatever the provider, confirm one presigned browser upload end to end before
   trusting the config — the client `PUT`s straight to the URL the API hands back.
4. Detection is off on the 512 MB free tier — torch does not fit. Change
   `ARG ML_INSTALL=0` to `1` in `backend/Dockerfile` and move to a 1 GB+
   instance to run YOLOv8 in the cloud; `pipeline.py` degrades to
   "detection skipped" when no weights are present.
5. The hosted schema is already migrated. After a model change run
   `alembic upgrade head` with `DATABASE_URL_SYNC` from a shell that can reach
   the pooler.

## 2. Frontend — Vercel

Project `urban-lens` builds `frontend/` with the standard Next.js preset.
Production is live at `https://urban-lens-seven.vercel.app`.
Environment variables (all build-time `NEXT_PUBLIC_*`, so they are visible in
the browser — publishable key only):

| Key | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://urban-lens-backend.onrender.com/v1` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `sb_publishable_...` |

Evidence photos need no storage variable: the API returns an absolute
`public_url` per media asset, built server-side from `STORAGE_PUBLIC_ENDPOINT`.

`vercel env add <KEY> production` then pipe the value; redeploy with
`vercel --prod` from `frontend/`. Redeploy whenever an env value changes —
`NEXT_PUBLIC_*` is baked into the client bundle at build time. Vercel rejects
deployments of Next.js releases with known CVEs, so keep `next` on the latest
15.5.x patch.

Add the production origin to the backend's `CORS_ORIGINS` or the browser will
block every API call.

## 3. Supabase side

- **Redirect / site URL**: Authentication -> URL Configuration -> add the
  Vercel domain to *Site URL* and *Redirect URLs*.
- Signup emails come from Supabase's own sender until you attach a custom SMTP
  (the free tier caps at 2 emails/hour, which also throttles `register`).
- `.demo` and other non-existent TLDs are rejected by the email validator, so
  demo accounts can only be created through `python -m app.seed`, which uses
  the admin API and skips validation.
