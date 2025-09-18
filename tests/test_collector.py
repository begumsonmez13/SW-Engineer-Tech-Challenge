import time
import pytest
from pydicom.dataset import Dataset
from client import SeriesCollector

def make_fake_dataset(suid="1.2.3.4", pid="123", pname="Doe^John", stid="0.0.0.0"):
    ds = Dataset()
    ds.SeriesInstanceUID = suid
    ds.PatientID = pid
    ds.PatientName = pname
    ds.StudyInstanceUID = stid
    return ds

def test_add_instance_and_num_instances():
    """
    Test add_instance and num_instances methods in the SeriesCollector class
    Add an instance with matching SeriesInstanceUID and one with a wrong UID
    and verify the number of instances collected.
    """
    ds1 = make_fake_dataset()
    series_collector = SeriesCollector(ds1)

    # Add a correct(matching) instance
    ds2 = make_fake_dataset()
    assert series_collector.add_instance(ds2) is True
    assert series_collector.num_instances() == 2

    # Add a wrong Series UID
    ds3 = make_fake_dataset(suid="1.1.1.1")
    assert series_collector.add_instance(ds3) is False
    assert series_collector.num_instances() == 2  # not added

def test_is_complete_timeout():
    """
    Test the is_complete method with timeou
    """
    data = make_fake_dataset()
    series_collector = SeriesCollector(data)

    # Should not be complete immediately
    assert not series_collector.is_complete(timeout=0.5)

    # Wait long enough to exceed timeout
    time.sleep(0.6)
    assert series_collector.is_complete(timeout=0.5)

def test_payload_structure():
    """"
    Test to check the payload dictionary has the correct structure and fields
    """
    data = make_fake_dataset()
    series_collector = SeriesCollector(data)
    payload = series_collector.to_payload()

    assert "PatientID" in payload
    assert "PatientName" in payload
    assert "StudyInstanceUID" in payload
    assert "SeriesInstanceUID" in payload
    assert "NumInstances" in payload
    assert payload["NumInstances"] == 1
