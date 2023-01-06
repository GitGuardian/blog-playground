import logging
from collections.abc import Iterable
from datetime import datetime
from itertools import islice
from typing import TypeVar

from django.db.models import Model
from django.utils import timezone
from tqdm import tqdm


ModelType = TypeVar("ModelType", bound=Model)
logger = logging.getLogger(__name__)


class BulkCreator:
    """Helper class to create a bunch of objects in bulk and display progress."""

    start_time: datetime

    def __init__(
        self,
        model: type["ModelType"],
        total: int | None = None,
        batch_size: int = 2_000,
        keep_results: bool = True,
        unit: str | None = None,
    ) -> None:
        self.model = model
        self._batch: list[ModelType] = []
        self._created: list[ModelType] = []
        self._total_created = 0
        self._total = total
        self.keep_results = keep_results
        self.batch_size = batch_size
        self._unit = unit or self.model.__name__.lower()
        assert batch_size > 0

    def __enter__(self) -> "BulkCreator":
        self.start_time = timezone.now()
        return self

    @property
    def results(self) -> list["ModelType"]:
        if not self.keep_results:
            raise RuntimeError("Results were not kept")
        return self._created

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._batch:
            self.flush()

    def add(self, instance: ModelType) -> None:
        self._batch.append(instance)
        if len(self._batch) >= self.batch_size:
            self.flush()

    def add_many(self, instances: Iterable[ModelType]) -> None:
        instances = iter(instances)

        with tqdm(
            total=self._total,
            unit=self._unit,
            disable=self._total is None or self._total < self.batch_size,
        ) as progress_bar:
            while True:
                chunk_size = self.batch_size - len(self._batch)
                chunk = list(islice(instances, chunk_size))
                self._batch += chunk
                if len(chunk) < chunk_size:
                    break
                self.flush()
                progress_bar.update(len(chunk))

    def flush(self) -> None:

        if len(self._batch) > 0:
            created = self.model.objects.bulk_create(self._batch)
            if self.keep_results:
                self._created += created
            self._total_created += len(created)
            self._batch = []
