from typing import override

import httpx

from app.tasks import DeliveryResult, DeliverySnapshot, SendFn


class FakeQueue:
    def __init__(self) -> None:
        self.enqueued = []

    async def enqueue(self, name, **kwargs):
        self.enqueued.append(kwargs)


class FakeRaisingQueue(FakeQueue):
    def __init__(self, fail_for: set[str], fail_all: bool = False) -> None:
        super().__init__()
        self.fail_for = fail_for
        self.fail_all = fail_all

    @override
    async def enqueue(self, name, **kwargs):
        if self.fail_all or kwargs["delivery_id"] in self.fail_for:
            raise RuntimeError
        await super().enqueue(name, **kwargs)


def send_fn(results: list[DeliveryResult], calls: list[DeliverySnapshot]) -> SendFn:
    async def _send_fn(
        client: httpx.AsyncClient, snapshot: DeliverySnapshot
    ) -> DeliveryResult:
        calls.append(snapshot)
        return results.pop(0)

    return _send_fn


class FakeWorker:
    def __init__(self, queue) -> None:
        self.queue = queue
