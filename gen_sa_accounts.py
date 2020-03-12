# -*- coding:utf-8 -*-

from __future__ import print_function
import sys
import errno
import time
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from argparse import ArgumentParser
from base64 import b64decode
from random import choice
from json import loads
from glob import glob

SCOPES = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/cloud-platform','https://www.googleapis.com/auth/iam']
project_create_ops = []
sleep_time = 1

# Create count SAs in project
# def _create_accounts(service,project,count):
#     batch = service.new_batch_http_request(callback=_batch_callback)
#     for i in range(100, 200):
#         # aid = _generate_id('mfc-')
#         aid = 'rclone'
#         for j in range(3 - len(str(i))):
#             aid = aid + '0'
#         aid = aid + str(i)
#         batch.add(service.projects().serviceAccounts().create(name='projects/' + project, body={ 'accountId': aid, 'serviceAccount': { 'displayName': aid }}))
#     batch.execute()
#     exit(0)

# Create accounts needed to fill project
def _create_accounts(iam, project, num):
    print('Creating accounts in %s' % project)
    sa_count = len(_get_sas(iam, project))
    batch = iam.new_batch_http_request(callback=_batch_callback)
    for i in range(189, 289):
        aid = 'rclone'
        while (len(aid) + len(str(i))) < 9:
            aid = aid + '0'
        aid = aid + str(i)
        batch.add(iam.projects().serviceAccounts().create(name='projects/' + project, body={ 'accountId': aid, 'serviceAccount': { 'displayName': aid }}))
    batch.execute()
    exit(0)

# Generate a random id
def _generate_id(prefix='saf-'):
    chars = '-abcdefghijklmnopqrstuvwxyz1234567890'
    return prefix + ''.join(choice(chars) for _ in range(25)) + choice(chars[1:])

# List projects using service
def _get_projects(cloud):
    return [i['projectId'] for i in cloud.projects().list().execute()['projects']]

# Default batch callback handler
def _batch_callback(id,resp,exception):
    if exception is None:
        print(resp)
        return
    if str(exception).startswith('<HttpError 429'):
        time.sleep(sleep_time)
        return
    else:
        print(str(exception))
        return

# Project Creation Batch Handler
# def _pc_resp(id,resp,exception):
#     global project_create_ops
#     if exception is not None:
#         print(str(exception))
#     else:
#         for i in resp.values():
#             project_create_ops.append(i)

# Project Creation
# def _create_projects(cloud,count):
#     global project_create_ops
#     batch = cloud.new_batch_http_request(callback=_pc_resp)
#     new_projs = []
#     for i in range(count):
#         new_proj = _generate_id()
#         new_projs.append(new_proj)
#         batch.add(cloud.projects().create(body={'project_id':new_proj}))
#     batch.execute()

#     for i in project_create_ops:
#         while True:
#             resp = cloud.operations().get(name=i).execute()
#             if 'done' in resp and resp['done']:
#                 break
#             time.sleep(3)
#     return new_projs

# Enable services ste for projects in projects
# def _enable_services(service,projects,ste):
#     batch = service.new_batch_http_request(callback=_batch_callback)
#     for i in projects:
#         for j in ste:
#             batch.add(service.services().enable(name='projects/%s/services/%s' % (i,j)))
#     batch.execute()

# List SAs in project
def _get_sas(iam, project):
    resp = iam.projects().serviceAccounts().list(name='projects/' + project, pageSize=100).execute()
    if 'accounts' in resp:
        return resp['accounts']
    else:
        return []
    
# Create Keys Batch Handler
def _download_sa_keys_callback(id,resp,exception):
    if exception is None:
        filename = resp['name'][resp['name'].rfind('/'):]
        file_content = b64decode(resp['privateKeyData']).decode('utf-8')
        with open(args.path + '/' + filename + '.json', 'w+') as fw:
            fw.write(file_content)
            fw.close()
        return
    else:
        print(str(exception))
        print("Download abort.")
        exit(1)
        
# Create Keys
def _download_sa_keys(iam, project, path):
    print("Start downloading..")
    batch = iam.new_batch_http_request(callback=_download_sa_keys_callback)
    saids = []
    for said in saids:
        batch.add(iam.projects().serviceAccounts().keys().create(
            name='projects/' + project + '/serviceAccounts/' + said,
            body={
                'privateKeyType':'TYPE_GOOGLE_CREDENTIALS_FILE',
                'keyAlgorithm':'KEY_ALG_RSA_2048'
            }
        ))
    batch.execute()
    exit(0)

# Delete Service Accounts
def _delete_sas(iam,project):
    sas = _get_sas(iam, project)
    batch = iam.new_batch_http_request(callback=_batch_callback)
    for i in sas:
        batch.add(iam.projects().serviceAccounts().delete(name=i['name']))
    batch.execute()

def serviceaccountfactory(credentials='',
                          token='',
                          path='',
                          list_projects=False,
                          list_sas=False,
                        #   create_projects=None,
                        #   max_projects=12,
                        #   enable_services=None,
                          services=['iam','drive'],
                          create_sas=False,
                          delete_sas=False,
                          download_keys=False):
    default_project = loads(open(credentials,'r').read())['installed']['project_id']
    if not os.path.exists(token):
        flow = InstalledAppFlow.from_client_secrets_file(credentials, SCOPES)
        creds = flow.run_console()
        with open(token, 'wb') as fwb:
            pickle.dump(creds, fwb)
    else:
        with open(token, 'rb') as frb:
            creds = pickle.load(frb)
            frb.close()
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

    cloud = build('cloudresourcemanager', 'v1', credentials=creds)
    iam = build('iam', 'v1', credentials=creds)
    # serviceusage = build('serviceusage','v1',credentials=creds)

    
    if list_projects:
        while True:
            try:
                projects = _get_projects(cloud)
            except HttpError as e:
                print(e._get_reason())
                input('Press Enter to retry.')
            else:
                break
        project_index = 0
        for project in projects:
            project_index += 1
            print('[' + str(project_index) + '] ' + project)
        exit(0)


    if list_sas:
        project = list_sas
        sas = _get_sas(iam, project)
        sas_index = 0
        for sa in sas:
            sas_index += 1
            print('[' + str(sas_index) + '] ' + sa['email'] + '\t' + sa['uniqueId'])
        exit(0)


    # if create_projects:
    #     print("creat projects: {}".format(create_projects))
    #     if create_projects > 0:
    #         current_count = len(_get_projects(cloud))
    #         if current_count + create_projects <= max_projects:
    #             print('Creating %d projects' % (create_projects))
    #             nprjs = _create_projects(cloud, create_projects)
    #             selected_projects = nprjs
    #         else:
    #             sys.exit('No, you cannot create %d new project (s).\n'
    #                   'Please reduce value of --quick-setup.\n'
    #                   'Remember that you can totally create %d projects (%d already).\n'
    #                   'Please do not delete existing projects unless you know what you are doing' % (create_projects, max_projects, current_count))
    #     else:
    #         print('Will overwrite all service accounts in existing projects.\n'
    #               'So make sure you have some projects already.')
    #         input("Press Enter to continue...")

    # if enable_services:
    #     ste = []
    #     ste.append(enable_services)
    #     if enable_services == '~':
    #         ste = selected_projects
    #     elif enable_services == '*':
    #         ste = _get_projects(cloud)
    #     services = [i + '.googleapis.com' for i in services]
    #     print('Enabling services')
    #     _enable_services(serviceusage,ste,services)


    if create_sas:
        project = create_sas
        _create_accounts(iam, project, 1)
        exit(0)

    if download_keys:
        try:
            os.mkdir(path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        project = download_keys
        # std = []
        # std.append(download_keys)
        # if download_keys == '~':
        #     std = selected_projects
        # elif download_keys == '*':
        #     std = _get_projects(cloud)
        _download_sa_keys(iam, project, path)
    # if delete_sas:
    #     std = []
    #     std.append(delete_sas)
    #     if delete_sas == '~':
    #         std = selected_projects
    #     elif delete_sas == '*':
    #         std = _get_projects(cloud)
    #     for i in std:
    #         print('Deleting service accounts in %s' % i)
    #         _delete_sas(iam,i)

if __name__ == '__main__':
    parse = ArgumentParser(description='A tool to create Google service accounts.')
    parse.add_argument('--path', '-p', default=sys.path[0]+'/accounts', metavar='/path/to/save/folder', help='Specify an alternate directory to output the credential files.')
    parse.add_argument('--token', default=sys.path[0]+'/credentials/token.pickle', metavar='/path/to/token', help='Specify the pickle token file path.')
    parse.add_argument('--credentials', default=sys.path[0]+'/credentials/credentials.json', metavar='/path/to/credentials', help='Specify the credentials file path.')
    parse.add_argument('--list-projects', default=False, action='store_true', help='List projects viewable by the user.')
    parse.add_argument('--list-sas', default=None, metavar='<project_name>', help='List service accounts in a project.')
    # parse.add_argument('--create-projects', type=int, default=None, help='Creates up to N projects.')
    # parse.add_argument('--max-projects', type=int, default=12, help='Max amount of project allowed. Default: 12')
    # parse.add_argument('--enable-services', default=None, help='Enables services on the project. Default: IAM and Drive')
    parse.add_argument('--services', nargs='+', default=['iam', 'drive'], help='Specify a different set of services to enable. Overrides the default.')
    parse.add_argument('--create-sas', default=None, metavar='<project_name>', help='Create service accounts in a project.')
    parse.add_argument('--delete-sas', default=None, metavar='<project_name>', help='Delete service accounts in a project.')
    parse.add_argument('--download-keys', default=None, metavar='<project_name>', help='Download keys for all the service accounts in a project.')
    parse.add_argument('--quick-setup', default=None, type=int, metavar='<1|2|3>', help='Create projects, enable services, create service accounts and download keys.')
    parse.add_argument('--new-only', default=False, action='store_true', help='Do not use exisiting projects.')
    args = parse.parse_args()
    # If credentials file is invalid, search for one.
    if not os.path.exists(args.credentials):
        print(
            'No credentials found. Please enable the Drive API in:\n' +
            'https://developers.google.com/drive/api/v3/quickstart/python\n' +
            'and save the json file as credentials.json'
        )
        exit(1)
    # if args.quick_setup:
    #     opt = '*'
    #     if args.new_only:
    #         opt = '~'
    #     args.services = ['iam','drive']
    #     args.create_projects = args.quick_setup
    #     args.enable_services = opt
    #     args.create_sas = opt
    #     args.download_keys = opt
    serviceaccountfactory(path=args.path,
                          token=args.token,
                          credentials=args.credentials,
                          list_projects=args.list_projects,
                          list_sas=args.list_sas,
                          # create_projects=args.create_projects,
                          # max_projects=args.max_projects,
                          create_sas=args.create_sas,
                          delete_sas=args.delete_sas,
                          # enable_services=args.enable_services,
                          services=args.services,
                          download_keys=args.download_keys)
    # if resp is not None:
    #     if args.list_projects:
    #         if resp:
    #             print('Projects (%d):' % len(resp))
    #             for i in resp:
    #                 print('  ' + i)
    #         else:
    #             print('No projects.')
    #     elif args.list_sas:
    #         if resp:
    #             print('Service accounts in %s (%d):' % (args.list_sas,len(resp)))
    #             for i in resp:
    #                 print('  %s (%s)' % (i['email'],i['uniqueId']))
    #         else:
    #             print('No service accounts.')
