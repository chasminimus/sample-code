# Request Schedular

I opted to use `asyncio` to implement the prompt because it's an intuitive choice for scheduling tasks like making API requests and because it's cool. This is written with Python 3.9.9, so I would run it with that to be *absolutely* safe, but I don't think I used anything particularly cutting-edge so 3.10 might be fine. It definitely needs at least Python 3.8 though.

## Usage

See the help command for the rundown:

```
$ python reqsched.py -h
usage: reqsched.py [-h] [-u URL] timestamps

Makes GET requests at each time in a given list.

positional arguments:
  timestamps         comma-separated list of times in HH:MM:SS format

optional arguments:
  -h, --help         show this help message and exit
  -u URL, --url URL  request URL
```

## Testing

Tests are located in `test.py`. VSCode does a good job of gathering the testcases and running them, but of course you can run them from the command line as follows:
```
$ python test.py
```