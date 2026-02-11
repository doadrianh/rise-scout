# Rise Scout

Contact Intelligence & MLS Search Platform for MoxiWorks/RISE.

Rise Scout scores real estate contacts based on behavioral signals, matches them against listing events via inverted search, and surfaces the most relevant contacts to agents through auto-refreshing cards with AI-generated insights.

## Architecture

```
Kafka Topics                    AWS Lambda                   Storage
──────────────                  ──────────                   ───────
ai_contact_change_payloads ───> contact-consumer ──────────> OpenSearch Serverless
ai_contact_interactions    ───> contact-consumer              (contacts index)
listings.updates           ───> listing-consumer
                                                             DynamoDB
EventBridge (scheduled)    ───> score-decay                   (agent cards)
EventBridge (scheduled)    ───> card-refresh ──────────────>
                                     │                       Redis
                                     └── Bedrock (Claude)    (refresh flags)
```

**Key design decisions:**

- **Inverted search** — listing events query the contacts index (not contacts querying listings), avoiding a separate listings index
- **Signal-based scoring** — configurable point weights per signal type with automatic time-based decay
- **Domain events** — `ContactScored` events decouple scoring side effects from application orchestration
- **RBAC** — MLS-based access control enforced at query time via `mls_id` terms filter

## Project Structure

```
src/
├── rise_scout/
│   ├── domain/                  # Core business logic (no external dependencies)
│   │   ├── contact/             #   Contact aggregate, repository protocol
│   │   ├── scoring/             #   ScoringEngine, DecayCalculator, signal types
│   │   ├── search/              #   ListingEvent, MatchedContact, search protocol
│   │   ├── cards/               #   Card model, LLM enrichment protocol
│   │   ├── embeddings/          #   Embedding service protocol
│   │   └── shared/              #   Domain events, types (ContactId, AgentId, etc.)
│   ├── application/             # Use case orchestration
│   │   ├── contact_ingestion.py #   Ingest contact changes & interactions
│   │   ├── listing_matching.py  #   Match listings to contacts, apply signals
│   │   ├── score_decay.py       #   Periodic score decay
│   │   ├── card_refresh.py      #   Generate agent cards with top contacts
│   │   └── event_handlers.py    #   Domain event dispatch (refresh flags)
│   └── infrastructure/          # External integrations
│       ├── opensearch/          #   Contact & search repository implementations
│       ├── dynamodb/            #   Card repository
│       ├── redis/               #   Refresh flags, event debouncing
│       ├── bedrock/             #   Embeddings (Titan), LLM insights (Claude)
│       ├── kafka/               #   Payload parsers
│       └── container.py         #   Dependency injection
├── lambdas/                     # Lambda handler entry points
│   ├── contact_consumer/
│   ├── listing_consumer/
│   ├── score_decay/
│   └── card_refresh/
cdk/                             # Infrastructure as Code (TypeScript CDK)
config/
└── scoring_weights.json         # Signal weights, decay rate, score cap
```

## Scoring Signals

| Category     | Signal              | Points |
|-------------|---------------------|--------|
| Profile      | preferences_complete | 15     |
| Profile      | has_email            | 5      |
| Profile      | has_phone            | 5      |
| Profile      | multi_agent          | 10     |
| Engagement   | listing_view         | 3      |
| Engagement   | listing_save         | 8      |
| Engagement   | listing_share        | 10     |
| Engagement   | search_performed     | 2      |
| Engagement   | open_house_rsvp      | 20     |
| Engagement   | document_signed      | 25     |
| Market       | new_listing_match    | 10     |
| Market       | price_drop_match     | 12     |
| Market       | status_change_match  | 8      |
| Market       | back_on_market_match | 15     |
| Relationship | agent_note_added     | 5      |
| Relationship | contacted_recently   | 7      |

Scores decay daily (rate: 0.95) and cap at 1000. Reasons older than 30 days are pruned.

## Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your AWS, Redis, and OpenSearch settings
```

### Environment Variables

All prefixed with `RISE_SCOUT_`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `dev` | Environment (`dev`, `staging`, `prod`) |
| `AWS_REGION` | `us-west-2` | AWS region |
| `AOSS_ENDPOINT` | | OpenSearch Serverless endpoint |
| `CONTACTS_INDEX` | `contacts` | OpenSearch index name |
| `CARDS_TABLE` | `rise-scout-cards` | DynamoDB table name |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `EMBEDDING_MODEL_ID` | `amazon.titan-embed-text-v2:0` | Bedrock embedding model |
| `LLM_MODEL_ID` | `anthropic.claude-3-haiku-20240307-v1:0` | Bedrock LLM model |

## Development

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests (requires local services)
pytest tests/integration/ -m integration

# Lint & format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/
```

## Infrastructure

CDK stacks are in `cdk/` (TypeScript):

```bash
cd cdk
npm install
npx cdk synth
npx cdk deploy --all
```
