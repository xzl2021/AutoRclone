# auto rclone
# Add service accounts to groups for your organization
#
# Author Telegram https://t.me/CodyDoby
# Inbox  codyd@qq.com

from __future__ import print_function
from google.oauth2.service_account import Credentials
import googleapiclient.discovery, json, progress.bar, glob, sys, argparse, time
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth import exceptions as auth_exceptions
import os
import pickle


def _batch_callback(id,resp,exception):
    if exception is None:
        print(resp)
        return
    if str(exception).startswith('<HttpError 429'):
        time.sleep(1)
        return
    print(str(exception))
    exit(1)

def _start_authorization(credentials_file, token_file):
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes=[
            'https://www.googleapis.com/auth/admin.directory.group',
            'https://www.googleapis.com/auth/admin.directory.group.member'
        ])
    # creds = flow.run_local_server(port=0)
    creds = flow.run_console()
    # Save the credentials for the next run
    with open(token_file, 'wb') as fwb:
        pickle.dump(creds, fwb)
    return creds

def main(args={}):
    group_id = args.groupaddr
    credentials_file = glob.glob(args.credentials)
    token_file = glob.glob(args.token)

    try:
        open(credentials_file, 'r')
        print('>> Found credentials.')
    except IndexError:
        print('>> No credentials found.')
        sys.exit(1)
    
    if os.path.exists(token_file):
        print(">> Found token file.")
        with open(token_file, 'rb') as frb:
            creds = pickle.load(frb)
            frb.close()
        if not creds.valid or creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except auth_exceptions.RefreshError as e:
                if e.args[0] == "invalid_grant: Token has been expired or revoked.":
                    print(e.args[0] + "please proceed Authorization:")
                    creds = _start_authorization(credentials_file, token_file)
        print(">> Token scopes:")
        print(creds.scopes)
    else:
        print(">> No token file found, please proceed Authorization:")
        creds = _start_authorization(credentials_file, token_file)
    print("")


    group = googleapiclient.discovery.build("admin", "directory_v1", credentials=creds)
    batch = group.new_batch_http_request(callback=_batch_callback)

    input(
            '>> Make sure **service accounts** .json files put in the \n' +
            '>> ' + args.path + '\n' +
            '(Press any key to continue)'
        )
    sa_files = glob.glob('%s/*.json' % args.path)
    # pbar = progress.bar.Bar("Readying accounts", max=len(sa))
    for i in sa_files:
        ce = json.loads(open(i, 'r').read())['client_email']
        print(ce)
        body = {
            "email": ce, 
            "delivery_settings": "NONE",
            "role": "MEMBER"
            }
        batch.add(group.members().insert(groupKey=group_id, body=body))
        # pbar.next()
    # pbar.finish()
    print('Adding...')
    batch.execute()
    print('Complete.')
    return

if __name__ == "__main__":
    stt = time.time()
    parse = argparse.ArgumentParser(description='A tool to add service accounts to groups for your organization from a folder containing credential files.')
    parse.add_argument('--path', '-p', default=sys.path[0]+'/accounts', help='Specify an alternative path to the service accounts folder.')
    parse.add_argument('--credentials', '-c', default=sys.path[0]+'/credentials/credentials.json', help='Specify the path to the credentials.json file.')
    parse.add_argument('--token', '-t', default=sys.path[0]+'/credentials/token.pickle', help='Specify the path to the token.')
    parsereq = parse.add_argument_group('required arguments')
    # service-account@googlegroups.com
    parsereq.add_argument('--group-id', '-id', help='The address of groups for your organization.', required=True)
    args = parse.parse_args()

    main()

    hours, rem = divmod((time.time() - stt), 3600)
    minutes, sec = divmod(rem, 60)
    print("Elapsed Time:\n{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), sec))
