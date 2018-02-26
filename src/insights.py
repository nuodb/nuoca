# (C) Copyright NuoDB, Inc. 2017-2018
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import os
import click
import requests
import json
import sys

from requests.auth import HTTPBasicAuth

# Dictionary key is used in Insights Server.
# Dictionary value is name used in domain or local file storage
subscription_fields = {
  u'subscriber_token': 'insights.sub.token',
  u'subscriber_dashboard_url': 'insights.sub.dashboard_url',
  u'subscriber_ingest_url': 'insights.sub.ingest_url',
  u'subscriber_id': 'insights.sub.id'
}

domain_session = None

def die(msg):
  print msg
  exit(1)

def get_domain_auth():
  auth = HTTPBasicAuth(os.environ['DOMAIN_USER'],
                       os.environ['DOMAIN_PASSWORD'])
  return auth

def get_domain_session():
  global domain_session
  if domain_session:
    return domain_session
  else:
    domain_session = requests.session()
    domain_session.auth = get_domain_auth()
    return domain_session

def check_env_var(env_var_name, check_dir=True):
  if env_var_name not in os.environ:
    die("Insights Error: Environment variable '%s' is not set." % env_var_name)
  env_var_value = os.environ[env_var_name]
  if check_dir and not os.path.isdir(env_var_value):
    die("Insights Error: Directory '%s' for environment variable '%s' " \
          "does not exist" % (env_var_value, env_var_name))

def check_environment():
  check_env_var('NUOCA_HOME')
  check_env_var('NUODB_HOME')
  check_env_var('NUODB_CFGDIR')
  check_env_var('NUODB_VARDIR')
  check_env_var('NUODB_LOGDIR')
  check_env_var('NUODB_RUNDIR')
  check_env_var('NUODB_INSIGHTS_SERVICE_API', check_dir=False)

def insights_tou_filepath():
  nuoca_home = os.environ['NUOCA_HOME']
  file_path = os.path.join(nuoca_home, 'etc', 'insights_tou.txt')
  return file_path

def display_insights_tou():
  with open(insights_tou_filepath()) as f:
    print f.read()

def ask_Y_N(question):
  # raw_input returns the empty string for "enter"
  yes = {'yes', 'y'}
  no = {'no', 'n'}
  while True:
    sys.stdout.write(question)
    choice = raw_input().lower()
    if choice in yes:
      return True
    elif choice in no:
      return False
    else:
      sys.stdout.write('Please answer Y or N.')

def accept_insights_tou():
  display_insights_tou()
  return ask_Y_N('Do you agree? Y or N: ')

def show_insights():
  filesystem_sub_info = read_stored_sub_info()
  domain_sub_info = get_domain_sub_info()
  if domain_sub_info:
    print "Domain:    %s" % str(domain_sub_info)
  else:
    print "Domain:     <empty>"
  if filesystem_sub_info:
    print "Filesystem: %s" % str(filesystem_sub_info)
  else:
    print "Filesystem: <empty>"

def check_subcription_response(sub_info):
  global subscription_fields
  for key in subscription_fields:
    if key not in sub_info:
      msg = "Insights Error: Malformed NuoDB Insights Service resposnse:\n%s" \
            % str(sub_info)
      die(msg)

def sub_filepath(file_name):
  nuodb_cfgdir = os.environ['NUODB_CFGDIR']
  file_path = os.path.join(nuodb_cfgdir, file_name)
  return file_path

def remove_file(file_path):
  try:
    print "removing: %s " % file_path
    os.remove(file_path)
  except:
    pass

def delete_stored_subscription_info():
  global subscription_fields
  for sub_value in subscription_fields.itervalues():
    remove_file(sub_filepath(sub_value))

def store_subscription_info(sub_info):
  global subscription_fields
  for sub_key in subscription_fields:
    filename = sub_filepath(subscription_fields[sub_key])
    with open(filename, 'w') as fp:
      fp.write(sub_info[sub_key] + "\n")

def read_stored_sub_info():
  global subscription_fields
  sub_info = {}
  try:
    for sub_key in subscription_fields:
      filename = sub_filepath(subscription_fields[sub_key])
      with open(filename, 'r') as fp:
        sub_info[sub_key] = fp.read().rstrip()
  except Exception, e:
    #print "Insights Error: reading stored sub info. %s" % str(e)
    return None
  return sub_info

def get_subscription(root_url=None, sub_id=None):
  try:
    sub_info = read_stored_sub_info()
    domain_info = get_domain_sub_info()
    if sub_info or domain_info:
      die("Insights Error: Insights is already enabled.")
  except Exception, e:
    die("Insights Error: Failed to obtain Insights subscription info: %s"
        % str(e))

  if not root_url:
    root_url = os.environ['NUODB_INSIGHTS_SERVICE_API']

  url = root_url + '/subscriber/'
  if sub_id:
    url += sub_id
  sub_info = None
  try:
    req = requests.get(url)
    sub_info = json.loads(req.text)
    check_subcription_response(sub_info)
  except Exception, e:
    die("Insights Error: Failed to reach NuoDB Insights Service "
        "Endpoint '%s'\n%s" % (url, str(e)))
  try:
    store_subscription_info(sub_info)
  except Exception, e:
    try:
      delete_stored_subscription_info()
    finally:
      die("Insights Error: Failed to store subscription info")
  return sub_info

def get_domain_config_value(key):
  url_base = 'http://localhost:8888/api/2/domain/config'
  url = "{}/configuration%2F{}".format(url_base, key)
  headers = {'Accept': 'application/json',
             'Content-Type': 'application/json'}
  ret = None
  try:
    domain_session = get_domain_session()
    req = domain_session.get(url, headers=headers)
    response = json.loads(req.text)
    if 'value' in response:
      return response['value']
  except:
    pass
  return ret

def get_domain_sub_info():
  global subscription_fields
  ret = {}
  for key,value in subscription_fields.items():
    item_value = get_domain_config_value(value)
    if not item_value:
      return None
    ret[key] = item_value
  return ret

def post_domain_config_value(key, value):
  domain_session = get_domain_session()
  url = 'http://localhost:8888/api/2/domain/config'
  headers = {'Accept': 'application/json',
             'Content-Type': 'application/json'}
  ret = None
  try:
    data = {"key": key,
            "value": value }
    req = domain_session.post(url, data=json.dumps(data), headers=headers)
    ret = req.text
  finally:
    return ret

def store_domain_sub_info(sub_info):
  global subscription_fields
  for key,value in subscription_fields.items():
    post_domain_config_value(value, sub_info[key])

def clear_domain_sub_info():
  global subscription_fields
  for sub_store_name in subscription_fields.itervalues():
    post_domain_config_value(sub_store_name, "")


@click.group()
@click.pass_context
def cli(ctx):
  pass

@click.command(short_help="Enable Insights")
@click.option('--subscriber-id', default=None,
              help='Subscriber ID')
@click.option('--accept-tou', default=None, is_flag=True,
              help='Accept Terms Of Use Agreement')
@click.option('--root-url', default=None,
              help='Root URL for Insights Server')
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.pass_context
def enable(ctx, subscriber_id, accept_tou, root_url, verbose):
  if not accept_tou:
    if not accept_insights_tou():
      sys.exit(1)
  sub_info = get_subscription(root_url, subscriber_id)
  print("Insights Subscriber ID: %s" % sub_info['subscriber_id'])
  print()
  print("NuoDB Insights is now enabled. To access your personalized dashboard, visit: %s"
        % sub_info['subscriber_dashboard_url'])


@click.command(short_help="Disable Insights")
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.pass_context
def disable(ctx, verbose):
  clear_domain_sub_info()
  delete_stored_subscription_info()
  print("Insights Disabled")

@click.command(short_help="Show Insights")
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.pass_context
def show(ctx, verbose):
  show_insights()

@click.command(short_help="Startup Insights")
@click.pass_context
def startup(ctx):
  filesystem_sub_info = None
  domain_sub_info = get_domain_sub_info()
  if not domain_sub_info:
    filesystem_sub_info = read_stored_sub_info()
    if not filesystem_sub_info:
      print "Skip"
      return
    store_domain_sub_info(filesystem_sub_info)
  filesystem_sub_info = read_stored_sub_info()
  if not filesystem_sub_info:
    store_subscription_info(domain_sub_info)
  print "Startup"

cli.add_command(enable)
cli.add_command(disable)
cli.add_command(show)
cli.add_command(startup)

# Customers do not call this directly.
if __name__ == '__main__':
  cli()

