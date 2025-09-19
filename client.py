import asyncio
import time
from pydicom import Dataset
from scp import ModalityStoreSCP
import json
import httpx

class SeriesCollector:
    """A Series Collector is used to build up a list of instances (a DICOM series) as they are received by the modality.
    It stores the (during collection incomplete) series, the Series (Instance) UID, the time the series was last updated
    with a new instance and the information whether the dispatch of the series was started.
    """
    def __init__(self, first_dataset: Dataset) -> None:
        """Initialization of the Series Collector with the first dataset (instance).

        Args:
            first_dataset (Dataset): The first dataset or the regarding series received from the modality.
        """
        self.series_instance_uid = first_dataset.SeriesInstanceUID
        self.series: list[Dataset] = [first_dataset]
        self.last_update_time = time.monotonic() # Change to .monotonic() to avoid system time jumps
        self.dispatch_started = False

    def add_instance(self, dataset: Dataset) -> bool:
        """Add an dataset to the series collected by this Series Collector if it has the correct Series UID.

        Args:
            dataset (Dataset): The dataset to add.

        Returns:
            bool: `True`, if the Series UID of the dataset to add matched and the dataset was therefore added, `False` otherwise.
        """
        if self.series_instance_uid == dataset.SeriesInstanceUID:
            self.series.append(dataset)
            self.last_update_time = time.monotonic()
            return True

        return False

    def num_instances(self) -> int:
        """Get the number of instances collected in this series.

        Returns:
            int: The number of instances collected in this series.
        """
        return len(self.series)

    def is_complete(self, timeout: float) -> bool:
        """Check if the series collection is complete.

        Args:
            timeout (float): The timeout duration in seconds.

        Returns:
            bool: `True` if the series collection is complete, `False` otherwise.
        """
        return  time.monotonic() - self.last_update_time > timeout

    def to_payload(self) -> dict:
        """Convert the series metadata to a payload dictionary.

        Returns:
            dict: A dictionary containing the series metadata.
        """
        first = self.series[0]

        metadata = {"PatientID": getattr(first, "PatientID", None),
            "PatientName": str(getattr(first, "PatientName", None)),
            "StudyInstanceUID": getattr(first, "StudyInstanceUID", None),
            "SeriesInstanceUID": self.series_instance_uid,
            "NumInstances": self.num_instances(),}
        metadata["idle_seconds"] = time.monotonic() - self.last_update_time #For logging/debug purposes if needed
        return metadata


class SeriesDispatcher:
    """This code provides a template for receiving data from a modality using DICOM.
    Be sure to understand how it works, then try to collect incoming series (hint: there is no attribute indicating how
    many instances are in a series, so you have to wait for some time to find out if a new instance is transmitted).
    For simplyfication, you can assume that only one series is transmitted at a time.
    You can use the given template, but you don't have to!
    """

    def __init__(self) -> None:
        """Initialize the Series Dispatcher.
        """

        self.loop: asyncio.AbstractEventLoop
        self.modality_scp = ModalityStoreSCP()
        self.series_collector: SeriesCollector | None = None

    async def main(self) -> None:
        """An infinitely running method used as hook for the asyncio event loop.
        Keeps the event loop alive whether or not datasets are received from the modality and prints a message
        regularly when no datasets are received.
        """
        while True:
            # TODO: Regulary check if new datasets are received and act if they are.
            # Information about Python asyncio: https://docs.python.org/3/library/asyncio.html
            # When datasets are received you should collect and process them
            # (e.g. using `asyncio.create_task(self.run_series_collector()`)

            # New dataset received from modality
            if self.modality_scp.incoming: # If the buffer is not empty
                await self.run_series_collectors()
            # SeriesCollector is complete and ready for dispatch
            elif self.series_collector and self.series_collector.is_complete(timeout=1.0):
                if not self.series_collector.dispatch_started:
                    self.series_collector.dispatch_started = True
                    asyncio.create_task(self.dispatch_series_collector())
            else:
                print("Waiting for Modality")

            await asyncio.sleep(0.2)


    async def run_series_collectors(self) -> None:
        """Runs the collection of datasets, which results in the Series Collector being filled.
        """
        # TODO: Get the data from the SCP and start dispatching
        while self.modality_scp.incoming:
            dataset = self.modality_scp.incoming.popleft() # Dequeue the oldest dataset, has O(1) compared to  list.pop(0) which has O(n)
            if not self.series_collector:
                # First dataset of a new series received, initialize the SeriesCollector
                self.series_collector = SeriesCollector(dataset)
            else:
                # Additional dataset belonging to the same series received, add it to the SeriesCollector
                self.series_collector.add_instance(dataset) # Assume only one series is transmitted at a time - no error statement


    async def dispatch_series_collector(self) -> None:
        """Tries to dispatch a Series Collector, i.e. to finish it's dataset collection and scheduling of further
        methods to extract the desired information.
        """
        # Check if the series collector hasn't had an update for a long enough timespan and send the series to the
        # server if it is complete
        # NOTE: This is the last given function, you should create more for extracting the information and
        # sending the data to the server
        if not self.series_collector:
            return

        payload = self.series_collector.to_payload()
        print(f"Dispatching series {payload['SeriesInstanceUID']} with {payload['NumInstances']} instances")

        # Using httpx to send a POST request:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8000/series", json=payload)
                response.raise_for_status()  # HTTP errors
        except httpx.HTTPError as e:
                print(f"Error dispatching series: {e}")

        # Clear the series collector after dspatch
        self.series_collector = None

if __name__ == "__main__":
    """Create a Series Dispatcher object and run it's infinite `main()` method in a event loop.
    """
    engine = SeriesDispatcher()
    engine.loop = asyncio.get_event_loop()
    engine.loop.run_until_complete(engine.main())
