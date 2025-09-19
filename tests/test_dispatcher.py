import asyncio
import pytest
from pydicom.dataset import Dataset
from client import SeriesDispatcher, SeriesCollector

def make_fake_dataset(suid="1.2.3.4"):
    ds = Dataset()
    ds.SeriesInstanceUID = suid
    ds.PatientID = "123"
    ds.PatientName = "Doe^John"
    ds.StudyInstanceUID = "0.0.0.0"
    return ds

@pytest.mark.asyncio
async def test_run_series_collectors_collects():
    """
    Test that run_series_collectors correctly collects datasets into a SeriesCollector.
    """
    disp = SeriesDispatcher()
    # Add a fake dataset to the incoming buffer
    ds1 = make_fake_dataset()
    disp.modality_scp.incoming.append(ds1)

    await disp.run_series_collectors()

    assert isinstance(disp.series_collector, SeriesCollector)
    assert disp.series_collector.num_instances() == 1


"""
Additional Tests:
1. Check the debounce structure - dispatch after no new datasets for a timeout period.
2. Check POST payload structure.
3. Check dispatching logic (mock HTTP POST).
"""
