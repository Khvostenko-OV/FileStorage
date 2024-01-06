from datetime import timedelta

from django.http import JsonResponse, HttpResponse

from back.settings import logger, OK_200, FILE_404, ERROR_SOME
from back.utils import auth_required, allowed_methods, parse_body, valid_filename
from storage.models import StoredFile, Link


@auth_required
@allowed_methods("GET")
def file_list(request):
    """  GET - List of files in current user's storage """

    return JsonResponse(
        {
            "ok": 200,
            "user": request.user.serializer,
            "files": [f.serializer for f in request.user.files.all()],
        })


@auth_required
@allowed_methods("GET", "PATCH", "DELETE")
def file_get_change_del(request, pk: int):
    """
        url param pk: pk of stored file
        GET - get file info
        PATCH - change file name and description
        DELETE - delete file
    """

    if request.user.is_superuser:
        file = StoredFile.objects.filter(pk=pk).first()
    else:
        file = request.user.files.filter(pk=pk).first()
    if not file:
        return JsonResponse(FILE_404)

#  Get file info
    if request.method == "GET":
        return JsonResponse({"ok": 200, "file": file.serializer})

#  Change filename and description
    if request.method == "PATCH":

        data = parse_body(request)
        err = file.rename(data.get("filename", file.name))
        if err:
            logger.error(f"User: {request.user} | Action: rename file {file.pk}: {file.name} | {err}")
            return JsonResponse({"error": 400, "error_msg": err})

        file.description = data.get("description", file.description)[:511]
        file.save()
        logger.info(f"User: {request.user} | Action: change file {file.pk}: {file.name}")
        return JsonResponse({"ok": 200, "file": file.serializer})

#  Delete file
    if request.method == "DELETE":
        pk = file.pk
        filename = file.name
        file.file.delete()
        file.delete()
        logger.info(f"User: {request.user} | Action: delete file {pk}: {filename}")
        return JsonResponse(OK_200)

    return JsonResponse(ERROR_SOME)


@auth_required
@allowed_methods("POST")
def file_upload(request):
    """
        POST - Upload file to FileStorage
        body params:
            force - Force to rewrite existing file
    """

    if "file" in request.FILES:
        file = request.FILES["file"]

        if not valid_filename(file.name):
            logger.error(f"User: {request.user} | Action: upload file {file.name} | Invalid filename!")
            return JsonResponse({"error": 400, "error_msg": f"Invalid filename - '{file.name}'"})

        description = request.POST.get("description", "")[:511]
        exist = request.user.files.filter(name=file.name).first()
        if exist:
            if request.POST.get("force"):
                exist.file.delete()
                Link.objects.filter(to_file=exist).delete()
                exist.file = file
                exist.description = description or exist.description
                exist.downloads = 0
                exist.save()
                logger.info(f"User: {request.user}. Action: overwrite file {exist.pk}: {exist.name}")
                return JsonResponse({"ok": 200, "file": exist.serializer})
            logger.error(f"User: {request.user} | Action: upload file {file.name} | File already exists!")
            return JsonResponse({"error": 400, "error_msg": f"File '{file.name}' already exists!"})

        new = StoredFile.objects.create(name=file.name, owner=request.user, file=file, description=description)
        logger.info(f"User: {request.user}. Action: upload file {new.pk}: {new.name}")
        return JsonResponse({"ok": 201, "file": new.serializer})

    return JsonResponse(OK_200)


@auth_required
@allowed_methods("GET")
def file_download(request, pk: int):
    """
        url param pk: pk of stored file
        GET - download file
    """

    if request.user.is_superuser:
        file = StoredFile.objects.filter(pk=pk).first()
    else:
        file = request.user.files.filter(pk=pk).first()
    if not file or not file.exists:
        return HttpResponse("<h1>File not found!</h1>")

    with open(file.file.path, 'rb') as f:
        response = HttpResponse(f.read())
        response["Content-Type"] = "application/octet-stream"
        response["Content-Disposition"] = f"attachment; filename='{file.name}'"
        file.downloads += 1
        file.save()
        logger.info(f"User: {request.user}. Action: download file {file.pk}: {file.name}")
        return response


@auth_required
@allowed_methods("POST")
def link_create(request):
    """
        POST - create link for file downloading
        body params:
            file_id - pk of stored file
            duration - link's lifetime in minutes
    """

    data = parse_body(request)
    pk = data.get("file_id")
    if not isinstance(pk, int):
        logger.error(f"User: {request.user} | Action: create download link to file {pk} | Invalid file id!")
        return JsonResponse({"error": 400, "error_msg": "Invalid file id"})

    file = request.user.files.filter(pk=pk).first()
    if not file or not file.exists:
        logger.error(f"User: {request.user} | Action: create download link to file {pk} | File not found!")
        return JsonResponse(FILE_404)

    link = Link.objects.create(to_file=file)
    delta = data.get("duration")
    if isinstance(delta, int) and delta > 0:
        link.expire_at = link.created_at + timedelta(minutes=delta)
        link.save()
    logger.info(f"User: {request.user}. Action: create download link to file {file.pk}: {file.name}")
    return JsonResponse({"ok": 201, "link": link.serializer})


@allowed_methods("GET")
def link_download(request):
    """
        GET - download file via link
        query params:
            link - link to stored file
    """

    href = request.GET.get("link", "")
    link = Link.objects.filter(href=href).first()
    if not link:
        logger.error(f"Action: download file via link '{href}' | Invalid Link!")
        return HttpResponse("<h1>Invalid Link!</h1>")

    if link.expired:
        logger.error(f"Action: download file via link '{href}' | Link has expired!")
        return HttpResponse("<h1>Link has expired!</h1>")

    if not link.to_file.exists:
        logger.error(
            f"Action: download file {link.to_file.pk}: {link.to_file.dir}/{link.to_file.name} via link | File not found!")
        return HttpResponse("<h1>File not found!</h1>")

    with open(link.to_file.file.path, 'rb') as f:
        response = HttpResponse(f.read())
        response["Content-Type"] = "application/octet-stream"
        response["Content-Disposition"] = f"attachment; filename='{link.to_file.name}'"
        link.to_file.downloads += 1
        link.to_file.save()
        logger.info(f"Action: download file {link.to_file.pk}: {link.to_file.dir}/{link.to_file.name} via link")
        return response
