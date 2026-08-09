# Grounded AI analysis

The atlas can add a short AI interpretation to the existing neighborhood inspector without making the model a data source. The feature is optional: the calculation-based narrative remains the default and the automatic fallback.

## Trust boundary

The GitHub Pages browser never receives an OpenAI API key. It sends only two allowlisted fields to the server:

```json
{"nta_code":"BK93","metric":"trees"}
```

The endpoint rejects extra fields, arbitrary prompts, unknown metrics, malformed codes, ineligible areas, disallowed origins, and excessive requests. It reloads `data/processed/nta_environmental_snapshot.geojson` on the server and derives comparison values and source links from that file. User-supplied facts never enter the model prompt.

The model returns two short qualitative sentences. Digits, currency, percentages, years, URLs, HTML, Markdown links, causal claims, and funding recommendations are prohibited. The endpoint rejects output that violates the machine-checkable format. Exact values, source years, and citations are created by application code and remain visible in the inspector's metric cards.

This follows the official OpenAI requirement to keep API keys out of browsers and load them from a server environment or key manager. The endpoint uses the Responses API with `store: false`, a request timeout, an in-memory response cache, origin checks, and a per-instance rate limit. For public production traffic, add the hosting provider's durable rate limiting as well.

## Server configuration

`api/interpret.mjs` is a dependency-free Node serverless function and `vercel.json` includes the validated GeoJSON in its deployment bundle. Configure these server-only environment variables in the hosting provider:

| Variable | Required | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | Yes | Server-side project API key; never prefix it with a public/client environment name |
| `OPENAI_MODEL` | No | Defaults to `gpt-5.6-luna` for a short, cost-conscious interpretation |
| `ALLOWED_ORIGINS` | No | Comma-separated additions to the GitHub Pages and localhost origin allowlist |

Import the repository into Vercel or deploy it with the Vercel CLI, add `OPENAI_API_KEY`, and set `ALLOWED_ORIGINS` to every production preview/custom origin that should call the endpoint. Test a deployed endpoint with a POST containing only `nta_code` and `metric`.

## Connect GitHub Pages

Once the HTTPS endpoint exists, add its full URL as the repository variable `ATLAS_AI_ENDPOINT`. For example:

```bash
gh variable set ATLAS_AI_ENDPOINT --body "https://your-service.example/api/interpret"
gh workflow run deploy.yml
```

The Pages workflow writes that public URL to `_site/data/ai-config.json`. It never reads or copies `OPENAI_API_KEY`. If the repository variable is unset, the committed config contains an empty endpoint and the browser makes no AI request.

## Verification

```bash
npm test
python3 scripts/validate_build.py
```

The Node tests verify prompt-injection rejection, server-side evidence reconstruction, unsafe-output rejection, missing-key behavior, CORS, and the successful Responses API contract using a mocked model response. The Python build validator verifies the public endpoint configuration and scans published source for API-key-like values.

Official references: [OpenAI API authentication](https://developers.openai.com/api/reference/overview#authentication) and [OpenAI developer quickstart](https://developers.openai.com/api/docs/quickstart).
