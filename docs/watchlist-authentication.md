# Authenticated watchlists: deployment setup

The Market and Scanner personal watchlists use the authenticated identity exposed by
Streamlit as `st.user`. A logged-out session must not access personal watchlists.

## 1. Configure an OIDC provider

For Streamlit Community Cloud, open **App settings → Secrets**. For another host,
put the same TOML configuration in that host's protected Streamlit secrets store.
Do not commit real credentials to this repository.

Example using Google OpenID Connect (replace every placeholder with values from
your OAuth client):

```toml
[auth]
redirect_uri = "https://YOUR-DEPLOYED-APP-URL/oauth2callback"
cookie_secret = "REPLACE_WITH_A_LONG_RANDOM_SECRET"
client_id = "YOUR_OAUTH_CLIENT_ID"
client_secret = "YOUR_OAUTH_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Register the exact `redirect_uri` with the identity provider's authorized redirect
URIs. For local development, use a separate OAuth client and
`http://localhost:8501/oauth2callback`. Never reuse or publish production secrets.

## 2. Configure durable watchlist storage

Set `WATCHLIST_DATABASE_PATH` to a writable path on durable storage supported by
your hosting platform. The default local SQLite file can be lost when an ephemeral
container restarts or redeploys. Back up the database according to your hosting
platform's storage guarantees.

## 3. Deploy and verify

1. Save the protected secrets and restart/redeploy the app.
2. Open Market and click **Sign in**.
3. Complete the provider login and return to Market.
4. Add a test symbol, refresh the page, and confirm it remains.
5. Open Scanner and choose **Personal Watchlist**; confirm it reads the same symbols.
6. Sign out or use a separate test account and confirm another identity cannot see the
   first account's saved symbols.

The application deliberately does not infer identity from form inputs, query
parameters, or a username typed by the visitor. If OIDC is not configured, the
personal watchlist stays unavailable; broad-market scanning remains available.
