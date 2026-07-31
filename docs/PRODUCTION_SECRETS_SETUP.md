# Production secrets — one-time setup

The `mizoki-website` Cloud Run service reads two secrets at runtime via Secret Manager (wired in `cloudbuild.yaml` via `--set-secrets`):

| Secret name | Maps to env var | What it does |
|:------------|:----------------|:-------------|
| `mizoki-website-secret-key` | `SECRET_KEY` | Flask session signing key. Pinning it means sessions survive container restarts. |
| `mizoki-website-demo-users` | `MIZOKI_DEMO_USERS_JSON` | `{email: password}` map for `/admin/login`. |

## Step 1 — generate strong values locally

Run this on your laptop (or in any throwaway shell). Output is **not** committed; copy it into `1Password` / `Bitwarden` / wherever you keep ops creds, then proceed to step 2.

```bash
python3 - <<'PY'
import secrets, string, json
sk = secrets.token_hex(32)
alphabet = (string.ascii_letters.replace('l','').replace('I','').replace('O','')
            + string.digits.replace('0','').replace('1','') + '!@#%^&*-_=+')
users = {
    'admin@mizoki3.com':        ''.join(secrets.choice(alphabet) for _ in range(24)),
    'ceo@mediaintelligence.ai': ''.join(secrets.choice(alphabet) for _ in range(24)),
}
print('SECRET_KEY:               ', sk)
print('MIZOKI_DEMO_USERS_JSON:   ', json.dumps(users))
PY
```

## Step 2 — push the values into Secret Manager

Replace `<SECRET_KEY>` and `<USERS_JSON>` with what step 1 printed.

```bash
PROJECT=spry-bus-425315-p6

# Create the secrets (idempotent: ignore "already exists")
gcloud secrets create mizoki-website-secret-key  --project="$PROJECT" --replication-policy=automatic 2>/dev/null || true
gcloud secrets create mizoki-website-demo-users --project="$PROJECT" --replication-policy=automatic 2>/dev/null || true

# Add a version to each. Use printf (not echo) so no trailing newline is included.
printf %s '<SECRET_KEY>' | \
  gcloud secrets versions add mizoki-website-secret-key  --project="$PROJECT" --data-file=-

printf %s '<USERS_JSON>' | \
  gcloud secrets versions add mizoki-website-demo-users --project="$PROJECT" --data-file=-
```

## Step 3 — grant the Cloud Run runtime SA read access

Cloud Run uses the default Compute Engine service account unless overridden. Grant it `secretAccessor` on each secret.

```bash
PROJECT=spry-bus-425315-p6
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
SA=${PROJECT_NUMBER}-compute@developer.gserviceaccount.com

for s in mizoki-website-secret-key mizoki-website-demo-users; do
  gcloud secrets add-iam-policy-binding "$s" \
    --project="$PROJECT" \
    --member="serviceAccount:${SA}" \
    --role=roles/secretmanager.secretAccessor
done
```

## Step 4 — deploy

```bash
gcloud builds submit "# MIZ OKI 3.5" \
  --config="# MIZ OKI 3.5/cloudbuild.yaml" \
  --project=spry-bus-425315-p6 \
  --region=us-central1
```

Cloud Build will pick up the `--set-secrets` lines in `cloudbuild.yaml` automatically. The service will boot with both env vars populated from Secret Manager.

## Step 5 — verify

```bash
# /admin/login should render the form
curl -sI https://mizoki3.com/admin/login | head -1
#   HTTP/2 200

# /admin without a session should 302 to /admin/login
curl -sI https://mizoki3.com/admin | head -2
#   HTTP/2 302
#   location: /admin/login

# Sign in with the credentials from step 1
```

## Rotating

To rotate either secret, add a new version (Cloud Run uses `:latest` so it picks up on next deploy):

```bash
printf %s '<NEW_VALUE>' | \
  gcloud secrets versions add mizoki-website-secret-key --project=spry-bus-425315-p6 --data-file=-

# Force Cloud Run to pick up the new version (otherwise it stays on the old one until next deploy)
gcloud run services update mizoki-website \
  --project=spry-bus-425315-p6 --region=us-central1 \
  --update-secrets=SECRET_KEY=mizoki-website-secret-key:latest
```

Rotating `SECRET_KEY` invalidates all existing admin sessions (everyone has to sign in again). Rotating `MIZOKI_DEMO_USERS_JSON` does **not** invalidate existing sessions — old session cookies stay valid until they expire (8 hours) or the user signs out.

## Gating the API surface

Once you're ready to require admin sign-in for `/api/mcp/*` and `/api/boss/*` (today they're public so the site-level chat demo can call them), flip:

```bash
gcloud run services update mizoki-website \
  --project=spry-bus-425315-p6 --region=us-central1 \
  --update-env-vars=MIZOKI_REQUIRE_AUTH_FOR_APIS=true
```

`/api/health` always stays public for monitoring. Anything else under `/api/mcp/*` or `/api/boss/*` will return `401 {"error":"Authentication required"}` to unauthenticated callers.
