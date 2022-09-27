import functools
import platform
from typing import List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.response import addinfourl
import urllib.request
import asyncio
from asyncio import Task
import argparse
from datetime import datetime, timedelta
import random
import logging
import sys


if platform.system() == "Windows":
  # really goofy thing you need to do to make it not freak out
  asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class CONFIG:
  """A simple class that holds global configuration values.

  ...

  Attributes
  ----------
  URL : str
    The URL to send requests to.
  LOG_PATH : str
    The path to store log files at.
  """

  URL = 'http://ifconfig.co/'
  TIMESTAMP_FMT = '%H:%M:%S'

def timestamp(sec: int) -> str:
  """Generates a timestamp for some number of seconds in the future.

  Args:
      sec (int): Seconds from now.

  Returns:
      str: A timestamp string in the format `HH:MM:SS`.
  """
  now = datetime.now()
  a_few_seconds = timedelta(seconds=sec)
  a_few_seconds_from_now = now + a_few_seconds
  return a_few_seconds_from_now.strftime(CONFIG.TIMESTAMP_FMT)

def timestamp_soon(a: int = 1, b: int = 5) -> str:
  """Generates a timestamp within a few seconds from now.

  Returns:
    str: A timestamp string in the format `HH:MM:SS`.
  """
  return timestamp(random.randint(1, 5))


def parse_timestring(timestring: str) -> datetime:
  """Parses a timestamp string into a datetime object with the day set to today.

  Args:
    timestamp (str): A string reprensting a time of day in the form of HH:MM:SS

  Returns:
    datetime.datetime: 
  """
  dt = datetime.strptime(timestring, CONFIG.TIMESTAMP_FMT)
  today = datetime.today()
  dt = dt.replace(year=today.year, month=today.month, day=today.day)
  return dt

async def wait_and_request(dt: datetime, url: str = CONFIG.URL, timeout: int = 1):
  """Waits until the given datetime and then performs a request.

  Args:
    dt (datetime): The datetime to wait until
    url (str): URL to request.
    timeout (int): Timeout to use.

  Returns:
    Future: The response.
  """
  now = datetime.now()
  seconds = (dt - now).total_seconds()
  logging.debug(f"Sleeping for {seconds}s")
  await asyncio.sleep(seconds)
  logging.debug("Done sleeping")
  loop = asyncio.get_running_loop()
  return await loop.run_in_executor(None, functools.partial(_do_request, url, timeout))

def _do_request(url: str = CONFIG.URL, timeout: int = 1) -> Optional[addinfourl]:
  """Perform a GET request on the given URL with a timeout.

  Args:
    url (str): URL to request.
    timeout (int): Timeout to use.

  Returns:
    str: The response.
  """
  # need to spoof user-agent to get response from ifconfig.co
  r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
  c: addinfourl = urllib.request.urlopen(r, timeout=timeout)
  try:
    logging.info(f"{c.status} from {c.url}")
    return c
  except HTTPError as e:
    logging.error(f"{e.code} - {e.reason} from {CONFIG.URL}")
    raise e
  except URLError as e:
    logging.exception("Exception making request!")
    raise e

def configure_logging() -> None:
  """Sets up logging.
  """
  root = logging.getLogger()
  formatter = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(message)s')

  todaystr = datetime.today().date().isoformat()
  stdout_handler = logging.StreamHandler(sys.stdout)
  file_handler = logging.FileHandler(f'{todaystr}.log', 'w')

  if __debug__:
    root.setLevel(logging.DEBUG)
    stdout_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
  else:
    root.setLevel(logging.INFO)
    stdout_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)

  stdout_handler.setLevel(logging.DEBUG)
  file_handler.setLevel(logging.DEBUG)

  stdout_handler.setFormatter(formatter)
  file_handler.setFormatter(formatter)
  root.addHandler(stdout_handler)
  root.addHandler(file_handler)

def _parse_cli() -> List[str]:
  """Gets arguments from the command line.

  Returns:
      str: _description_
  """
  parser = argparse.ArgumentParser(
    description="Makes GET requests at each time in a given list.")
  parser.add_argument("timestamps", type=str,
            help="comma-separated list of times in HH:MM:SS format")
  parser.add_argument("-u", "--url", type=str, help="request URL")
  args = parser.parse_args()
  if args.url:
    logging.debug(f"Request URL set to {args.url}")
    CONFIG.URL = args.url
  return args.timestamps.split(',')

async def start(timestamps: List[str]) -> Tuple[int, int, int]:
  """Takes a list of timestamp strings and schedules requests for them.

  Args:
      timestamps (List[str]): A list of HH:MM:SS timestamp strings.

  Returns:
      Tuple[int, int]: A tuple with the number of requests made and skipped respectively.
  """
  passes, skips = 0, 0
  tasks: List[Task[Optional[addinfourl]]] = []
  for timestring in timestamps:
    try:
      dt = parse_timestring(timestring)
      # if this is being ran after 00:00 for some reason, don't schedule times already passed
      if dt.time() < datetime.now().time():
        logging.warning(
          f"Timestamp {timestring} already passed, skipping")
        skips += 1
        continue
      task = asyncio.create_task(wait_and_request(dt))
      tasks.append(task)
      logging.debug(f"Registered event for {timestring}")
      passes += 1
    except ValueError:
      logging.error(f"Couldn't parse {timestring}")
      skips += 1
  logging.info(f"Registered {passes} events with {skips} skipped")
  
  errors = 0
  for coro in asyncio.as_completed(tasks):
    try:
      result = await coro
      if result:
        logging.info(f"{result.status} from {result.url}")
    except HTTPError as e:
      logging.error(f"{e.code} - {e.reason} from {CONFIG.URL}")
      errors += 1
    except Exception as e:
      logging.exception("Exception making request!")
      errors += 1
  return passes, skips, errors

if __name__ == '__main__':
  configure_logging()
  timestamps_list = _parse_cli()
  asyncio.run(start(timestamps_list), debug=True)