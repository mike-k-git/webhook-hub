# webhook-hub

webhook-hub is a self-hosted router for webhooks. It takes in webhooks from the sources you configure, checks their signatures, and drops duplicates. Every event gets saved. Then it fans each one out to one or more destinations and keeps trying until it succeeds. You get retries, backoff, dead-lettering, and replay. There's also a React dashboard for inspecting payloads and replaying anything that failed.

The goal is infrastructure you'd put between a provider and your services. Nothing gets delivered from the request path. No event is acknowledged until it's stored. And the database, not the queue, decides what still needs to go out.

## How it works

A handful of decisions shape the whole thing. They're all on purpose.

**Postgres is the ledger. Redis just runs the jobs.** Delivery state and the retry schedule live in Postgres. Putting a job on the queue is only a "look now" nudge. It is never the record that a delivery is owed. So if a queue message goes missing, no webhook quietly disappears. A sweeper checks the ledger on a timer and re-dispatches anything that's due or stuck.

**The request path stays fast.** Ingest does only the quick work. It reads the raw bytes, checks the signature, drops duplicates, saves the event and its delivery rows in one transaction, and returns `202`. That's it. Every outbound call happens later, in a separate async worker. Webhook senders time out in seconds, so this matters.

**At-least-once, and honest about it.** Duplicates are caught at ingest with a unique constraint on `(source, idempotency_key)`. Each delivery is claimed atomically before any work starts, so two workers can't run the same one. Delivery can still duplicate when things go wrong. That's expected, and destinations should handle it. The system doesn't claim exactly-once, because it can't.

**Destinations are locked in at ingest.** When an event arrives, its list of destinations is frozen. Replay re-runs that same list. The delivery history stays an honest record of what happened.

Signatures are checked as `HMAC-SHA256` over the exact raw bytes. It never re-serializes the JSON first. The comparison is constant-time. A failed check always returns the same `401`, so it doesn't leak which part failed.

## Stack

Backend is FastAPI and Pydantic v2 on Python. Data goes through async SQLAlchemy 2.0 and asyncpg into PostgreSQL, with Alembic for migrations. The delivery worker runs on Redis and SAQ. Outbound calls use httpx. Tests are pytest with pytest-asyncio and respx. The frontend is React and TypeScript on Vite, with TanStack Query and Tailwind. It all runs under Docker Compose.

## Running locally

```bash
cp backend/.env.example backend/.env   # set POSTGRES_* and the DSNs
docker compose up --build
```

That starts Postgres, Redis, the API on `:8000`, and the worker. From there you can configure sources, destinations, and routes. Send webhooks to `POST /ingest/{source}`. Read back the event feed, the full detail for any event including its delivery attempts, and the dead-letter inbox.

## Status

Still being built, but the core loop runs end to end. Signature checks, idempotent dedupe, routing with fan-out, the read API, and the async delivery worker are all done and tested. The worker claims each delivery atomically, POSTs it, records the attempt, and reschedules failures for another try. A sweeper recovers anything a lost enqueue or a crashed worker left stranded. So an event can come in, get verified and stored, and be delivered to every destination with retries, today.

Next up is making those retries smart: backoff, an attempt cap, and dead-lettering.

## Planned

Retries already happen, just on a flat delay. The next step makes them smart: exponential backoff with jitter so they don't stampede, a cap on attempts, and dead-letter for whatever runs out. Then failed deliveries become replayable in one click. A React dashboard will sit on top of the read API for inspecting payloads and replaying failures. After that, a one-command deploy to Fly.io or Railway. Further out, the hub will reshape payloads per route and sign its own outbound requests.
