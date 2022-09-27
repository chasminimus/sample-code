import asyncio
import unittest
from unittest import TestCase
import unittest.mock as mock
from datetime import datetime, timedelta
import reqsched
from reqsched import CONFIG


class SoonTest(TestCase):
  def test_timestamp_soon(self):
    """Assert that generated soon timestamps are indeed within a few seconds.
    """
    ten_seconds_from_now = datetime.now() + timedelta(seconds=10)
    for _ in range(50):
      soon = datetime.strptime(reqsched.timestamp_soon(), CONFIG.TIMESTAMP_FMT)
      self.assertTrue(soon < ten_seconds_from_now)


midnight = datetime.today().replace(hour=0, minute=0, second=0)

# dummy wrapper for replacing methods with
class DummyDate(datetime):
  pass
DummyDate.now = classmethod(lambda cls: midnight)  # type: ignore

class Test(unittest.IsolatedAsyncioTestCase):
  """Tests that requests are properly scheduled and made.
  """
  @mock.patch('reqsched.datetime', DummyDate)
  async def _test_n_requests(self, n: int):
    timestamps = [reqsched.timestamp_soon(a=0) for _ in range(n)]
    passes, skips, errors = await reqsched.start(timestamps)
    await asyncio.sleep(7) 
    self.assertEqual(passes + skips, n)

  async def test_some(self):
    """Tests a small number of scheduled tasks.
    """
    await self._test_n_requests(5)

  async def test_many(self):
    """Tests a more dense number of scheduled tasks, some overlapping. It is expected to get HTTP 429 errors if using ifconfig.co.
    """
    await self._test_n_requests(10)


if __name__ == "__main__":
  reqsched.configure_logging()
  unittest.main()
