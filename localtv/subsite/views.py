from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from localtv import models
from localtv.decorators import get_sitelocation


@get_sitelocation
def subsite_index(request, sitelocation=None):
    return render_to_response(
        'localtv/subsite/index.html',
        {'sitelocation': sitelocation,
         'request': request},
        context_instance=RequestContext(request))


@get_sitelocation
def view_video(request, video_id, sitelocation=None):
    video = get_object_or_404(models.Video, pk=video_id, site=sitelocation.site)

    return render_to_response(
        'localtv/subsite/view_video.html',
        {'sitelocation': sitelocation,
         'current_video': video},
        context_instance=RequestContext(request))
