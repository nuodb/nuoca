import os
import logging
import nuoca_util


def _nuoca_init():
  if not os.path.exists("/tmp/nuoca"):
    os.mkdir("/tmp/nuoca")
  nuoca_util.nuoca_set_log_level(logging.INFO)
  nuoca_util.nuoca_log(logging.INFO, "nuoca server init.")


def _nuoca_shutdown():
  nuoca_util.nuoca_log(logging.INFO, "nuoca server shutdown")
  nuoca_util.nuoca_logging_shutdown()


def main():
  try:
    _nuoca_init()
  except Exception as e:
    nuoca_util.nuoca_log(logging.ERROR, "Unhandled exception: %s" % e)
  finally:
    _nuoca_shutdown()
  print("Done.")


if __name__ == "__main__":
  main()

