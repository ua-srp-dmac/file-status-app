import json
import requests
import time
import os
from urllib.parse import urlencode, quote

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from app.models import CyVerseAccount
from app.helpers import format_size


def file_list(request):
    """ Returns the fastq files in the user's home directory (for now).
    TODO: Dynamically show files specific to the user's Group affiliations.
    """

    if request.user.is_authenticated:

        username = request.user.username
        path = request.GET.get('path', None)
        account = CyVerseAccount.objects.get(user__username=username)
        
        if not path:
            path = account.default_folder.path
        
        query_params = {
            "path": path,
            "limit": 100,
            "offset": 0,
        }

        try:
            url = "https://de.cyverse.org/terrain/secured/filesystem/paged-directory"
            auth_headers = {"Authorization": "Bearer " + account.api_token}
            r = requests.get(url, headers=auth_headers, params=query_params)
            r.raise_for_status()

            fileList = []

            # {
            #     'infoType': 'fastq',
            #     'path': '/iplant/home/michellito/ERR008015.fastq',
            #     'date-created': 1599070087000,
            #     'permission': 'own',
            #     'date-modified': 1599070087000,
            #     'file-size': 2394058,
            #     'badName': False,
            #     'isFavorite': False,
            #     'label': 'ERR008015.fastq',
            #     'id': '4139e402-ed47-11ea-9281-90e2ba675364'
            # }

            for item in r.json()['folders']:

                updated = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(item['date-modified']/1000.0))

                fileList.append({
                    "name": item['label'],
                    "last_updated": updated,
                    "type": "folder",
                    "path": item['path'],
                    "id": item['id']
                })
            
            for item in r.json()['files']:
                
                # only display .fastq or .fastq.gz files
                if (item['label'].endswith('.fastq') or item['label'].endswith('.fastq.gz')):
                    
                    updated = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(item['date-modified']/1000.0))
                    size = format_size(item['file-size'])

                    fileList.append({
                        "name": item['label'],
                        "last_updated": updated,
                        "size": size,
                        "type": "file",
                        "path": item['path'],
                        "id": item['id']
                    })
            
            response = {
                'fileList': fileList,
                'currentPath': path
            }

            return JsonResponse(response, safe=False)

        except Exception as e:
            pass

    return HttpResponse(status=400)


def get_user_folders(request):
    """ Returns the path the current user's default CyVerse folder.
    """

    if request.user.is_authenticated:

        username = request.user.username
        account = CyVerseAccount.objects.get(user__username=username)

        response = {
            'default_folder': account.default_folder.path,
        }

        return JsonResponse(response, safe=False)

    return HttpResponse(status=403)


def analysis_list(request):
    """ Returns the user's analyses and their statuses.
    """

    if request.user.is_authenticated:

        username = request.user.username

        query_params = {
            "filter": json.dumps([
                { "field": "app_name", "value": "demeter" }
            ]),
        }

        query_str = urlencode(query_params, encoding='utf-8', quote_via=quote)

        try:
            account = CyVerseAccount.objects.get(user__username=username)
            url = "https://de.cyverse.org/terrain/analyses?" + query_str
            auth_headers = {"Authorization": "Bearer " + account.api_token}
            r = requests.get(url, headers=auth_headers)
            r.raise_for_status()

            analysisList = []

            for item in r.json()['analyses']:
                
                start_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(float(item['startdate'])/1000.0))
                end_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(float(item['enddate'])/1000.0))
                
                analysisList.append({
                    "name": item['name'],
                    "app_name": item['app_name'],
                    "results_folder": item['resultfolderid'],
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": item['status']
                })

            return JsonResponse(analysisList, safe=False)

        except Exception as e:
            pass

    return HttpResponse(status=400)
    
            
@csrf_exempt
def file_transfer(request):
    """ Receives a POST request containing a ReadsPerGene.out.tab file generated
        by STAR and writes file to server.
    """

    if request.method == 'POST':

        rename = request.POST.get('rename', None)
        save_path = request.POST.get('path', None)
        transfer_file = request.FILES[rename]

        complete_path = os.path.join(settings.MEDIA_ROOT, save_path, 'Ares/Data')

        fs = FileSystemStorage(location=complete_path) 
        filename = fs.save(rename, transfer_file)
        file_url = fs.url(filename)

        return HttpResponse(transfer_file.size, content_type='text/plain', status=200)

    



