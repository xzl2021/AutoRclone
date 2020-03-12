from __future__ import print_function
from google.oauth2.service_account import Credentials
import googleapiclient.discovery, json, progress.bar, glob, sys, argparse, time
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth import exceptions as auth_exceptions
import os, pickle


def _batch_callback(id,resp,exception):
    if exception is None:
        print(resp)
        time.sleep(0.1)
        return
    if str(exception).startswith('<HttpError 429'):
        time.sleep(1)
        return
    print(str(exception))
    exit(1)

def _start_authorization(credentials_file, token_file):
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes=[
            'https://www.googleapis.com/auth/drive',
        ])
    # creds = flow.run_local_server(port=0)
    creds = flow.run_console()
    # Save the credentials for the next run
    with open(token_file, 'wb') as fwb:
        pickle.dump(creds, fwb)
    return creds


def main(args={}):
    drive_id = args.drive_id
    credentials_file = glob.glob(args.credentials)[0]
    token_file = glob.glob(args.token)[0]

    try:
        open(credentials_file, 'r')
        print('>> Found credentials.')
    except IndexError:
        print('>> No credentials found.')
        sys.exit(1)

    # if not args.yes:
    #     # input('Make sure the following client id is added to the shared drive as Manager:\n' + json.loads((open(
    #     # credentials[0],'r').read()))['installed']['client_id'])
    #     

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

    drive = googleapiclient.discovery.build("drive", "v3", credentials=creds)
    batch = drive.new_batch_http_request(callback=_batch_callback)

    if args.list_permissions:
        respond = {
            "nextPageToken": None
        }
        # respond = drive.permissions().list(fileId=drive_id, supportsAllDrives=True).execute()
        permissions = []
        while "nextPageToken" in respond:
            respond = drive.permissions().list(fileId=drive_id, pageToken=respond["nextPageToken"], supportsAllDrives=True).execute()
            permissions.extend(respond["permissions"])
        for permission in permissions:
            for k,v in permission.items():
                print("\"" + str(k) + "\": \"" + str(v) + "\"")
            print("")
        print("Total: " + str(len(permissions)))
        return

    if args.delete_permissions:
        permission_ids = []
        input(
                ">> Total " + str(len(permission_ids)) + " permissions to delete.\n" +
                ">> Are you for sure?\n" + 
                "(Press ANY key to continue)"
            )
        # ['02141601424200628116', '02482054663463184183', '03458301049368687699', '05472616075107853203', '06179172643197434308', '06838779262513544058', '08254740790703609454']
        for permission_id in permission_ids:
            batch.add(drive.permissions().delete(fileId=drive_id, permissionId=permission_id, supportsAllDrives=True))
        batch.execute()
        return

    if args.add_permissions:
        input(
                '>> Make sure **service accounts** .json files put in the \n' +
                '>> ' + args.path + '\n' +
                '(Press any key to continue)'
            )
        sa_files = glob.glob(args.path + '/*.json')
        # pbar = progress.bar.Bar("Readying accounts", max=len(accounts))
        for i in sa_files:
            ce = json.loads(open(i, 'rt').read())['client_email']
            print(ce)
            batch.add(drive.permissions().create(fileId=drive_id, supportsAllDrives=True, body={
                "role": "fileOrganizer",
                "type": "user",
                "emailAddress": ce
            }))
            # pbar.next()
        # pbar.finish()
        print('Adding...')
        batch.execute()
        print('Complete.')
        return


if __name__ == "__main__":
    stt = time.time()
    parse = argparse.ArgumentParser(description='A tool to add service accounts to a shared drive from a folder containing credential files.')
    parse.add_argument('--path', '-p', default=sys.path[0]+'/accounts', help='Specify an alternative path to the service accounts folder.')
    parse.add_argument('--token', default=sys.path[0]+'/credentials/token.pickle', metavar='/path/to/token', help='Specify the pickle token file path.')
    parse.add_argument('--credentials', '-c', default=sys.path[0]+'/credentials/credentials.json', help='Specify the relative path for the credentials file.')
    parse.add_argument('--yes', '-y', default=False, action='store_true', help='Skips the sanity prompt.')
    parse.add_argument('--list-permissions', default=False, action="store_true", help='List permissions of the Shared Drive.')
    parse.add_argument('--delete-permissions', default=False, action="store_true", help='List permissions of the Shared Drive.')
    parse.add_argument('--add-permissions', default=False, action="store_true", help='List permissions of the Shared Drive.')
    parsereq = parse.add_argument_group('required arguments')
    parsereq.add_argument('--drive-id', '-id', help='The ID of the Shared Drive.', required=True)
    args = parse.parse_args()

    main(args=args)

    hours, rem = divmod((time.time() - stt), 3600)
    minutes, sec = divmod(rem, 60)
    print("Elapsed Time:\n{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), sec))
    exit(0)
