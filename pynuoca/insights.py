# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import os
import click
import requests
import json
import sys

from requests.auth import HTTPBasicAuth

try:
    from pynuoadmin import nuodb_mgmt
except ImportError:
    import nuodb_mgmt

# Allow calls the localhost Admin API without server verification.
# https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
import urllib3

urllib3.disable_warnings()

# Dictionary key is used in Insights Server.
# Dictionary value is name used in domain or local file storage
subscription_fields = {
    u'subscriber_token': 'insights.sub.token',
    u'subscriber_dashboard_url': 'insights.sub.dashboard_url',
    u'subscriber_ingest_url': 'insights.sub.ingest_url',
    u'subscriber_id': 'insights.sub.id'
}

legacy_domain_session = None
admin_layer = None


def die(msg):
    print msg
    try:
        insights_log_path = os.path.join(os.environ['NUODB_LOGDIR'],
                                         'insights.log')
        insights_log_fp = open(insights_log_path, "a")
        insights_log_fp.write(msg + '\n')
        insights_log_fp.close()
    except:
        pass
    exit(1)


def get_legacy_domain_auth():
    auth = HTTPBasicAuth(os.environ['DOMAIN_USER'].strip(),
                         os.environ['DOMAIN_PASSWORD'].strip())
    return auth


def get_legacy_domain_session():
    global legacy_domain_session
    if legacy_domain_session:
        return legacy_domain_session
    else:
        legacy_domain_session = requests.session()
        legacy_domain_session.auth = get_legacy_domain_auth()
        return legacy_domain_session


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


def show_insights(admin_layer):
    print "Admin layer: " + admin_layer
    filesystem_sub_info = read_stored_sub_info()
    domain_sub_info = get_domain_sub_info(admin_layer)
    if domain_sub_info:
        print "Domain:    %s" % str(domain_sub_info)
    else:
        print "Domain:     <empty>"
    if filesystem_sub_info:
        print "Filesystem: %s" % str(filesystem_sub_info)
    else:
        print "Filesystem: <empty>"


def check_subscription_response(sub_info):
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
    except Exception as e:
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
    except Exception as e:
        # print "Insights Error: reading stored sub info. %s" % str(e)
        return None
    return sub_info


def get_subscription(root_url=None, sub_id=None):
    admin_layer = what_admin_layer()
    if not admin_layer:
        die("ERROR: Cannot find Admin Layer")
    try:
        sub_info = read_stored_sub_info()
        domain_info = get_domain_sub_info(admin_layer)
        if sub_info or domain_info:
            die("Insights Error: Insights is already enabled.")
    except Exception as e:
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
        check_subscription_response(sub_info)
    except Exception as e:
        die("Insights Error: Failed to reach NuoDB Insights Service "
            "Endpoint '%s'\n%s" % (url, str(e)))
    try:
        store_subscription_info(sub_info)
        if admin_layer == "legacy":
            post_legacy_domain_config_value("disable_insights", "")
        else:
            store_nuoadmin_domain_config_value("disable_insights", "")
    except Exception as e:
        try:
            delete_stored_subscription_info()
        finally:
            die("Insights Error: Failed to store subscription info")
    return sub_info


def get_legacy_domain_config_value(key):
    url_base = 'http://localhost:8888/api/2/domain/config'
    url = "{}/configuration%2F{}".format(url_base, key)
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json'}
    ret = None
    try:
        legacy_domain_session = get_legacy_domain_session()
        req = legacy_domain_session.get(url, headers=headers)
        response = json.loads(req.text)
        if 'value' in response:
            return response['value']
    except Exception as e:
        pass
    return ret


def get_nuoadmin_domain_config_value(key):
    ret = None
    try:
        conn = _find_nuoadmin_conn()
        ret = conn.get_value(key)
    except Exception as e:
        pass
    return ret


def get_domain_sub_info(admin_layer):
    global subscription_fields
    ret = {}
    for key, value in subscription_fields.items():
        if admin_layer == "legacy":
            item_value = get_legacy_domain_config_value(value)
        else:
            item_value = get_nuoadmin_domain_config_value(value)
        if not item_value:
            return None
        ret[key] = item_value
    return ret


def store_nuoadmin_domain_config_value(key, value):
    ret = None
    try:
        conn = _find_nuoadmin_conn()
        ret = conn.set_value(key, value, conditional=False)
    except Exception as e:
        pass
    return ret


def post_legacy_domain_config_value(key, value):
    legacy_domain_session = get_legacy_domain_session()
    url = 'http://localhost:8888/api/2/domain/config'
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json'}
    ret = None
    try:
        data = {"key": key,
                "value": value}
        req = legacy_domain_session.post(url,
                                         data=json.dumps(data),
                                         headers=headers)
        ret = req.text
    finally:
        return ret


def store_domain_sub_info(sub_info):
    global subscription_fields
    admin_layer = what_admin_layer()
    if not admin_layer:
        print "ERROR: Cannot find Admin Layer"
        sys.exit(1)
    for key, value in subscription_fields.items():
        if admin_layer == "legacy":
            post_legacy_domain_config_value(value, sub_info[key])
        else:
            store_nuoadmin_domain_config_value(value, sub_info[key])


def clear_domain_sub_info():
    global subscription_fields
    admin_layer = what_admin_layer()
    if not admin_layer:
        print "ERROR: Cannot find Admin Layer"
        sys.exit(1)
    for sub_store_name in subscription_fields.itervalues():
        if admin_layer == "legacy":
            post_legacy_domain_config_value(sub_store_name, "")
        else:
            store_nuoadmin_domain_config_value(sub_store_name, "")
    if admin_layer == "legacy":
        post_legacy_domain_config_value("disable_insights", True)
    else:
        store_nuoadmin_domain_config_value("disable_insights", True)


def _find_nuoadmin_conn():
    nuoadmin_ssl_url_base = "https://localhost:8888"
    nuoadmin_nonssl_url_base = "http://localhost:8888"
    default_client_key = None
    default_server_cert = None
    conn = None
    test_client_key = None
    test_url_base = None
    conn_success = False

    # Try nuoadmin ssl first.
    try:
        test_client_key = os.environ['NUODB_INSIGHTS_KEY']
    except KeyError:
        test_client_key = default_client_key

    try:
        test_url_base = os.environ['NUOADMIN_API_SERVER_SSL']
    except Exception as e:
        test_url_base = nuoadmin_ssl_url_base

    try:
        conn = nuodb_mgmt.AdminConnection(test_url_base, test_client_key, False)
        admin_cfg = conn.get_admin_config()
        if admin_cfg and admin_cfg.properties:
            conn_success = True
    except Exception as e:
        conn = None
    if conn_success:
        return conn

    # Try nuoadmin non-ssl next.
    try:
        test_url_base = os.environ['NUOADMIN_API_SERVER_NONSSL']
    except Exception as e:
        test_url_base = nuoadmin_nonssl_url_base
    try:
        conn = nuodb_mgmt.AdminConnection(test_url_base, None, False)
        admin_cfg = conn.get_admin_config()
        if admin_cfg and admin_cfg.properties:
            conn_success = True
    except Exception as e:
        conn = None
    if conn_success:
        return conn

    return conn


def _find_legacy_admin():
    url = 'http://localhost:8888/api/2/domain/enforcer'
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json'}
    ret = None
    try:
        legacy_domain_session = get_legacy_domain_session()
        req = legacy_domain_session.get(url, headers=headers)
        response = json.loads(req.text)
        if 'domainEnforcerEnabled' in response:
            return response['domainEnforcerEnabled']
    except Exception as e:
        pass
    return ret


def startup_legacy_admin():
    check_if_insights_disabled = get_legacy_domain_config_value("disable_insights")
    filesystem_sub_info = None
    domain_sub_info = get_domain_sub_info("legacy")
    if not domain_sub_info:
        filesystem_sub_info = read_stored_sub_info()
        if not filesystem_sub_info:
            print "Skip"
            return
        if not check_if_insights_disabled:
            store_domain_sub_info(filesystem_sub_info)
    filesystem_sub_info = read_stored_sub_info()
    if not filesystem_sub_info:
        store_subscription_info(domain_sub_info)
    if check_if_insights_disabled:
        print "Disable"
    else:
        print "Startup"


def what_admin_layer():
    global admin_layer
    if admin_layer:
        return admin_layer
    if _find_nuoadmin_conn():
        admin_layer = "nuoadmin"
        return admin_layer
    if _find_legacy_admin():
        admin_layer = "legacy"
        return admin_layer
    return admin_layer


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
    print('')
    print("NuoDB Insights is now enabled. To access your personalized dashboard, visit: %s"
          % sub_info['subscriber_dashboard_url'])


@click.command(short_help="Disable Insights")
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.pass_context
def disable(ctx, verbose):
    if not what_admin_layer():
        print "ERROR: Cannot find Admin Layer"
        sys.exit(1)
    clear_domain_sub_info()
    delete_stored_subscription_info()
    print("Insights Disabled")


@click.command(short_help="Show Insights")
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.pass_context
def show(ctx, verbose):
    admin_layer = what_admin_layer()
    if not admin_layer:
        print "ERROR: Cannot find Admin Layer"
        sys.exit(1)
    show_insights(admin_layer)


@click.command(short_help="Find Admin Connection")
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.pass_context
def find_nuoadmin_connection(ctx, verbose):
    conn = _find_nuoadmin_conn()
    if conn:
        print "Found Admin Connection: url_base=%s client_key=%s" % \
              (conn.url_base, conn.client_key)
    else:
        print "Unable to find a connection"


@click.command(short_help="Find Legacy Admin")
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.pass_context
def find_legacy_admin(ctx, verbose):
    result = _find_legacy_admin()
    if not result:
        print "Unable to find legacy Admin"
    else:
        print "Found legacy Admin"


@click.command(short_help="Startup Insights")
@click.pass_context
def startup(ctx):
    admin_layer = what_admin_layer()
    if not admin_layer:
        print "ERROR: Cannot find Admin Layer"
        sys.exit(1)
    if admin_layer == "legacy":
        check_if_insights_disabled = get_legacy_domain_config_value("disable_insights")
    else:
        check_if_insights_disabled = get_nuoadmin_domain_config_value("disable_insights")
    filesystem_sub_info = None
    domain_sub_info = get_domain_sub_info(admin_layer)
    if not domain_sub_info:
        filesystem_sub_info = read_stored_sub_info()
        if not filesystem_sub_info:
            print "Skip"
            return
        if not check_if_insights_disabled:
            store_domain_sub_info(filesystem_sub_info)
    filesystem_sub_info = read_stored_sub_info()
    if not filesystem_sub_info:
        store_subscription_info(domain_sub_info)
    if check_if_insights_disabled:
        print "Disable"
        return
    if admin_layer == "legacy":
        print "Startup"
    elif admin_layer == "nuoadmin":
        print "Startup nuoadmin"
    else:
        print "Skip"


cli.add_command(enable)
cli.add_command(disable)
cli.add_command(show)
cli.add_command(startup)
cli.add_command(find_nuoadmin_connection)
cli.add_command(find_legacy_admin)

# Customers do not call this directly.
if __name__ == '__main__':
    cli()
