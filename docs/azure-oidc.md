# Azure OIDC Setup for GitHub Actions Deployment

This document explains how to configure the Azure Entra ID (Azure AD) federated
credential so that the `azure/login@v2` step in the GitHub Actions workflow can
authenticate using OpenID Connect (OIDC) — **without storing any long-lived
secrets**.

---

## Why OIDC?

Instead of storing a client secret or certificate in GitHub Secrets, GitHub
generates a short-lived OIDC token for each workflow run. Azure validates that
token against a **federated credential** registered on your App Registration (or
Managed Identity). This is more secure because no static credential ever leaves
Azure.

---

## Required Azure Federated Credential

You must add a federated credential to the Azure Entra ID App Registration (or
User-Assigned Managed Identity) whose `client-id` is stored in the GitHub
secret `AZUREAPPSERVICE_CLIENTID_*`.

### Credential values

| Field       | Value |
|-------------|-------|
| **Issuer**  | `https://token.actions.githubusercontent.com` |
| **Audience**| `api://AzureADTokenExchange` |
| **Subject** | `repo:elikimz/simba_cement_api:ref:refs/heads/main` |

The subject **must exactly match** the OIDC token claim GitHub sends. The
subject is determined by how the workflow is triggered:

| Trigger | Subject |
|---------|---------|
| Push / PR to `main` | `repo:elikimz/simba_cement_api:ref:refs/heads/main` |
| `workflow_dispatch` on `main` | `repo:elikimz/simba_cement_api:ref:refs/heads/main` |
| Tag push (e.g. `v1.0.0`) | `repo:elikimz/simba_cement_api:ref:refs/tags/v1.0.0` |

> Push to `main` and `workflow_dispatch` on `main` share the same subject, so
> a single credential covers both. For tag-based deployments, create an
> additional federated credential with the corresponding tag subject.

---

## Step-by-step: Adding the Federated Credential

### Option A — Azure Portal

1. Go to **Azure Portal → Azure Entra ID → App registrations**.
2. Select the app registration whose **Application (client) ID** matches the
   `AZUREAPPSERVICE_CLIENTID_*` secret value.
3. In the left panel choose **Certificates & secrets → Federated credentials**.
4. Click **+ Add credential** and fill in:
   - **Federated credential scenario**: *GitHub Actions deploying Azure resources*
   - **Organization**: `elikimz`
   - **Repository**: `simba_cement_api`
   - **Entity type**: *Branch*
   - **Branch**: `main`
   - **Name**: e.g. `github-actions-main`
5. Confirm that the generated **Subject identifier** reads:
   ```
   repo:elikimz/simba_cement_api:ref:refs/heads/main
   ```
6. Click **Add**.

### Option B — Azure CLI

```bash
az ad app federated-credential create \
  --id <APPLICATION_OBJECT_ID> \
  --parameters '{
    "name": "github-actions-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:elikimz/simba_cement_api:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

Replace `<APPLICATION_OBJECT_ID>` with the **Object ID** of the App Registration
(different from the Client/Application ID).

---

## Required GitHub Secrets

The following repository secrets must be set under
**Settings → Secrets and variables → Actions**:

| Secret name | Where to find the value |
|-------------|------------------------|
| `AZUREAPPSERVICE_CLIENTID_*` | App Registration → **Application (client) ID** |
| `AZUREAPPSERVICE_TENANTID_*` | App Registration → **Directory (tenant) ID** |
| `AZUREAPPSERVICE_SUBSCRIPTIONID_*` | Azure Portal → **Subscriptions → Subscription ID** |

> The `*` suffix in the secret names above represents the unique identifier
> suffix already present in the workflow file. Do **not** change the secret
> names — the workflow references them exactly as they appear.

---

## Verifying the Setup

After adding the federated credential and secrets, trigger the workflow by
pushing to `main`. The `Login to Azure` step should succeed. If it fails with
`AADSTS700213`, double-check that the **Subject** on the Azure credential
exactly matches `repo:elikimz/simba_cement_api:ref:refs/heads/main`.

---

## References

- [GitHub docs — OIDC with Azure](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-azure)
- [Azure docs — Workload identity federation](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust)
- [`azure/login` action](https://github.com/Azure/login)
